from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ParsedDocument(Base):
    __tablename__ = "parsed_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    parsed_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    file_id: Mapped[str] = mapped_column(ForeignKey("uploaded_files.file_id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(32))
    parse_status: Mapped[str] = mapped_column(String(32), default="pending")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    text_preview: Mapped[str] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    ocr_provider: Mapped[str] = mapped_column(String(32), default="")
    ocr_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    ocr_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_warning: Mapped[str] = mapped_column(Text, default="")
    safety_categories: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
