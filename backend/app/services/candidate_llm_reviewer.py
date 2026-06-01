import json

from app.core.config import settings
from app.services.candidate_noise_classifier import is_non_person_type
from app.services.personhood_validator import validate_person_candidate


MAX_REVIEW_CANDIDATES = 30
MAX_EVIDENCE_CHARS = 360


def review_candidates(
    project_id: str,
    candidates: list[dict],
    segments_summary: list[dict] | None = None,
    evidence_summary: dict | None = None,
    options: dict | None = None,
) -> list[dict]:
    if can_use_openai_compatible_reviewer():
        try:
            return OpenAICompatibleCandidateReviewer().review(
                project_id,
                candidates,
                segments_summary or [],
                evidence_summary or {},
            )
        except Exception as exc:
            return RuleCandidateReviewer(
                fallback_reason=f"LLM reviewer failed: {safe_error(exc)}"
            ).review(project_id, candidates)
    return RuleCandidateReviewer(
        fallback_reason="LLM reviewer skipped because provider/key/model is not fully configured"
    ).review(project_id, candidates)


def can_use_openai_compatible_reviewer() -> bool:
    return (
        settings.llm_provider == "openai_compatible"
        and bool(settings.llm_api_key)
        and bool(settings.llm_model)
        and settings.llm_model != "mock-model"
    )


class RuleCandidateReviewer:
    provider = "rule"

    def __init__(self, fallback_reason: str = "Rule reviewer fallback") -> None:
        self.fallback_reason = fallback_reason

    def review(self, project_id: str, candidates: list[dict]) -> list[dict]:
        reviewed: list[dict] = []
        for candidate in candidates:
            candidate_type = str(candidate.get("candidate_type") or "unknown")
            source_types = set(candidate.get("source_types") or [])
            dialogue_count = int(candidate.get("dialogue_count") or 0)
            mention_count = int(candidate.get("mention_count") or 0)
            validation = validate_person_candidate(candidate)
            if validation["candidate_type"] != "unknown":
                candidate_type = str(validation["candidate_type"])

            is_person = candidate_type == "person"
            if is_non_person_type(candidate_type):
                confidence_level = "low"
                needs_review = False
                reason = f"规则分类为非人物：{candidate_type}"
            elif is_person and has_strong_person_evidence(source_types, dialogue_count):
                confidence_level = "high"
                needs_review = False
                reason = "具备强角色证据"
            elif is_person and ("relationship_sentence" in source_types or mention_count >= 2):
                confidence_level = "medium"
                needs_review = True
                reason = "来自关系/复现证据，需要用户确认"
            else:
                confidence_level = "low"
                needs_review = True
                reason = "证据较弱，保留为待确认候选"

            reviewed.append(
                {
                    "canonical_name": candidate.get("canonical_name") or candidate.get("name"),
                    "is_person": is_person,
                    "candidate_type": candidate_type,
                    "confidence_level": confidence_level,
                    "merge_to": "",
                    "needs_human_review": needs_review,
                    "reason": reason,
                    "reviewer_provider": self.provider,
                    "reviewer_status": "rule_fallback",
                    "reviewer_reason": f"{self.fallback_reason}；{reason}",
                }
            )
        return reviewed


class OpenAICompatibleCandidateReviewer:
    provider = "openai_compatible"

    def review(
        self,
        project_id: str,
        candidates: list[dict],
        segments_summary: list[dict],
        evidence_summary: dict,
    ) -> list[dict]:
        from openai import OpenAI

        client_kwargs: dict[str, object] = {
            "api_key": settings.llm_api_key,
            "timeout": settings.llm_timeout_seconds,
        }
        if settings.llm_base_url:
            client_kwargs["base_url"] = settings.llm_base_url
        client = OpenAI(**client_kwargs)
        payload = {
            "project_id": project_id,
            "candidates": [compact_candidate(candidate) for candidate in candidates[:MAX_REVIEW_CANDIDATES]],
            "segments_summary": segments_summary[:20],
            "evidence_summary": evidence_summary,
        }
        messages = [
            {
                "role": "system",
                "content": (
                    "你是剧本文档 ingestion 的候选角色复核器。"
                    "只根据给出的候选摘要和证据判断，不要补充全文中没有的信息。"
                    "输出严格 JSON 数组，不要 markdown。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请判断每个候选是否为人物，并返回字段："
                    "canonical_name,is_person,candidate_type,confidence_level,"
                    "merge_to,needs_human_review,reason。\n"
                    + json.dumps(payload, ensure_ascii=False)
                ),
            },
        ]
        completion = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0,
        )
        text = (completion.choices[0].message.content or "").strip()
        parsed = json.loads(text)
        if not isinstance(parsed, list):
            raise ValueError("reviewer output is not a list")
        for item in parsed:
            item["reviewer_provider"] = self.provider
            item["reviewer_status"] = "success"
        return parsed


def compact_candidate(candidate: dict) -> dict:
    return {
        "canonical_name": candidate.get("canonical_name") or candidate.get("name"),
        "candidate_type": candidate.get("candidate_type"),
        "source_types": candidate.get("source_types", []),
        "dialogue_count": candidate.get("dialogue_count", 0),
        "mention_count": candidate.get("mention_count", 0),
        "relationship_evidence": candidate.get("relationship_evidence", [])[:5],
        "evidence_spans": [
            str(item)[:MAX_EVIDENCE_CHARS]
            for item in (candidate.get("evidence_spans") or [])[:5]
        ],
    }


def has_strong_person_evidence(source_types: set[str], dialogue_count: int) -> bool:
    strong_sources = {"current_character", "identity_field", "filename", "title", "llm_review"}
    if source_types & strong_sources:
        return True
    if "dialogue_label" in source_types and (
        dialogue_count >= 2
        or bool(source_types - {"dialogue_label", "relationship_sentence"})
        or "relationship_sentence" in source_types
    ):
        return True
    return False


def safe_error(exc: Exception) -> str:
    text = str(exc).replace(settings.llm_api_key or "", "[redacted]")
    return text[:160] or exc.__class__.__name__
