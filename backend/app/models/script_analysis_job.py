from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScriptAnalysisJob(Base):
    __tablename__ = "script_analysis_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    provider: Mapped[str] = mapped_column(String(32), default="rule_fallback")
    model: Mapped[str] = mapped_column(String(128), default="")
    documents_count: Mapped[int] = mapped_column(Integer, default=0)
    chunks_count: Mapped[int] = mapped_column(Integer, default=0)
    characters_count: Mapped[int] = mapped_column(Integer, default=0)
    relationships_count: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[str] = mapped_column(Text, default="[]")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
