from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.character_candidate_merger import merge_candidate_payloads
from app.services.llm_prompt_loader import load_prompt_template
from app.services.structured_llm_client import StructuredLLMClient


def merge_characters_with_llm(
    db: Session,
    *,
    project_id: str,
    user_id: str | None,
    characters: list[dict[str, Any]],
    corpus_analysis: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "characters": characters[:80],
        "corpus_analysis_summary": corpus_analysis.get("corpus_summary", {}),
        "rules": {
            "same_canonical_name_merge": True,
            "x_de_y_belongs_to_x": True,
            "do_not_auto_merge_ambiguous_ocr_variants": True,
        },
    }
    client = StructuredLLMClient(db)
    result = client.generate_json(
        project_id=project_id,
        user_id=user_id,
        prompt_type="character_merger",
        system_prompt=load_prompt_template("character_merger.md"),
        payload=payload,
        fallback_factory=lambda reason: build_rule_merge_output(characters, reason),
    )
    data = result.data if isinstance(result.data, dict) else build_rule_merge_output(characters, result.error)
    merged = data.get("characters") or data.get("merged_characters") or []
    if not isinstance(merged, list):
        merged = merge_candidate_payloads(characters)
    data["characters"] = merge_candidate_payloads([item for item in merged if isinstance(item, dict)])
    data["provider"] = result.provider
    data["model"] = result.model
    data["reviewer_status"] = result.status
    data["fallback"] = result.fallback
    if result.error:
        data.setdefault("warnings", []).append(result.error)
    return data


def build_rule_merge_output(characters: list[dict[str, Any]], reason: str) -> dict[str, Any]:
    merged = merge_candidate_payloads(characters)
    for item in merged:
        if "的" in str(item.get("canonical_name") or ""):
            item["candidate_type"] = "prop"
            item["confidence_level"] = "low"
            item["needs_human_review"] = False
            item["rejected_reason"] = "X的Y 结构归属到 X 的证据，不作为独立角色。"
    return {
        "characters": merged,
        "merge_suggestions": [],
        "warnings": [reason],
    }
