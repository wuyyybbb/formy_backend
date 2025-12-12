"""
用户模型
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """用户模型"""
    user_id: UUID = Field(..., description="用户 ID（UUID 格式）")
    email: EmailStr = Field(..., description="邮箱地址")
    username: Optional[str] = Field(None, description="用户名")
    avatar: Optional[str] = Field(None, description="头像 URL")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    is_active: bool = Field(default=True, description="是否激活")
    signup_bonus_granted: bool = Field(default=False, description="注册/白名单奖励是否已发放")
    
    # 密码（加密存储，可选）
    password_hash: Optional[str] = Field(None, description="密码哈希值（bcrypt）")
    has_password: bool = Field(default=False, description="是否设置了密码")
    
    # 套餐和算力相关字段
    current_plan_id: Optional[str] = Field(None, description="当前套餐ID（starter/basic/pro/ultimate）")
    current_credits: int = Field(default=0, description="当前剩余算力")
    plan_renew_at: Optional[datetime] = Field(None, description="套餐下次续费时间（算力重置时间）")
    total_credits_used: int = Field(default=0, description="累计使用算力")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class VerificationCode(BaseModel):
    """验证码模型"""
    email: EmailStr
    code: str
    expires_at: datetime
    is_used: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

