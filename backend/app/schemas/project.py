from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    source_type: str = "upload"


class ProjectUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    source_type: str | None = None
    cover_image: str | None = None
    project_status: str | None = None


class ProjectSummary(BaseModel):
    file_count: int
    parsed_document_count: int
    character_count: int
    knowledge_chunk_count: int
    latest_updated_at: datetime | None = None


class ProjectResponse(BaseModel):
    project_id: str
    user_id: str | None = None
    title: str
    description: str
    source_type: str
    cover_image: str
    project_status: str
    created_at: datetime
    updated_at: datetime
    summary: ProjectSummary | None = None
