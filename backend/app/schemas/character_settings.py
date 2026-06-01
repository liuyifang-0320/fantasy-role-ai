from datetime import datetime
from typing import Literal

from pydantic import BaseModel


ToneStyle = Literal[
    "gentle",
    "cold",
    "playful",
    "mature",
    "yandere_light",
    "poetic",
    "original",
]
ReplyLength = Literal["short", "medium", "long"]
IntimacyMode = Literal["low", "normal", "high"]
PetPosition = Literal["bottom_right", "bottom_left", "floating"]
SpoilerMode = Literal["non_spoiler", "semi_spoiler", "full_spoiler"]


class CharacterSettingsResponse(BaseModel):
    settings_id: str
    user_id: str | None = None
    project_id: str | None = None
    character_id: str
    display_name: str
    user_persona_name: str
    nickname_for_user: str
    relationship_with_user: str
    relationship_stage: str
    tone_style: ToneStyle
    reply_length: ReplyLength
    intimacy_mode: IntimacyMode
    spoiler_mode: SpoilerMode
    spoiler_protection: bool
    pet_enabled: bool
    pet_position: PetPosition
    personality_override: str
    speaking_style_override: str
    custom_prompt_notes: str
    forbidden_topics: str
    created_at: datetime
    updated_at: datetime | None


class CharacterSettingsUpdateRequest(BaseModel):
    display_name: str | None = None
    user_persona_name: str | None = None
    nickname_for_user: str | None = None
    relationship_with_user: str | None = None
    relationship_stage: str | None = None
    tone_style: ToneStyle | None = None
    reply_length: ReplyLength | None = None
    intimacy_mode: IntimacyMode | None = None
    spoiler_mode: SpoilerMode | None = None
    spoiler_protection: bool | None = None
    pet_enabled: bool | None = None
    pet_position: PetPosition | None = None
    personality_override: str | None = None
    speaking_style_override: str | None = None
    custom_prompt_notes: str | None = None
    forbidden_topics: str | None = None


class CharacterSettingsPromptPreviewResponse(BaseModel):
    character_id: str
    settings_id: str
    prompt_preview: str
