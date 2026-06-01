from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.character_candidate import (
    CharacterCandidateResponse,
    CharacterCandidateUpdateRequest,
)
from app.services.access_control import ensure_user_can_access_candidate
from app.services.auth import get_current_user
from app.services.character_candidates import (
    get_candidate,
    ignore_candidate,
    parse_json_list,
    update_candidate,
)


router = APIRouter()


def serialize_candidate(candidate) -> CharacterCandidateResponse:
    return CharacterCandidateResponse(
        candidate_id=candidate.candidate_id,
        user_id=candidate.user_id,
        project_id=candidate.project_id,
        name=candidate.name,
        canonical_name=candidate.canonical_name or candidate.name,
        display_name=candidate.display_name or candidate.name,
        normalized_name=candidate.normalized_name or candidate.canonical_name or candidate.name,
        aliases=parse_json_list(candidate.aliases),
        candidate_type=candidate.candidate_type or "unknown",
        source_types=parse_json_list(candidate.source_types),
        evidence_spans=parse_json_list(candidate.evidence_spans),
        dialogue_count=candidate.dialogue_count or 0,
        mention_count=candidate.mention_count or 0,
        relationship_evidence=parse_json_list(candidate.relationship_evidence),
        identity_hint=candidate.identity_hint,
        personality_hint=candidate.personality_hint,
        relationship_hints=parse_json_list(candidate.relationship_hints),
        evidence=candidate.evidence,
        source_document_ids=parse_json_list(candidate.source_document_ids),
        source_documents=parse_json_list(getattr(candidate, "source_documents", "") or candidate.source_document_ids),
        evidence_json=parse_json_list(getattr(candidate, "evidence_json", "") or candidate.evidence_spans),
        role_type=getattr(candidate, "role_type", "") or candidate.candidate_type or "unknown",
        extraction_method=getattr(candidate, "extraction_method", "") or "rule_fallback",
        llm_confidence=float(getattr(candidate, "llm_confidence", 0.0) or 0.0),
        llm_reason=getattr(candidate, "llm_reason", "") or "",
        llm_evidence=getattr(candidate, "llm_evidence", "") or "",
        confidence=candidate.confidence,
        confidence_level=candidate.confidence_level or "low",
        needs_human_review=bool(candidate.needs_human_review),
        rejected_reason=candidate.rejected_reason or "",
        merge_suggestions=parse_json_list(candidate.merge_suggestions),
        reviewer_provider=candidate.reviewer_provider or "",
        reviewer_status=candidate.reviewer_status or "",
        reviewer_reason=candidate.reviewer_reason or "",
        candidate_status=candidate.candidate_status,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
    )


@router.get("/{candidate_id}", response_model=CharacterCandidateResponse)
def get_character_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterCandidateResponse:
    candidate = get_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    ensure_user_can_access_candidate(current_user, candidate)
    return serialize_candidate(candidate)


@router.patch("/{candidate_id}", response_model=CharacterCandidateResponse)
def patch_character_candidate(
    candidate_id: str,
    payload: CharacterCandidateUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterCandidateResponse:
    candidate = get_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    ensure_user_can_access_candidate(current_user, candidate)
    update_candidate(db, candidate, payload)
    db.commit()
    db.refresh(candidate)
    return serialize_candidate(candidate)


@router.delete("/{candidate_id}", response_model=CharacterCandidateResponse)
def delete_character_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterCandidateResponse:
    candidate = get_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    ensure_user_can_access_candidate(current_user, candidate)
    ignore_candidate(db, candidate)
    db.commit()
    db.refresh(candidate)
    return serialize_candidate(candidate)
