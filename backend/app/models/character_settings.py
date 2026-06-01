from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CharacterSettings(Base):
    __tablename__ = "character_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    settings_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.character_id"),
        unique=True,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(64), default="")
    user_persona_name: Mapped[str] = mapped_column(String(64), default="")
    nickname_for_user: Mapped[str] = mapped_column(String(64), default="")
    relationship_with_user: Mapped[str] = mapped_column(String(128), default="")
    relationship_stage: Mapped[str] = mapped_column(String(64), default="")
    tone_style: Mapped[str] = mapped_column(String(32), default="original")
    reply_length: Mapped[str] = mapped_column(String(16), default="medium")
    intimacy_mode: Mapped[str] = mapped_column(String(16), default="normal")
    spoiler_mode: Mapped[str] = mapped_column(String(16), default="non_spoiler")
    spoiler_protection: Mapped[bool] = mapped_column(Boolean, default=True)
    pet_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    pet_position: Mapped[str] = mapped_column(String(32), default="bottom_right")
    personality_override: Mapped[str] = mapped_column(Text, default="")
    speaking_style_override: Mapped[str] = mapped_column(Text, default="")
    custom_prompt_notes: Mapped[str] = mapped_column(Text, default="")
    forbidden_topics: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    character = relationship("Character", back_populates="settings")
