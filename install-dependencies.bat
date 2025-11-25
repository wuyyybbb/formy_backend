@echo off
echo ========================================
echo       安装 Formy 项目依赖
echo ========================================
echo.
echo 这个脚本会自动安装后端和前端的所有依赖
echo 只需要在第一次使用时运行一次
echo.
echo 按任意键开始安装...
pause > nul
echo.

echo ========================================
echo [1/2] 安装后端 Python 依赖
echo ========================================
cd /d F:\formy\backend
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [错误] 后端依赖安装失败！
    echo 请确保已安装 Python 3.10 或更高版本
    pause
    exit /b 1
)

echo.
echo ✓ 后端依赖安装完成
echo.

echo ========================================
echo [2/2] 安装前端 Node.js 依赖
echo ========================================
cd /d F:\formy\frontend
npm install

if errorlevel 1 (
    echo.
    echo [错误] 前端依赖安装失败！
    echo 请确保已安装 Node.js 16 或更高版本
    pause
    exit /b 1
)

echo.
echo ✓ 前端依赖安装完成
echo.

echo ========================================
echo       安装完成！
echo ========================================
echo.
echo 现在你可以：
echo 1. 双击 start-backend.bat 启动后端
echo 2. 双击 start-worker.bat 启动 Worker
echo 3. 双击 start-frontend.bat 启动前端
echo 4. 打开浏览器访问 http://localhost:5173
echo.
echo 祝你使用愉快！
echo.
pause

