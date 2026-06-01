from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.character_relationship import (
    CharacterRelationshipResponse,
    CharacterRelationshipUpdateRequest,
)
from app.services.access_control import ensure_user_can_access_relationship
from app.services.auth import get_current_user
from app.services.character_relationships import (
    get_relationship,
    ignore_relationship,
    parse_json_list,
    update_relationship,
)


router = APIRouter()


def serialize_relationship(relationship) -> CharacterRelationshipResponse:
    return CharacterRelationshipResponse(
        relationship_id=relationship.relationship_id,
        user_id=relationship.user_id,
        project_id=relationship.project_id,
        source_character_name=relationship.source_character_name,
        target_character_name=relationship.target_character_name,
        relation_type=relationship.relation_type,
        relation_summary=relationship.relation_summary,
        evidence=relationship.evidence,
        source_document_ids=parse_json_list(relationship.source_document_ids),
        is_explicit=bool(getattr(relationship, "is_explicit", True)),
        is_inferred=bool(getattr(relationship, "is_inferred", False)),
        evidence_summary=getattr(relationship, "evidence_summary", "") or relationship.evidence,
        evidence_json=parse_json_list(getattr(relationship, "evidence_json", "") or relationship.source_document_ids),
        confidence_level=getattr(relationship, "confidence_level", "") or "medium",
        spoiler_level=getattr(relationship, "spoiler_level", "") or "none",
        visibility=getattr(relationship, "visibility", "") or "public",
        needs_human_review=bool(getattr(relationship, "needs_human_review", True)),
        extraction_method=getattr(relationship, "extraction_method", "") or "rule_fallback",
        reviewer_provider=getattr(relationship, "reviewer_provider", "") or "rule",
        reviewer_status=getattr(relationship, "reviewer_status", "") or "rule_fallback",
        confidence=relationship.confidence,
        relationship_status=relationship.relationship_status,
        created_at=relationship.created_at,
        updated_at=relationship.updated_at,
    )


@router.get("/{relationship_id}", response_model=CharacterRelationshipResponse)
def get_character_relationship(
    relationship_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterRelationshipResponse:
    relationship = get_relationship(db, relationship_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found",
        )
    ensure_user_can_access_relationship(current_user, relationship)
    return serialize_relationship(relationship)


@router.patch("/{relationship_id}", response_model=CharacterRelationshipResponse)
def patch_character_relationship(
    relationship_id: str,
    payload: CharacterRelationshipUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterRelationshipResponse:
    relationship = get_relationship(db, relationship_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found",
        )
    ensure_user_can_access_relationship(current_user, relationship)
    update_relationship(db, relationship, payload)
    db.commit()
    db.refresh(relationship)
    return serialize_relationship(relationship)


@router.delete("/{relationship_id}", response_model=CharacterRelationshipResponse)
def delete_character_relationship(
    relationship_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterRelationshipResponse:
    relationship = get_relationship(db, relationship_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found",
        )
    ensure_user_can_access_relationship(current_user, relationship)
    ignore_relationship(db, relationship)
    db.commit()
    db.refresh(relationship)
    return serialize_relationship(relationship)
