from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import ParsedDocument
from app.services.character_relationship_extractor import extract_character_relationships
from app.services.llm_prompt_loader import load_prompt_template
from app.services.structured_llm_client import StructuredLLMClient


def extract_relationships_with_llm(
    db: Session,
    *,
    project_id: str,
    user_id: str | None,
    documents: list[ParsedDocument],
    characters: list[dict[str, Any]],
    corpus_analysis: dict[str, Any],
) -> dict[str, Any]:
    rule_relationships = extract_character_relationships(project_id, documents)
    payload = {
        "characters": [
            {
                "canonical_name": item.get("canonical_name") or item.get("name"),
                "candidate_type": item.get("candidate_type"),
                "confidence_level": item.get("confidence_level"),
            }
            for item in characters[:80]
        ],
        "rule_relationship_evidence": [
            compact_relationship(item) for item in rule_relationships[:80]
        ],
        "corpus_analysis_summary": corpus_analysis.get("corpus_summary", {}),
        "requirements": {
            "short_relationship_sentence_only": True,
            "explicit_vs_inferred": True,
            "spoiler_level_required": True,
        },
    }
    client = StructuredLLMClient(db)
    result = client.generate_json(
        project_id=project_id,
        user_id=user_id,
        prompt_type="relationship_extractor",
        system_prompt=load_prompt_template("relationship_extractor.md"),
        payload=payload,
        fallback_factory=lambda reason: build_rule_relationship_output(rule_relationships, reason),
    )
    data = normalize_relationship_output(result.data, rule_relationships)
    data["provider"] = result.provider
    data["model"] = result.model
    data["reviewer_status"] = result.status
    data["fallback"] = result.fallback
    if result.error:
        data.setdefault("warnings", []).append(result.error)
    return data


def compact_relationship(relationship: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_character_name": relationship.get("source_character_name"),
        "target_character_name": relationship.get("target_character_name"),
        "relation_type": relationship.get("relation_type"),
        "relation_summary": relationship.get("relation_summary"),
        "evidence_summary": str(relationship.get("evidence") or "")[:240],
        "source_document_ids": relationship.get("source_document_ids") or [],
        "confidence": relationship.get("confidence", 0.0),
    }


def build_rule_relationship_output(rule_relationships: list[dict[str, Any]], reason: str) -> dict[str, Any]:
    relationships = []
    for item in rule_relationships:
        relationships.append(
            {
                **compact_relationship(item),
                "is_explicit": True,
                "is_inferred": False,
                "evidence": str(item.get("evidence") or "")[:500],
                "evidence_json": item.get("source_document_ids") or [],
                "confidence_level": confidence_level(float(item.get("confidence") or 0.0)),
                "spoiler_level": "none",
                "visibility": "public",
                "needs_human_review": float(item.get("confidence") or 0.0) < 0.8,
                "reviewer_provider": "rule_fallback",
                "reviewer_status": "rule_fallback",
                "extraction_method": "rule_fallback",
            }
        )
    return {"relationships": relationships, "warnings": [reason]}


def normalize_relationship_output(data: Any, rule_relationships: list[dict[str, Any]]) -> dict[str, Any]:
    if isinstance(data, list):
        relationships = data
        warnings: list[str] = []
    elif isinstance(data, dict):
        relationships = data.get("relationships") or []
        warnings = [str(item) for item in data.get("warnings", [])]
    else:
        return build_rule_relationship_output(rule_relationships, "LLM output was not structured; rule fallback used.")
    if not isinstance(relationships, list):
        return build_rule_relationship_output(rule_relationships, "LLM relationships field was not a list; rule fallback used.")
    normalized: list[dict[str, Any]] = []
    for item in relationships:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source_character_name") or "").strip()
        target = str(item.get("target_character_name") or "").strip()
        if not source or not target or source == target:
            continue
        confidence = float(item.get("confidence") or 0.0)
        normalized.append(
            {
                "source_character_name": source,
                "target_character_name": target,
                "relation_type": str(item.get("relation_type") or "未知"),
                "relation_summary": str(item.get("relation_summary") or "")[:200],
                "evidence": str(item.get("evidence") or item.get("evidence_summary") or "")[:500],
                "source_document_ids": item.get("source_document_ids") or [],
                "is_explicit": bool(item.get("is_explicit", True)),
                "is_inferred": bool(item.get("is_inferred", False)),
                "evidence_summary": str(item.get("evidence_summary") or item.get("evidence") or "")[:500],
                "evidence_json": item.get("evidence_json") or item.get("source_document_ids") or [],
                "confidence": confidence,
                "confidence_level": str(item.get("confidence_level") or confidence_level(confidence)),
                "spoiler_level": str(item.get("spoiler_level") or "none"),
                "visibility": str(item.get("visibility") or "public"),
                "needs_human_review": bool(item.get("needs_human_review", confidence < 0.75)),
                "reviewer_provider": str(item.get("reviewer_provider") or "openai_compatible"),
                "reviewer_status": str(item.get("reviewer_status") or "success"),
                "extraction_method": str(item.get("extraction_method") or "llm"),
            }
        )
    return {"relationships": normalized, "warnings": warnings}


def confidence_level(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.45:
        return "medium"
    return "low"
