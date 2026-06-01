from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CharacterCandidate, CharacterRelationship, ParsedDocument
from app.services.character_candidate_extractor import extract_character_candidates
from app.services.character_candidates import upsert_candidate
from app.services.character_relationship_extractor import extract_character_relationships
from app.services.character_relationships import upsert_relationship
from app.services.current_character_detector import detect_current_character
from app.services.script_chunker import build_script_chunks
from app.services.script_segmenter import build_script_segments
from app.services.script_text_cleaner import clean_script_text


def run_script_intelligence_pipeline(
    db: Session,
    *,
    project_id: str,
    current_user=None,
    parsed_document_ids: list[str] | None = None,
    options: dict | None = None,
) -> dict[str, object]:
    user_id = getattr(current_user, "user_id", None) if current_user else None
    documents = load_documents(db, project_id, parsed_document_ids, user_id=user_id)
    warnings: list[str] = []
    segments_created = 0
    chunks_created = 0
    candidates_created = 0
    candidates_updated = 0
    relationships_created = 0

    for document in documents:
        clean_result = clean_script_text(document.raw_text or "", document.filename)
        warnings.extend(str(item) for item in clean_result.get("warnings", []))
        clean_text = str(clean_result["clean_text"])
        current_detection = detect_current_character(document.filename, clean_text, [])
        current_name = str(current_detection.get("current_character_name") or "")
        segments = build_script_segments(
            db,
            document,
            clean_text=clean_text,
            current_character_name=current_name,
        )
        chunks = build_script_chunks(db, segments, character_scope=current_name)
        segments_created += len(segments)
        chunks_created += len(chunks)

    candidate_payloads = extract_character_candidates(project_id, documents)
    for payload in candidate_payloads:
        payload["user_id"] = user_id
        before = existing_candidate_count(db, project_id, str(payload.get("canonical_name") or payload.get("name")))
        upsert_candidate(db, payload)
        if before:
            candidates_updated += 1
        else:
            candidates_created += 1

    candidate_models = list(
        db.scalars(
            select(CharacterCandidate)
            .where(CharacterCandidate.project_id == project_id)
            .order_by(CharacterCandidate.id.asc())
        )
    )
    relationship_payloads = extract_character_relationships(
        project_id,
        documents,
        character_candidates=candidate_models,
    )
    for payload in relationship_payloads:
        payload["user_id"] = user_id
        upsert_relationship(db, payload)
        relationships_created += 1

    return {
        "project_id": project_id,
        "documents_processed": len(documents),
        "segments_created": segments_created,
        "chunks_created": chunks_created,
        "candidates_created": candidates_created,
        "candidates_updated": candidates_updated,
        "relationships_created": relationships_created,
        "warnings": warnings[:20],
    }


def load_documents(
    db: Session,
    project_id: str,
    parsed_document_ids: list[str] | None,
    *,
    user_id: str | None,
) -> list[ParsedDocument]:
    statement = select(ParsedDocument).where(ParsedDocument.project_id == project_id)
    if user_id:
        statement = statement.where(
            (ParsedDocument.user_id == user_id) | ParsedDocument.user_id.is_(None)
        )
    if parsed_document_ids:
        statement = statement.where(ParsedDocument.parsed_id.in_(parsed_document_ids))
    return list(
        db.scalars(statement.order_by(ParsedDocument.created_at.asc(), ParsedDocument.id.asc()))
    )


def existing_candidate_count(db: Session, project_id: str, canonical_name: str) -> int:
    if not canonical_name:
        return 0
    return len(
        list(
            db.scalars(
                select(CharacterCandidate.id).where(
                    CharacterCandidate.project_id == project_id,
                    (
                        (CharacterCandidate.canonical_name == canonical_name)
                        | (CharacterCandidate.name == canonical_name)
                    ),
                )
            )
        )
    )
