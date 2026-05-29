from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """创建用户 - 请求体"""
    username: str = Field(min_length=1, max_length=64, description="登录用户名")
    email: EmailStr = Field(description="邮箱地址")
    password: str = Field(min_length=6, max_length=128, description="明文密码")


class UserUpdate(BaseModel):
    """更新用户 - 请求体。所有字段可选，只传要改的"""
    username: Optional[str] = Field(default=None, min_length=1, max_length=64)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=1, max_length=128)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """用户信息 - 响应体。绝不包含 hashed_password"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
