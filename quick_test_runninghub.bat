@echo off
echo ========================================
echo   RunningHub 集成快速测试
echo ========================================
echo.

cd /d "%~dp0"

echo [1] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo 错误：未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)
echo.

echo [2] 运行 RunningHub 测试脚本...
echo.
python test_runninghub.py

echo.
echo ========================================
echo 测试完成！
echo ========================================
echo.

pause

