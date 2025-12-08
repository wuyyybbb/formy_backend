print("[DB] __init__ loaded VERSION = 2025-12-08-1535")


"""
数据库模块 & PostgreSQL 连接管理（使用 asyncpg）
用于连接 Supabase PostgreSQL 数据库
"""

import asyncpg
from typing import Optional
from app.core.config import settings

# 从子模块导出用户相关的 CRUD 方法
from .crud_users import get_user_by_email, create_user, verify_user

# 全局连接池
_db_pool: Optional[asyncpg.Pool] = None


async def connect_to_db() -> None:
    """
    创建 PostgreSQL 连接池

    从环境变量读取数据库连接信息：
    - DATABASE_URL: 完整的 PostgreSQL 连接字符串（推荐）
    或
    - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD: 分散的配置项
    """
    global _db_pool

    if _db_pool is not None:
        print("[DB] ⚠️  连接池已存在，跳过创建")
        return

    try:
        # 优先使用 DATABASE_URL（Supabase 提供的连接字符串）
        if settings.DATABASE_URL:
            database_url = settings.DATABASE_URL
            print(f"[DB] 🔗 使用 DATABASE_URL 连接数据库...")
        else:
            # 从分散的配置项构建连接字符串
            database_url = (
                f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
                f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            )
            print(
                f"[DB] 🔗 使用配置项连接数据库: "
                f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            )

        # 创建连接池
        _db_pool = await asyncpg.create_pool(
            database_url,
            min_size=2,   # 最小连接数
            max_size=10,  # 最大连接数
            command_timeout=60,  # 命令超时时间（秒）
            server_settings={
                "application_name": "formy_backend",
            },
        )

        # 测试连接
        async with _db_pool.acquire() as conn:
            version = await conn.fetchval("SELECT version()")
            print("[DB] ✅ PostgreSQL 连接池创建成功")
            print(f"[DB] 📊 数据库版本: {version.split(',')[0]}")

    except Exception as e:
        print(f"[DB] ❌ 创建数据库连接池失败: {e}")
        raise


async def close_db_connection() -> None:
    """
    关闭 PostgreSQL 连接池
    """
    global _db_pool

    if _db_pool is None:
        print("[DB] ⚠️  连接池不存在，跳过关闭")
        return

    try:
        await _db_pool.close()
        _db_pool = None
        print("[DB] ✅ 数据库连接池已关闭")
    except Exception as e:
        print(f"[DB] ❌ 关闭数据库连接池失败: {e}")


def get_pool() -> Optional[asyncpg.Pool]:
    """
    获取数据库连接池
    """
    return _db_pool


__all__ = [
    "connect_to_db",
    "close_db_connection",
    "get_pool",
    "get_user_by_email",
    "create_user",
    "verify_user",
]
