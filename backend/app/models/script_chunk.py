from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScriptChunk(Base):
    __tablename__ = "script_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    chunk_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str] = mapped_column(String(32), index=True)
    parsed_document_id: Mapped[str] = mapped_column(String(32), index=True)
    segment_id: Mapped[str] = mapped_column(String(32), index=True)
    chunk_text: Mapped[str] = mapped_column(Text, default="")
    clean_text: Mapped[str] = mapped_column(Text, default="")
    chunk_index: Mapped[int] = mapped_column(Integer, default=1)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    document_type: Mapped[str] = mapped_column(String(48), default="unknown")
    owner_character_name: Mapped[str] = mapped_column(String(64), default="")
    perspective: Mapped[str] = mapped_column(String(32), default="unknown")
    visibility: Mapped[str] = mapped_column(String(32), default="public")
    spoiler_level: Mapped[str] = mapped_column(String(32), default="none")
    source_type: Mapped[str] = mapped_column(String(32), default="parsed_text")
    character_scope: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
