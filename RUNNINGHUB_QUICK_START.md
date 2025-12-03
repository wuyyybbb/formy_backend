# RunningHub 快速启动指南 🚀

## ⚡ 5 分钟快速部署

### 1️⃣ 验证配置（1 分钟）

```bash
cd backend
python test_runninghub.py
```

或者在 Windows 上双击：
```
quick_test_runninghub.bat
```

**预期输出**:
```
✅ 所有测试通过！RunningHub Engine 配置成功
```

### 2️⃣ 启动服务（2 分钟）

#### Windows:

打开 **3 个** 命令行窗口：

**窗口 1 - 后端服务:**
```cmd
start-backend.bat
```

**窗口 2 - Worker 进程:**
```cmd
start-worker.bat
```

**窗口 3 - 前端服务 (可选):**
```cmd
cd ..\frontend
npm run dev
```

#### Linux/Mac:

```bash
# 终端 1 - 后端
cd backend
./start.sh

# 终端 2 - Worker
cd backend
python -m app.services.tasks.worker

# 终端 3 - 前端 (可选)
cd frontend
npm run dev
```

### 3️⃣ 测试 API（2 分钟）

#### 方式 1: 使用前端界面

访问 `http://localhost:5173/editor`，选择"换姿势"模式，上传图片测试。

#### 方式 2: 使用 cURL

```bash
# 创建任务
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "POSE_CHANGE",
    "source_image": "path/to/source.jpg",
    "reference_image": "path/to/pose.jpg"
  }'

# 查询任务状态（替换 {task_id}）
curl "http://localhost:8000/api/v1/tasks/{task_id}"
```

## ✅ 成功标志

如果看到以下输出，说明部署成功：

1. **测试脚本**:
   ```
   ✅ 健康检查通过！RunningHub API 连接正常
   ```

2. **后端日志**:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   [EngineRegistry] 配置加载成功
   [EngineRegistry] 引擎注册成功: runninghub_pose_transfer
   ```

3. **Worker 日志**:
   ```
   Worker started successfully
   Waiting for tasks...
   ```

4. **API 响应**:
   ```json
   {
     "task_id": "xxx",
     "status": "pending",
     "task_type": "POSE_CHANGE"
   }
   ```

## 🔧 配置位置

所有配置在 `backend/engine_config.yml`:

```yaml
engines:
  runninghub_pose_transfer:
    type: runninghub
    config:
      api_key: "84427127c24546879969f10983fe578a"  # ✅ 已配置
      workflow_id: "1996080571212349442"           # ✅ 已配置
      api_base_url: "https://api.runninghub.ai"   # ✅ 已配置
      timeout: 300
      poll_interval: 3

pipelines:
  pose_change:
    enabled: true  # ✅ 已启用
    steps:
      pose_transfer:
        engine: runninghub_pose_transfer  # ✅ 使用 RunningHub
```

## ❌ 常见错误

### 错误 1: 端口被占用

```
Error: Address already in use
```

**解决**: 关闭占用端口的进程或修改端口：

```bash
# Windows 查看端口占用
netstat -ano | findstr :8000

# Linux/Mac 查看端口占用
lsof -i :8000

# 修改端口（在 start-backend.bat 或 start.sh 中）
uvicorn app.main:app --port 8001
```

### 错误 2: Redis 连接失败

```
Error: Connection refused (redis)
```

**解决**: 启动 Redis 服务：

```bash
# Windows (使用 Memurai 或 Redis for Windows)
# 下载: https://www.memurai.com/

# Linux
sudo service redis-server start

# Mac
brew services start redis

# 或使用 Docker
docker run -d -p 6379:6379 redis
```

### 错误 3: 模块导入错误

```
ModuleNotFoundError: No module named 'xxx'
```

**解决**: 安装依赖：

```bash
cd backend
pip install -r requirements.txt
```

## 📊 监控面板

访问以下 URL 查看服务状态：

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **Engine 状态**: 查看后端日志
- **任务队列**: 查看 Worker 日志

## 📞 需要帮助？

如果遇到问题：

1. ✅ 查看 `RUNNINGHUB_DEPLOYMENT.md` 详细文档
2. ✅ 检查日志输出中的错误信息
3. ✅ 确认 API Key 和 Workflow ID 正确
4. ✅ 运行 `python test_runninghub.py` 诊断问题

## 🎉 部署成功！

现在您可以：

- ✅ 通过前端界面使用姿势迁移功能
- ✅ 通过 API 调用 RunningHub 工作流
- ✅ 处理大量图片任务
- ✅ 享受云端计算的便利

---

**配置时间**: < 5 分钟  
**上手难度**: ⭐⭐ (简单)  
**推荐指数**: ⭐⭐⭐⭐⭐

Happy coding! 🚀

