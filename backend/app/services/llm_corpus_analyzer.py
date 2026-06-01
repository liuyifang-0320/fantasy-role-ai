from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.models import ParsedDocument, ScriptChunk
from app.services.llm_prompt_loader import load_prompt_template
from app.services.script_text_cleaner import clean_script_text
from app.services.structured_llm_client import StructuredLLMClient


def analyze_corpus(
    db: Session,
    *,
    project_id: str,
    user_id: str | None,
    documents: list[ParsedDocument],
    chunks: list[ScriptChunk],
    owner_hints: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    manifest = build_corpus_manifest(documents, chunks, owner_hints or [])
    client = StructuredLLMClient(db)
    result = client.generate_json(
        project_id=project_id,
        user_id=user_id,
        prompt_type="script_corpus_analyzer",
        system_prompt=load_prompt_template("script_corpus_analyzer.md"),
        payload=manifest,
        fallback_factory=lambda reason: build_rule_corpus_analysis(manifest, reason),
    )
    data = result.data if isinstance(result.data, dict) else build_rule_corpus_analysis(manifest, result.error)
    data.setdefault("provider", result.provider)
    data.setdefault("model", result.model)
    data.setdefault("reviewer_status", result.status)
    data.setdefault("fallback", result.fallback)
    if result.error:
        data.setdefault("warnings", []).append(result.error)
    return data


def build_corpus_manifest(
    documents: list[ParsedDocument],
    chunks: list[ScriptChunk],
    owner_hints: list[dict[str, str]],
) -> dict[str, Any]:
    hint_by_doc = {
        str(item.get("parsed_document_id") or ""): item
        for item in owner_hints
        if item.get("parsed_document_id")
    }
    chunk_counter = Counter(chunk.parsed_document_id for chunk in chunks)
    documents_manifest: list[dict[str, Any]] = []
    for document in documents:
        clean_result = clean_script_text(document.raw_text or "", document.filename)
        hint = hint_by_doc.get(document.parsed_id, {})
        documents_manifest.append(
            {
                "parsed_document_id": document.parsed_id,
                "filename": document.filename,
                "file_type": getattr(document, "file_type", "") or "",
                "word_count": document.word_count,
                "text_length": len(document.raw_text or ""),
                "clean_length": len(str(clean_result.get("clean_text", ""))),
                "preview": str(clean_result.get("clean_text", ""))[:500],
                "chunk_count": chunk_counter.get(document.parsed_id, 0),
                "owner_character_hint": hint.get("owner_character_name", ""),
                "document_scope_hint": hint.get("document_scope", "unknown"),
                "ocr_provider": document.ocr_provider or "",
                "parse_status": document.parse_status,
                "safety_warning": document.safety_warning or "",
            }
        )
    chunk_summary = [
        {
            "chunk_id": chunk.chunk_id,
            "parsed_document_id": chunk.parsed_document_id,
            "document_type": getattr(chunk, "document_type", "") or "unknown",
            "visibility": chunk.visibility,
            "spoiler_level": chunk.spoiler_level,
            "character_scope": chunk.character_scope,
            "preview": (chunk.clean_text or chunk.chunk_text or "")[:220],
        }
        for chunk in chunks[:80]
    ]
    return {
        "documents": documents_manifest,
        "chunks": chunk_summary,
        "owner_hints": owner_hints,
        "instructions": {
            "do_not_reproduce_full_script": True,
            "use_evidence_only": True,
            "uncertain_means_needs_human_review": True,
        },
    }


def build_rule_corpus_analysis(manifest: dict[str, Any], reason: str) -> dict[str, Any]:
    documents = manifest.get("documents", [])
    type_counts: Counter[str] = Counter()
    owner_hints: list[dict[str, str]] = []
    for document in documents:
        scope = str(document.get("document_scope_hint") or "unknown")
        filename = str(document.get("filename") or "")
        preview = str(document.get("preview") or "")
        if scope != "unknown":
            document_type = scope
        elif any(word in filename + preview for word in ("真相", "复盘", "结局", "凶手")):
            document_type = "truth_reveal"
        elif any(word in filename for word in ("角色本", "个人本")):
            document_type = "character_book"
        elif any(word in preview for word in ("线索", "证据", "搜证")):
            document_type = "clue"
        else:
            document_type = "unknown"
        type_counts[document_type] += 1
        if document.get("owner_character_hint"):
            owner_hints.append(
                {
                    "parsed_document_id": str(document.get("parsed_document_id")),
                    "owner_character_name": str(document.get("owner_character_hint")),
                    "confidence": "manual_hint",
                }
            )
    return {
        "corpus_summary": {
            "documents_count": len(documents),
            "document_type_counts": dict(type_counts),
            "owner_hints": owner_hints,
        },
        "warnings": [reason],
        "reviewer_status": "rule_fallback",
        "fallback": True,
    }
