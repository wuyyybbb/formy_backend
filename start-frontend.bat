@echo off
echo ========================================
echo       启动 Formy 前端界面
echo ========================================
echo.

cd /d F:\formy\frontend

echo 正在启动前端服务...
echo 启动成功后会自动显示访问地址
echo 通常是: http://localhost:5173
echo.
echo 按 Ctrl+C 可以停止服务
echo ========================================
echo.

npm run dev

pause

