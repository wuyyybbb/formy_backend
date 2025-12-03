#!/bin/bash
# ==========================================
# Formy Backend - 启动脚本
# 同时启动 API 服务器和 Worker
# ==========================================

echo "=========================================="
echo "🚀 Starting Formy Backend Services"
echo "=========================================="

# 启动 API 服务器（后台）
echo "📡 Starting API Server..."
gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - &

API_PID=$!
echo "✅ API Server started (PID: $API_PID)"

# 等待 API 服务器启动
sleep 3

# 启动 Worker（前台）
echo "⚡ Starting Pipeline Worker..."
python run_worker_pipeline.py &

WORKER_PID=$!
echo "✅ Worker started (PID: $WORKER_PID)"

echo "=========================================="
echo "✅ All services started successfully!"
echo "   API Server: http://0.0.0.0:${PORT:-8000}"
echo "   Worker: Running"
echo "=========================================="

# 等待任一进程退出
wait -n

# 如果任一进程退出，杀死所有进程
kill $API_PID $WORKER_PID 2>/dev/null
echo "❌ Service stopped"

