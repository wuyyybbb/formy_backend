"""
认证相关路由
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional

from app.schemas.auth import (
    SendCodeRequest,
    SendCodeResponse,
    LoginRequest,
    LoginResponse,
    UserInfo,
    CurrentUserResponse,
    SetPasswordRequest,
    SetPasswordResponse,
    PasswordLoginRequest,
    SignupRequest,
    SignupResponse
)
from app.services.auth.auth_service import get_auth_service
from app.services.email.email_factory import get_email_service
from app.db import get_pool


router = APIRouter()


@router.post("/auth/send-code", response_model=SendCodeResponse)
async def send_verification_code(request: SendCodeRequest):
    """
    API 1: 发送验证码
    
    发送 6 位数字验证码到指定邮箱
    验证码有效期 10 分钟
    """
    try:
        print(f"📧 收到发送验证码请求: {request.email}")
        
        auth_service = get_auth_service()
        email_service = get_email_service()
        
        # 生成验证码
        code = auth_service.generate_code()
        print(f"🔑 生成验证码: {code} (仅用于调试，生产环境应删除)")
        
        # 保存验证码到 Redis
        print(f"💾 正在保存验证码到 Redis...")
        save_result = auth_service.save_verification_code(request.email, code)
        print(f"💾 保存结果: {save_result}")
        
        if not save_result:
            print(f"❌ Redis 保存失败")
            raise HTTPException(
                status_code=500,
                detail="保存验证码失败，请检查 Redis 连接"
            )
        
        # 发送邮件
        print(f"📤 正在发送邮件到 {request.email}...")
        
        # 检查邮件服务配置（根据服务类型检查不同的配置项）
        from app.core.config import settings
        if settings.EMAIL_PROVIDER == "resend":
            if not hasattr(email_service, 'api_key') or not email_service.api_key:
                print(f"❌ RESEND_API_KEY 未配置")
                raise HTTPException(
                    status_code=500,
                    detail="邮件服务未配置，请检查 RESEND_API_KEY 环境变量"
                )
        elif settings.EMAIL_PROVIDER == "smtp":
            if not hasattr(email_service, 'username') or not email_service.username:
                print(f"❌ SMTP_USER 未配置")
                raise HTTPException(
                    status_code=500,
                    detail="邮件服务未配置，请检查 SMTP_USER 环境变量"
                )
            if not hasattr(email_service, 'password') or not email_service.password:
                print(f"❌ SMTP_PASSWORD 未配置")
                raise HTTPException(
                    status_code=500,
                    detail="邮件服务未配置，请检查 SMTP_PASSWORD 环境变量"
                )
        
        send_result = await email_service.send_verification_code(request.email, code)
        print(f"📤 发送结果: {send_result}")
        
        if not send_result:
            print(f"❌ 邮件发送失败，请查看上方详细错误信息")
            
            # 邮件发送失败
            raise HTTPException(
                status_code=500,
                detail="发送邮件失败，请查看后端日志获取详细错误信息。"
            )
        
        print(f"✅ 验证码发送成功: {request.email}")
        return SendCodeResponse(
            success=True,
            message=f"验证码已发送到 {request.email}",
            expires_in=600  # 10 分钟
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 发送验证码异常: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"发送验证码失败: {str(e)}"
        )


@router.post("/auth/login", response_model=LoginResponse)
async def login_with_code(request: LoginRequest):
    """
    API 2: 验证码登录
    
    使用邮箱和验证码登录
    登录成功返回 JWT 令牌
    """
    try:
        auth_service = get_auth_service()
        
        # 验证验证码
        if not auth_service.verify_code(request.email, request.code):
            raise HTTPException(
                status_code=400,
                detail="验证码错误或已过期"
            )
        
        # 获取或创建用户
        user = auth_service.get_or_create_user(request.email)
        
        # 创建访问令牌
        access_token = auth_service.create_access_token(user)
        
        # 返回用户信息和令牌
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserInfo(
                user_id=user.user_id,
                email=user.email,
                username=user.username,
                avatar=user.avatar,
                created_at=user.created_at.isoformat(),
                last_login=user.last_login.isoformat() if user.last_login else None
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"登录失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"登录失败: {str(e)}"
        )


async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    依赖项：从 Authorization header 获取当前用户
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="未登录"
        )
    
    try:
        # 解析 Bearer token
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="无效的认证方案"
            )
        
        # 解码 JWT
        auth_service = get_auth_service()
        payload = auth_service.decode_access_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="无效的令牌"
            )
        
        # 获取用户
        user_id = payload.get("sub")
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="用户不存在"
            )
        
        return user
        
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="无效的 Authorization header"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取当前用户失败: {e}")
        raise HTTPException(
            status_code=401,
            detail="认证失败"
        )


@router.get("/auth/me", response_model=CurrentUserResponse)
async def get_current_user_info(current_user=Depends(get_current_user)):
    """
    API 3: 获取当前用户信息
    
    需要在 Header 中提供 Authorization: Bearer <token>
    """
    return CurrentUserResponse(
        user=UserInfo(
            user_id=current_user.user_id,
            email=current_user.email,
            username=current_user.username,
            avatar=current_user.avatar,
            created_at=current_user.created_at.isoformat(),
            last_login=current_user.last_login.isoformat() if current_user.last_login else None
        )
    )


@router.post("/auth/set-password", response_model=SetPasswordResponse)
async def set_password(
    request: SetPasswordRequest,
    current_user=Depends(get_current_user)
):
    """
    API 4: 设置密码（需要登录）
    
    用户登录后设置密码，使用 token 认证而不是验证码
    这样避免了验证码重复使用的问题
    """
    try:
        auth_service = get_auth_service()
        
        # 1. 用户已经通过 token 认证，直接设置密码
        # 2. 设置密码
        success = auth_service.set_user_password(current_user.email, request.password)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="设置密码失败"
            )
        
        print(f"✅ 用户 {current_user.email} 设置密码成功")
        
        return SetPasswordResponse(
            success=True,
            message="密码设置成功！您现在可以使用邮箱+密码登录了"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"设置密码失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"设置密码失败: {str(e)}"
        )


@router.post("/auth/login-password", response_model=LoginResponse)
async def login_with_password(request: PasswordLoginRequest):
    """
    API 5: 密码登录
    
    使用邮箱和密码登录
    登录成功返回 JWT 令牌
    """
    try:
        auth_service = get_auth_service()
        
        # 验证用户密码
        user = auth_service.verify_user_password(request.email, request.password)
        
        if not user:
            raise HTTPException(
                status_code=400,
                detail="邮箱或密码错误"
            )
        
        # 创建访问令牌
        access_token = auth_service.create_access_token(user)
        
        # 返回用户信息和令牌
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserInfo(
                user_id=user.user_id,
                email=user.email,
                username=user.username,
                avatar=user.avatar,
                created_at=user.created_at.isoformat(),
                last_login=user.last_login.isoformat() if user.last_login else None
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"密码登录失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/auth/signup", response_model=SignupResponse)
async def signup(request: SignupRequest):
    """
    注册新用户（使用 PostgreSQL）
    
    使用邮箱和密码注册
    注册时初始化 credits=100，signup_bonus_granted=true
    注册成功返回 JWT 令牌
    """
    try:
        from app.db.crud_users import get_user_by_email, create_user
        from app.services.auth.auth_service import get_auth_service
        import bcrypt
        
        auth_service = get_auth_service()
        
        # 检查用户是否已存在
        existing_user = await get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="该邮箱已被注册"
            )
        
        # 哈希密码
        password_hash = auth_service.hash_password(request.password)
        
        # 创建用户（初始化 credits=100）
        new_user = await create_user(
            email=request.email,
            password_hash=password_hash,
            current_credits=100,  # 注册奖励 100 算力
            is_active=True
        )
        
        # 更新 signup_bonus_granted 字段（如果数据库表中有此字段）
        # 注意：如果数据库表中没有 signup_bonus_granted 字段，这行会失败
        # 用户需要确保 Supabase users 表中有此字段
        pool = get_pool()
        if pool:
            try:
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE users
                        SET signup_bonus_granted = true
                        WHERE user_id = $1
                        """,
                        new_user.user_id
                    )
            except Exception as e:
                # 如果字段不存在，只记录警告，不影响注册流程
                print(f"⚠️  更新 signup_bonus_granted 失败（可能字段不存在）: {e}")
        
        # 创建访问令牌
        access_token = auth_service.create_access_token(new_user)
        
        # 返回用户信息和令牌
        return SignupResponse(
            success=True,
            message="注册成功！您已获得 100 算力奖励",
            access_token=access_token,
            token_type="bearer",
            user=UserInfo(
                user_id=new_user.user_id,
                email=new_user.email,
                username=new_user.username,
                avatar=new_user.avatar,
                created_at=new_user.created_at.isoformat(),
                last_login=new_user.last_login.isoformat() if new_user.last_login else None
            )
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # 处理用户已存在的错误
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        print(f"注册失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/auth/login-password-db", response_model=LoginResponse)
async def login_with_password_db(request: PasswordLoginRequest):
    """
    密码登录（使用 PostgreSQL）
    
    使用邮箱和密码登录
    登录成功返回 JWT 令牌
    """
    try:
        from app.db.crud_users import get_user_by_email
        from app.services.auth.auth_service import get_auth_service
        
        auth_service = get_auth_service()
        
        # 从数据库获取用户
        user = await get_user_by_email(request.email)
        
        if not user:
            raise HTTPException(
                status_code=400,
                detail="邮箱或密码错误"
            )
        
        if not user.password_hash:
            raise HTTPException(
                status_code=400,
                detail="该账户未设置密码，请使用验证码登录"
            )
        
        # 验证密码
        if not auth_service.verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=400,
                detail="邮箱或密码错误"
            )
        
        # 更新最后登录时间
        pool = get_pool()
        if pool:
            from datetime import datetime
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE users
                    SET last_login = $1
                    WHERE user_id = $2
                    """,
                    datetime.utcnow(),
                    user.user_id
                )
        
        # 创建访问令牌
        access_token = auth_service.create_access_token(user)
        
        # 返回用户信息和令牌
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserInfo(
                user_id=user.user_id,
                email=user.email,
                username=user.username,
                avatar=user.avatar,
                created_at=user.created_at.isoformat(),
                last_login=user.last_login.isoformat() if user.last_login else None
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"密码登录失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/auth/test-email")
async def test_email_service(email: str = "test@example.com"):
    """
    测试邮件服务配置（仅用于调试）
    
    发送一封测试邮件到指定邮箱，用于诊断邮件服务问题
    """
    try:
        from app.services.email.email_factory import get_email_service
        from app.core.config import settings
        
        email_service = get_email_service()
        
        # 检查配置（根据服务类型）
        config_status = {
            "provider": settings.EMAIL_PROVIDER,
            "from_email": email_service.from_email,
        }
        
        if settings.EMAIL_PROVIDER == "resend":
            config_status.update({
                "api_key_configured": bool(hasattr(email_service, 'api_key') and email_service.api_key),
                "api_key_length": len(email_service.api_key) if hasattr(email_service, 'api_key') and email_service.api_key else 0,
                "api_key_preview": f"{email_service.api_key[:10]}...{email_service.api_key[-5:]}" if hasattr(email_service, 'api_key') and email_service.api_key and len(email_service.api_key) > 15 else "N/A",
            })
        elif settings.EMAIL_PROVIDER == "smtp":
            config_status.update({
                "smtp_host": email_service.host if hasattr(email_service, 'host') else "N/A",
                "smtp_port": email_service.port if hasattr(email_service, 'port') else "N/A",
                "smtp_user": email_service.username if hasattr(email_service, 'username') else "N/A",
                "smtp_password_configured": bool(hasattr(email_service, 'password') and email_service.password),
                "use_tls": email_service.use_tls if hasattr(email_service, 'use_tls') else "N/A",
            })
        
        # 尝试发送测试邮件
        test_code = "123456"
        send_result = await email_service.send_verification_code(email, test_code)
        
        return {
            "success": send_result,
            "config": config_status,
            "message": "测试邮件已发送" if send_result else "测试邮件发送失败，请查看后端日志"
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

