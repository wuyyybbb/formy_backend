"""
认证相关的数据传输对象
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    email: EmailStr = Field(..., description="邮箱地址")


class SendCodeResponse(BaseModel):
    """发送验证码响应"""
    success: bool
    message: str
    expires_in: int = Field(..., description="验证码有效期（秒）")


class LoginRequest(BaseModel):
    """验证码登录请求"""
    email: EmailStr = Field(..., description="邮箱地址")
    code: str = Field(..., min_length=6, max_length=6, description="6位验证码")


class SetPasswordRequest(BaseModel):
    """设置密码请求（需要登录，使用 token 认证）"""
    password: str = Field(..., min_length=6, max_length=50, description="密码（6-50位）")


class SetPasswordResponse(BaseModel):
    """设置密码响应"""
    success: bool
    message: str


class PasswordLoginRequest(BaseModel):
    """密码登录请求"""
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: "UserInfo"
    refresh_token: Optional[str] = Field(None, description="刷新令牌（用于获取新的 access_token）")


class UserInfo(BaseModel):
    """用户信息"""
    user_id: UUID
    email: EmailStr
    username: Optional[str] = None
    avatar: Optional[str] = None
    created_at: str
    last_login: Optional[str] = None


class CurrentUserResponse(BaseModel):
    """当前用户响应"""
    user: UserInfo


class SignupRequest(BaseModel):
    """注册请求（使用 PostgreSQL）"""
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=50, description="密码（6-50位）")


class SignupResponse(BaseModel):
    """注册响应"""
    success: bool
    message: str
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: UserInfo
    refresh_token: Optional[str] = Field(None, description="刷新令牌（用于获取新的 access_token）")


class RefreshRequest(BaseModel):
    """刷新 token 请求"""
    refresh_token: str


class RefreshResponse(BaseModel):
    """刷新 token 响应"""
    access_token: str
    token_type: str = Field(default="bearer")
    refresh_token: Optional[str] = None

