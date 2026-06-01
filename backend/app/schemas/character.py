from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.file import ParsedDocumentSummary
from app.schemas.knowledge import KnowledgeChunkPreview
from app.schemas.pet import PetInfo
from app.schemas.pet_asset import PetAssetSummary
from app.schemas.profile import CharacterProfileResponse


class CharacterGenerateRequest(BaseModel):
    project_id: str | None = None
    uploaded_file_ids: list[str]
    target_character_name: str
    user_persona_name: str
    relationship_hint: str


class CharacterResponse(BaseModel):
    character_id: str
    user_id: str | None = None
    project_id: str | None = None
    character_name: str
    character_identity: str
    personality: str
    description: str
    user_persona_name: str
    relationship_with_user: str
    relationship_stage: str
    intimacy_level: int
    avatar: str
    pet: PetInfo
    profile_id: str | None = None
    profile: CharacterProfileResponse | None = None
    knowledge_chunk_count: int = 0
    knowledge_chunks_preview: list[KnowledgeChunkPreview] = Field(default_factory=list)
    pet_assets: list[PetAssetSummary] = Field(default_factory=list)
    active_pet_asset: PetAssetSummary | None = None


class CharacterListItem(CharacterResponse):
    last_message: str
    updated_at: datetime


class GeneratedCharacterResponse(CharacterResponse):
    parsed_document_ids: list[str]
    parsed_documents: list[ParsedDocumentSummary]
