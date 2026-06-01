import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CharacterCandidate, CharacterRelationship, ParsedDocument
from app.services.character_relationship_extractor import (
    SYMMETRIC_RELATION_TYPES,
    extract_character_relationships,
    relationship_key,
)
from app.services.ids import next_prefixed_id


RELATIONSHIP_STATUSES = {"pending", "confirmed", "ignored"}


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
    return value if value in RELATIONSHIP_STATUSES else "pending"


def extract_relationships_for_project(
    db: Session,
    *,
    project_id: str,
    user_id: str | None = None,
) -> list[CharacterRelationship]:
    parsed_documents = list(
        db.scalars(
            select(ParsedDocument)
            .where(ParsedDocument.project_id == project_id)
            .order_by(ParsedDocument.created_at.asc(), ParsedDocument.id.asc())
        )
    )
    candidates = list(
        db.scalars(
            select(CharacterCandidate)
            .where(CharacterCandidate.project_id == project_id)
            .order_by(CharacterCandidate.id.asc())
        )
    )
    extracted = extract_character_relationships(
        project_id,
        parsed_documents,
        character_candidates=candidates,
    )
    saved: list[CharacterRelationship] = []
    for relationship_data in extracted:
        relationship_data["user_id"] = user_id
        saved.append(upsert_relationship(db, relationship_data))
    return saved


def upsert_relationship(
    db: Session,
    relationship_data: dict[str, str | float | list[str]],
) -> CharacterRelationship:
    project_id = str(relationship_data["project_id"])
    source = str(relationship_data["source_character_name"]).strip()
    target = str(relationship_data["target_character_name"]).strip()
    relation_type = str(relationship_data["relation_type"]).strip() or "未知"
    existing = find_existing_relationship(db, project_id, source, target, relation_type)
    if existing:
        if existing.relationship_status == "ignored":
            return existing
        if existing.user_id is None and relationship_data.get("user_id"):
            existing.user_id = str(relationship_data.get("user_id"))
        existing.relation_summary = (
            str(relationship_data.get("relation_summary") or existing.relation_summary)[:200]
        )
        existing.evidence = merge_evidence(
            existing.evidence,
            str(relationship_data.get("evidence") or ""),
        )
        existing.source_document_ids = merge_json_lists(
            existing.source_document_ids,
            relationship_data.get("source_document_ids"),
        )
        existing.is_explicit = bool(relationship_data.get("is_explicit", existing.is_explicit))
        existing.is_inferred = bool(relationship_data.get("is_inferred", existing.is_inferred))
        existing.evidence_summary = str(
            relationship_data.get("evidence_summary")
            or existing.evidence_summary
            or existing.evidence
        )[:500]
        existing.evidence_json = merge_json_lists(
            getattr(existing, "evidence_json", "[]"),
            relationship_data.get("evidence_json") or relationship_data.get("source_document_ids"),
        )
        existing.confidence_level = str(
            relationship_data.get("confidence_level") or existing.confidence_level or "medium"
        )
        existing.spoiler_level = str(
            relationship_data.get("spoiler_level") or existing.spoiler_level or "none"
        )
        existing.visibility = str(
            relationship_data.get("visibility") or existing.visibility or "public"
        )
        existing.needs_human_review = bool(
            relationship_data.get("needs_human_review", existing.needs_human_review)
        )
        existing.extraction_method = str(
            relationship_data.get("extraction_method") or existing.extraction_method or "rule_fallback"
        )
        existing.reviewer_provider = str(
            relationship_data.get("reviewer_provider") or existing.reviewer_provider or "rule"
        )
        existing.reviewer_status = str(
            relationship_data.get("reviewer_status") or existing.reviewer_status or "rule_fallback"
        )
        existing.confidence = max(
            existing.confidence,
            float(relationship_data.get("confidence") or 0.0),
        )
        existing.updated_at = datetime.utcnow()
        db.flush()
        return existing

    relationship = CharacterRelationship(
        relationship_id=next_prefixed_id(db, CharacterRelationship, "rel"),
        user_id=str(relationship_data.get("user_id") or "") or None,
        project_id=project_id,
        source_character_name=source,
        target_character_name=target,
        relation_type=relation_type,
        relation_summary=str(relationship_data.get("relation_summary") or "")[:200],
        evidence=str(relationship_data.get("evidence") or "")[:500],
        source_document_ids=dump_json_list(relationship_data.get("source_document_ids")),
        is_explicit=bool(relationship_data.get("is_explicit", True)),
        is_inferred=bool(relationship_data.get("is_inferred", False)),
        evidence_summary=str(relationship_data.get("evidence_summary") or relationship_data.get("evidence") or "")[:500],
        evidence_json=dump_json_list(relationship_data.get("evidence_json") or relationship_data.get("source_document_ids")),
        confidence_level=str(relationship_data.get("confidence_level") or "medium"),
        spoiler_level=str(relationship_data.get("spoiler_level") or "none"),
        visibility=str(relationship_data.get("visibility") or "public"),
        needs_human_review=bool(relationship_data.get("needs_human_review", True)),
        extraction_method=str(relationship_data.get("extraction_method") or "rule_fallback"),
        reviewer_provider=str(relationship_data.get("reviewer_provider") or "rule"),
        reviewer_status=str(relationship_data.get("reviewer_status") or "rule_fallback"),
        confidence=float(relationship_data.get("confidence") or 0.0),
        relationship_status="pending",
    )
    db.add(relationship)
    db.flush()
    return relationship


def find_existing_relationship(
    db: Session,
    project_id: str,
    source: str,
    target: str,
    relation_type: str,
) -> CharacterRelationship | None:
    relationships = list(
        db.scalars(
            select(CharacterRelationship).where(
                CharacterRelationship.project_id == project_id,
                CharacterRelationship.relation_type == relation_type,
            )
        )
    )
    expected_key = relationship_key(project_id, source, target, relation_type)
    for relationship in relationships:
        current_key = relationship_key(
            relationship.project_id,
            relationship.source_character_name,
            relationship.target_character_name,
            relationship.relation_type,
        )
        if current_key == expected_key:
            return relationship
    return None


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


def list_relationships(
    db: Session,
    *,
    project_id: str,
    status: str | None = None,
) -> list[CharacterRelationship]:
    statement = select(CharacterRelationship).where(CharacterRelationship.project_id == project_id)
    if status:
        statement = statement.where(CharacterRelationship.relationship_status == status)
    return list(
        db.scalars(
            statement.order_by(
                CharacterRelationship.relationship_status.asc(),
                CharacterRelationship.confidence.desc(),
                CharacterRelationship.updated_at.desc(),
                CharacterRelationship.id.desc(),
            )
        )
    )


def get_relationship(db: Session, relationship_id: str) -> CharacterRelationship | None:
    return db.scalar(
        select(CharacterRelationship).where(
            CharacterRelationship.relationship_id == relationship_id
        )
    )


def update_relationship(db: Session, relationship: CharacterRelationship, payload) -> CharacterRelationship:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if value is None:
            continue
        if field == "relationship_status":
            value = normalize_status(value)
        if isinstance(value, str):
            value = value.strip()
        setattr(relationship, field, value)
    relationship.updated_at = datetime.utcnow()
    db.flush()
    return relationship


def ignore_relationship(db: Session, relationship: CharacterRelationship) -> CharacterRelationship:
    relationship.relationship_status = "ignored"
    relationship.updated_at = datetime.utcnow()
    db.flush()
    return relationship


def get_relationships_for_character(
    db: Session,
    *,
    project_id: str | None,
    character_name: str,
    include_pending: bool = True,
    limit: int = 12,
) -> list[CharacterRelationship]:
    if not project_id or not character_name:
        return []
    statuses = ["confirmed", "pending"] if include_pending else ["confirmed"]
    return list(
        db.scalars(
            select(CharacterRelationship)
            .where(
                CharacterRelationship.project_id == project_id,
                CharacterRelationship.relationship_status.in_(statuses),
                (
                    (CharacterRelationship.source_character_name == character_name)
                    | (CharacterRelationship.target_character_name == character_name)
                ),
            )
            .order_by(
                CharacterRelationship.relationship_status.asc(),
                CharacterRelationship.confidence.desc(),
                CharacterRelationship.updated_at.desc(),
            )
            .limit(limit)
        )
    )


def build_relationship_graph(
    relationships: list[CharacterRelationship],
) -> dict[str, list[dict[str, str]]]:
    node_names: list[str] = []
    edges: list[dict[str, str]] = []
    for relationship in relationships:
        if relationship.relationship_status == "ignored":
            continue
        for name in [relationship.source_character_name, relationship.target_character_name]:
            if name not in node_names:
                node_names.append(name)
        edges.append(
            {
                "id": relationship.relationship_id,
                "source": relationship.source_character_name,
                "target": relationship.target_character_name,
                "label": relationship.relation_type,
                "summary": relationship.relation_summary,
            }
        )
    return {
        "nodes": [{"id": name, "label": name} for name in node_names],
        "edges": edges,
    }


def summarize_relationship_hints(
    relationships: list[CharacterRelationship],
    *,
    limit: int = 200,
) -> str:
    hints: list[str] = []
    for relationship in relationships:
        summary = relationship.relation_summary.strip()
        if not summary:
            summary = (
                f"{relationship.source_character_name}与"
                f"{relationship.target_character_name}：{relationship.relation_type}"
            )
        if summary not in hints:
            hints.append(summary)
        candidate = "；".join(hints)
        if len(candidate) >= limit:
            return candidate[:limit]
    return "；".join(hints)[:limit]
