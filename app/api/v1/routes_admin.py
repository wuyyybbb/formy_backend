"""
管理员路由 - 用于白名单管理等管理员功能
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.services.auth.auth_service import get_auth_service

router = APIRouter()


class AddWhitelistRequest(BaseModel):
    """添加白名单请求"""
    email: EmailStr
    admin_password: str


class RemoveWhitelistRequest(BaseModel):
    """移除白名单请求"""
    email: EmailStr
    admin_password: str


class WhitelistResponse(BaseModel):
    """白名单响应"""
    success: bool
    message: str
    whitelist: list


def verify_admin_password(password: str) -> bool:
    """验证管理员密码"""
    return password == settings.ADMIN_PASSWORD


@router.post("/admin/whitelist/add", response_model=WhitelistResponse)
async def add_to_whitelist(request: AddWhitelistRequest):
    """
    添加邮箱到白名单（需要管理员密码）
    
    添加成功后，该用户下次登录时将获得白名单算力
    """
    # 验证管理员密码
    if not verify_admin_password(request.admin_password):
        raise HTTPException(
            status_code=403,
            detail="管理员密码错误"
        )
    
    # 获取当前白名单
    current_whitelist = settings.get_whitelist_emails
    
    # 检查是否已在白名单中
    if request.email.lower() in current_whitelist:
        return WhitelistResponse(
            success=False,
            message=f"邮箱 {request.email} 已在白名单中",
            whitelist=list(current_whitelist)
        )
    
    # 添加到白名单（注意：这只是内存中的修改，实际需要更新环境变量）
    print(f"⚠️  注意：需要在 Render 环境变量中将此邮箱添加到 WHITELIST_EMAILS")
    print(f"⚠️  当前 WHITELIST_EMAILS: {settings.WHITELIST_EMAILS}")
    print(f"⚠️  建议添加: {settings.WHITELIST_EMAILS},{request.email}")
    
    return WhitelistResponse(
        success=False,
        message=f"请在 Render 环境变量中添加 {request.email} 到 WHITELIST_EMAILS",
        whitelist=list(current_whitelist)
    )


@router.post("/admin/whitelist/remove", response_model=WhitelistResponse)
async def remove_from_whitelist(request: RemoveWhitelistRequest):
    """
    从白名单中移除邮箱（需要管理员密码）
    """
    # 验证管理员密码
    if not verify_admin_password(request.admin_password):
        raise HTTPException(
            status_code=403,
            detail="管理员密码错误"
        )
    
    # 获取当前白名单
    current_whitelist = settings.get_whitelist_emails
    
    # 检查是否在白名单中
    if request.email.lower() not in current_whitelist:
        return WhitelistResponse(
            success=False,
            message=f"邮箱 {request.email} 不在白名单中",
            whitelist=list(current_whitelist)
        )
    
    print(f"⚠️  注意：需要在 Render 环境变量中将此邮箱从 WHITELIST_EMAILS 中移除")
    print(f"⚠️  当前 WHITELIST_EMAILS: {settings.WHITELIST_EMAILS}")
    
    return WhitelistResponse(
        success=False,
        message=f"请在 Render 环境变量中从 WHITELIST_EMAILS 移除 {request.email}",
        whitelist=list(current_whitelist)
    )


@router.get("/admin/whitelist/list")
async def list_whitelist(admin_password: Optional[str] = Header(None, alias="X-Admin-Password")):
    """
    查看当前白名单（需要管理员密码）
    
    在请求头中设置 X-Admin-Password
    """
    # 验证管理员密码
    if not admin_password or not verify_admin_password(admin_password):
        raise HTTPException(
            status_code=403,
            detail="管理员密码错误或缺失"
        )
    
    current_whitelist = settings.get_whitelist_emails
    
    return WhitelistResponse(
        success=True,
        message=f"当前白名单共有 {len(current_whitelist)} 个邮箱",
        whitelist=list(current_whitelist)
    )


@router.post("/admin/user/grant-credits")
async def grant_user_credits(
    email: EmailStr,
    credits: int,
    admin_password: str
):
    """
    为指定用户增加算力（需要管理员密码）
    """
    # 验证管理员密码
    if not verify_admin_password(admin_password):
        raise HTTPException(
            status_code=403,
            detail="管理员密码错误"
        )
    
    if credits <= 0:
        raise HTTPException(
            status_code=400,
            detail="算力必须大于 0"
        )
    
    try:
        auth_service = get_auth_service()
        user = auth_service.get_user_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"用户 {email} 不存在"
            )
        
        # 增加算力
        old_credits = user.current_credits
        user.current_credits += credits
        auth_service.save_user(user)
        
        print(f"💰 管理员为用户 {email} 增加 {credits} 算力")
        print(f"   原算力: {old_credits}, 新算力: {user.current_credits}")
        
        return {
            "success": True,
            "message": f"成功为 {email} 增加 {credits} 算力",
            "old_credits": old_credits,
            "new_credits": user.current_credits
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"增加算力失败: {str(e)}"
        )

