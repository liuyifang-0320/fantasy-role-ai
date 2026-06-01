from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.character import GeneratedCharacterResponse


CandidateStatus = Literal["pending", "confirmed", "ignored", "generated", "rejected"]
CandidateType = Literal[
    "person",
    "organization",
    "place",
    "prop",
    "clue",
    "document_term",
    "structure_term",
    "abstract",
    "action_phrase",
    "noise",
    "unknown",
]
ConfidenceLevel = Literal["high", "medium", "low"]


class CharacterCandidateResponse(BaseModel):
    candidate_id: str
    user_id: str | None = None
    project_id: str
    name: str
    canonical_name: str = ""
    display_name: str = ""
    normalized_name: str = ""
    aliases: list[str] = Field(default_factory=list)
    candidate_type: CandidateType = "unknown"
    source_types: list[str] = Field(default_factory=list)
    evidence_spans: list[str] = Field(default_factory=list)
    dialogue_count: int = 0
    mention_count: int = 0
    relationship_evidence: list[str] = Field(default_factory=list)
    identity_hint: str
    personality_hint: str
    relationship_hints: list[str] = Field(default_factory=list)
    evidence: str
    source_document_ids: list[str] = Field(default_factory=list)
    source_documents: list[str] = Field(default_factory=list)
    evidence_json: list[str] = Field(default_factory=list)
    role_type: str = "unknown"
    extraction_method: str = "rule_fallback"
    llm_confidence: float = 0.0
    llm_reason: str = ""
    llm_evidence: str = ""
    confidence: float
    confidence_level: ConfidenceLevel = "low"
    needs_human_review: bool = True
    rejected_reason: str = ""
    merge_suggestions: list[str] = Field(default_factory=list)
    reviewer_provider: str = ""
    reviewer_status: str = ""
    reviewer_reason: str = ""
    candidate_status: CandidateStatus
    created_at: datetime
    updated_at: datetime | None


class CharacterCandidateUpdateRequest(BaseModel):
    name: str | None = None
    canonical_name: str | None = None
    display_name: str | None = None
    aliases: list[str] | str | None = None
    candidate_type: CandidateType | None = None
    confidence_level: ConfidenceLevel | None = None
    needs_human_review: bool | None = None
    rejected_reason: str | None = None
    merge_suggestions: list[str] | str | None = None
    identity_hint: str | None = None
    personality_hint: str | None = None
    relationship_hints: list[str] | str | None = None
    role_type: str | None = None
    candidate_status: CandidateStatus | None = None


class BatchGenerateRequest(BaseModel):
    candidate_ids: list[str]
    user_persona_name: str
    default_relationship_hint: str = "根据剧本资料生成"
    relationship_overrides: dict[str, str] = Field(default_factory=dict)


class BatchGenerateSkipped(BaseModel):
    candidate_id: str
    name: str
    reason: str


class BatchGenerateFailed(BaseModel):
    candidate_id: str
    name: str
    reason: str


class BatchGenerateResponse(BaseModel):
    generated: list[GeneratedCharacterResponse] = Field(default_factory=list)
    skipped: list[BatchGenerateSkipped] = Field(default_factory=list)
    failed: list[BatchGenerateFailed] = Field(default_factory=list)
