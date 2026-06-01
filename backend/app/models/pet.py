from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(primary_key=True)
    pet_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.character_id"),
        unique=True,
    )
    pet_name: Mapped[str] = mapped_column(String(64))
    pet_avatar: Mapped[str] = mapped_column(String(255))
    pet_type: Mapped[str] = mapped_column(String(32), default="q_chibi")
    pet_status: Mapped[str] = mapped_column(String(32), default="idle")
    available_actions: Mapped[list[str]] = mapped_column(JSON)

    character = relationship("Character", back_populates="pet")
