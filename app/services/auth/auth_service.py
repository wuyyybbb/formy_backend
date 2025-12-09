"""
认证服务
"""
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict
import redis
import json
import jwt
import bcrypt
from jwt.exceptions import InvalidTokenError as JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.models.user import User, VerificationCode
from app.utils.id_generator import generate_user_id
from app.utils.redis_client import get_redis_client


class AuthService:
    """认证服务类"""
    
    def __init__(self):
        """初始化认证服务"""
        try:
            # 使用统一的 Redis 客户端（基于 REDIS_URL）
            self.redis_client = get_redis_client()
            
            # 测试 Redis 连接
            self.redis_client.ping()
            print(f"✅ Redis 连接成功！")
            
        except redis.ConnectionError as e:
            print(f"❌ Redis 连接失败: {e}")
            print(f"📋 当前配置:")
            if settings.REDIS_URL:
                print(f"   REDIS_URL: {settings.REDIS_URL[:30]}...")
            else:
                print(f"   REDIS_URL: 未设置")
            print(f"")
            print(f"🔧 解决方案:")
            print(f"   1. 在 Render 创建 Redis 实例")
            print(f"   2. 在环境变量中设置 REDIS_URL")
            print(f"   3. REDIS_URL 格式: redis://[:password@]host[:port][/db]")
            raise Exception(f"Redis 连接失败，请检查配置: {str(e)}")
        except ValueError as e:
            print(f"❌ Redis 配置错误: {e}")
            raise Exception(f"Redis 配置错误: {str(e)}")
        except Exception as e:
            print(f"❌ 初始化认证服务失败: {e}")
            raise
            
        self.code_expiry = 600  # 10 分钟
        self.jwt_secret = settings.get_jwt_secret
        self.jwt_algorithm = settings.ALGORITHM
    
    def generate_code(self) -> str:
        """生成 6 位数字验证码"""
        return ''.join(random.choices(string.digits, k=6))
    
    def save_verification_code(self, email: str, code: str) -> bool:
        """
        保存验证码到 Redis
        
        Args:
            email: 邮箱地址
            code: 验证码
            
        Returns:
            bool: 是否保存成功
        """
        try:
            key = f"verification_code:{email}"
            data = {
                "code": code,
                "created_at": datetime.now().isoformat(),
                "is_used": False
            }
            # 设置 10 分钟过期
            self.redis_client.setex(
                key,
                self.code_expiry,
                json.dumps(data, default=str)
            )
            return True
        except Exception as e:
            print(f"保存验证码失败: {e}")
            return False
    
    def verify_code(self, email: str, code: str) -> bool:
        """
        验证验证码
        
        Args:
            email: 邮箱地址
            code: 验证码
            
        Returns:
            bool: 验证是否成功
        """
        try:
            key = f"verification_code:{email}"
            data_str = self.redis_client.get(key)
            
            if not data_str:
                print(f"验证码不存在或已过期: {email}")
                return False
            
            data = json.loads(data_str)
            
            if data.get("is_used"):
                print(f"验证码已使用: {email}")
                return False
            
            if data.get("code") != code:
                print(f"验证码错误: {email}")
                return False
            
            # 标记为已使用
            data["is_used"] = True
            self.redis_client.setex(
                key,
                self.code_expiry,
                json.dumps(data, default=str)
            )
            
            return True
            
        except Exception as e:
            print(f"验证验证码失败: {e}")
            return False
    
    async def get_or_create_user(self, email: str) -> User:
        """
        获取或创建用户（同时保存到 PostgreSQL 和 Redis）
        
        Args:
            email: 邮箱地址
            
        Returns:
            User: 用户对象
        """
        from app.db.crud_users import get_user_by_email, create_user
        
        try:
            # 先从 PostgreSQL 查询（数据源）
            user = await get_user_by_email(email)
            
            if user:
                # 用户已存在，更新最后登录时间
                user.last_login = datetime.now()
                
                # 检查白名单：如果用户在白名单中，确保算力至少是 100000
                is_whitelist = settings.is_whitelisted(email)
                if is_whitelist and user.current_credits < settings.WHITELIST_CREDITS:
                    old_credits = user.current_credits
                    user.current_credits = settings.WHITELIST_CREDITS
                    print(f"🌟 白名单用户登录: {email}, 算力已从 {old_credits} 补充到 {user.current_credits}")
                    # 更新白名单用户的算力到数据库
                    from app.db.crud_users import update_user_credits
                    await update_user_credits(user.user_id, user.current_credits - old_credits, update_total_used=False)
            else:
                # 创建新用户，分配免费算力
                # 检查是否在白名单中
                is_whitelist = settings.is_whitelisted(email)
                initial_credits = settings.WHITELIST_CREDITS if is_whitelist else 100
                
                # 直接创建到 PostgreSQL
                user = await create_user(
                    email=email,
                    username=email.split('@')[0],
                    current_credits=initial_credits,
                    is_active=True
                )
                
                if is_whitelist:
                    print(f"🌟 白名单用户注册: {email}, 初始算力: {initial_credits}")
                else:
                    print(f"✅ 普通用户注册: {email}, 初始算力: {initial_credits}")
            
            # 保存用户信息到 Redis（缓存）
            self.save_user(user)
            
            return user
            
        except Exception as e:
            print(f"获取或创建用户失败: {e}")
            raise
    
    def save_user(self, user: User) -> bool:
        """
        保存用户信息到 Redis
        
        Args:
            user: 用户对象
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 按邮箱索引
            user_key = f"user:email:{user.email}"
            # 按 ID 索引
            user_id_key = f"user:id:{user.user_id}"
            
            user_data = user.model_dump(mode='json')
            user_data_str = json.dumps(user_data, default=str)
            
            # 保存用户数据（不过期）
            self.redis_client.set(user_key, user_data_str)
            self.redis_client.set(user_id_key, user_data_str)
            
            return True
            
        except Exception as e:
            print(f"保存用户失败: {e}")
            return False
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        根据 ID 获取用户（优先从 PostgreSQL，其次从 Redis）
        
        Args:
            user_id: 用户 ID
            
        Returns:
            Optional[User]: 用户对象
        """
        from app.db.crud_users import get_user_by_id as db_get_user_by_id
        
        try:
            # 先尝试从数据库查询
            user = await db_get_user_by_id(user_id)
            if user:
                # 缓存到 Redis
                self.save_user(user)
                return user
            
            # 数据库中没有，尝试从 Redis 读取（兼容性）
            user_id_key = f"user:id:{user_id}"
            user_data_str = self.redis_client.get(user_id_key)
            
            if user_data_str:
                user_data = json.loads(user_data_str)
                # Pydantic 会自动将字符串 user_id 转换为 UUID，将 ISO 字符串转换为 datetime
                return User(**user_data)
            
            return None
            
        except Exception as e:
            print(f"获取用户失败: {e}")
            return None
    
    def create_access_token(self, user: User) -> str:
        """
        创建访问令牌（JWT）
        
        Args:
            user: 用户对象
            
        Returns:
            str: JWT 令牌
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": str(user.user_id),  # 确保 user_id 转换为字符串
            "email": user.email,
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.jwt_secret,
            algorithm=self.jwt_algorithm
        )
        
        return encoded_jwt

    # ----------------- Refresh Token -----------------
    def create_refresh_token(self, user_id) -> str:
        """
        创建并保存 refresh token（随机字符串），存储到 Redis
        Args:
            user_id: 用户 ID（UUID 或 str）
        Returns: refresh_token string
        """
        try:
            token = uuid.uuid4().hex
            key = f"refresh_token:{token}"
            data = {
                "user_id": str(user_id),  # 确保存储为字符串
                "created_at": datetime.utcnow().isoformat()
            }
            expiry_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
            self.redis_client.setex(key, expiry_seconds, json.dumps(data, ensure_ascii=False, default=str))
            return token
        except Exception as e:
            print(f"创建 refresh token 失败: {e}")
            raise

    def verify_refresh_token(self, token: str) -> Optional[str]:
        """
        验证 refresh token 是否存在且未过期，返回关联的 user_id 或 None
        """
        try:
            key = f"refresh_token:{token}"
            data_str = self.redis_client.get(key)
            if not data_str:
                return None
            data = json.loads(data_str)
            return data.get("user_id")
        except Exception as e:
            print(f"验证 refresh token 失败: {e}")
            return None

    def revoke_refresh_token(self, token: str) -> bool:
        """
        撤销（删除） refresh token
        """
        try:
            key = f"refresh_token:{token}"
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"撤销 refresh token 失败: {e}")
            return False
    
    def decode_access_token(self, token: str) -> Optional[Dict]:
        """
        解码访问令牌
        
        Args:
            token: JWT 令牌
            
        Returns:
            Optional[Dict]: 解码后的数据
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            return payload
        except JWTError as e:
            print(f"JWT 解码失败: {e}")
            return None

    def decode_access_token_verbose(self, token: str) -> tuple[Optional[Dict], Optional[str]]:
        """
        解码访问令牌并返回 (payload, error_message)

        Returns:
            (payload, None) if successful
            (None, error_message) if failed
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            return payload, None
        except JWTError as e:
            err = str(e)
            print(f"JWT 解码失败（详细）: {err}")
            return None, err
    
    def hash_password(self, password: str) -> str:
        """
        对密码进行哈希加密
        
        Args:
            password: 明文密码
            
        Returns:
            str: 加密后的密码哈希值
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码是否正确
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            bool: 密码是否匹配
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            print(f"验证密码失败: {e}")
            return False
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户（优先从 PostgreSQL，其次从 Redis）
        
        Args:
            email: 邮箱地址
            
        Returns:
            Optional[User]: 用户对象
        """
        from app.db.crud_users import get_user_by_email as db_get_user_by_email
        
        try:
            # 先尝试从数据库查询
            user = await db_get_user_by_email(email)
            if user:
                # 缓存到 Redis
                self.save_user(user)
                return user
            
            # 数据库中没有，尝试从 Redis 读取（兼容性）
            user_key = f"user:email:{email}"
            user_data_str = self.redis_client.get(user_key)
            
            if user_data_str:
                user_data = json.loads(user_data_str)
                return User(**user_data)
            
            return None
            
        except Exception as e:
            print(f"获取用户失败: {e}")
            return None
    
    def set_user_password(self, email: str, password: str) -> bool:
        """
        为用户设置密码
        
        Args:
            email: 邮箱地址
            password: 明文密码
            
        Returns:
            bool: 是否设置成功
        """
        try:
            user = self.get_user_by_email(email)
            
            if not user:
                print(f"用户不存在: {email}")
                return False
            
            # 加密密码
            password_hash = self.hash_password(password)
            
            # 更新用户信息
            user.password_hash = password_hash
            user.has_password = True
            
            # 保存到数据库
            return self.save_user(user)
            
        except Exception as e:
            print(f"设置密码失败: {e}")
            return False
    
    def verify_user_password(self, email: str, password: str) -> Optional[User]:
        """
        验证用户密码并返回用户对象
        
        Args:
            email: 邮箱地址
            password: 明文密码
            
        Returns:
            Optional[User]: 如果密码正确返回用户对象，否则返回 None
        """
        try:
            user = self.get_user_by_email(email)
            
            if not user:
                print(f"用户不存在: {email}")
                return None
            
            if not user.has_password or not user.password_hash:
                print(f"用户未设置密码: {email}")
                return None
            
            # 验证密码
            if self.verify_password(password, user.password_hash):
                # 更新最后登录时间
                user.last_login = datetime.now()
                self.save_user(user)
                return user
            else:
                print(f"密码错误: {email}")
                return None
                
        except Exception as e:
            print(f"验证用户密码失败: {e}")
            return None


# 全局认证服务实例
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """获取认证服务实例（单例）"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


# HTTP Bearer 安全方案
security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    从 JWT token 中获取当前用户 ID（FastAPI 依赖）
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        str: 用户 ID
        
    Raises:
        HTTPException: 如果 token 无效或缺失
    """
    # 如果没有提供 token，返回 401
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials

    # 解码 token（获取详细错误信息以便返回更明确的提示）
    auth_service = get_auth_service()
    payload, err = auth_service.decode_access_token_verbose(token)

    if err:
        # 返回更明确的错误原因（如过期、签名无效等）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"无效的认证凭据: {err}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 从 payload 中提取用户 ID
    user_id: Optional[str] = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id

