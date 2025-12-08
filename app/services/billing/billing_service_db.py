# -*- coding: utf-8 -*-
"""
计费服务（数据库版本）
管理用户套餐、算力等（使用 PostgreSQL 而不是 Redis）
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from app.models.user import User
from app.schemas.billing import UserBillingInfo, ChangePlanResponse
from app.config.plans import get_plan_by_id
from app.db import crud_users


class BillingServiceDB:
    """计费服务（数据库版本）"""
    
    def get_user(self, user_id: str) -> Optional[User]:
        """
        从数据库获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象，如果不存在则返回 None
        """
        return asyncio.run(crud_users.get_user_by_id(user_id))
    
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
        
        # 计算新的积分值
        new_credits = new_plan.monthly_credits if reset_credits else user.current_credits
        
        # 设置下次续费时间（当前时间 + 1 个月）
        now = datetime.now()
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 更新数据库
        async def _update_plan():
            from app.db import get_pool
            pool = get_pool()
            if not pool:
                raise Exception("数据库连接池未初始化")
            
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE users
                    SET 
                        current_plan_id = $1,
                        current_credits = $2,
                        plan_renew_at = $3
                    WHERE user_id = $4
                    """,
                    new_plan_id,
                    new_credits,
                    next_month,
                    user_id
                )
        
        asyncio.run(_update_plan())
        
        return ChangePlanResponse(
            success=True,
            message=f"成功切换到 {new_plan.name} 套餐",
            new_plan_id=new_plan_id,
            new_plan_name=new_plan.name,
            new_credits=new_credits,
            plan_renew_at=next_month
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
        # 先检查用户是否存在且积分足够
        user = self.get_user(user_id)
        if not user:
            print(f"[Billing] 用户不存在: {user_id}")
            return False
        
        if user.current_credits < amount:
            print(f"[Billing] 积分不足: user={user_id}, required={amount}, current={user.current_credits}")
            return False
        
        # 扣除积分（使用负数表示扣除，同时更新 total_used）
        success = asyncio.run(crud_users.update_user_credits(
            user_id=user_id,
            credits_delta=-amount,
            update_total_used=True
        ))
        
        if success:
            print(f"[Billing] ✓ 积分扣除成功: user={user_id}, amount={amount}, remaining={user.current_credits - amount}")
        else:
            print(f"[Billing] ✗ 积分扣除失败: user={user_id}, amount={amount}")
        
        return success
    
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
            print(f"[Billing] 用户不存在: {user_id}")
            return False
        
        # 增加积分（使用正数）
        success = asyncio.run(crud_users.update_user_credits(
            user_id=user_id,
            credits_delta=amount,
            update_total_used=False
        ))
        
        if success:
            print(f"[Billing] ✓ 积分增加成功: user={user_id}, amount={amount}, new_total={user.current_credits + amount}")
        else:
            print(f"[Billing] ✗ 积分增加失败: user={user_id}, amount={amount}")
        
        return success
    
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
                new_credits = plan.monthly_credits
                
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
                
                # 更新数据库
                async def _renew_plan():
                    from app.db import get_pool
                    pool = get_pool()
                    if not pool:
                        raise Exception("数据库连接池未初始化")
                    
                    async with pool.acquire() as conn:
                        await conn.execute(
                            """
                            UPDATE users
                            SET 
                                current_credits = $1,
                                plan_renew_at = $2
                            WHERE user_id = $3
                            """,
                            new_credits,
                            next_month,
                            user_id
                        )
                
                asyncio.run(_renew_plan())
                print(f"[Billing] ✓ 套餐已续费: user={user_id}, plan={user.current_plan_id}, credits={new_credits}")
                return True
        
        return False


# 全局实例（数据库版本）
billing_service_db = BillingServiceDB()

