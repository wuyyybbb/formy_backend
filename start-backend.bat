@echo off
echo ========================================
echo       启动 Formy 后端 API 服务
echo ========================================
echo.

cd /d F:\formy\backend

echo 正在启动后端服务...
echo 如果看到 "Application startup complete." 说明启动成功
echo 成功后请访问: http://localhost:8000/health
echo.
echo 按 Ctrl+C 可以停止服务
echo ========================================
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause

