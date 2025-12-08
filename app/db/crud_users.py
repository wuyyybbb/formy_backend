"""
用户 CRUD 操作（使用 asyncpg 连接 Supabase PostgreSQL）
"""
from datetime import datetime
from typing import Optional
import asyncpg
from app.db import get_pool
from app.models.user import User


async def get_user_by_email(email: str) -> Optional[User]:
    """
    根据邮箱获取用户
    
    Args:
        email: 用户邮箱地址
        
    Returns:
        Optional[User]: 用户对象，如果不存在则返回 None
        
    Raises:
        Exception: 数据库连接错误
    """
    pool = get_pool()
    if not pool:
        raise Exception("数据库连接池未初始化")
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 
                user_id,
                email,
                username,
                avatar,
                created_at,
                last_login,
                is_active,
                password_hash,
                has_password,
                current_plan_id,
                current_credits,
                plan_renew_at,
                total_credits_used
            FROM users
            WHERE email = $1
            """,
            email.lower()  # 邮箱统一转为小写
        )
        
        if not row:
            return None
        
        # 将数据库行转换为 User 对象
        return User(
            user_id=row['user_id'],
            email=row['email'],
            username=row['username'],
            avatar=row['avatar'],
            created_at=row['created_at'],
            last_login=row['last_login'],
            is_active=row['is_active'],
            password_hash=row['password_hash'],
            has_password=row['has_password'] if row['has_password'] is not None else (row['password_hash'] is not None),
            current_plan_id=row['current_plan_id'],
            current_credits=row['current_credits'] or 0,
            plan_renew_at=row['plan_renew_at'],
            total_credits_used=row['total_credits_used'] or 0
        )


async def create_user(
    email: str,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    avatar: Optional[str] = None,
    password_hash: Optional[str] = None,
    current_plan_id: Optional[str] = None,
    current_credits: int = 100,  # 默认100积分（注册奖励）
    is_active: bool = True,
    signup_bonus_granted: bool = True  # 注册时默认已发放奖励
) -> User:
    """
    创建新用户
    
    Args:
        email: 用户邮箱地址（必需）
        user_id: 用户 ID（可选，如果不提供则自动生成）
        username: 用户名（可选）
        avatar: 头像 URL（可选）
        password_hash: 密码哈希值（可选）
        current_plan_id: 当前套餐 ID（可选）
        current_credits: 初始算力（默认 100，注册奖励）
        is_active: 是否激活（默认 True）
        signup_bonus_granted: 注册奖励是否已发放（默认 True）
        
    Returns:
        User: 创建的用户对象
        
    Raises:
        Exception: 数据库连接错误或用户已存在
    """
    pool = get_pool()
    if not pool:
        raise Exception("数据库连接池未初始化")
    
    # 如果没有提供 user_id，生成一个（格式：usr_xxxxxxxx）
    if not user_id:
        import uuid
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
    
    # 统一邮箱为小写
    email = email.lower()
    
    # 检查用户是否已存在
    existing_user = await get_user_by_email(email)
    if existing_user:
        raise ValueError(f"用户 {email} 已存在")
    
    now = datetime.utcnow()
    has_password = password_hash is not None
    
    async with pool.acquire() as conn:
        # 首先检查表中是否存在 signup_bonus_granted 列
        columns_exist = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'signup_bonus_granted'
            )
            """
        )
        
        if columns_exist:
            # 如果字段存在，包含 signup_bonus_granted
            await conn.execute(
                """
                INSERT INTO users (
                    user_id,
                    email,
                    username,
                    avatar,
                    created_at,
                    last_login,
                    is_active,
                    password_hash,
                    has_password,
                    current_plan_id,
                    current_credits,
                    plan_renew_at,
                    total_credits_used,
                    signup_bonus_granted
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                )
                """,
                user_id,
                email,
                username,
                avatar,
                now,
                now,
                is_active,
                password_hash,
                has_password,
                current_plan_id,
                current_credits,
                None,
                0,
                signup_bonus_granted
            )
        else:
            # 如果字段不存在，不包含 signup_bonus_granted（向后兼容）
            print("⚠️  users 表中没有 signup_bonus_granted 字段，跳过该字段")
            await conn.execute(
                """
                INSERT INTO users (
                    user_id,
                    email,
                    username,
                    avatar,
                    created_at,
                    last_login,
                    is_active,
                    password_hash,
                    has_password,
                    current_plan_id,
                    current_credits,
                    plan_renew_at,
                    total_credits_used
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                )
                """,
                user_id,
                email,
                username,
                avatar,
                now,
                now,
                is_active,
                password_hash,
                has_password,
                current_plan_id,
                current_credits,
                None,
                0
            )
    
    # 返回创建的用户对象
    return User(
        user_id=user_id,
        email=email,
        username=username,
        avatar=avatar,
        created_at=now,
        last_login=now,
        is_active=is_active,
        password_hash=password_hash,
        has_password=has_password,
        current_plan_id=current_plan_id,
        current_credits=current_credits,
        plan_renew_at=None,
        total_credits_used=0
    )


async def update_user_credits(
    user_id: str,
    credits_delta: int,
    update_total_used: bool = False
) -> bool:
    """
    更新用户积分
    
    Args:
        user_id: 用户ID
        credits_delta: 积分变化量（正数表示增加，负数表示扣除）
        update_total_used: 是否同时更新 total_credits_used（扣除时为 True）
        
    Returns:
        bool: 是否更新成功
        
    Raises:
        Exception: 数据库连接错误
    """
    pool = get_pool()
    if not pool:
        raise Exception("数据库连接池未初始化")
    
    async with pool.acquire() as conn:
        if update_total_used and credits_delta < 0:
            # 扣除积分时，同时更新 total_credits_used
            result = await conn.execute(
                """
                UPDATE users
                SET 
                    current_credits = current_credits + $1,
                    total_credits_used = total_credits_used + $2
                WHERE user_id = $3
                """,
                credits_delta,
                abs(credits_delta),  # total_used 总是增加正数
                user_id
            )
        else:
            # 仅更新 current_credits（增加积分或不更新总使用量）
            result = await conn.execute(
                """
                UPDATE users
                SET current_credits = current_credits + $1
                WHERE user_id = $2
                """,
                credits_delta,
                user_id
            )
        
        # 检查是否有行被更新
        return result == "UPDATE 1"


async def get_user_by_id(user_id: str) -> Optional[User]:
    """
    根据用户ID获取用户
    
    Args:
        user_id: 用户ID
        
    Returns:
        Optional[User]: 用户对象，如果不存在则返回 None
        
    Raises:
        Exception: 数据库连接错误
    """
    pool = get_pool()
    if not pool:
        raise Exception("数据库连接池未初始化")
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 
                user_id,
                email,
                username,
                avatar,
                created_at,
                last_login,
                is_active,
                password_hash,
                has_password,
                current_plan_id,
                current_credits,
                plan_renew_at,
                total_credits_used
            FROM users
            WHERE user_id = $1
            """,
            user_id
        )
        
        if not row:
            return None
        
        # 将数据库行转换为 User 对象
        return User(
            user_id=row['user_id'],
            email=row['email'],
            username=row['username'],
            avatar=row['avatar'],
            created_at=row['created_at'],
            last_login=row['last_login'],
            is_active=row['is_active'],
            password_hash=row['password_hash'],
            has_password=row['has_password'] if row['has_password'] is not None else (row['password_hash'] is not None),
            current_plan_id=row['current_plan_id'],
            current_credits=row['current_credits'] or 0,
            plan_renew_at=row['plan_renew_at'],
            total_credits_used=row['total_credits_used'] or 0
        )


async def verify_user(email: str, password_hash: str) -> Optional[User]:
    """
    验证用户密码（通过密码哈希值验证）
    
    Args:
        email: 用户邮箱地址
        password_hash: 密码哈希值（用于验证）
        
    Returns:
        Optional[User]: 如果验证成功返回用户对象，否则返回 None
        
    Raises:
        Exception: 数据库连接错误
    """
    pool = get_pool()
    if not pool:
        raise Exception("数据库连接池未初始化")
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 
                user_id,
                email,
                username,
                avatar,
                created_at,
                last_login,
                is_active,
                password_hash,
                has_password,
                current_plan_id,
                current_credits,
                plan_renew_at,
                total_credits_used
            FROM users
            WHERE email = $1 AND password_hash = $2 AND is_active = true
            """,
            email.lower(),
            password_hash
        )
        
        if not row:
            return None
        
        # 更新最后登录时间
        await conn.execute(
            """
            UPDATE users
            SET last_login = $1
            WHERE user_id = $2
            """,
            datetime.utcnow(),
            row['user_id']
        )
        
        # 将数据库行转换为 User 对象
        return User(
            user_id=row['user_id'],
            email=row['email'],
            username=row['username'],
            avatar=row['avatar'],
            created_at=row['created_at'],
            last_login=datetime.utcnow(),  # 使用更新后的时间
            is_active=row['is_active'],
            password_hash=row['password_hash'],
            has_password=row['has_password'] if row['has_password'] is not None else (row['password_hash'] is not None),
            current_plan_id=row['current_plan_id'],
            current_credits=row['current_credits'] or 0,
            plan_renew_at=row['plan_renew_at'],
            total_credits_used=row['total_credits_used'] or 0
        )

