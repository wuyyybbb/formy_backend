@echo off
REM ==========================================
REM Docker 本地测试脚本（Windows）
REM ==========================================

echo.
echo ========================================
echo   Formy Backend Docker 本地测试
echo ========================================
echo.

REM 检查 Docker 是否运行
echo [1/5] 检查 Docker 状态...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker 未运行！请先启动 Docker Desktop
    pause
    exit /b 1
)
echo ✅ Docker 正在运行

REM 检查 .env 文件
echo.
echo [2/5] 检查环境变量文件...
if not exist .env (
    echo ⚠️  .env 文件不存在，从示例文件创建...
    copy .env.example .env >nul
    echo ✅ 已创建 .env 文件，请编辑后重新运行
    echo.
    echo 必须修改以下配置：
    echo   - SECRET_KEY
    echo   - RESEND_API_KEY
    pause
    exit /b 0
)
echo ✅ .env 文件存在

REM 构建并启动服务
echo.
echo [3/5] 构建 Docker 镜像...
docker-compose build
if errorlevel 1 (
    echo ❌ 构建失败！
    pause
    exit /b 1
)
echo ✅ 构建成功

echo.
echo [4/5] 启动服务...
docker-compose up -d
if errorlevel 1 (
    echo ❌ 启动失败！
    pause
    exit /b 1
)
echo ✅ 服务已启动

REM 等待服务就绪
echo.
echo [5/5] 等待服务就绪...
timeout /t 5 /nobreak >nul

REM 健康检查
echo.
echo 正在检查服务健康状态...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  服务可能还在启动中...
    echo 请等待 10-20 秒后访问: http://localhost:8000/health
) else (
    echo ✅ 服务健康检查通过！
)

REM 显示服务状态
echo.
echo ========================================
echo   服务状态
echo ========================================
docker-compose ps

REM 显示访问信息
echo.
echo ========================================
echo   访问地址
echo ========================================
echo.
echo   API 文档:     http://localhost:8000/docs
echo   健康检查:     http://localhost:8000/health
echo   根路径:       http://localhost:8000/
echo.
echo ========================================
echo   常用命令
echo ========================================
echo.
echo   查看日志:     docker-compose logs -f backend
echo   停止服务:     docker-compose down
echo   重启服务:     docker-compose restart
echo.

REM 询问是否查看日志
echo.
set /p view_logs="是否查看实时日志？(Y/N): "
if /i "%view_logs%"=="Y" (
    echo.
    echo 按 Ctrl+C 停止查看日志
    timeout /t 2 /nobreak >nul
    docker-compose logs -f backend
)

pause
