from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CharacterRelationship(Base):
    __tablename__ = "character_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    relationship_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str] = mapped_column(String(32), index=True)
    source_character_name: Mapped[str] = mapped_column(String(64), index=True)
    target_character_name: Mapped[str] = mapped_column(String(64), index=True)
    relation_type: Mapped[str] = mapped_column(String(32), default="未知")
    relation_summary: Mapped[str] = mapped_column(String(255), default="")
    evidence: Mapped[str] = mapped_column(Text, default="")
    source_document_ids: Mapped[str] = mapped_column(Text, default="[]")
    is_explicit: Mapped[bool] = mapped_column(default=True)
    is_inferred: Mapped[bool] = mapped_column(default=False)
    evidence_summary: Mapped[str] = mapped_column(Text, default="")
    evidence_json: Mapped[str] = mapped_column(Text, default="[]")
    confidence_level: Mapped[str] = mapped_column(String(16), default="medium")
    spoiler_level: Mapped[str] = mapped_column(String(16), default="none")
    visibility: Mapped[str] = mapped_column(String(16), default="public")
    needs_human_review: Mapped[bool] = mapped_column(default=True)
    extraction_method: Mapped[str] = mapped_column(String(32), default="rule_fallback")
    reviewer_provider: Mapped[str] = mapped_column(String(32), default="rule")
    reviewer_status: Mapped[str] = mapped_column(String(32), default="rule_fallback")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    relationship_status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
