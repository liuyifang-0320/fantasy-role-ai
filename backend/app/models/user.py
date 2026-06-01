from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(64), default="")
    avatar: Mapped[str] = mapped_column(String(255), default="")
    auth_provider: Mapped[str] = mapped_column(String(32), default="dev_mock")
    openid: Mapped[str] = mapped_column(String(128), default="")
    unionid: Mapped[str] = mapped_column(String(128), default="")
    phone: Mapped[str] = mapped_column(String(32), default="")
    user_status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
