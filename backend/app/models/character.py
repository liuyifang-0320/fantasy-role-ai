from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    character_name: Mapped[str] = mapped_column(String(64))
    character_identity: Mapped[str] = mapped_column(String(255))
    personality: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    user_persona_name: Mapped[str] = mapped_column(String(64))
    relationship_with_user: Mapped[str] = mapped_column(String(64))
    relationship_stage: Mapped[str] = mapped_column(String(64))
    intimacy_level: Mapped[int] = mapped_column(Integer, default=1)
    avatar: Mapped[str] = mapped_column(String(255))
    last_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    pet = relationship("Pet", back_populates="character", uselist=False)
    memories = relationship("Memory", back_populates="character")
    profiles = relationship("CharacterProfile", back_populates="character")
    chat_sessions = relationship("ChatSession", back_populates="character")
    chat_messages = relationship("ChatMessage", back_populates="character")
    settings = relationship("CharacterSettings", back_populates="character", uselist=False)
    pet_assets = relationship("PetAsset", back_populates="character")
