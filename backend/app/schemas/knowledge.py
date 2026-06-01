from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBuildRequest(BaseModel):
    project_id: str | None = None
    parsed_document_ids: list[str]
    target_character_name: str
    user_persona_name: str
    character_id: str | None = None


class KnowledgeChunkPreview(BaseModel):
    chunk_id: str
    chapter: str
    visibility: str
    content_preview: str


class KnowledgeBuildResponse(BaseModel):
    knowledge_chunk_count: int
    knowledge_chunks_preview: list[KnowledgeChunkPreview]


class KnowledgeChunkResponse(KnowledgeChunkPreview):
    user_id: str | None = None
    project_id: str | None = None
    parsed_document_id: str
    file_id: str
    character_id: str | None
    target_character_name: str
    user_persona_name: str
    chunk_index: int
    content: str
    keywords: str
    source_type: str
    created_at: datetime


class KnowledgeSearchRequest(BaseModel):
    character_id: str
    project_id: str | None = None
    query: str
    limit: int = Field(default=5, ge=1, le=20)


class RetrievedKnowledgeChunk(BaseModel):
    chunk_id: str
    content_preview: str
    content: str
    score: int
    visibility: str
    restricted: bool
    retrieval_scope: str
    retrieval_project_scope: str | None = None
    project_id: str | None = None
