from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScriptSegment(Base):
    __tablename__ = "script_segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    segment_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str] = mapped_column(String(32), index=True)
    parsed_document_id: Mapped[str] = mapped_column(String(32), index=True)
    segment_type: Mapped[str] = mapped_column(String(48), default="unknown")
    title: Mapped[str] = mapped_column(String(255), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    clean_content: Mapped[str] = mapped_column(Text, default="")
    start_offset: Mapped[int] = mapped_column(Integer, default=0)
    end_offset: Mapped[int] = mapped_column(Integer, default=0)
    visibility: Mapped[str] = mapped_column(String(32), default="public")
    spoiler_level: Mapped[str] = mapped_column(String(32), default="none")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source_filename: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
