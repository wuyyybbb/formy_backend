# -*- coding: utf-8 -*-
"""
计费和套餐相关的 Pydantic 模型
"""
from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class UserBillingInfo(BaseModel):
    """用户计费信息"""
    user_id: UUID = Field(..., description="用户ID（UUID 格式）")
    email: str = Field(..., description="邮箱地址")
    
    # 当前套餐
    current_plan_id: Optional[str] = Field(None, description="当前套餐ID")
    current_plan_name: Optional[str] = Field(None, description="当前套餐名称")
    
    # 算力信息
    current_credits: int = Field(..., description="当前剩余算力")
    monthly_credits: int = Field(default=0, description="每月总算力额度")
    total_credits_used: int = Field(default=0, description="累计使用算力")
    
    # 时间信息
    plan_renew_at: Optional[datetime] = Field(None, description="套餐下次续费时间")
    
    # 计算字段
    credits_usage_percentage: float = Field(default=0.0, description="本月算力使用百分比")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "email": "user@example.com",
                "current_plan_id": "pro",
                "current_plan_name": "PRO",
                "current_credits": 8500,
                "monthly_credits": 12000,
                "total_credits_used": 35000,
                "plan_renew_at": "2025-12-01T00:00:00",
                "credits_usage_percentage": 29.17
            }
        }


class ChangePlanRequest(BaseModel):
    """切换套餐请求"""
    plan_id: str = Field(..., description="目标套餐ID（starter/basic/pro/ultimate）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "pro"
            }
        }


class ChangePlanResponse(BaseModel):
    """切换套餐响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="操作消息")
    new_plan_id: str = Field(..., description="新套餐ID")
    new_plan_name: str = Field(..., description="新套餐名称")
    new_credits: int = Field(..., description="新的算力额度")
    plan_renew_at: datetime = Field(..., description="下次续费时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "套餐切换成功",
                "new_plan_id": "pro",
                "new_plan_name": "PRO",
                "new_credits": 12000,
                "plan_renew_at": "2025-12-01T00:00:00"
            }
        }


class CreditTransaction(BaseModel):
    """算力交易记录（未来扩展）"""
    transaction_id: str
    user_id: UUID
    amount: int  # 正数为增加，负数为消耗
    balance_after: int
    transaction_type: str  # "recharge", "consume", "refund", "monthly_reset"
    description: str
    created_at: datetime = Field(default_factory=datetime.now)

