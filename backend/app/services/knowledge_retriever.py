import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Character, CharacterProfile, KnowledgeChunk
from app.services.knowledge_chunker import DOMAIN_KEYWORDS


RESTRICTED_QUERY_MARKERS = ("真相", "凶手", "秘密")
SCOPE_CHARACTER_BOUND = "character_bound"
SCOPE_FALLBACK_BY_CHARACTER_NAME = "fallback_by_character_name"
SCOPE_NONE = "none"
PROJECT_SCOPE_PROJECT_BOUND = "project_bound"
PROJECT_SCOPE_LEGACY_NO_PROJECT = "legacy_no_project"
PROJECT_SCOPE_NONE = "none"


@dataclass
class KnowledgeRetrievalResult:
    chunks: list[dict[str, str | int | bool]]
    retrieval_scope: str
    retrieval_project_scope: str
    project_id: str | None = None


def retrieve_knowledge_chunks(
    db: Session,
    *,
    character: Character,
    profile: CharacterProfile | None,
    query: str,
    limit: int = 5,
    project_id: str | None = None,
    spoiler_mode: str = "non_spoiler",
) -> list[dict[str, str | int | bool]]:
    return retrieve_knowledge(
        db,
        character=character,
        profile=profile,
        query=query,
        limit=limit,
        project_id=project_id,
        spoiler_mode=spoiler_mode,
    ).chunks


def retrieve_knowledge(
    db: Session,
    *,
    character: Character,
    profile: CharacterProfile | None,
    query: str,
    limit: int = 5,
    project_id: str | None = None,
    spoiler_mode: str = "non_spoiler",
) -> KnowledgeRetrievalResult:
    candidates, retrieval_scope, retrieval_project_scope, effective_project_id = select_candidates(
        db,
        character,
        project_id=project_id,
    )
    if not candidates:
        return KnowledgeRetrievalResult(
            chunks=[],
            retrieval_scope=SCOPE_NONE,
            retrieval_project_scope=retrieval_project_scope,
            project_id=effective_project_id,
        )

    query_terms = extract_query_terms(
        query,
        target_character_name=character.character_name,
        user_persona_name=character.user_persona_name,
    )
    allow_hidden = any(marker in query for marker in RESTRICTED_QUERY_MARKERS)

    scored: list[dict[str, str | int | bool]] = []
    for chunk in candidates:
        if not passes_spoiler_filter(chunk, spoiler_mode=spoiler_mode, allow_hidden_query=allow_hidden):
            continue
        restricted = chunk.visibility in {"hidden", "restricted"} or chunk.spoiler_level == "heavy"
        score = score_chunk(
            chunk,
            query_terms=query_terms,
            target_character_name=character.character_name,
            user_persona_name=character.user_persona_name,
        )
        if score <= 0:
            continue
        scored.append(
            {
                "chunk_id": chunk.chunk_id,
                "content_preview": chunk.content_preview,
                "content": chunk.content,
                "score": score,
                "visibility": chunk.visibility,
                "restricted": restricted,
                "retrieval_scope": retrieval_scope,
                "retrieval_project_scope": retrieval_project_scope,
                "project_id": effective_project_id or "",
                "_is_current_character_bound": (
                    chunk.character_id == character.character_id
                ),
            }
        )

    deduped = dedupe_scored_chunks(scored)
    sorted_chunks = sorted(
        deduped,
        key=lambda item: (
            bool(item["_is_current_character_bound"]),
            int(item["score"]),
        ),
        reverse=True,
    )[:limit]
    return KnowledgeRetrievalResult(
        chunks=[strip_internal_fields(chunk) for chunk in sorted_chunks],
        retrieval_scope=retrieval_scope,
        retrieval_project_scope=retrieval_project_scope,
        project_id=effective_project_id,
    )


def select_candidates(
    db: Session,
    character: Character,
    *,
    project_id: str | None = None,
) -> tuple[list[KnowledgeChunk], str, str, str | None]:
    effective_project_id = character.project_id or (
        project_id.strip() if project_id else None
    )
    if effective_project_id:
        user_filter = user_scoped_condition(character)
        character_bound_chunks = list(
            db.scalars(
                select(KnowledgeChunk)
                .where(
                    KnowledgeChunk.project_id == effective_project_id,
                    KnowledgeChunk.character_id == character.character_id,
                    user_filter,
                )
                .order_by(KnowledgeChunk.created_at.desc(), KnowledgeChunk.id.desc())
            )
        )
        if character_bound_chunks:
            return (
                character_bound_chunks,
                SCOPE_CHARACTER_BOUND,
                PROJECT_SCOPE_PROJECT_BOUND,
                effective_project_id,
            )

        fallback_chunks = list(
            db.scalars(
                select(KnowledgeChunk)
                .where(
                    KnowledgeChunk.project_id == effective_project_id,
                    KnowledgeChunk.character_id.is_(None),
                    KnowledgeChunk.target_character_name == character.character_name,
                    user_filter,
                )
                .order_by(KnowledgeChunk.created_at.desc(), KnowledgeChunk.id.desc())
            )
        )
        if fallback_chunks:
            return (
                fallback_chunks,
                SCOPE_FALLBACK_BY_CHARACTER_NAME,
                PROJECT_SCOPE_PROJECT_BOUND,
                effective_project_id,
            )
        return [], SCOPE_NONE, PROJECT_SCOPE_PROJECT_BOUND, effective_project_id

    character_bound_chunks = list(
        db.scalars(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.character_id == character.character_id, user_scoped_condition(character))
            .order_by(KnowledgeChunk.created_at.desc(), KnowledgeChunk.id.desc())
        )
    )
    if character_bound_chunks:
        return (
            character_bound_chunks,
            SCOPE_CHARACTER_BOUND,
            PROJECT_SCOPE_LEGACY_NO_PROJECT,
            None,
        )

    fallback_chunks = list(
        db.scalars(
            select(KnowledgeChunk)
            .where(
                KnowledgeChunk.character_id.is_(None),
                KnowledgeChunk.target_character_name == character.character_name,
                user_scoped_condition(character),
            )
            .order_by(KnowledgeChunk.created_at.desc(), KnowledgeChunk.id.desc())
        )
    )
    if fallback_chunks:
        return (
            fallback_chunks,
            SCOPE_FALLBACK_BY_CHARACTER_NAME,
            PROJECT_SCOPE_LEGACY_NO_PROJECT,
            None,
        )
    return [], SCOPE_NONE, PROJECT_SCOPE_NONE, None


def user_scoped_condition(character: Character):
    if character.user_id:
        return KnowledgeChunk.user_id == character.user_id
    return KnowledgeChunk.user_id.is_(None)


def dedupe_scored_chunks(
    scored_chunks: list[dict[str, str | int | bool]],
) -> list[dict[str, str | int | bool]]:
    deduped: dict[str, dict[str, str | int | bool]] = {}
    for chunk in scored_chunks:
        content_key = str(chunk["content"])
        existing = deduped.get(content_key)
        if not existing or should_replace_duplicate(chunk, existing):
            deduped[content_key] = chunk
    return list(deduped.values())


def should_replace_duplicate(
    candidate: dict[str, str | int | bool],
    existing: dict[str, str | int | bool],
) -> bool:
    candidate_bound = bool(candidate["_is_current_character_bound"])
    existing_bound = bool(existing["_is_current_character_bound"])
    if candidate_bound != existing_bound:
        return candidate_bound
    return int(candidate["score"]) > int(existing["score"])


def strip_internal_fields(
    chunk: dict[str, str | int | bool],
) -> dict[str, str | int | bool]:
    return {
        key: value
        for key, value in chunk.items()
        if not key.startswith("_")
    }


def extract_query_terms(
    query: str,
    *,
    target_character_name: str,
    user_persona_name: str,
) -> list[str]:
    terms: list[str] = []
    for candidate in (target_character_name, user_persona_name, *DOMAIN_KEYWORDS):
        if candidate and candidate in query and candidate not in terms:
            terms.append(candidate)
    terms.extend(
        token
        for token in re.findall(r"[\u4e00-\u9fff]{2,4}", query)
        if token not in terms
    )
    return terms


def score_chunk(
    chunk: KnowledgeChunk,
    *,
    query_terms: list[str],
    target_character_name: str,
    user_persona_name: str,
) -> int:
    keywords = {keyword for keyword in chunk.keywords.split(",") if keyword}
    score = 0
    for term in query_terms:
        if term in chunk.content:
            score += 2
        if term in keywords:
            score += 1
    if target_character_name and target_character_name in chunk.content:
        score += 1
    if user_persona_name and user_persona_name in chunk.content:
        score += 1
    return score


def passes_spoiler_filter(
    chunk: KnowledgeChunk,
    *,
    spoiler_mode: str,
    allow_hidden_query: bool,
) -> bool:
    mode = spoiler_mode or "non_spoiler"
    if mode == "full_spoiler":
        return True
    if chunk.spoiler_level == "heavy" or chunk.visibility in {"hidden", "restricted"}:
        return bool(allow_hidden_query and mode == "semi_spoiler")
    if mode == "semi_spoiler":
        return chunk.spoiler_level in {"none", "mild", ""}
    return chunk.spoiler_level in {"none", "mild", ""} and chunk.visibility not in {"hidden", "restricted"}
