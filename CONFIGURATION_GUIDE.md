# Formy Backend 配置指南

## 📋 概述

Formy Backend 使用**环境变量驱动**的配置方式，所有配置项都可以通过环境变量设置，无需修改代码。这使得在不同云平台（Render、阿里云、AWS等）部署时更加灵活。

## 🚀 快速开始

### 1. 复制环境变量模板

```bash
cp env.example .env
```

### 2. 编辑 `.env` 文件

填入您的实际配置值。

### 3. 启动应用

```bash
python -m uvicorn app.main:app --reload
```

---

## 📖 配置项详细说明

### 🔴 **必需配置**（必须设置）

#### Redis (缓存和任务队列)

```bash
# 方式1：完整 URL（推荐，适合云平台）
REDIS_URL=redis://localhost:6379/0

# 方式2：分散配置（本地开发）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # 如有密码
```

**云平台示例：**

- **Render**: 直接复制 Redis Internal URL
  ```bash
  REDIS_URL=redis://red-xxxxx:6379
  ```

- **阿里云 Redis**: 
  ```bash
  REDIS_URL=redis://:password@r-xxx.redis.rds.aliyuncs.com:6379/0
  ```

#### ComfyUI AI Engine

```bash
COMFYUI_BASE_URL=http://your-comfyui-server.com:7860
```

**当前使用的 ComfyUI 服务：**
```bash
# Onething AI GPU 实例
COMFYUI_BASE_URL=http://d5m-dbdcym9t4h0p6ianf-qdkzkd4d-custom.service.onethingrobot.com:7860
```

**阿里云部署 ComfyUI：**
1. 在阿里云 ECS (GPU 实例) 上部署 ComfyUI
2. 设置环境变量：
   ```bash
   COMFYUI_BASE_URL=http://your-aliyun-ecs-ip:7860
   # 或使用内网地址（更快更安全）
   COMFYUI_BASE_URL=http://172.16.x.x:7860
   ```

#### JWT Secret (用户认证)

```bash
# 生成随机密钥
SECRET_KEY=$(openssl rand -base64 32)
```

**示例：**
```bash
SECRET_KEY=hK7mP9nQ2rS4tU6vW8xY0zA1bC3dE5fG7hI9jK0lM2nO4p
```

---

### 🟡 **重要配置**（建议设置）

#### CORS (跨域资源共享)

```bash
# 逗号分隔的前端域名列表
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://your-frontend.com
```

**示例（Vercel + 阿里云）：**
```bash
CORS_ORIGINS=https://your-app.vercel.app,https://your-domain.com
```

#### Email Service (邮件服务)

**选项1：Resend (当前使用)**
```bash
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_your_api_key_here
FROM_EMAIL=noreply@your-domain.com
```

**选项2：阿里云 DirectMail**
```bash
EMAIL_PROVIDER=aliyun
ALIYUN_EMAIL_REGION=cn-hangzhou
ALIYUN_EMAIL_ACCESS_KEY_ID=your_access_key_id
ALIYUN_EMAIL_ACCESS_KEY_SECRET=your_access_key_secret
FROM_EMAIL=noreply@your-verified-domain.com
```

**选项3：SMTP (通用)**
```bash
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
FROM_EMAIL=your_email@gmail.com
```

---

### 🟢 **可选配置**

#### Storage (文件存储)

**本地存储 (默认)**
```bash
STORAGE_TYPE=local
UPLOAD_DIR=./uploads
RESULT_DIR=./results
```

**阿里云 OSS**
```bash
STORAGE_TYPE=oss
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_BUCKET_NAME=formy-uploads
OSS_BUCKET_DOMAIN=https://your-cdn-domain.com  # 可选，CDN加速域名
```

**优势：**
- ✅ 多实例共享文件
- ✅ 容器重启不丢失数据
- ✅ CDN 加速
- ✅ 自动备份

#### Application Settings

```bash
# 环境
ENVIRONMENT=production  # development / staging / production

# Debug 模式（生产环境建议关闭）
DEBUG=false

# 服务器配置
HOST=0.0.0.0
PORT=8000  # Render 等平台会自动设置 $PORT

# 日志
LOG_LEVEL=INFO  # DEBUG / INFO / WARNING / ERROR
LOG_FORMAT=json  # json / text

# 任务管理
TASK_RETENTION_DAYS=7
MAX_CONCURRENT_TASKS_PER_USER=3
```

#### Monitoring (监控)

```bash
# Sentry 错误追踪
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# 启用指标收集
ENABLE_METRICS=true
```

---

## 🌐 云平台部署配置

### Render 部署

1. **创建 Web Service**
2. **设置环境变量**（在 Dashboard 中）：

```bash
# 必需
REDIS_URL=<从 Render Redis 获取 Internal URL>
COMFYUI_BASE_URL=http://d5m-dbdcym9t4h0p6ianf-qdkzkd4d-custom.service.onethingrobot.com:7860
SECRET_KEY=<自动生成或手动设置>
RESEND_API_KEY=<从 Resend 获取>

# 可选
CORS_ORIGINS=https://your-frontend.vercel.app
FROM_EMAIL=noreply@your-domain.com
ENVIRONMENT=production
DEBUG=false
```

3. **Start Command**:
   ```bash
   # 后端 + Worker 合并模式
   python run_worker_pipeline.py & uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

---

### 阿里云部署

#### 方案1：阿里云 ECS + Docker

1. **创建 ECS 实例**

2. **设置环境变量**（在 `/etc/environment` 或 Docker Compose）：

```bash
# Redis (使用阿里云 Redis)
REDIS_URL=redis://:password@r-xxx.redis.rds.aliyuncs.com:6379/0

# ComfyUI (部署在同一 VPC 的 GPU 实例)
COMFYUI_BASE_URL=http://172.16.x.x:7860  # 内网地址

# Storage (使用阿里云 OSS)
STORAGE_TYPE=oss
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_BUCKET_NAME=formy-uploads

# Email (使用阿里云 DirectMail)
EMAIL_PROVIDER=aliyun
ALIYUN_EMAIL_REGION=cn-hangzhou
ALIYUN_EMAIL_ACCESS_KEY_ID=your_key_id
ALIYUN_EMAIL_ACCESS_KEY_SECRET=your_key_secret

# JWT
SECRET_KEY=$(openssl rand -base64 32)

# CORS (前端域名)
CORS_ORIGINS=https://your-domain.com

# 其他
ENVIRONMENT=production
DEBUG=false
```

3. **启动**:
   ```bash
   docker-compose up -d
   ```

#### 方案2：阿里云 SAE (Serverless 应用引擎)

在 SAE 控制台设置相同的环境变量。

---

## 🔧 engine_config.yml 环境变量支持

`engine_config.yml` 现在支持 `${ENV_VAR}` 占位符：

```yaml
engines:
  comfyui_pose_transfer:
    type: comfyui
    config:
      comfyui_url: "${COMFYUI_BASE_URL}"  # 从环境变量读取
      workflow_path: "./workflows/pose_swap_workflow.json"
      timeout: ${COMFYUI_TIMEOUT:300}  # 默认 300
      poll_interval: ${COMFYUI_POLL_INTERVAL:2}  # 默认 2
```

**支持的语法：**
- `${VAR_NAME}` - 读取环境变量
- `${VAR_NAME:default}` - 如果未设置，使用默认值

---

## 📝 配置优先级

1. **环境变量** (最高优先级)
2. **`.env` 文件**
3. **代码中的默认值** (最低优先级)

---

## ✅ 配置验证

### 启动时检查

应用启动时会自动打印配置状态：

```
============================================================
📋 Current Configuration
============================================================
Environment: production
Debug Mode: False
API Version: 1.0.0

Redis: redis://localhost:6379/0...
ComfyUI: http://your-comfyui-server.com:7860
Storage Type: local
Email Provider: resend
CORS Origins: http://localhost:3000, http://localhost:5173
============================================================
```

### 手动验证

```python
from app.core.config import settings, print_current_config

# 打印当前配置
print_current_config()

# 检查特定配置
print(f"Redis URL: {settings.get_redis_url}")
print(f"ComfyUI URL: {settings.COMFYUI_BASE_URL}")
```

### 环境变量检查工具

```python
from app.utils.env_parser import print_env_status

required_vars = [
    'REDIS_URL',
    'COMFYUI_BASE_URL',
    'SECRET_KEY',
    'RESEND_API_KEY'
]

print_env_status(required_vars, show_values=False)
```

---

## 🛠️ 故障排查

### Redis 连接失败

```
ValueError: REDIS_URL 未配置
```

**解决方案：**
1. 确认 `REDIS_URL` 环境变量已设置
2. 格式检查：`redis://[:password@]host[:port][/db]`
3. 测试连接：`redis-cli -u $REDIS_URL ping`

### ComfyUI 不可用

```
[EngineRegistry] ❌ 配置加载失败
```

**解决方案：**
1. 确认 `COMFYUI_BASE_URL` 已设置
2. 测试连接：`curl $COMFYUI_BASE_URL/system_stats`
3. 检查防火墙和网络策略

### 邮件发送失败

```
Resend API 返回错误: 403
```

**解决方案：**
1. 确认 `RESEND_API_KEY` 格式正确（以 `re_` 开头）
2. 检查 API Key 权限
3. Resend 免费版只能发送到注册邮箱

---

## 📚 参考资源

- [Pydantic Settings 文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [阿里云 OSS SDK](https://help.aliyun.com/document_detail/32026.html)
- [阿里云 DirectMail](https://help.aliyun.com/document_detail/29444.html)
- [Render 环境变量](https://render.com/docs/environment-variables)

---

## 💡 最佳实践

1. ✅ **使用环境变量**存储敏感信息（密钥、密码）
2. ✅ **不要提交** `.env` 文件到 Git
3. ✅ **定期轮换** JWT Secret Key
4. ✅ **使用 OSS/S3** 而非本地文件系统（生产环境）
5. ✅ **启用监控**（Sentry）以便快速发现问题
6. ✅ **使用内网地址**访问同 VPC 内的服务（如 Redis、ComfyUI）

---

## 🆘 获取帮助

如遇问题，请检查：
1. 环境变量是否正确设置
2. 服务（Redis、ComfyUI）是否正常运行
3. 网络连通性（防火墙、安全组）
4. 查看应用日志获取详细错误信息

