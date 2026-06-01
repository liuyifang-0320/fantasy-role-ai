from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SafetyLog(Base):
    __tablename__ = "safety_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    safety_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    character_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    message_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    direction: Mapped[str] = mapped_column(String(32), index=True)
    input_text: Mapped[str] = mapped_column(Text, default="")
    matched_categories: Mapped[str] = mapped_column(Text, default="[]")
    action: Mapped[str] = mapped_column(String(32), default="allow")
    safe_reply: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
