"""
认证服务
"""
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict
import redis
import json
import jwt
from jwt.exceptions import InvalidTokenError as JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.models.user import User, VerificationCode
from app.utils.id_generator import generate_user_id


class AuthService:
    """认证服务类"""
    
    def __init__(self):
        """初始化认证服务"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试 Redis 连接
            self.redis_client.ping()
            print(f"✅ Redis 连接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except redis.ConnectionError as e:
            print(f"❌ Redis 连接失败: {e}")
            print(f"   Host: {settings.REDIS_HOST}")
            print(f"   Port: {settings.REDIS_PORT}")
            print(f"   DB: {settings.REDIS_DB}")
            raise Exception(f"Redis 连接失败，请检查配置: {str(e)}")
        except Exception as e:
            print(f"❌ 初始化认证服务失败: {e}")
            raise
            
        self.code_expiry = 600  # 10 分钟
        self.jwt_secret = settings.SECRET_KEY
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
                json.dumps(data)
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
                json.dumps(data)
            )
            
            return True
            
        except Exception as e:
            print(f"验证验证码失败: {e}")
            return False
    
    def get_or_create_user(self, email: str) -> User:
        """
        获取或创建用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            User: 用户对象
        """
        try:
            # 尝试从 Redis 获取用户
            user_key = f"user:email:{email}"
            user_data_str = self.redis_client.get(user_key)
            
            if user_data_str:
                user_data = json.loads(user_data_str)
                user = User(**user_data)
                # 更新最后登录时间
                user.last_login = datetime.now()
            else:
                # 创建新用户
                user = User(
                    user_id=generate_user_id(),
                    email=email,
                    username=email.split('@')[0],
                    created_at=datetime.now(),
                    last_login=datetime.now()
                )
            
            # 保存用户信息
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
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        根据 ID 获取用户
        
        Args:
            user_id: 用户 ID
            
        Returns:
            Optional[User]: 用户对象
        """
        try:
            user_id_key = f"user:id:{user_id}"
            user_data_str = self.redis_client.get(user_id_key)
            
            if not user_data_str:
                return None
            
            user_data = json.loads(user_data_str)
            return User(**user_data)
            
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
            "sub": user.user_id,
            "email": user.email,
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.jwt_secret,
            algorithm=self.jwt_algorithm
        )
        
        return encoded_jwt
    
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
    
    # 解码 token
    auth_service = get_auth_service()
    payload = auth_service.decode_access_token(token)
    
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

