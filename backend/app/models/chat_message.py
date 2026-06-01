from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("chat_sessions.session_id"),
        index=True,
    )
    character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.character_id"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    pet_action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    memory_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_snapshot: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
    character = relationship("Character", back_populates="chat_messages")
