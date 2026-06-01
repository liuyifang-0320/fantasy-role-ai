from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.llm_prompt_loader import load_prompt_template
from app.services.structured_llm_client import StructuredLLMClient


def build_profiles_with_llm(
    db: Session,
    *,
    project_id: str,
    user_id: str | None,
    characters: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    corpus_analysis: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "characters": characters[:60],
        "relationships": relationships[:80],
        "corpus_summary": corpus_analysis.get("corpus_summary", {}),
        "requirements": {
            "do_not_invent_missing_facts": True,
            "use_evidence_summary_only": True,
            "mark_unknown_if_unclear": True,
        },
    }
    client = StructuredLLMClient(db)
    result = client.generate_json(
        project_id=project_id,
        user_id=user_id,
        prompt_type="profile_builder",
        system_prompt=load_prompt_template("profile_builder.md"),
        payload=payload,
        fallback_factory=lambda reason: build_rule_profiles(characters, relationships, reason),
    )
    data = result.data if isinstance(result.data, dict) else build_rule_profiles(characters, relationships, result.error)
    profiles = data.get("profiles") or []
    if not isinstance(profiles, list):
        data = build_rule_profiles(characters, relationships, "Profile output was invalid; rule fallback used.")
    data["provider"] = result.provider
    data["model"] = result.model
    data["reviewer_status"] = result.status
    data["fallback"] = result.fallback
    if result.error:
        data.setdefault("warnings", []).append(result.error)
    return data


def build_rule_profiles(characters: list[dict[str, Any]], relationships: list[dict[str, Any]], reason: str) -> dict[str, Any]:
    profiles: list[dict[str, Any]] = []
    for character in characters:
        if character.get("candidate_type") != "person":
            continue
        name = str(character.get("canonical_name") or character.get("name") or "")
        if not name:
            continue
        relation_lines = [
            str(item.get("relation_summary") or "")
            for item in relationships
            if name in {item.get("source_character_name"), item.get("target_character_name")}
        ][:5]
        profiles.append(
            {
                "canonical_name": name,
                "extracted_identity": character.get("identity_hint") or "由剧本资料识别出的角色候选",
                "extracted_personality": character.get("personality_hint") or "需用户确认后补充",
                "speaking_style": "遵循原剧本语气，避免客服式回复",
                "background_summary": str(character.get("evidence") or "")[:240],
                "relationship_summary": "；".join(relation_lines)[:240],
                "story_stage": "待用户确认",
                "known_facts": relation_lines,
                "hidden_secrets": ["当前阶段不主动暴露隐藏真相"],
                "spoiler_guardrails": ["资料不足时不编造", "hidden/restricted 内容不在 non_spoiler 模式直接剧透"],
                "reviewer_provider": "rule_fallback",
                "reviewer_status": "rule_fallback",
            }
        )
    return {"profiles": profiles, "warnings": [reason]}
