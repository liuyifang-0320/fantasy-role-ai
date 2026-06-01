from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.auth import (
    DevLoginRequest,
    SwitchDevUserRequest,
    UserResponse,
    WechatLoginRequest,
    WechatLoginReservedResponse,
)
from app.services.auth import create_dev_user, get_current_user, get_or_create_user


router = APIRouter()


def serialize_user(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        nickname=user.nickname,
        avatar=user.avatar,
        auth_provider=user.auth_provider,
        user_status=user.user_status,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return serialize_user(current_user)


@router.post("/dev-login", response_model=UserResponse)
def dev_login(
    payload: DevLoginRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    user = create_dev_user(db, payload.nickname)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.post("/switch-dev-user", response_model=UserResponse)
def switch_dev_user(
    payload: SwitchDevUserRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    user = get_or_create_user(db, user_id=payload.user_id, nickname=payload.user_id)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.post("/wechat-login", response_model=WechatLoginReservedResponse)
def wechat_login_reserved(
    payload: WechatLoginRequest,
) -> WechatLoginReservedResponse:
    return WechatLoginReservedResponse(
        status="not_implemented",
        message="微信登录接口已预留，正式上线阶段接入 code2session。",
    )
