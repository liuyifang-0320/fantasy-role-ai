from datetime import datetime

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.services.ids import next_prefixed_id


DEFAULT_DEV_USER_ID = "dev_user"
DEFAULT_DEV_NICKNAME = "开发测试用户"


def get_or_create_user(
    db: Session,
    *,
    user_id: str,
    nickname: str | None = None,
    auth_provider: str = "dev_mock",
) -> User:
    normalized_user_id = (user_id or DEFAULT_DEV_USER_ID).strip() or DEFAULT_DEV_USER_ID
    user = db.scalar(select(User).where(User.user_id == normalized_user_id))
    if user:
        if nickname and nickname.strip() and user.nickname != nickname.strip():
            user.nickname = nickname.strip()
            user.updated_at = datetime.utcnow()
            db.flush()
        return user

    user = User(
        user_id=normalized_user_id,
        nickname=(nickname or DEFAULT_DEV_NICKNAME).strip() or DEFAULT_DEV_NICKNAME,
        auth_provider=auth_provider,
        user_status="active",
    )
    db.add(user)
    db.flush()
    return user


def create_dev_user(db: Session, nickname: str) -> User:
    user = User(
        user_id=next_prefixed_id(db, User, "user"),
        nickname=nickname.strip() or DEFAULT_DEV_NICKNAME,
        auth_provider="dev_mock",
        user_status="active",
    )
    db.add(user)
    db.flush()
    return user


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    requested_user_id = request.headers.get("X-User-Id") or DEFAULT_DEV_USER_ID
    user = get_or_create_user(
        db,
        user_id=requested_user_id,
        nickname=DEFAULT_DEV_NICKNAME if requested_user_id == DEFAULT_DEV_USER_ID else None,
    )
    db.commit()
    db.refresh(user)
    return user
