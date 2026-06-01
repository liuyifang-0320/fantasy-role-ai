import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CharacterCandidate, ParsedDocument
from app.services.character_candidate_extractor import extract_character_candidates
from app.services.ids import next_prefixed_id


CANDIDATE_STATUSES = {"pending", "confirmed", "ignored", "generated", "rejected"}
JSON_LIST_FIELDS = {
    "aliases",
    "relationship_hints",
    "source_document_ids",
    "source_types",
    "evidence_spans",
    "source_documents",
    "evidence_json",
    "relationship_evidence",
    "merge_suggestions",
}


def dump_json_list(values: list[str] | str | None) -> str:
    if values is None:
        return "[]"
    if isinstance(values, str):
        split_values = [
            item.strip()
            for item in values.replace("\n", ",").split(",")
            if item.strip()
        ]
        return json.dumps(split_values, ensure_ascii=False)
    return json.dumps([str(value).strip() for value in values if str(value).strip()], ensure_ascii=False)


def parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [item.strip() for item in value.split(",") if item.strip()]
    return parsed if isinstance(parsed, list) else []


def normalize_status(status: str | None) -> str:
    value = (status or "pending").strip()
    return value if value in CANDIDATE_STATUSES else "pending"


def extract_candidates_for_project(
    db: Session,
    *,
    project_id: str,
    user_id: str | None = None,
) -> list[CharacterCandidate]:
    parsed_documents = list(
        db.scalars(
            select(ParsedDocument)
            .where(ParsedDocument.project_id == project_id)
            .order_by(ParsedDocument.created_at.asc(), ParsedDocument.id.asc())
        )
    )
    extracted = extract_character_candidates(project_id, parsed_documents)
    saved: list[CharacterCandidate] = []
    for candidate_data in extracted:
        candidate_data["user_id"] = user_id
        candidate = upsert_candidate(db, candidate_data)
        saved.append(candidate)
    return saved


def upsert_candidate(
    db: Session,
    candidate_data: dict[str, str | float | list[str]],
) -> CharacterCandidate:
    project_id = str(candidate_data["project_id"])
    name = str(candidate_data["name"]).strip()
    canonical_name = str(candidate_data.get("canonical_name") or name).strip()
    existing = db.scalar(
        select(CharacterCandidate).where(
            CharacterCandidate.project_id == project_id,
            CharacterCandidate.canonical_name == canonical_name,
        )
    )
    if not existing:
        existing = db.scalar(
            select(CharacterCandidate).where(
                CharacterCandidate.project_id == project_id,
                CharacterCandidate.name == name,
            )
        )
    if existing:
        if existing.candidate_status == "generated":
            return existing
        if existing.user_id is None and candidate_data.get("user_id"):
            existing.user_id = str(candidate_data.get("user_id"))
        existing.canonical_name = canonical_name or existing.canonical_name or existing.name
        existing.display_name = str(candidate_data.get("display_name") or existing.display_name or existing.name)
        existing.normalized_name = str(candidate_data.get("normalized_name") or existing.normalized_name or existing.canonical_name)
        existing.aliases = merge_json_lists(existing.aliases, candidate_data.get("aliases"))
        existing.candidate_type = str(candidate_data.get("candidate_type") or existing.candidate_type or "unknown")
        existing.source_types = merge_json_lists(existing.source_types, candidate_data.get("source_types"))
        existing.evidence_spans = merge_json_lists(existing.evidence_spans, candidate_data.get("evidence_spans"))
        existing.dialogue_count = max(existing.dialogue_count or 0, int(candidate_data.get("dialogue_count") or 0))
        existing.mention_count = max(existing.mention_count or 0, int(candidate_data.get("mention_count") or 0))
        existing.relationship_evidence = merge_json_lists(existing.relationship_evidence, candidate_data.get("relationship_evidence"))
        existing.identity_hint = str(candidate_data.get("identity_hint") or existing.identity_hint)
        existing.personality_hint = str(candidate_data.get("personality_hint") or existing.personality_hint)
        existing.relationship_hints = merge_json_lists(
            existing.relationship_hints,
            candidate_data.get("relationship_hints"),
        )
        existing.evidence = merge_evidence(
            existing.evidence,
            str(candidate_data.get("evidence") or ""),
        )
        existing.source_document_ids = merge_json_lists(
            existing.source_document_ids,
            candidate_data.get("source_document_ids"),
        )
        existing.source_documents = merge_json_lists(
            getattr(existing, "source_documents", "[]"),
            candidate_data.get("source_documents") or candidate_data.get("source_document_ids"),
        )
        existing.evidence_json = merge_json_lists(
            getattr(existing, "evidence_json", "[]"),
            candidate_data.get("evidence_json") or candidate_data.get("evidence_spans"),
        )
        existing.role_type = str(candidate_data.get("role_type") or existing.role_type or existing.candidate_type or "unknown")
        existing.extraction_method = str(candidate_data.get("extraction_method") or existing.extraction_method or "rule_fallback")
        existing.llm_confidence = max(float(existing.llm_confidence or 0.0), float(candidate_data.get("llm_confidence") or 0.0))
        existing.llm_reason = str(candidate_data.get("llm_reason") or existing.llm_reason or "")
        existing.llm_evidence = merge_evidence(
            existing.llm_evidence or "",
            str(candidate_data.get("llm_evidence") or ""),
        )
        existing.confidence = max(existing.confidence, float(candidate_data.get("confidence") or 0.0))
        existing.confidence_level = str(candidate_data.get("confidence_level") or existing.confidence_level or "low")
        existing.needs_human_review = bool(
            candidate_data.get("needs_human_review", existing.needs_human_review)
        )
        existing.rejected_reason = str(candidate_data.get("rejected_reason") or existing.rejected_reason or "")
        existing.merge_suggestions = merge_json_lists(existing.merge_suggestions, candidate_data.get("merge_suggestions"))
        existing.reviewer_provider = str(candidate_data.get("reviewer_provider") or existing.reviewer_provider or "")
        existing.reviewer_status = str(candidate_data.get("reviewer_status") or existing.reviewer_status or "")
        existing.reviewer_reason = str(candidate_data.get("reviewer_reason") or existing.reviewer_reason or "")
        existing.updated_at = datetime.utcnow()
        db.flush()
        return existing

    candidate = CharacterCandidate(
        candidate_id=next_prefixed_id(db, CharacterCandidate, "candidate"),
        user_id=str(candidate_data.get("user_id") or "") or None,
        project_id=project_id,
        name=name,
        canonical_name=canonical_name or name,
        display_name=str(candidate_data.get("display_name") or name),
        normalized_name=str(candidate_data.get("normalized_name") or canonical_name or name),
        aliases=dump_json_list(candidate_data.get("aliases")),
        candidate_type=str(candidate_data.get("candidate_type") or "unknown"),
        source_types=dump_json_list(candidate_data.get("source_types")),
        evidence_spans=dump_json_list(candidate_data.get("evidence_spans")),
        dialogue_count=int(candidate_data.get("dialogue_count") or 0),
        mention_count=int(candidate_data.get("mention_count") or 0),
        relationship_evidence=dump_json_list(candidate_data.get("relationship_evidence")),
        identity_hint=str(candidate_data.get("identity_hint") or ""),
        personality_hint=str(candidate_data.get("personality_hint") or ""),
        relationship_hints=dump_json_list(candidate_data.get("relationship_hints")),
        evidence=str(candidate_data.get("evidence") or "")[:500],
        source_document_ids=dump_json_list(candidate_data.get("source_document_ids")),
        source_documents=dump_json_list(candidate_data.get("source_documents") or candidate_data.get("source_document_ids")),
        evidence_json=dump_json_list(candidate_data.get("evidence_json") or candidate_data.get("evidence_spans")),
        role_type=str(candidate_data.get("role_type") or candidate_data.get("candidate_type") or "unknown"),
        extraction_method=str(candidate_data.get("extraction_method") or "rule_fallback"),
        llm_confidence=float(candidate_data.get("llm_confidence") or 0.0),
        llm_reason=str(candidate_data.get("llm_reason") or ""),
        llm_evidence=str(candidate_data.get("llm_evidence") or "")[:500],
        confidence=float(candidate_data.get("confidence") or 0.0),
        confidence_level=str(candidate_data.get("confidence_level") or "low"),
        needs_human_review=bool(candidate_data.get("needs_human_review", True)),
        rejected_reason=str(candidate_data.get("rejected_reason") or ""),
        merge_suggestions=dump_json_list(candidate_data.get("merge_suggestions")),
        reviewer_provider=str(candidate_data.get("reviewer_provider") or ""),
        reviewer_status=str(candidate_data.get("reviewer_status") or ""),
        reviewer_reason=str(candidate_data.get("reviewer_reason") or ""),
        candidate_status="pending",
    )
    db.add(candidate)
    db.flush()
    return candidate


def merge_json_lists(existing_value: str, new_value: list[str] | str | None) -> str:
    merged: list[str] = []
    for value in [*parse_json_list(existing_value), *parse_json_list(dump_json_list(new_value))]:
        if value not in merged:
            merged.append(value)
    return json.dumps(merged, ensure_ascii=False)


def merge_evidence(existing: str, new: str) -> str:
    parts = [part for part in [existing.strip(), new.strip()] if part]
    merged: list[str] = []
    for part in parts:
        if part not in merged:
            merged.append(part)
    return "；".join(merged)[:500]


def list_candidates(
    db: Session,
    *,
    project_id: str,
    status: str | None = None,
) -> list[CharacterCandidate]:
    statement = select(CharacterCandidate).where(CharacterCandidate.project_id == project_id)
    if status:
        statement = statement.where(CharacterCandidate.candidate_status == status)
    return list(
        db.scalars(
            statement.order_by(
                CharacterCandidate.candidate_status.asc(),
                CharacterCandidate.confidence.desc(),
                CharacterCandidate.updated_at.desc(),
                CharacterCandidate.id.desc(),
            )
        )
    )


def get_candidate(db: Session, candidate_id: str) -> CharacterCandidate | None:
    return db.scalar(
        select(CharacterCandidate).where(CharacterCandidate.candidate_id == candidate_id)
    )


def update_candidate(db: Session, candidate: CharacterCandidate, payload) -> CharacterCandidate:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if value is None:
            continue
        if field in JSON_LIST_FIELDS:
            setattr(candidate, field, dump_json_list(value))
            continue
        if field == "candidate_status":
            value = normalize_status(value)
        if field == "candidate_type" and value != "person" and candidate.candidate_status == "confirmed":
            candidate.candidate_status = "pending"
        if isinstance(value, str):
            value = value.strip()
        setattr(candidate, field, value)
    if candidate.display_name:
        candidate.name = candidate.display_name
    if not candidate.canonical_name:
        candidate.canonical_name = candidate.name
    if not candidate.normalized_name:
        candidate.normalized_name = candidate.canonical_name
    if (
        candidate.candidate_type == "person"
        and candidate.candidate_status == "confirmed"
        and candidate.confidence_level == "high"
        and not candidate.needs_human_review
    ):
        candidate.reviewer_provider = candidate.reviewer_provider or "manual"
        candidate.reviewer_status = "manual"
        candidate.reviewer_reason = candidate.reviewer_reason or "User confirmed this candidate as a playable character."
    candidate.updated_at = datetime.utcnow()
    db.flush()
    return candidate


def ignore_candidate(db: Session, candidate: CharacterCandidate) -> CharacterCandidate:
    candidate.candidate_status = "ignored"
    candidate.updated_at = datetime.utcnow()
    db.flush()
    return candidate


def mark_candidate_generated(db: Session, candidate: CharacterCandidate) -> CharacterCandidate:
    candidate.candidate_status = "generated"
    candidate.updated_at = datetime.utcnow()
    db.flush()
    return candidate


def can_generate_candidate(candidate: CharacterCandidate) -> tuple[bool, str]:
    if candidate.candidate_status == "generated":
        return False, "Candidate already generated"
    if candidate.candidate_status == "ignored":
        return False, "Candidate ignored"
    if candidate.candidate_status == "rejected":
        return False, "Candidate rejected"
    if candidate.candidate_type != "person":
        return False, f"Candidate type is {candidate.candidate_type}, not person"
    if candidate.candidate_status == "confirmed":
        return True, ""
    reviewer_status = candidate.reviewer_status or ""
    if candidate.needs_human_review:
        return False, "Candidate needs human confirmation before generation"
    if reviewer_status not in {"success", "rule_fallback", "manual"}:
        return False, "Candidate reviewer has not completed"
    if candidate.confidence_level == "high":
        return True, ""
    return False, "Candidate needs human confirmation before generation"


def candidate_generation_name(candidate: CharacterCandidate) -> str:
    return candidate.display_name or candidate.canonical_name or candidate.name
