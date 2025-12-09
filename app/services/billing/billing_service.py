# -*- coding: utf-8 -*-
"""
计费服务
管理用户套餐、算力等
"""
import redis
import json
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.models.user import User
from app.schemas.billing import UserBillingInfo, ChangePlanResponse
from app.config.plans import get_plan_by_id
from app.utils.redis_client import get_redis_client


class BillingService:
    """计费服务"""
    
    def __init__(self):
        # 使用统一的 Redis 客户端（基于 REDIS_URL）
        self.redis_client = get_redis_client()
    
    def _get_user_key(self, user_id: str) -> str:
        """获取用户在 Redis 中的键"""
        return f"user:id:{user_id}"
    
    def get_user(self, user_id: str) -> Optional[User]:
        """
        从 Redis 获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象，如果不存在则返回 None
        """
        user_key = self._get_user_key(user_id)
        user_data = self.redis_client.get(user_key)
        
        if not user_data:
            return None
        
        user_dict = json.loads(user_data)
        # 转换日期时间字符串为 datetime 对象
        if user_dict.get("created_at"):
            user_dict["created_at"] = datetime.fromisoformat(user_dict["created_at"])
        if user_dict.get("last_login"):
            user_dict["last_login"] = datetime.fromisoformat(user_dict["last_login"])
        if user_dict.get("plan_renew_at"):
            user_dict["plan_renew_at"] = datetime.fromisoformat(user_dict["plan_renew_at"])
        
        return User(**user_dict)
    
    def save_user(self, user: User) -> None:
        """
        保存用户信息到 Redis
        
        Args:
            user: 用户对象
        """
        user_key = self._get_user_key(user.user_id)
        user_dict = user.model_dump()
        
        # 转换 datetime 对象为字符串
        if user_dict.get("created_at"):
            user_dict["created_at"] = user_dict["created_at"].isoformat()
        if user_dict.get("last_login"):
            user_dict["last_login"] = user_dict["last_login"].isoformat()
        if user_dict.get("plan_renew_at"):
            user_dict["plan_renew_at"] = user_dict["plan_renew_at"].isoformat()
        
        self.redis_client.set(user_key, json.dumps(user_dict, default=str))
    
    def get_user_billing_info(self, user_id: str) -> Optional[UserBillingInfo]:
        """
        获取用户的计费信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户计费信息，如果用户不存在则返回 None
        """
        user = self.get_user(user_id)
        if not user:
            return None
        
        # 获取当前套餐信息
        plan = get_plan_by_id(user.current_plan_id) if user.current_plan_id else None
        plan_name = plan.name if plan else None
        monthly_credits = plan.monthly_credits if plan else 0
        
        # 计算使用百分比
        usage_percentage = 0.0
        if monthly_credits > 0:
            used_credits = monthly_credits - user.current_credits
            usage_percentage = round((used_credits / monthly_credits) * 100, 2)
        
        return UserBillingInfo(
            user_id=user.user_id,
            email=user.email,
            current_plan_id=user.current_plan_id,
            current_plan_name=plan_name,
            current_credits=user.current_credits,
            monthly_credits=monthly_credits,
            total_credits_used=user.total_credits_used,
            plan_renew_at=user.plan_renew_at,
            credits_usage_percentage=usage_percentage
        )
    
    def change_plan(
        self,
        user_id: str,
        new_plan_id: str,
        reset_credits: bool = True
    ) -> ChangePlanResponse:
        """
        切换用户套餐
        
        Args:
            user_id: 用户ID
            new_plan_id: 新套餐ID
            reset_credits: 是否重置算力（默认 True）
            
        Returns:
            切换结果
            
        Raises:
            ValueError: 如果套餐不存在或用户不存在
        """
        # 获取用户
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"用户 {user_id} 不存在")
        
        # 获取新套餐
        new_plan = get_plan_by_id(new_plan_id)
        if not new_plan:
            raise ValueError(f"套餐 {new_plan_id} 不存在")
        
        # 更新用户套餐
        user.current_plan_id = new_plan_id
        
        # 重置算力
        if reset_credits:
            user.current_credits = new_plan.monthly_credits
        
        # 设置下次续费时间（当前时间 + 1 个月）
        now = datetime.now()
        # 计算下个月的同一天
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        user.plan_renew_at = next_month
        
        # 保存用户
        self.save_user(user)
        
        return ChangePlanResponse(
            success=True,
            message=f"成功切换到 {new_plan.name} 套餐",
            new_plan_id=new_plan_id,
            new_plan_name=new_plan.name,
            new_credits=user.current_credits,
            plan_renew_at=user.plan_renew_at
        )
    
    def consume_credits(self, user_id: str, amount: int) -> bool:
        """
        消耗用户算力
        
        Args:
            user_id: 用户ID
            amount: 消耗的算力数量
            
        Returns:
            是否成功
        """
        user = self.get_user(user_id)
        if not user:
            return False
        
        # 检查算力是否足够
        if user.current_credits < amount:
            return False
        
        # 扣除算力
        user.current_credits -= amount
        user.total_credits_used += amount
        
        # 保存
        self.save_user(user)
        return True
    
    def add_credits(self, user_id: str, amount: int) -> bool:
        """
        增加用户算力（充值、赠送等）
        
        Args:
            user_id: 用户ID
            amount: 增加的算力数量
            
        Returns:
            是否成功
        """
        user = self.get_user(user_id)
        if not user:
            return False
        
        user.current_credits += amount
        self.save_user(user)
        return True
    
    def check_and_renew_plan(self, user_id: str) -> bool:
        """
        检查并自动续费套餐（如果到期）
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否进行了续费
        """
        user = self.get_user(user_id)
        if not user or not user.plan_renew_at:
            return False
        
        # 检查是否到期
        now = datetime.now()
        if now >= user.plan_renew_at:
            # 重置算力
            plan = get_plan_by_id(user.current_plan_id)
            if plan:
                user.current_credits = plan.monthly_credits
                
                # 设置下次续费时间
                if user.plan_renew_at.month == 12:
                    next_month = user.plan_renew_at.replace(
                        year=user.plan_renew_at.year + 1,
                        month=1
                    )
                else:
                    next_month = user.plan_renew_at.replace(
                        month=user.plan_renew_at.month + 1
                    )
                
                user.plan_renew_at = next_month
                self.save_user(user)
                return True
        
        return False


# 全局实例
billing_service = BillingService()

