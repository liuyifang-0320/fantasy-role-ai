from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import ScriptChunk
from app.services.llm_prompt_loader import load_prompt_template
from app.services.structured_llm_client import StructuredLLMClient


HEAVY_MARKERS = ("真相", "复盘", "凶手", "隐藏身份", "最终任务", "结局")
MILD_MARKERS = ("线索", "证据", "搜证", "任务")


def classify_spoilers_with_llm(
    db: Session,
    *,
    project_id: str,
    user_id: str | None,
    chunks: list[ScriptChunk],
    corpus_analysis: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "chunks": [
            {
                "chunk_id": chunk.chunk_id,
                "segment_id": chunk.segment_id,
                "document_type": getattr(chunk, "document_type", "") or "unknown",
                "visibility": chunk.visibility,
                "spoiler_level": chunk.spoiler_level,
                "preview": (chunk.clean_text or chunk.chunk_text or "")[:240],
            }
            for chunk in chunks[:100]
        ],
        "corpus_summary": corpus_analysis.get("corpus_summary", {}),
        "requirements": {
            "non_spoiler_excludes_heavy": True,
            "restricted_content_not_directly_roleplayed": True,
        },
    }
    client = StructuredLLMClient(db)
    result = client.generate_json(
        project_id=project_id,
        user_id=user_id,
        prompt_type="spoiler_classifier",
        system_prompt=load_prompt_template("spoiler_classifier.md"),
        payload=payload,
        fallback_factory=lambda reason: build_rule_spoiler_output(chunks, reason),
    )
    data = result.data if isinstance(result.data, dict) else build_rule_spoiler_output(chunks, result.error)
    classifications = data.get("classifications") or []
    if isinstance(classifications, list):
        apply_spoiler_classifications(chunks, classifications)
    data["provider"] = result.provider
    data["model"] = result.model
    data["reviewer_status"] = result.status
    data["fallback"] = result.fallback
    if result.error:
        data.setdefault("warnings", []).append(result.error)
    return data


def build_rule_spoiler_output(chunks: list[ScriptChunk], reason: str) -> dict[str, Any]:
    classifications: list[dict[str, Any]] = []
    for chunk in chunks:
        text = chunk.clean_text or chunk.chunk_text or ""
        if any(marker in text for marker in HEAVY_MARKERS):
            spoiler_level = "heavy"
            visibility = "restricted"
        elif any(marker in text for marker in MILD_MARKERS):
            spoiler_level = "mild"
            visibility = chunk.visibility or "public"
        else:
            spoiler_level = chunk.spoiler_level or "none"
            visibility = chunk.visibility or "public"
        classifications.append(
            {
                "chunk_id": chunk.chunk_id,
                "spoiler_level": spoiler_level,
                "visibility": visibility,
                "reason": reason,
            }
        )
    return {"classifications": classifications, "warnings": [reason]}


def apply_spoiler_classifications(chunks: list[ScriptChunk], classifications: list[dict[str, Any]]) -> None:
    by_id = {chunk.chunk_id: chunk for chunk in chunks}
    for item in classifications:
        chunk = by_id.get(str(item.get("chunk_id") or ""))
        if not chunk:
            continue
        spoiler_level = str(item.get("spoiler_level") or chunk.spoiler_level or "none")
        visibility = str(item.get("visibility") or chunk.visibility or "public")
        chunk.spoiler_level = spoiler_level
        chunk.visibility = visibility
