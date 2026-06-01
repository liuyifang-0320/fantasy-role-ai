from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import ParsedDocument
from app.services.character_candidate_extractor import extract_character_candidates
from app.services.llm_prompt_loader import load_prompt_template
from app.services.structured_llm_client import StructuredLLMClient


def extract_characters_with_llm(
    db: Session,
    *,
    project_id: str,
    user_id: str | None,
    documents: list[ParsedDocument],
    corpus_analysis: dict[str, Any],
) -> dict[str, Any]:
    rule_evidence = extract_character_candidates(project_id, documents)
    payload = {
        "corpus_analysis": corpus_analysis,
        "evidence_candidates": [
            compact_candidate(candidate) for candidate in rule_evidence[:80]
        ],
        "requirements": {
            "only_evidence_driven": True,
            "do_not_create_person_from_single_common_noun": True,
            "x_de_y_belongs_to_x": True,
            "needs_human_review_for_uncertain": True,
        },
    }
    client = StructuredLLMClient(db)
    result = client.generate_json(
        project_id=project_id,
        user_id=user_id,
        prompt_type="character_extractor",
        system_prompt=load_prompt_template("character_extractor.md"),
        payload=payload,
        fallback_factory=lambda reason: build_rule_character_output(rule_evidence, reason),
    )
    data = normalize_character_output(result.data, rule_evidence)
    data["provider"] = result.provider
    data["model"] = result.model
    data["reviewer_status"] = result.status
    data["fallback"] = result.fallback
    if result.error:
        data.setdefault("warnings", []).append(result.error)
    return data


def compact_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical_name": candidate.get("canonical_name") or candidate.get("name"),
        "display_name": candidate.get("display_name") or candidate.get("name"),
        "candidate_type": candidate.get("candidate_type"),
        "source_types": candidate.get("source_types", []),
        "evidence_spans": [str(item)[:220] for item in candidate.get("evidence_spans", [])[:6]],
        "relationship_evidence": candidate.get("relationship_evidence", [])[:6],
        "source_document_ids": candidate.get("source_document_ids", [])[:8],
        "dialogue_count": candidate.get("dialogue_count", 0),
        "mention_count": candidate.get("mention_count", 0),
        "confidence": candidate.get("confidence", 0.0),
        "confidence_level": candidate.get("confidence_level", "low"),
        "needs_human_review": candidate.get("needs_human_review", True),
    }


def build_rule_character_output(rule_evidence: list[dict[str, Any]], reason: str) -> dict[str, Any]:
    candidates = []
    for candidate in rule_evidence:
        candidates.append(
            {
                **compact_candidate(candidate),
                "aliases": candidate.get("aliases", []),
                "role_type": candidate.get("candidate_type", "unknown"),
                "llm_confidence": 0.0,
                "llm_reason": reason,
                "llm_evidence": "",
                "reviewer_provider": "rule_fallback",
                "reviewer_status": "rule_fallback",
                "reviewer_reason": candidate.get("reviewer_reason") or reason,
                "extraction_method": "rule_fallback",
            }
        )
    return {
        "characters": candidates,
        "warnings": [reason],
    }


def normalize_character_output(data: Any, rule_evidence: list[dict[str, Any]]) -> dict[str, Any]:
    if isinstance(data, list):
        characters = data
        warnings: list[str] = []
    elif isinstance(data, dict):
        characters = data.get("characters") or data.get("candidates") or []
        warnings = [str(item) for item in data.get("warnings", [])]
    else:
        return build_rule_character_output(rule_evidence, "LLM output was not structured; rule fallback used.")
    if not isinstance(characters, list):
        return build_rule_character_output(rule_evidence, "LLM characters field was not a list; rule fallback used.")
    normalized: list[dict[str, Any]] = []
    for item in characters:
        if not isinstance(item, dict):
            continue
        name = str(item.get("canonical_name") or item.get("display_name") or item.get("name") or "").strip()
        if not name:
            continue
        normalized.append(
            {
                "name": name,
                "canonical_name": name,
                "display_name": str(item.get("display_name") or name),
                "aliases": item.get("aliases") or [],
                "candidate_type": str(item.get("candidate_type") or item.get("role_type") or "unknown"),
                "role_type": str(item.get("role_type") or item.get("candidate_type") or "unknown"),
                "source_types": item.get("source_types") or ["llm_review"],
                "evidence_spans": item.get("evidence_spans") or item.get("evidence_json") or [],
                "relationship_evidence": item.get("relationship_evidence") or [],
                "relationship_hints": item.get("relationship_hints") or item.get("relationship_evidence") or [],
                "source_document_ids": item.get("source_document_ids") or item.get("source_documents") or [],
                "source_documents": item.get("source_documents") or item.get("source_document_ids") or [],
                "evidence_json": item.get("evidence_json") or item.get("evidence_spans") or [],
                "identity_hint": str(item.get("identity_hint") or ""),
                "personality_hint": str(item.get("personality_hint") or ""),
                "evidence": str(item.get("evidence") or item.get("llm_evidence") or "")[:500],
                "dialogue_count": int(item.get("dialogue_count") or 0),
                "mention_count": int(item.get("mention_count") or 0),
                "confidence": float(item.get("confidence") or item.get("llm_confidence") or 0.0),
                "confidence_level": str(item.get("confidence_level") or "low"),
                "needs_human_review": bool(item.get("needs_human_review", True)),
                "llm_confidence": float(item.get("llm_confidence") or item.get("confidence") or 0.0),
                "llm_reason": str(item.get("llm_reason") or item.get("reason") or ""),
                "llm_evidence": str(item.get("llm_evidence") or item.get("evidence") or "")[:500],
                "reviewer_provider": str(item.get("reviewer_provider") or "openai_compatible"),
                "reviewer_status": str(item.get("reviewer_status") or "success"),
                "reviewer_reason": str(item.get("reviewer_reason") or item.get("reason") or ""),
                "extraction_method": str(item.get("extraction_method") or "llm"),
            }
        )
    return {"characters": normalized, "warnings": warnings}
