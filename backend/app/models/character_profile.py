from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CharacterProfile(Base):
    __tablename__ = "character_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    character_id: Mapped[str | None] = mapped_column(
        ForeignKey("characters.character_id"),
        nullable=True,
        index=True,
    )
    parsed_document_id: Mapped[str | None] = mapped_column(
        ForeignKey("parsed_documents.parsed_id"),
        nullable=True,
        index=True,
    )
    target_character_name: Mapped[str] = mapped_column(String(64))
    user_persona_name: Mapped[str] = mapped_column(String(64))
    relationship_hint: Mapped[str] = mapped_column(String(128))
    extracted_identity: Mapped[str] = mapped_column(String(255))
    extracted_personality: Mapped[str] = mapped_column(String(255))
    speaking_style: Mapped[str] = mapped_column(String(255))
    background_summary: Mapped[str] = mapped_column(Text)
    relationship_summary: Mapped[str] = mapped_column(Text)
    story_stage: Mapped[str] = mapped_column(String(64))
    known_facts: Mapped[str] = mapped_column(Text, default="[]")
    hidden_secrets: Mapped[str] = mapped_column(Text, default="[]")
    spoiler_guardrails: Mapped[str] = mapped_column(Text, default="[]")
    source_preview: Mapped[str] = mapped_column(Text, default="")
    extraction_status: Mapped[str] = mapped_column(String(32), default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    character = relationship("Character", back_populates="profiles")
