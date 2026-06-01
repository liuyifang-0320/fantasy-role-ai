from datetime import datetime
from typing import Literal

from pydantic import BaseModel


PetAssetType = Literal[
    "static_image",
    "multi_pose_pack",
    "live2d_placeholder",
    "spine_placeholder",
    "vrm_placeholder",
]
PetAssetStyle = Literal[
    "q_chibi",
    "anime_chibi",
    "soft_dream",
    "mystery_dark",
    "cute_pet",
]


class PetAssetSummary(BaseModel):
    asset_id: str
    style: str
    image_url: str
    generation_provider: str
    generation_status: str
    is_active: bool = False


class PetAssetResponse(BaseModel):
    asset_id: str
    user_id: str | None = None
    project_id: str | None = None
    character_id: str
    pet_id: str
    asset_type: str
    style: str
    prompt: str
    negative_prompt: str
    image_url: str
    local_path: str
    generation_provider: str
    generation_status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PetAssetGenerateRequest(BaseModel):
    style: PetAssetStyle = "q_chibi"
    prompt_override: str | None = None


class ImageGenerationStatusResponse(BaseModel):
    image_provider: str
    active_provider: str
    api_key_configured: bool
    base_url_configured: bool
    model: str
    timeout_seconds: int
