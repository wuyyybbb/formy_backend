# RunningHub 部署指南

本指南将帮助您将后端从 onething/autodl 切换到 RunningHub 云端工作流服务。

## 📋 配置概览

### 已完成的修改

1. ✅ 创建 `RunningHubEngine` - 专用于 RunningHub API 调用
2. ✅ 更新 `engine_config.yml` - 配置 RunningHub 工作流
3. ✅ 注册新引擎类型 - 添加到引擎注册表
4. ✅ 禁用旧引擎 - 注释掉 onething/autodl 相关配置

### RunningHub 配置信息

- **API Key**: `84427127c24546879969f10983fe578a`
- **Workflow ID**: `1996080571212349442`
- **Workflow URL**: https://www.runninghub.ai/workflow/1996080571212349442?source=workspace
- **API Base URL**: `https://api.runninghub.ai`

## 🚀 部署步骤

### 1. 验证配置

首先运行测试脚本验证配置是否正确：

```bash
cd backend
python test_runninghub.py
```

测试脚本会检查：
- Engine 注册是否成功
- API Key 和 Workflow ID 是否有效
- RunningHub API 连接是否正常
- Pipeline 配置是否正确

### 2. 安装依赖

确保已安装所有必要的 Python 包：

```bash
pip install -r requirements.txt
```

主要依赖：
- `requests` - HTTP 请求
- `PyYAML` - 配置文件解析
- `fastapi` - Web 框架
- `redis` - 任务队列

### 3. 环境变量配置（可选）

如果需要将 API Key 存储为环境变量：

```bash
# Linux/Mac
export RUNNINGHUB_API_KEY="84427127c24546879969f10983fe578a"

# Windows
set RUNNINGHUB_API_KEY=84427127c24546879969f10983fe578a
```

然后修改 `engine_config.yml`:

```yaml
engines:
  runninghub_pose_transfer:
    type: runninghub
    config:
      api_key: "${RUNNINGHUB_API_KEY}"  # 使用环境变量
      workflow_id: "1996080571212349442"
      # ...
```

### 4. 启动后端服务

#### 方式 1: 使用启动脚本（推荐）

```bash
# Windows
start-backend.bat

# Linux/Mac
./start.sh
```

#### 方式 2: 手动启动

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 启动 Worker

Worker 负责处理异步任务：

```bash
cd backend
python -m app.services.tasks.worker
```

或使用启动脚本：

```bash
# Windows
start-worker.bat
```

### 6. 测试 API

#### 测试姿势迁移任务

```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "POSE_CHANGE",
    "source_image": "/path/to/source_image.jpg",
    "reference_image": "/path/to/pose_image.jpg"
  }'
```

响应示例：

```json
{
  "task_id": "task_abc123",
  "status": "pending",
  "task_type": "POSE_CHANGE",
  "created_at": "2025-12-03T12:00:00Z"
}
```

#### 查询任务状态

```bash
curl "http://localhost:8000/api/v1/tasks/{task_id}"
```

## 📂 文件结构

```
backend/
├── app/
│   └── services/
│       └── image/
│           ├── engines/
│           │   ├── base.py                      # Engine 基类
│           │   ├── runninghub_engine.py        # ✨ 新增：RunningHub Engine
│           │   ├── registry.py                 # ✅ 已更新：注册 RunningHub
│           │   └── __init__.py                 # ✅ 已更新：导出 RunningHub
│           └── pipelines/
│               └── pose_change_pipeline.py     # 姿势迁移 Pipeline
├── engine_config.yml                           # ✅ 已更新：配置 RunningHub
├── test_runninghub.py                          # ✨ 新增：测试脚本
└── RUNNINGHUB_DEPLOYMENT.md                    # ✨ 新增：本文档
```

## 🔧 配置说明

### engine_config.yml

```yaml
engines:
  # RunningHub 姿势迁移工作流
  runninghub_pose_transfer:
    type: runninghub                    # 引擎类型
    config:
      api_key: "YOUR_API_KEY"          # RunningHub API Key
      workflow_id: "WORKFLOW_ID"       # 工作流 ID
      api_base_url: "https://api.runninghub.ai"  # API 基础 URL
      timeout: 300                     # 超时时间（秒）
      poll_interval: 3                 # 轮询间隔（秒）

pipelines:
  # 换姿势 Pipeline
  pose_change:
    enabled: true
    steps:
      pose_transfer:
        engine: runninghub_pose_transfer  # 使用 RunningHub 引擎
        description: "RunningHub 姿势迁移工作流"
```

### 配置参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `api_key` | RunningHub API Key（必填） | - |
| `workflow_id` | 工作流 ID（必填） | - |
| `api_base_url` | API 基础 URL | `https://api.runninghub.ai` |
| `timeout` | 任务执行超时时间（秒） | `300` |
| `poll_interval` | 状态轮询间隔（秒） | `3` |

## 🔍 工作流程

### 姿势迁移任务流程

```
1. 前端上传图片
   ↓
2. 后端创建任务 (POST /api/v1/tasks)
   ↓
3. 任务写入 Redis 队列
   ↓
4. Worker 消费任务
   ↓
5. PoseChangePipeline.execute()
   ↓
6. RunningHubEngine.execute()
   ├── 上传图片到 RunningHub
   ├── 提交工作流
   ├── 轮询任务状态
   └── 下载结果图片
   ↓
7. 更新任务状态为 completed
   ↓
8. 前端轮询获取结果
```

### RunningHub API 调用流程

```python
# 1. 上传图片
POST /v1/upload
→ 返回图片 URL

# 2. 提交工作流
POST /v1/workflows/{workflow_id}/run
Body: {
  "inputs": {
    "raw_image": "image_url_1",
    "pose_image": "image_url_2"
  }
}
→ 返回 task_id

# 3. 轮询任务状态（每 3 秒）
GET /v1/tasks/{task_id}
→ 返回状态和结果

# 4. 下载结果图片
GET {output_image_url}
→ 保存到本地
```

## 🐛 故障排查

### 问题 1: 引擎未注册

**错误信息**:
```
[EngineRegistry] 不支持的引擎类型: runninghub
```

**解决方法**:
1. 检查 `app/services/image/engines/registry.py` 中是否添加了 RunningHub
2. 确认 `engine_classes` 字典包含 `"runninghub": RunningHubEngine`

### 问题 2: API Key 无效

**错误信息**:
```
提交工作流失败: HTTP 401, Unauthorized
```

**解决方法**:
1. 检查 `engine_config.yml` 中的 `api_key` 是否正确
2. 在 RunningHub 网站上验证 API Key 是否有效
3. 确认 API Key 没有多余的空格或换行

### 问题 3: Workflow ID 错误

**错误信息**:
```
提交工作流失败: HTTP 404, Workflow not found
```

**解决方法**:
1. 从 RunningHub URL 中提取正确的 Workflow ID
2. URL 格式: `https://www.runninghub.ai/workflow/{WORKFLOW_ID}`
3. 示例: URL 是 `...workflow/1996080571212349442...`，则 ID 是 `1996080571212349442`

### 问题 4: 任务超时

**错误信息**:
```
任务执行超时: 300 秒
```

**解决方法**:
1. 增加 `timeout` 配置值（例如 600 秒）
2. 检查 RunningHub 服务是否正常
3. 查看任务是否在 RunningHub 控制台中显示为运行中

### 问题 5: 图片上传失败

**错误信息**:
```
上传图片失败: FileNotFoundError
```

**解决方法**:
1. 确认图片文件路径正确
2. 检查文件权限
3. 确认图片格式支持（JPG, PNG）

## 📊 监控和日志

### 查看日志

Engine 会输出详细的执行日志：

```
[INFO] [RunningHubEngine] RunningHub Engine 初始化完成 - Workflow: 1996080571212349442
[INFO] [RunningHubEngine] 开始执行 RunningHub 工作流: 1996080571212349442
[INFO] [RunningHubEngine] 图片已上传到 RunningHub: source.jpg -> https://...
[INFO] [RunningHubEngine] 提交工作流到 RunningHub: https://api.runninghub.ai/v1/workflows/.../run
[INFO] [RunningHubEngine] 工作流已提交，任务 ID: task_abc123
[INFO] [RunningHubEngine] 等待任务完成: task_abc123
[INFO] [RunningHubEngine] 任务状态: running (已用时 5 秒)
[INFO] [RunningHubEngine] 任务状态: completed (已用时 45 秒)
[INFO] [RunningHubEngine] 任务结果解析成功，输出图片: https://...
[INFO] [RunningHubEngine] RunningHub 工作流执行成功
```

### 健康检查

定期检查 Engine 健康状态：

```python
from app.services.image.engines import get_engine_registry

registry = get_engine_registry()
health_status = registry.health_check_all()

print(health_status)
# {'runninghub_pose_transfer': True}
```

## 🔐 安全建议

1. **不要将 API Key 提交到 Git**
   - 使用环境变量
   - 添加到 `.gitignore`
   - 使用密钥管理服务（如 AWS Secrets Manager）

2. **API Key 权限管理**
   - 定期轮换 API Key
   - 限制 API Key 权限范围
   - 监控 API 使用情况

3. **网络安全**
   - 使用 HTTPS
   - 配置防火墙规则
   - 限制 API 访问速率

## 📈 性能优化

1. **调整轮询间隔**
   - 短任务：`poll_interval: 2` 秒
   - 长任务：`poll_interval: 5` 秒

2. **并发处理**
   - 启动多个 Worker 实例
   - 使用 Redis 队列负载均衡

3. **缓存优化**
   - 缓存上传的图片 URL
   - 复用相同的输入图片

## 📚 相关资源

- **RunningHub 官网**: https://www.runninghub.ai
- **Workflow URL**: https://www.runninghub.ai/workflow/1996080571212349442?source=workspace
- **API 文档**: 查看 RunningHub 官方文档
- **技术支持**: 联系 RunningHub 客服

## ✅ 部署检查清单

部署前请确认：

- [ ] 已安装所有依赖包
- [ ] `engine_config.yml` 配置正确
- [ ] API Key 已设置
- [ ] Workflow ID 已设置
- [ ] 运行测试脚本通过
- [ ] 后端服务启动成功
- [ ] Worker 进程运行正常
- [ ] Redis 服务可用
- [ ] 测试 API 调用成功
- [ ] 已禁用旧的 onething/autodl 配置

---

**部署完成！** 🎉

现在您的后端已成功切换到 RunningHub，可以开始使用云端工作流服务了。

