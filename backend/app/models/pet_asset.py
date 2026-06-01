from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PetAsset(Base):
    __tablename__ = "pet_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.character_id"),
        index=True,
    )
    pet_id: Mapped[str] = mapped_column(
        ForeignKey("pets.pet_id"),
        index=True,
    )
    asset_type: Mapped[str] = mapped_column(String(32), default="static_image")
    style: Mapped[str] = mapped_column(String(32), default="q_chibi")
    prompt: Mapped[str] = mapped_column(Text, default="")
    negative_prompt: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(String(255), default="")
    local_path: Mapped[str] = mapped_column(String(255), default="")
    generation_provider: Mapped[str] = mapped_column(String(32), default="mock")
    generation_status: Mapped[str] = mapped_column(String(32), default="mock")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    character = relationship("Character", back_populates="pet_assets")
    pet = relationship("Pet")
