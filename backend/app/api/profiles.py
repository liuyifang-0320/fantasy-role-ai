from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ParsedDocument, User
from app.schemas.profile import CharacterProfileExtractRequest, CharacterProfileResponse
from app.services.access_control import (
    ensure_user_can_access_parsed_document,
    ensure_user_can_access_project,
    ensure_user_can_access_resource,
)
from app.services.auth import get_current_user
from app.services.profile_extractor import (
    create_character_profile,
    get_profile,
    list_profiles,
    parse_json_list,
)
from app.services.projects import get_project


router = APIRouter()


def serialize_profile(profile) -> CharacterProfileResponse:
    return CharacterProfileResponse(
        profile_id=profile.profile_id,
        user_id=profile.user_id,
        project_id=profile.project_id,
        character_id=profile.character_id,
        parsed_document_id=profile.parsed_document_id,
        target_character_name=profile.target_character_name,
        user_persona_name=profile.user_persona_name,
        relationship_hint=profile.relationship_hint,
        extracted_identity=profile.extracted_identity,
        extracted_personality=profile.extracted_personality,
        speaking_style=profile.speaking_style,
        background_summary=profile.background_summary,
        relationship_summary=profile.relationship_summary,
        story_stage=profile.story_stage,
        known_facts=parse_json_list(profile.known_facts),
        hidden_secrets=parse_json_list(profile.hidden_secrets),
        spoiler_guardrails=parse_json_list(profile.spoiler_guardrails),
        source_preview=profile.source_preview,
        extraction_status=profile.extraction_status,
        created_at=profile.created_at,
    )


@router.post("/extract", response_model=CharacterProfileResponse)
def extract_profile(
    payload: CharacterProfileExtractRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterProfileResponse:
    parsed_documents = list(
        db.scalars(
            select(ParsedDocument).where(
                ParsedDocument.parsed_id.in_(payload.parsed_document_ids)
            )
        )
    )
    if len(parsed_documents) != len(payload.parsed_document_ids):
        missing_ids = set(payload.parsed_document_ids) - {
            parsed_document.parsed_id for parsed_document in parsed_documents
        }
        missing_text = ", ".join(sorted(missing_ids))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown parsed_document_ids: {missing_text}",
        )
    for parsed_document in parsed_documents:
        ensure_user_can_access_parsed_document(current_user, parsed_document)
    project_id = payload.project_id.strip() if payload.project_id else None
    if project_id:
        project = get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        ensure_user_can_access_project(current_user, project)
        mismatched_parsed_ids = [
            parsed_document.parsed_id
            for parsed_document in parsed_documents
            if parsed_document.project_id != project_id
        ]
        if mismatched_parsed_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Parsed documents do not belong to project: "
                    + ", ".join(sorted(mismatched_parsed_ids))
                ),
            )

    profile = create_character_profile(
        db,
        parsed_documents=parsed_documents,
        target_character_name=payload.target_character_name,
        user_persona_name=payload.user_persona_name,
        relationship_hint=payload.relationship_hint,
        project_id=project_id,
        user_id=current_user.user_id,
    )
    db.commit()
    db.refresh(profile)
    return serialize_profile(profile)


@router.get("", response_model=list[CharacterProfileResponse])
def get_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CharacterProfileResponse]:
    return [
        serialize_profile(profile)
        for profile in list_profiles(db, user_id=current_user.user_id)
    ]


@router.get("/{profile_id}", response_model=CharacterProfileResponse)
def get_profile_detail(
    profile_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterProfileResponse:
    profile = get_profile(db, profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character profile not found",
        )
    ensure_user_can_access_resource(current_user, profile, "Character profile")
    return serialize_profile(profile)
