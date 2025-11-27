"""
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.api.v1 import routes_upload, routes_tasks, routes_auth, routes_plans, routes_billing

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# 配置 CORS
# 支持 Vercel 预览域名（*.vercel.app）和生产域名
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware

app.add_middleware(
    StarletteCORSMiddleware,
    # 使用正则表达式匹配所有 Vercel 域名和本地开发域名
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+|https://formy-frontend\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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

