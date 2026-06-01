from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    character_id: str
    session_id: str | None = None
    message: str


class RetrievedChunkPreview(BaseModel):
    chunk_id: str
    visibility: str
    content_preview: str
    restricted: bool


class ActiveMemoryPreview(BaseModel):
    memory_id: str
    memory_type: str
    content: str
    importance: int


class RelationshipPreview(BaseModel):
    relationship_id: str
    source_character_name: str
    target_character_name: str
    relation_type: str
    relation_summary: str


class PromptDebug(BaseModel):
    project_id: str | None = None
    retrieval_project_scope: str
    system_prompt_preview: str
    context_message_count: int
    uses_character_profile: bool
    uses_character_settings: bool
    uses_safety_prompt: bool
    settings_prompt_preview: str
    retrieval_scope: str
    retrieved_chunk_count: int
    retrieved_chunks_preview: list[RetrievedChunkPreview]
    active_memory_count: int
    active_memories_preview: list[ActiveMemoryPreview]
    active_relationship_count: int
    relationships_preview: list[RelationshipPreview]


class MemoryCandidateDebug(BaseModel):
    memory_type: str
    content: str
    importance: int
    saved: bool
    reason: str


class MemoryDebug(BaseModel):
    created_count: int
    candidates: list[MemoryCandidateDebug]


class ProviderDebug(BaseModel):
    configured_provider: str
    provider: str
    model: str
    base_url_configured: bool
    api_key_configured: bool
    fallback: bool
    fallback_reason: str | None


class SafetyDebug(BaseModel):
    user_input_action: str
    assistant_output_action: str
    matched_categories: list[str]


class ChatResponse(BaseModel):
    reply: str
    pet_action: str
    memory_hint: str
    session_id: str
    message_id: str
    prompt_debug: PromptDebug | None
    memory_debug: MemoryDebug | None
    safety_debug: SafetyDebug | None = None
    provider_debug: ProviderDebug


class ChatMessageResponse(BaseModel):
    message_id: str
    session_id: str
    user_id: str | None = None
    project_id: str | None = None
    character_id: str
    role: str
    content: str
    pet_action: str | None
    memory_hint: str | None
    created_at: datetime


class ChatSessionResponse(BaseModel):
    session_id: str
    user_id: str | None = None
    project_id: str | None = None
    character_id: str
    title: str
    created_at: datetime
    updated_at: datetime
