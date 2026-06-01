from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.character_settings import (
    CharacterSettingsPromptPreviewResponse,
    CharacterSettingsResponse,
    CharacterSettingsUpdateRequest,
)
from app.schemas.character import (
    CharacterGenerateRequest,
    CharacterListItem,
    CharacterResponse,
    GeneratedCharacterResponse,
)
from app.schemas.file import ParsedDocumentSummary
from app.schemas.pet import PetInfo
from app.schemas.pet_asset import (
    PetAssetGenerateRequest,
    PetAssetResponse,
    PetAssetSummary,
)
from app.api.profiles import serialize_profile
from app.services.access_control import (
    ensure_user_can_access_character,
    ensure_user_can_access_pet_asset,
)
from app.services.auth import get_current_user
from app.services.characters import generate_character, get_character, list_characters
from app.services.character_settings import (
    build_settings_prompt,
    get_or_create_settings,
    reset_settings,
    update_settings,
)
from app.services.content_safety import (
    check_character_settings,
    create_safety_log,
)
from app.services.knowledge_chunker import (
    count_character_chunks,
    list_character_chunk_previews,
)
from app.services.pet_assets import (
    generate_pet_asset,
    get_active_pet_asset,
    list_pet_assets,
    serialize_pet_asset_summary,
    set_active_pet_asset,
)
from app.services.profile_extractor import get_latest_profile_for_character
from app.services.profile_extractor import parse_json_list
from app.schemas.knowledge import KnowledgeChunkPreview


router = APIRouter()


def serialize_settings(settings) -> CharacterSettingsResponse:
    return CharacterSettingsResponse(
        settings_id=settings.settings_id,
        user_id=settings.user_id,
        project_id=settings.project_id,
        character_id=settings.character_id,
        display_name=settings.display_name,
        user_persona_name=settings.user_persona_name,
        nickname_for_user=settings.nickname_for_user,
        relationship_with_user=settings.relationship_with_user,
        relationship_stage=settings.relationship_stage,
        tone_style=settings.tone_style,
        reply_length=settings.reply_length,
        intimacy_mode=settings.intimacy_mode,
        spoiler_mode=settings.spoiler_mode,
        spoiler_protection=settings.spoiler_protection,
        pet_enabled=settings.pet_enabled,
        pet_position=settings.pet_position,
        personality_override=settings.personality_override,
        speaking_style_override=settings.speaking_style_override,
        custom_prompt_notes=settings.custom_prompt_notes,
        forbidden_topics=settings.forbidden_topics,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


def serialize_character(character, profile=None, db: Session | None = None) -> CharacterResponse:
    knowledge_chunks = (
        list_character_chunk_previews(db, character.character_id)
        if db
        else []
    )
    pet_assets = list_pet_assets(db, character.character_id) if db else []
    active_pet_asset = (
        get_active_pet_asset(db, character.character_id)
        if db
        else None
    )
    return CharacterResponse(
        character_id=character.character_id,
        user_id=character.user_id,
        project_id=character.project_id,
        character_name=character.character_name,
        character_identity=character.character_identity,
        personality=character.personality,
        description=character.description,
        user_persona_name=character.user_persona_name,
        relationship_with_user=character.relationship_with_user,
        relationship_stage=character.relationship_stage,
        intimacy_level=character.intimacy_level,
        avatar=character.avatar,
        pet=PetInfo(
            pet_id=character.pet.pet_id,
            pet_name=character.pet.pet_name,
            pet_avatar=character.pet.pet_avatar,
            pet_type=character.pet.pet_type,
            pet_status=character.pet.pet_status,
            available_actions=character.pet.available_actions,
        ),
        profile_id=profile.profile_id if profile else None,
        profile=serialize_profile(profile) if profile else None,
        knowledge_chunk_count=(
            count_character_chunks(db, character.character_id) if db else 0
        ),
        knowledge_chunks_preview=[
            KnowledgeChunkPreview(
                chunk_id=chunk.chunk_id,
                chapter=chunk.chapter,
                visibility=chunk.visibility,
                content_preview=chunk.content_preview,
            )
            for chunk in knowledge_chunks
        ],
        pet_assets=[
            PetAssetSummary(**serialize_pet_asset_summary(asset))
            for asset in pet_assets
        ],
        active_pet_asset=(
            PetAssetSummary(**serialize_pet_asset_summary(active_pet_asset))
            if active_pet_asset
            else None
        ),
    )


def serialize_pet_asset(asset) -> PetAssetResponse:
    return PetAssetResponse(
        asset_id=asset.asset_id,
        user_id=asset.user_id,
        project_id=asset.project_id,
        character_id=asset.character_id,
        pet_id=asset.pet_id,
        asset_type=asset.asset_type,
        style=asset.style,
        prompt=asset.prompt,
        negative_prompt=asset.negative_prompt,
        image_url=asset.image_url,
        local_path=asset.local_path,
        generation_provider=asset.generation_provider,
        generation_status=asset.generation_status,
        is_active=asset.is_active,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def build_generated_character_response(
    db: Session,
    character,
    parsed_documents,
    profile,
) -> GeneratedCharacterResponse:
    return GeneratedCharacterResponse(
        **serialize_character(character, profile, db).model_dump(),
        parsed_document_ids=[
            parsed_document.parsed_id for parsed_document in parsed_documents
        ],
        parsed_documents=[
            ParsedDocumentSummary(
                parsed_id=parsed_document.parsed_id,
                file_id=parsed_document.file_id,
                user_id=parsed_document.user_id,
                project_id=parsed_document.project_id,
                filename=parsed_document.filename,
                file_type=parsed_document.file_type,
                parse_status=parsed_document.parse_status,
                text_preview=parsed_document.text_preview,
                word_count=parsed_document.word_count,
                ocr_provider=parsed_document.ocr_provider or "",
                ocr_confidence=parsed_document.ocr_confidence or 0.0,
                ocr_error=parsed_document.ocr_error,
                safety_warning=parsed_document.safety_warning or "",
                safety_categories=parse_json_list(parsed_document.safety_categories or "[]"),
            )
            for parsed_document in parsed_documents
        ],
    )


@router.post("/generate", response_model=GeneratedCharacterResponse)
def create_character(
    payload: CharacterGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GeneratedCharacterResponse:
    try:
        character, parsed_documents, profile, knowledge_chunks = generate_character(
            db,
            payload,
            user_id=current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return build_generated_character_response(db, character, parsed_documents, profile)


@router.get("", response_model=list[CharacterListItem])
def get_characters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CharacterListItem]:
    characters = list_characters(db, user_id=current_user.user_id)
    return [
        CharacterListItem(
            **serialize_character(
                character,
                get_latest_profile_for_character(db, character.character_id),
                db,
            ).model_dump(),
            last_message=character.last_message,
            updated_at=character.updated_at,
        )
        for character in characters
    ]


@router.get("/{character_id}/pet-assets", response_model=list[PetAssetResponse])
def get_character_pet_assets(
    character_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PetAssetResponse]:
    character = get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    ensure_user_can_access_character(current_user, character)
    return [serialize_pet_asset(asset) for asset in list_pet_assets(db, character_id)]


@router.post("/{character_id}/pet-assets/generate", response_model=PetAssetResponse)
def create_character_pet_asset(
    character_id: str,
    payload: PetAssetGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PetAssetResponse:
    character = get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    ensure_user_can_access_character(current_user, character)
    try:
        asset = generate_pet_asset(
            db,
            character,
            style=payload.style,
            prompt_override=payload.prompt_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    db.refresh(asset)
    return serialize_pet_asset(asset)


@router.patch(
    "/{character_id}/pet-assets/{asset_id}/active",
    response_model=PetAssetResponse,
)
def patch_active_pet_asset(
    character_id: str,
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PetAssetResponse:
    character = get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    ensure_user_can_access_character(current_user, character)
    try:
        asset = set_active_pet_asset(
            db,
            character_id=character_id,
            asset_id=asset_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    ensure_user_can_access_pet_asset(current_user, asset)
    db.commit()
    db.refresh(asset)
    return serialize_pet_asset(asset)


@router.get("/{character_id}/settings", response_model=CharacterSettingsResponse)
def get_character_settings(
    character_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterSettingsResponse:
    character = get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    ensure_user_can_access_character(current_user, character)
    settings = get_or_create_settings(db, character)
    db.commit()
    db.refresh(settings)
    return serialize_settings(settings)


@router.patch("/{character_id}/settings", response_model=CharacterSettingsResponse)
def patch_character_settings(
    character_id: str,
    payload: CharacterSettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterSettingsResponse:
    character = get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    ensure_user_can_access_character(current_user, character)
    safety_result = check_character_settings(
        payload.model_dump(exclude_unset=True),
        {"character": character, "user_id": current_user.user_id},
    )
    if safety_result.matched_categories:
        create_safety_log(
            db,
            result=safety_result,
            direction="character_setting",
            input_text=str(payload.model_dump(exclude_unset=True)),
            user_id=character.user_id,
            project_id=character.project_id,
            character_id=character.character_id,
        )
        db.commit()
    if not safety_result.allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=safety_result.reason or "角色调教配置包含不适合保存的安全风险内容",
        )
    settings = update_settings(db, character, payload)
    db.commit()
    db.refresh(settings)
    return serialize_settings(settings)


@router.post("/{character_id}/settings/reset", response_model=CharacterSettingsResponse)
def reset_character_settings(
    character_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterSettingsResponse:
    character = get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    ensure_user_can_access_character(current_user, character)
    settings = reset_settings(db, character)
    db.commit()
    db.refresh(settings)
    return serialize_settings(settings)


@router.get(
    "/{character_id}/settings/prompt-preview",
    response_model=CharacterSettingsPromptPreviewResponse,
)
def get_character_settings_prompt_preview(
    character_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterSettingsPromptPreviewResponse:
    character = get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    ensure_user_can_access_character(current_user, character)
    settings = get_or_create_settings(db, character)
    db.commit()
    db.refresh(settings)
    return CharacterSettingsPromptPreviewResponse(
        character_id=character.character_id,
        settings_id=settings.settings_id,
        prompt_preview=build_settings_prompt(settings),
    )


@router.get("/{character_id}", response_model=CharacterResponse)
def get_character_detail(
    character_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterResponse:
    character = get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    ensure_user_can_access_character(current_user, character)
    return serialize_character(
        character,
        get_latest_profile_for_character(db, character.character_id),
        db,
    )
