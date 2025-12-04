"""
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.api.v1 import routes_upload, routes_tasks, routes_auth, routes_plans, routes_billing, routes_admin

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# 配置 CORS
# 从环境变量读取允许的来源（支持任何前端域名）
print("\n" + "="*60)
print("🔒 CORS Configuration")
print("="*60)
cors_origins = settings.get_cors_origins
print(f"Allowed Origins: {cors_origins}")
print("="*60 + "\n")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # 从环境变量 CORS_ORIGINS 读取
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 确保上传目录存在
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.RESULT_DIR).mkdir(parents=True, exist_ok=True)

# 挂载静态文件服务（用于访问上传的图片）
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/results", StaticFiles(directory=settings.RESULT_DIR), name="results")

# 注册 API 路由
app.include_router(routes_upload.router, prefix=settings.API_V1_PREFIX, tags=["upload"])
app.include_router(routes_tasks.router, prefix=settings.API_V1_PREFIX, tags=["tasks"])
app.include_router(routes_auth.router, prefix=settings.API_V1_PREFIX, tags=["auth"])
app.include_router(routes_plans.router, prefix=settings.API_V1_PREFIX, tags=["plans"])
app.include_router(routes_billing.router, prefix=settings.API_V1_PREFIX, tags=["billing"])
app.include_router(routes_admin.router, prefix=settings.API_V1_PREFIX, tags=["admin"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Formy API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    import os
    
    # 从配置读取，支持云平台的动态端口（如 Render 的 $PORT）
    port = int(os.getenv("PORT", settings.PORT))
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting Formy Backend Server")
    print(f"{'='*60}")
    print(f"Host: {settings.HOST}")
    print(f"Port: {port}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"{'='*60}\n")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=port,
        reload=settings.DEBUG
    )

