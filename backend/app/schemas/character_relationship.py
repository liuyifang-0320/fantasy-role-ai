from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RelationshipStatus = Literal["pending", "confirmed", "ignored"]


class CharacterRelationshipResponse(BaseModel):
    relationship_id: str
    user_id: str | None = None
    project_id: str
    source_character_name: str
    target_character_name: str
    relation_type: str
    relation_summary: str
    evidence: str
    source_document_ids: list[str] = Field(default_factory=list)
    is_explicit: bool = True
    is_inferred: bool = False
    evidence_summary: str = ""
    evidence_json: list[str] = Field(default_factory=list)
    confidence_level: str = "medium"
    spoiler_level: str = "none"
    visibility: str = "public"
    needs_human_review: bool = True
    extraction_method: str = "rule_fallback"
    reviewer_provider: str = "rule"
    reviewer_status: str = "rule_fallback"
    confidence: float
    relationship_status: RelationshipStatus
    created_at: datetime
    updated_at: datetime | None


class CharacterRelationshipUpdateRequest(BaseModel):
    source_character_name: str | None = None
    target_character_name: str | None = None
    relation_type: str | None = None
    relation_summary: str | None = None
    relationship_status: RelationshipStatus | None = None


class RelationshipGraphNode(BaseModel):
    id: str
    label: str


class RelationshipGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    summary: str


class RelationshipGraphResponse(BaseModel):
    nodes: list[RelationshipGraphNode] = Field(default_factory=list)
    edges: list[RelationshipGraphEdge] = Field(default_factory=list)
