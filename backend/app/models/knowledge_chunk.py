from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    chunk_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    parsed_document_id: Mapped[str] = mapped_column(
        ForeignKey("parsed_documents.parsed_id"),
        index=True,
    )
    file_id: Mapped[str] = mapped_column(ForeignKey("uploaded_files.file_id"), index=True)
    character_id: Mapped[str | None] = mapped_column(
        ForeignKey("characters.character_id"),
        nullable=True,
        index=True,
    )
    target_character_name: Mapped[str] = mapped_column(String(64))
    user_persona_name: Mapped[str] = mapped_column(String(64))
    chapter: Mapped[str] = mapped_column(String(64), default="未分章")
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_preview: Mapped[str] = mapped_column(Text)
    keywords: Mapped[str] = mapped_column(Text, default="")
    visibility: Mapped[str] = mapped_column(String(32), default="unknown")
    segment_type: Mapped[str] = mapped_column(String(48), default="unknown")
    spoiler_level: Mapped[str] = mapped_column(String(32), default="none")
    character_scope: Mapped[str] = mapped_column(String(64), default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    source_type: Mapped[str] = mapped_column(String(32), default="parsed_text")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
