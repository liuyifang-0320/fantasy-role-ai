from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    user_id: str
    nickname: str
    avatar: str
    auth_provider: str
    user_status: str
    created_at: datetime
    updated_at: datetime | None = None


class DevLoginRequest(BaseModel):
    nickname: str = "开发测试用户"


class SwitchDevUserRequest(BaseModel):
    user_id: str


class WechatLoginRequest(BaseModel):
    code: str


class WechatLoginReservedResponse(BaseModel):
    status: str
    message: str
