from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CharacterCandidate,
    CharacterRelationship,
    ParsedDocument,
    ScriptAnalysisJob,
    ScriptChunk,
)
from app.services.character_candidates import upsert_candidate
from app.services.character_relationships import upsert_relationship
from app.services.ids import next_prefixed_id
from app.services.llm_character_extractor import extract_characters_with_llm
from app.services.llm_character_merger import merge_characters_with_llm
from app.services.llm_corpus_analyzer import analyze_corpus
from app.services.llm_profile_builder import build_profiles_with_llm
from app.services.llm_relationship_extractor import extract_relationships_with_llm
from app.services.llm_spoiler_classifier import classify_spoilers_with_llm
from app.services.script_intelligence_pipeline import run_script_intelligence_pipeline


def run_llm_script_understanding(
    db: Session,
    *,
    project_id: str,
    user_id: str | None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    options = options or {}
    parsed_document_ids = options.get("parsed_document_ids") or None
    owner_hints = options.get("owner_hints") or []

    job = ScriptAnalysisJob(
        analysis_id=next_prefixed_id(db, ScriptAnalysisJob, "analysis"),
        user_id=user_id,
        project_id=project_id,
        status="running",
        provider="pending",
        model="",
        warnings="[]",
        result_json="{}",
    )
    db.add(job)
    db.flush()

    warnings: list[str] = []
    try:
        preprocessing = run_script_intelligence_pipeline(
            db,
            project_id=project_id,
            current_user=type("CurrentUser", (), {"user_id": user_id})() if user_id else None,
            parsed_document_ids=parsed_document_ids,
            options=options,
        )
        warnings.extend(str(item) for item in preprocessing.get("warnings", []))
        documents = load_documents(db, project_id, parsed_document_ids, user_id=user_id)
        chunks = load_script_chunks(db, project_id, [document.parsed_id for document in documents], user_id=user_id)

        corpus_analysis = analyze_corpus(
            db,
            project_id=project_id,
            user_id=user_id,
            documents=documents,
            chunks=chunks,
            owner_hints=owner_hints,
        )
        character_output = extract_characters_with_llm(
            db,
            project_id=project_id,
            user_id=user_id,
            documents=documents,
            corpus_analysis=corpus_analysis,
        )
        merged_output = merge_characters_with_llm(
            db,
            project_id=project_id,
            user_id=user_id,
            characters=character_output.get("characters", []),
            corpus_analysis=corpus_analysis,
        )
        characters = merged_output.get("characters", [])
        relationships_output = extract_relationships_with_llm(
            db,
            project_id=project_id,
            user_id=user_id,
            documents=documents,
            characters=characters,
            corpus_analysis=corpus_analysis,
        )
        relationships = relationships_output.get("relationships", [])
        profiles_output = build_profiles_with_llm(
            db,
            project_id=project_id,
            user_id=user_id,
            characters=characters,
            relationships=relationships,
            corpus_analysis=corpus_analysis,
        )
        spoiler_output = classify_spoilers_with_llm(
            db,
            project_id=project_id,
            user_id=user_id,
            chunks=chunks,
            corpus_analysis=corpus_analysis,
        )
        saved_candidates = save_candidates(db, project_id, user_id, characters)
        saved_relationships = save_relationships(db, project_id, user_id, relationships)
        warnings.extend(collect_warnings(corpus_analysis, character_output, merged_output, relationships_output, profiles_output, spoiler_output))

        provider = choose_primary_provider(
            corpus_analysis,
            character_output,
            merged_output,
            relationships_output,
            profiles_output,
            spoiler_output,
        )
        status = "fallback" if provider == "rule_fallback" else "success"
        result = {
            "analysis_id": job.analysis_id,
            "project_id": project_id,
            "status": status,
            "provider": provider,
            "model": choose_primary_model(
                corpus_analysis,
                character_output,
                merged_output,
                relationships_output,
                profiles_output,
                spoiler_output,
            ),
            "preprocessing": preprocessing,
            "corpus_analysis": corpus_analysis,
            "characters": [serialize_candidate(candidate) for candidate in saved_candidates],
            "relationships": [serialize_relationship(relationship) for relationship in saved_relationships],
            "profiles": profiles_output.get("profiles", []),
            "spoiler_summary": summarize_spoilers(spoiler_output),
            "warnings": warnings[:30],
            "message": (
                "当前未配置真实 LLM API，已使用规则 fallback，结果仅供测试。"
                if provider == "rule_fallback"
                else "LLM-first 剧本理解已完成，请在生成数字人前确认候选与关系。"
            ),
        }
        job.status = status
        job.provider = provider
        job.model = str(result["model"])
        job.documents_count = len(documents)
        job.chunks_count = len(chunks)
        job.characters_count = len(saved_candidates)
        job.relationships_count = len(saved_relationships)
        job.warnings = json.dumps(warnings[:30], ensure_ascii=False)
        job.result_json = json.dumps(result, ensure_ascii=False)
        job.updated_at = datetime.utcnow()
        db.flush()
        return result
    except Exception as exc:
        warning = f"{exc.__class__.__name__}: {str(exc)[:300]}"
        job.status = "failed"
        job.provider = "rule_fallback"
        job.warnings = json.dumps([warning], ensure_ascii=False)
        job.result_json = json.dumps(
            {
                "analysis_id": job.analysis_id,
                "project_id": project_id,
                "status": "failed",
                "warnings": [warning],
            },
            ensure_ascii=False,
        )
        job.updated_at = datetime.utcnow()
        db.flush()
        raise


def load_documents(
    db: Session,
    project_id: str,
    parsed_document_ids: list[str] | None,
    *,
    user_id: str | None,
) -> list[ParsedDocument]:
    statement = select(ParsedDocument).where(ParsedDocument.project_id == project_id)
    if parsed_document_ids:
        statement = statement.where(ParsedDocument.parsed_id.in_(parsed_document_ids))
    if user_id:
        statement = statement.where((ParsedDocument.user_id == user_id) | ParsedDocument.user_id.is_(None))
    return list(db.scalars(statement.order_by(ParsedDocument.created_at.asc(), ParsedDocument.id.asc())))


def load_script_chunks(
    db: Session,
    project_id: str,
    parsed_document_ids: list[str],
    *,
    user_id: str | None,
) -> list[ScriptChunk]:
    statement = select(ScriptChunk).where(ScriptChunk.project_id == project_id)
    if parsed_document_ids:
        statement = statement.where(ScriptChunk.parsed_document_id.in_(parsed_document_ids))
    if user_id:
        statement = statement.where((ScriptChunk.user_id == user_id) | ScriptChunk.user_id.is_(None))
    return list(db.scalars(statement.order_by(ScriptChunk.created_at.asc(), ScriptChunk.id.asc())))


def save_candidates(
    db: Session,
    project_id: str,
    user_id: str | None,
    characters: list[dict[str, Any]],
) -> list[CharacterCandidate]:
    saved: list[CharacterCandidate] = []
    for character in characters:
        payload = dict(character)
        payload["project_id"] = project_id
        payload["user_id"] = user_id
        if payload.get("candidate_type") == "person" and payload.get("confidence_level") == "high":
            payload.setdefault("needs_human_review", False)
        saved.append(upsert_candidate(db, payload))
    return saved


def save_relationships(
    db: Session,
    project_id: str,
    user_id: str | None,
    relationships: list[dict[str, Any]],
) -> list[CharacterRelationship]:
    saved: list[CharacterRelationship] = []
    for relationship in relationships:
        payload = dict(relationship)
        payload["project_id"] = project_id
        payload["user_id"] = user_id
        saved.append(upsert_relationship(db, payload))
    return saved


def get_latest_analysis_job(
    db: Session,
    *,
    project_id: str,
    user_id: str | None,
) -> ScriptAnalysisJob | None:
    statement = select(ScriptAnalysisJob).where(ScriptAnalysisJob.project_id == project_id)
    if user_id:
        statement = statement.where((ScriptAnalysisJob.user_id == user_id) | ScriptAnalysisJob.user_id.is_(None))
    return db.scalar(statement.order_by(ScriptAnalysisJob.created_at.desc(), ScriptAnalysisJob.id.desc()))


def get_analysis_result(job: ScriptAnalysisJob | None) -> dict[str, Any]:
    if not job or not job.result_json:
        return {}
    try:
        parsed = json.loads(job.result_json)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def confirm_script_intelligence(
    db: Session,
    *,
    project_id: str,
    user_id: str | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    confirmed_candidate_ids = set(payload.get("confirmed_candidate_ids") or [])
    rejected_candidate_ids = set(payload.get("rejected_candidate_ids") or [])
    confirmed_relationship_ids = set(payload.get("confirmed_relationship_ids") or [])
    rejected_relationship_ids = set(payload.get("rejected_relationship_ids") or [])
    candidates_updated = 0
    relationships_updated = 0

    candidates = list(db.scalars(select(CharacterCandidate).where(CharacterCandidate.project_id == project_id)))
    for candidate in candidates:
        if user_id and candidate.user_id not in {user_id, None}:
            continue
        if candidate.candidate_id in confirmed_candidate_ids:
            candidate.candidate_status = "confirmed"
            candidate.candidate_type = "person"
            candidate.confidence_level = "high"
            candidate.needs_human_review = False
            candidate.reviewer_provider = candidate.reviewer_provider or "manual"
            candidate.reviewer_status = "manual"
            candidates_updated += 1
        if candidate.candidate_id in rejected_candidate_ids:
            candidate.candidate_status = "rejected"
            candidate.rejected_reason = "User rejected this candidate during LLM-first confirmation."
            candidates_updated += 1

    relationships = list(db.scalars(select(CharacterRelationship).where(CharacterRelationship.project_id == project_id)))
    for relationship in relationships:
        if user_id and relationship.user_id not in {user_id, None}:
            continue
        if relationship.relationship_id in confirmed_relationship_ids:
            relationship.relationship_status = "confirmed"
            relationship.needs_human_review = False
            relationships_updated += 1
        if relationship.relationship_id in rejected_relationship_ids:
            relationship.relationship_status = "ignored"
            relationships_updated += 1

    db.flush()
    return {
        "project_id": project_id,
        "confirmed_candidates": len(confirmed_candidate_ids),
        "rejected_candidates": len(rejected_candidate_ids),
        "confirmed_relationships": len(confirmed_relationship_ids),
        "rejected_relationships": len(rejected_relationship_ids),
        "candidates_updated": candidates_updated,
        "relationships_updated": relationships_updated,
    }


def collect_warnings(*outputs: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for output in outputs:
        for warning in output.get("warnings", []) if isinstance(output, dict) else []:
            text = str(warning)
            if text and text not in warnings:
                warnings.append(text)
    return warnings


def choose_primary_provider(*outputs: dict[str, Any]) -> str:
    providers = [str(output.get("provider") or "") for output in outputs if isinstance(output, dict)]
    return "openai_compatible" if "openai_compatible" in providers else "rule_fallback"


def choose_primary_model(*outputs: dict[str, Any]) -> str:
    for output in outputs:
        model = str(output.get("model") or "") if isinstance(output, dict) else ""
        if model and model != "mock-model":
            return model
    return "mock-model"


def summarize_spoilers(spoiler_output: dict[str, Any]) -> dict[str, int]:
    counts = {"none": 0, "mild": 0, "heavy": 0}
    for item in spoiler_output.get("classifications", []):
        level = str(item.get("spoiler_level") or "none")
        counts[level] = counts.get(level, 0) + 1
    return counts


def serialize_candidate(candidate: CharacterCandidate) -> dict[str, Any]:
    return {
        "candidate_id": candidate.candidate_id,
        "canonical_name": candidate.canonical_name or candidate.name,
        "display_name": candidate.display_name or candidate.name,
        "candidate_type": candidate.candidate_type,
        "role_type": getattr(candidate, "role_type", "") or candidate.candidate_type,
        "confidence": candidate.confidence,
        "confidence_level": candidate.confidence_level,
        "llm_confidence": getattr(candidate, "llm_confidence", 0.0) or 0.0,
        "llm_reason": getattr(candidate, "llm_reason", "") or "",
        "evidence": candidate.evidence,
        "source_documents": safe_json_list(getattr(candidate, "source_documents", "") or candidate.source_document_ids),
        "needs_human_review": bool(candidate.needs_human_review),
        "reviewer_status": candidate.reviewer_status,
        "reviewer_reason": candidate.reviewer_reason,
        "candidate_status": candidate.candidate_status,
    }


def serialize_relationship(relationship: CharacterRelationship) -> dict[str, Any]:
    return {
        "relationship_id": relationship.relationship_id,
        "source_character_name": relationship.source_character_name,
        "target_character_name": relationship.target_character_name,
        "relation_type": relationship.relation_type,
        "relation_summary": relationship.relation_summary,
        "confidence": relationship.confidence,
        "confidence_level": getattr(relationship, "confidence_level", "") or "medium",
        "is_explicit": bool(getattr(relationship, "is_explicit", True)),
        "is_inferred": bool(getattr(relationship, "is_inferred", False)),
        "spoiler_level": getattr(relationship, "spoiler_level", "") or "none",
        "visibility": getattr(relationship, "visibility", "") or "public",
        "evidence_summary": getattr(relationship, "evidence_summary", "") or relationship.evidence,
        "needs_human_review": bool(getattr(relationship, "needs_human_review", True)),
        "relationship_status": relationship.relationship_status,
    }


def safe_json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return [item.strip() for item in (value or "").split(",") if item.strip()]
    return parsed if isinstance(parsed, list) else []
