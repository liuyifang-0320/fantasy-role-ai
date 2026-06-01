from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CharacterCandidate(Base):
    __tablename__ = "character_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    canonical_name: Mapped[str] = mapped_column(String(64), default="", index=True)
    display_name: Mapped[str] = mapped_column(String(64), default="")
    normalized_name: Mapped[str] = mapped_column(String(64), default="", index=True)
    aliases: Mapped[str] = mapped_column(Text, default="[]")
    candidate_type: Mapped[str] = mapped_column(String(32), default="unknown")
    source_types: Mapped[str] = mapped_column(Text, default="[]")
    evidence_spans: Mapped[str] = mapped_column(Text, default="[]")
    dialogue_count: Mapped[int] = mapped_column(default=0)
    mention_count: Mapped[int] = mapped_column(default=0)
    relationship_evidence: Mapped[str] = mapped_column(Text, default="[]")
    identity_hint: Mapped[str] = mapped_column(String(255), default="")
    personality_hint: Mapped[str] = mapped_column(String(255), default="")
    relationship_hints: Mapped[str] = mapped_column(Text, default="[]")
    evidence: Mapped[str] = mapped_column(Text, default="")
    source_document_ids: Mapped[str] = mapped_column(Text, default="[]")
    source_documents: Mapped[str] = mapped_column(Text, default="[]")
    evidence_json: Mapped[str] = mapped_column(Text, default="[]")
    role_type: Mapped[str] = mapped_column(String(32), default="unknown")
    extraction_method: Mapped[str] = mapped_column(String(32), default="rule_fallback")
    llm_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    llm_reason: Mapped[str] = mapped_column(Text, default="")
    llm_evidence: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_level: Mapped[str] = mapped_column(String(16), default="low")
    needs_human_review: Mapped[bool] = mapped_column(default=True)
    rejected_reason: Mapped[str] = mapped_column(Text, default="")
    merge_suggestions: Mapped[str] = mapped_column(Text, default="[]")
    reviewer_provider: Mapped[str] = mapped_column(String(32), default="rule")
    reviewer_status: Mapped[str] = mapped_column(String(32), default="not_reviewed")
    reviewer_reason: Mapped[str] = mapped_column(Text, default="")
    candidate_status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
