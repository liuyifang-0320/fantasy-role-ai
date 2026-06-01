from typing import Literal

from pydantic import BaseModel, Field


SpoilerMode = Literal["non_spoiler", "semi_spoiler", "full_spoiler"]


class OwnerHint(BaseModel):
    parsed_document_id: str
    owner_character_name: str = ""
    document_scope: str = "unknown"


class LLMAnalyzeRequest(BaseModel):
    parsed_document_ids: list[str] = Field(default_factory=list)
    force_rebuild: bool = False
    use_llm: bool = True
    spoiler_mode: SpoilerMode = "non_spoiler"
    owner_hints: list[OwnerHint] = Field(default_factory=list)


class LLMAnalyzeResponse(BaseModel):
    analysis_id: str
    status: str
    summary: dict


class ScriptIntelligenceStatusResponse(BaseModel):
    analysis_id: str | None = None
    status: str = "not_started"
    provider: str = ""
    model: str = ""
    documents_count: int = 0
    chunks_count: int = 0
    characters_count: int = 0
    relationships_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class ScriptIntelligenceResultResponse(BaseModel):
    analysis_id: str | None = None
    status: str = "not_started"
    result: dict = Field(default_factory=dict)


class ScriptIntelligenceConfirmRequest(BaseModel):
    confirmed_candidate_ids: list[str] = Field(default_factory=list)
    rejected_candidate_ids: list[str] = Field(default_factory=list)
    confirmed_relationship_ids: list[str] = Field(default_factory=list)
    rejected_relationship_ids: list[str] = Field(default_factory=list)
    document_ownership: list[OwnerHint] = Field(default_factory=list)
    spoiler_mode: SpoilerMode = "non_spoiler"


class ScriptIntelligenceConfirmResponse(BaseModel):
    project_id: str
    confirmed_candidates: int = 0
    rejected_candidates: int = 0
    confirmed_relationships: int = 0
    rejected_relationships: int = 0
    candidates_updated: int = 0
    relationships_updated: int = 0
