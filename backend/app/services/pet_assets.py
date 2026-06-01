from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Character, CharacterProfile, CharacterSettings, Pet, PetAsset
from app.services.character_settings import get_or_create_settings
from app.services.ids import next_prefixed_id
from app.services.image_generation_provider import get_image_generation_provider
from app.services.profile_extractor import get_latest_profile_for_character


STYLE_LABELS = {
    "q_chibi": "Q版小人",
    "anime_chibi": "日系Q版",
    "soft_dream": "柔和梦幻",
    "mystery_dark": "悬疑暗色",
    "cute_pet": "可爱桌宠",
}

DEFAULT_NEGATIVE_PROMPT = "恐怖、血腥、色情、真实人物肖像、低俗元素、低清晰度、畸形肢体"


def list_pet_assets(db: Session, character_id: str) -> list[PetAsset]:
    return list(
        db.scalars(
            select(PetAsset)
            .where(PetAsset.character_id == character_id)
            .order_by(PetAsset.is_active.desc(), PetAsset.created_at.desc(), PetAsset.id.desc())
        )
    )


def get_pet_asset(db: Session, asset_id: str) -> PetAsset | None:
    return db.scalar(select(PetAsset).where(PetAsset.asset_id == asset_id))


def get_active_pet_asset(db: Session, character_id: str) -> PetAsset | None:
    return db.scalar(
        select(PetAsset)
        .where(PetAsset.character_id == character_id, PetAsset.is_active.is_(True))
        .order_by(PetAsset.updated_at.desc(), PetAsset.id.desc())
    )


def create_default_pet_asset(
    db: Session,
    character: Character,
    pet: Pet,
) -> PetAsset:
    existing_active = get_active_pet_asset(db, character.character_id)
    if existing_active:
        if existing_active.user_id is None and character.user_id:
            existing_active.user_id = character.user_id
            db.flush()
        return existing_active

    profile = get_latest_profile_for_character(db, character.character_id)
    settings = get_or_create_settings(db, character)
    return _create_asset(
        db,
        character=character,
        pet=pet,
        profile=profile,
        settings=settings,
        style="q_chibi",
        prompt_override=None,
        is_active=True,
    )


def generate_pet_asset(
    db: Session,
    character: Character,
    *,
    style: str,
    prompt_override: str | None = None,
) -> PetAsset:
    if not character.pet:
        raise ValueError("Character has no pet")
    profile = get_latest_profile_for_character(db, character.character_id)
    settings = get_or_create_settings(db, character)
    return _create_asset(
        db,
        character=character,
        pet=character.pet,
        profile=profile,
        settings=settings,
        style=style,
        prompt_override=prompt_override,
        is_active=True,
    )


def set_active_pet_asset(
    db: Session,
    *,
    character_id: str,
    asset_id: str,
) -> PetAsset:
    target = get_pet_asset(db, asset_id)
    if not target or target.character_id != character_id:
        raise ValueError("Pet asset not found for character")

    for asset in list_pet_assets(db, character_id):
        asset.is_active = asset.asset_id == asset_id
        asset.updated_at = datetime.utcnow()
    db.flush()
    return target


def build_pet_prompt(
    character: Character,
    profile: CharacterProfile | None,
    settings: CharacterSettings | None,
    style: str,
) -> str:
    identity = (
        profile.extracted_identity
        if profile and profile.extracted_identity
        else character.character_identity
    )
    personality = (
        settings.personality_override
        if settings and settings.personality_override
        else character.personality
    )
    speaking_style = (
        settings.speaking_style_override
        if settings and settings.speaking_style_override
        else (profile.speaking_style if profile else "")
    )
    style_label = STYLE_LABELS.get(style, style)
    lines = [
        f"角色名：{character.character_name}",
        f"身份：{identity}",
        f"性格：{personality}",
        f"说话风格：{speaking_style or '克制、带有故事感'}",
        f"风格：{style_label}，圆头身，适合作为小程序聊天页桌宠形象",
        "画面：柔和、干净、可爱但保留角色气质，透明或简洁背景",
        "禁止：恐怖、血腥、色情、真实人物肖像、低俗元素",
    ]
    return "\n".join(line for line in lines if line)


def serialize_pet_asset_summary(asset: PetAsset | None) -> dict | None:
    if not asset:
        return None
    return {
        "asset_id": asset.asset_id,
        "style": asset.style,
        "image_url": asset.image_url,
        "generation_provider": asset.generation_provider,
        "generation_status": asset.generation_status,
        "is_active": asset.is_active,
    }


def _create_asset(
    db: Session,
    *,
    character: Character,
    pet: Pet,
    profile: CharacterProfile | None,
    settings: CharacterSettings | None,
    style: str,
    prompt_override: str | None,
    is_active: bool,
) -> PetAsset:
    prompt = (prompt_override or "").strip() or build_pet_prompt(
        character,
        profile,
        settings,
        style,
    )
    negative_prompt = DEFAULT_NEGATIVE_PROMPT
    result = get_image_generation_provider().generate_image(
        prompt=prompt,
        negative_prompt=negative_prompt,
        style=style,
    )

    if is_active:
        for asset in list_pet_assets(db, character.character_id):
            asset.is_active = False
            asset.updated_at = datetime.utcnow()

    asset = PetAsset(
        asset_id=next_prefixed_id(db, PetAsset, "pet_asset"),
        user_id=character.user_id,
        project_id=character.project_id,
        character_id=character.character_id,
        pet_id=pet.pet_id,
        asset_type="static_image",
        style=style,
        prompt=prompt,
        negative_prompt=negative_prompt,
        image_url=result.image_url,
        local_path=result.local_path,
        generation_provider=result.provider,
        generation_status=result.status,
        is_active=is_active,
    )
    db.add(asset)
    db.flush()
    return asset
