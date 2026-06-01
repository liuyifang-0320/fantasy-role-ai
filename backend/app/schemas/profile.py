from datetime import datetime

from pydantic import BaseModel


class CharacterProfileExtractRequest(BaseModel):
    project_id: str | None = None
    parsed_document_ids: list[str]
    target_character_name: str
    user_persona_name: str
    relationship_hint: str


class CharacterProfileResponse(BaseModel):
    profile_id: str
    user_id: str | None = None
    project_id: str | None = None
    character_id: str | None
    parsed_document_id: str | None
    target_character_name: str
    user_persona_name: str
    relationship_hint: str
    extracted_identity: str
    extracted_personality: str
    speaking_style: str
    background_summary: str
    relationship_summary: str
    story_stage: str
    known_facts: list[str]
    hidden_secrets: list[str]
    spoiler_guardrails: list[str]
    source_preview: str
    extraction_status: str
    created_at: datetime
