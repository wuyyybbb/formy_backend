"""
应用配置 - 统一环境变量管理

所有配置项都支持通过环境变量设置，方便云平台部署。
环境变量名与类属性名一致（大写）。

示例：
    export REDIS_URL="redis://localhost:6379/0"
    export COMFYUI_BASE_URL="http://your-comfyui-server.com:7860"
"""
from typing import Optional
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """应用配置类 - 所有配置项都可通过环境变量覆盖"""
    
    # ==================== 应用基础配置 ====================
    APP_NAME: str = "Formy"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # 生产环境默认关闭 Debug
    ENVIRONMENT: str = "production"  # development / staging / production
    
    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # ==================== Redis 配置 ====================
    # 方式1: 使用完整的 Redis URL（推荐，适合云平台）
    REDIS_URL: Optional[str] = None
    # 方式2: 分别配置各项（备选，本地开发）
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def get_redis_url(self) -> str:
        """获取 Redis 连接 URL（优先使用 REDIS_URL）"""
        if self.REDIS_URL:
            return self.REDIS_URL
        
        # 如果没有 REDIS_URL，从分散的配置项构建
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ==================== AI Engine 配置 ====================
    # ComfyUI 服务地址（用于 AI 图像处理）
    COMFYUI_BASE_URL: Optional[str] = None
    COMFYUI_TIMEOUT: int = 300  # ComfyUI 请求超时时间（秒）
    COMFYUI_POLL_INTERVAL: int = 2  # 轮询间隔（秒）
    
    # Engine 配置文件路径
    ENGINE_CONFIG_PATH: str = "./engine_config.yml"
    
    # ==================== 数据库配置 ====================
    # 预留数据库配置（如果未来需要）
    DATABASE_URL: Optional[str] = None
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # ==================== 文件存储配置 ====================
    # 存储类型：local（本地文件系统）/ oss（阿里云OSS）/ s3（AWS S3）
    STORAGE_TYPE: str = "local"
    
    # 本地存储配置
    UPLOAD_DIR: str = "./uploads"
    RESULT_DIR: str = "./results"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".webp"}
    
    # 阿里云 OSS 配置（当 STORAGE_TYPE=oss 时使用）
    OSS_ENDPOINT: Optional[str] = None
    OSS_ACCESS_KEY_ID: Optional[str] = None
    OSS_ACCESS_KEY_SECRET: Optional[str] = None
    OSS_BUCKET_NAME: Optional[str] = None
    OSS_BUCKET_DOMAIN: Optional[str] = None  # 自定义域名（可选）
    
    # ==================== 任务配置 ====================
    TASK_RETENTION_DAYS: int = 7
    MAX_CONCURRENT_TASKS_PER_USER: int = 3
    TASK_QUEUE_NAME: str = "formy:tasks"
    
    # ==================== JWT 认证配置 ====================
    # 支持 JWT_SECRET 和 SECRET_KEY（向后兼容）
    JWT_SECRET: Optional[str] = None
    SECRET_KEY: str = "formy-secret-key-change-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时
    
    @property
    def get_jwt_secret(self) -> str:
        """获取 JWT 密钥（优先使用 JWT_SECRET，否则使用 SECRET_KEY）"""
        return self.JWT_SECRET or self.SECRET_KEY
    
    # ==================== CORS 配置 ====================
    # 允许的前端来源（逗号分隔），支持任何域名
    # 示例: "http://localhost:3000,https://your-domain.com,https://app.example.com"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    @property
    def get_cors_origins(self) -> list:
        """
        解析 CORS 配置（支持逗号分隔的字符串）
        
        从环境变量 CORS_ORIGINS 读取允许的来源列表。
        支持任何域名，不限于特定云平台。
        
        示例环境变量：
            CORS_ORIGINS="https://formy-frontend.vercel.app,https://your-domain.com"
        
        Returns:
            list: 允许的来源列表
        """
        if isinstance(self.CORS_ORIGINS, str):
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
            # 去重并保持顺序
            seen = set()
            unique_origins = []
            for origin in origins:
                if origin not in seen:
                    seen.add(origin)
                    unique_origins.append(origin)
            return unique_origins
        return self.CORS_ORIGINS if isinstance(self.CORS_ORIGINS, list) else []
    
    # ==================== 邮件服务配置 ====================
    # 邮件提供商：resend / aliyun / smtp
    EMAIL_PROVIDER: str = "smtp"  # 默认使用 Gmail SMTP
    
    # Resend 配置
    RESEND_API_KEY: Optional[str] = None
    RESEND_API_URL: str = "https://api.resend.com/emails"
    
    # 阿里云邮件推送配置
    ALIYUN_EMAIL_REGION: str = "cn-hangzhou"
    ALIYUN_EMAIL_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_EMAIL_ACCESS_KEY_SECRET: Optional[str] = None
    
    # SMTP 配置（Gmail SMTP）
    SMTP_HOST: Optional[str] = "smtp.gmail.com"  # Gmail SMTP 服务器
    SMTP_PORT: int = 587  # Gmail SMTP 端口（TLS）
    SMTP_USER: Optional[str] = None  # Gmail 邮箱地址
    SMTP_PASSWORD: Optional[str] = None  # Gmail 应用专用密码
    SMTP_USE_TLS: bool = True  # 使用 TLS 加密
    
    # 发件人配置
    FROM_EMAIL: str = "wuyebei3206@gmail.com"  # Gmail 发件邮箱
    FROM_NAME: str = "Formy"
    
    # ==================== 白名单配置 ====================
    # 白名单用户邮箱列表（逗号分隔），这些用户将获得特殊算力
    WHITELIST_EMAILS: str = "wyb3206@163.com,wuyebei3206@gmail.com"
    # 白名单用户的算力额度
    WHITELIST_CREDITS: int = 100000
    # 管理员密码（用于管理白名单）
    ADMIN_PASSWORD: str = "wyb518"
    
    @property
    def get_whitelist_emails(self) -> set:
        """
        获取白名单邮箱列表
        
        Returns:
            set: 白名单邮箱集合（小写）
        """
        if not self.WHITELIST_EMAILS:
            return set()
        emails = [email.strip().lower() for email in self.WHITELIST_EMAILS.split(",") if email.strip()]
        return set(emails)
    
    def is_whitelisted(self, email: str) -> bool:
        """
        检查邮箱是否在白名单中
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 是否在白名单中
        """
        return email.lower() in self.get_whitelist_emails
    
    # ==================== 日志配置 ====================
    LOG_LEVEL: str = "INFO"  # DEBUG / INFO / WARNING / ERROR
    LOG_FORMAT: str = "json"  # json / text
    
    # ==================== 监控配置 ====================
    SENTRY_DSN: Optional[str] = None  # Sentry 错误追踪
    ENABLE_METRICS: bool = False  # 是否启用指标收集
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # 允许从环境变量读取配置
        env_file_encoding = 'utf-8'


# 全局配置实例
settings = Settings()


def print_current_config():
    """打印当前配置（用于调试，敏感信息会脱敏）"""
    print("\n" + "="*60)
    print("📋 Current Configuration")
    print("="*60)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"API Version: {settings.APP_VERSION}")
    print(f"\nRedis: {settings.get_redis_url[:30]}..." if settings.get_redis_url else "Redis: Not configured")
    print(f"ComfyUI: {settings.COMFYUI_BASE_URL or 'Not configured'}")
    print(f"Storage Type: {settings.STORAGE_TYPE}")
    print(f"Email Provider: {settings.EMAIL_PROVIDER}")
    print(f"CORS Origins: {', '.join(settings.get_cors_origins[:3])}")
    print("="*60 + "\n")

