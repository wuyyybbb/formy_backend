"""
Redis 客户端工具
统一管理 Redis 连接，使用 REDIS_URL 配置
"""
import redis
from app.core.config import settings


def get_redis_client() -> redis.Redis:
    """
    获取 Redis 客户端实例
    
    统一使用 REDIS_URL 配置，不再使用 localhost
    
    Returns:
        redis.Redis: Redis 客户端实例
        
    Raises:
        ValueError: 如果 REDIS_URL 未配置
    """
    if not settings.REDIS_URL:
        raise ValueError(
            "REDIS_URL 未配置。请在环境变量中设置 REDIS_URL，"
            "格式: redis://[:password@]host[:port][/db]"
        )
    
    # 使用 REDIS_URL 创建连接
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    
    return redis_client

