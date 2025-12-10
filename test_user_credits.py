"""
测试用户积分是否会被重置

检查普通用户登录时积分是否保持不变
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.db.crud_users import get_user_by_email
from app.core.config import settings


async def test_user_credits(email: str):
    """测试用户积分"""
    print(f"\n{'='*60}")
    print(f"检查用户积分: {email}")
    print(f"{'='*60}\n")
    
    # 检查是否在白名单
    if settings.is_vip_whitelisted(email):
        print(f"🌟 用户类型: VIP 白名单")
        print(f"   应得积分: {settings.VIP_WHITELIST_CREDITS}")
    elif settings.is_trial_whitelisted(email):
        print(f"🎁 用户类型: 试用白名单")
        print(f"   应得积分: {settings.TRIAL_WHITELIST_CREDITS}")
    else:
        print(f"👥 用户类型: 普通用户")
        print(f"   首次注册: 100 积分")
    
    # 从数据库查询
    user = await get_user_by_email(email)
    
    if user:
        print(f"\n✅ 用户存在于数据库")
        print(f"   用户ID: {user.user_id}")
        print(f"   当前积分: {user.current_credits}")
        print(f"   总使用: {user.total_credits_used}")
        print(f"   创建时间: {user.created_at}")
        print(f"   最后登录: {user.last_login}")
    else:
        print(f"\n❌ 用户不存在于数据库")
    
    print(f"\n{'='*60}\n")


async def main():
    """主函数"""
    # 测试几个邮箱
    test_emails = [
        "wyb3206@163.com",  # VIP
        "553588070@qq.com",  # Trial
        "test@example.com",  # 普通用户（如果存在）
    ]
    
    for email in test_emails:
        await test_user_credits(email)


if __name__ == "__main__":
    asyncio.run(main())
