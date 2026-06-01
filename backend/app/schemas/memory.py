from datetime import datetime

from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    memory_id: str
    user_id: str | None = None
    project_id: str | None = None
    memory_content: str
    memory_type: str
    importance: int
    source: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


class MemoryResponse(BaseModel):
    character_id: str
    user_id: str | None = None
    project_id: str | None = None
    user_preference_memory: list[MemoryItem] = Field(default_factory=list)
    relationship_memory: list[MemoryItem] = Field(default_factory=list)
    story_interaction_memory: list[MemoryItem] = Field(default_factory=list)
    emotional_state_memory: list[MemoryItem] = Field(default_factory=list)
    custom_memory: list[MemoryItem] = Field(default_factory=list)


class MemoryUpdateRequest(BaseModel):
    character_id: str
    memory_content: str
    memory_type: str
    importance: int = Field(default=3, ge=1, le=5)


class MemoryPatchRequest(BaseModel):
    content: str | None = None
    memory_content: str | None = None
    memory_type: str | None = None
    importance: int | None = Field(default=None, ge=1, le=5)

    def resolved_content(self) -> str | None:
        if self.memory_content is not None:
            return self.memory_content
        return self.content


class MemoryUpdateResponse(BaseModel):
    success: bool
    memory_id: str
    message: str
    memory: MemoryItem


class MemoryDeleteResponse(BaseModel):
    success: bool
    memory_id: str
    message: str


class MemoryDebugResponse(BaseModel):
    character_id: str
    user_id: str | None = None
    project_id: str | None = None
    memories: list[MemoryItem]
