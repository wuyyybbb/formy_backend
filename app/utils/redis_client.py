"""
Redis 客户端工具
统一管理 Redis 连接，使用 REDIS_URL 配置
"""
import redis
from app.core.config import settings


def get_redis_client() -> redis.Redis:
    """
    获取 Redis 客户端实例
    
    优先使用 REDIS_URL，如果未配置则从分散的配置项构建连接
    
    Returns:
        redis.Redis: Redis 客户端实例
        
    Raises:
        ValueError: 如果 Redis 配置不完整
    """
    # 使用配置对象的 get_redis_url 方法获取连接 URL
    redis_url = settings.get_redis_url
    
    if not redis_url:
        raise ValueError(
            "Redis 未配置。请设置以下任一方式：\n"
            "方式1（推荐）: 设置 REDIS_URL 环境变量\n"
            "  格式: redis://[:password@]host[:port][/db]\n"
            "  示例: redis://localhost:6379/0\n"
            "方式2: 分别设置 REDIS_HOST, REDIS_PORT 等环境变量"
        )
    
    try:
        # 使用 REDIS_URL 创建连接
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # 测试连接
        redis_client.ping()
        print(f"[Redis] ✅ Connected to {redis_url[:30]}...")
        
        return redis_client
        
    except redis.ConnectionError as e:
        print(f"[Redis] ❌ Connection failed: {e}")
        raise ValueError(f"Redis 连接失败: {e}")
    except Exception as e:
        print(f"[Redis] ❌ Unexpected error: {e}")
        raise

