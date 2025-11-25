@echo off
echo ========================================
echo       启动 Formy Worker (任务处理)
echo ========================================
echo.

cd /d F:\formy\backend

echo 正在启动 Worker...
echo Worker 会处理图片任务并更新进度
echo.
echo 按 Ctrl+C 可以停止 Worker
echo ========================================
echo.

python run_worker_simple.py

pause

