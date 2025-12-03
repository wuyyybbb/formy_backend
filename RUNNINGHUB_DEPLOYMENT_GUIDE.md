# RunningHub 部署指南

## 📋 概述

本项目已经集成了 RunningHub 作为 AI 图像处理引擎，用于姿势迁移功能。

**RunningHub 工作流链接：**
https://www.runninghub.ai/workflow/1996080571212349442?source=workspace

**API Key:** `84427127c24546879969f10983fe578a`

---

## ✅ 已完成的集成

### 1. Engine 实现
- ✅ `backend/app/services/image/engines/runninghub_engine.py` - 完整实现
- ✅ 支持图片上传、工作流提交、状态轮询、结果下载

### 2. 配置文件
- ✅ `backend/engine_config.yml` - 已配置 RunningHub 引擎
```yaml
engines:
  runninghub_pose_transfer:
    type: runninghub
    config:
      api_key: "84427127c24546879969f10983fe578a"
      workflow_id: "1996080571212349442"
      api_base_url: "https://api.runninghub.ai"
      timeout: 300
      poll_interval: 3

pipelines:
  pose_change:
    enabled: true
    steps:
      pose_transfer:
        engine: runninghub_pose_transfer
```

### 3. Pipeline 集成
- ✅ `pose_change_pipeline.py` - 自动从注册表获取 RunningHub 引擎
- ✅ 支持自动图片上传、工作流执行、结果保存

---

## 🚀 部署步骤

### 方案 1: Render 部署（推荐）

#### 1. 配置环境变量（可选）
如果需要从环境变量读取 API Key：

```bash
# 在 Render Dashboard 中添加环境变量
RUNNINGHUB_API_KEY=84427127c24546879969f10983fe578a
```

然后修改 `engine_config.yml`：
```yaml
api_key: "${RUNNINGHUB_API_KEY}"
```

#### 2. 部署后端
```bash
# 后端会自动启动，无需额外配置
# Engine Registry 会在启动时自动加载配置并初始化 RunningHub Engine
```

#### 3. 验证部署
访问健康检查接口：
```bash
curl https://your-backend.onrender.com/api/v1/health
```

---

### 方案 2: 本地部署测试

#### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 2. 确认配置文件
检查 `backend/engine_config.yml` 中 RunningHub 配置是否正确。

#### 3. 启动后端
```bash
# Windows
.\start-backend.bat

# Linux/Mac
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. 测试 RunningHub 引擎
```python
# 测试脚本
import sys
sys.path.append('./backend')

from app.services.image.engines.registry import get_engine_registry

# 获取注册表
registry = get_engine_registry('./backend/engine_config.yml')

# 获取 RunningHub 引擎
engine = registry.get_engine('runninghub_pose_transfer')

# 健康检查
is_healthy = engine.health_check()
print(f"RunningHub Engine 健康状态: {is_healthy}")

# 测试执行（需要准备测试图片）
result = engine.execute({
    "raw_image": "/path/to/source_image.jpg",
    "pose_image": "/path/to/pose_reference.jpg"
})
print(f"执行结果: {result}")
```

---

## 🔧 配置说明

### Engine 配置参数

```yaml
runninghub_pose_transfer:
  type: runninghub  # 引擎类型
  config:
    api_key: "YOUR_API_KEY"              # RunningHub API Key
    workflow_id: "YOUR_WORKFLOW_ID"      # 工作流 ID（从 URL 中提取）
    api_base_url: "https://api.runninghub.ai"  # API 基础 URL
    timeout: 300        # 超时时间（秒），默认 300
    poll_interval: 3    # 轮询间隔（秒），默认 3
```

### 从 URL 提取 Workflow ID

工作流 URL：
```
https://www.runninghub.ai/workflow/1996080571212349442?source=workspace
```

提取出的 Workflow ID：
```
1996080571212349442
```

---

## 📡 API 调用流程

### 1. 前端提交任务
```javascript
POST /api/v1/tasks
{
  "task_type": "pose_change",
  "source_image": "file_123456",
  "config": {
    "pose_image": "file_789012"
  }
}
```

### 2. 后端处理流程
```
1. Task Manager 接收任务
2. Worker 从 Redis 队列中获取任务
3. 调用 PoseChangePipeline
4. Pipeline 从 Registry 获取 runninghub_pose_transfer 引擎
5. RunningHub Engine:
   - 上传图片到 RunningHub
   - 提交工作流执行请求
   - 轮询任务状态（每 3 秒）
   - 下载结果图片
6. 保存结果到本地
7. 更新任务状态为 completed
```

### 3. 前端轮询结果
```javascript
GET /api/v1/tasks/{task_id}
{
  "status": "completed",
  "result": {
    "output_image": "/results/task_xxx_output.jpg"
  }
}
```

---

## 🐛 调试和排错

### 查看日志
```bash
# 查看 RunningHub Engine 日志
# 日志会输出到控制台和日志文件

# 关键日志标识：
# [RunningHub Engine] 初始化完成
# [RunningHub Engine] 提交工作流到 RunningHub
# [RunningHub Engine] 任务状态: running
# [RunningHub Engine] 任务结果解析成功
```

### 常见问题

#### 1. API Key 无效
```
错误：提交工作流失败: HTTP 401
解决：检查 engine_config.yml 中的 api_key 是否正确
```

#### 2. Workflow ID 不存在
```
错误：提交工作流失败: HTTP 404
解决：确认 workflow_id 是否正确，访问工作流 URL 验证
```

#### 3. 超时错误
```
错误：任务执行超时: 300 秒
解决：增加 timeout 配置或检查 RunningHub 服务状态
```

#### 4. 图片上传失败
```
错误：上传图片失败
解决：检查图片文件是否存在，文件格式是否支持（JPG/PNG）
```

### 健康检查
```python
# 检查 RunningHub Engine 是否可用
from app.services.image.engines.registry import get_engine_registry

registry = get_engine_registry()
health_status = registry.health_check_all()
print(health_status)

# 输出示例：
# {'runninghub_pose_transfer': True}
```

---

## 📊 性能优化建议

### 1. 并发处理
- 使用 Redis 队列 + Worker 模式
- 可启动多个 Worker 实例并发处理任务

### 2. 图片缓存
- 启用配置文件中的缓存选项
- 相同输入可直接返回缓存结果

### 3. 超时设置
```yaml
# 根据实际情况调整
timeout: 300  # 复杂任务可增加到 600
poll_interval: 3  # 降低轮询频率节省 API 调用
```

### 4. 错误重试
```yaml
global:
  retry:
    max_attempts: 3  # 最多重试 3 次
    retry_delay: 2   # 重试间隔 2 秒
```

---

## 🔒 安全建议

1. **不要在代码中硬编码 API Key**
   - 使用环境变量或配置文件
   - 不要将 `engine_config.yml` 提交到公开仓库（已添加到 .gitignore）

2. **API Key 轮换**
   - 定期更换 RunningHub API Key
   - 使用 Render 的环境变量功能动态注入

3. **访问控制**
   - 后端 API 需要用户认证
   - 限制任务创建频率（防止滥用）

---

## 📚 参考资料

- **RunningHub 官网：** https://www.runninghub.ai
- **工作流管理：** https://www.runninghub.ai/workflow/1996080571212349442
- **API 文档：** https://api.runninghub.ai/docs

---

## ✅ 部署清单

- [x] RunningHub Engine 已实现
- [x] engine_config.yml 已配置
- [x] API Key 已设置
- [x] Workflow ID 已设置
- [x] Pipeline 已集成
- [x] 注册表自动加载引擎
- [ ] 环境变量配置（可选）
- [ ] 健康检查测试
- [ ] 完整功能测试

---

## 🎉 总结

您的后端已经完整集成了 RunningHub！**无需额外部署步骤**，只需：

1. ✅ 确认配置文件正确（已完成）
2. ✅ 启动后端服务
3. ✅ 测试姿势迁移功能

**现在就可以直接使用！**

