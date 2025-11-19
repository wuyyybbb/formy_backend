# Docker 部署指南 - Render

## 📋 目录

1. [本地测试](#本地测试)
2. [Render 部署](#render-部署)
3. [环境变量配置](#环境变量配置)
4. [常见问题](#常见问题)

---

## 🏗️ 项目结构

```
backend/
├── Dockerfile              # Docker 镜像定义
├── .dockerignore          # Docker 忽略文件
├── docker-compose.yml     # 本地测试配置
├── render.yaml            # Render 部署配置
├── requirements.txt       # Python 依赖
├── app/                   # 应用代码
│   ├── main.py           # FastAPI 入口
│   ├── api/              # API 路由
│   ├── core/             # 核心配置
│   ├── models/           # 数据模型
│   ├── schemas/          # Pydantic 模型
│   └── services/         # 业务逻辑
└── run_worker_simple.py  # Worker 脚本
```

---

## 🐳 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| **Python** | 3.11 | 官方镜像 `python:3.11-slim` |
| **FastAPI** | 0.104.1 | Web 框架 |
| **Uvicorn** | 0.24.0 | ASGI 服务器 |
| **Gunicorn** | 21.2.0 | 生产级 WSGI 服务器 |
| **Redis** | 7-alpine | 任务队列 + 缓存 |

---

## 🧪 本地测试

### 方法 1: 使用 Docker Compose（推荐）

#### 1. 启动所有服务

```bash
cd F:\formy\backend

# 构建并启动
docker-compose up --build

# 或者在后台运行
docker-compose up -d --build
```

这会启动 3 个容器：
- ✅ **backend**: FastAPI API 服务（端口 8000）
- ✅ **redis**: Redis 数据库（端口 6379）
- ✅ **worker**: 异步任务处理器

#### 2. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 只查看 backend 日志
docker-compose logs -f backend

# 只查看 worker 日志
docker-compose logs -f worker
```

#### 3. 测试 API

```bash
# 健康检查
curl http://localhost:8000/health

# API 文档
浏览器打开: http://localhost:8000/docs

# 测试上传
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@test_image.jpg" \
  -F "purpose=source"
```

#### 4. 停止服务

```bash
# 停止并删除容器
docker-compose down

# 停止并删除容器 + 数据卷
docker-compose down -v
```

---

### 方法 2: 只构建 Docker 镜像

```bash
cd F:\formy\backend

# 构建镜像
docker build -t formy-backend:latest .

# 运行容器
docker run -p 8000:8000 \
  -e REDIS_HOST=host.docker.internal \
  -e SECRET_KEY=your-secret-key \
  -e RESEND_API_KEY=your-resend-key \
  formy-backend:latest
```

---

## 🚀 Render 部署

### 步骤 1: 准备 GitHub 仓库

确保以下文件已推送到 GitHub：
```
✅ Dockerfile
✅ .dockerignore
✅ requirements.txt
✅ render.yaml（可选）
✅ 完整的 app/ 目录
```

推送代码：
```bash
cd F:\formy\backend
git add .
git commit -m "Add Docker configuration for Render deployment"
git push origin main
```

---

### 步骤 2: 创建 Render 账号

1. 访问 https://render.com
2. 使用 GitHub 账号登录
3. 连接你的 GitHub 仓库

---

### 步骤 3: 部署 Redis（必需）

1. 在 Render Dashboard 点击 **"New +"**
2. 选择 **"Redis"**
3. 配置：
   - **Name**: `formy-redis`
   - **Plan**: `Starter` ($7/月) 或 `Free`（有限制）
   - **Region**: `Oregon (US West)`
4. 点击 **"Create Redis"**
5. 记下 **Internal Redis URL**（格式：`redis://red-xxxxx:6379`）

---

### 步骤 4: 部署 Backend API

#### 方式 A: 使用 render.yaml（推荐）

1. 在 Render Dashboard 点击 **"New +"**
2. 选择 **"Blueprint"**
3. 选择你的 GitHub 仓库 `formy_backend`
4. Render 会自动读取 `render.yaml` 并创建服务
5. 手动配置敏感信息（见下方）

#### 方式 B: 手动创建

1. 在 Render Dashboard 点击 **"New +"**
2. 选择 **"Web Service"**
3. 选择你的 GitHub 仓库 `formy_backend`
4. 配置：

| 配置项 | 值 |
|--------|-----|
| **Name** | `formy-backend` |
| **Region** | `Oregon (US West)` |
| **Branch** | `main` |
| **Runtime** | `Docker` |
| **Instance Type** | `Starter` ($7/月) 或 `Free`（有限制） |

5. 点击 **"Create Web Service"**

---

### 步骤 5: 配置环境变量

在 Render 服务页面，点击 **"Environment"** 标签，添加以下环境变量：

#### 必需的环境变量

| Key | Value | 说明 |
|-----|-------|------|
| `APP_NAME` | `Formy API` | 应用名称 |
| `APP_VERSION` | `1.0.0` | 版本号 |
| `DEBUG` | `false` | 生产环境设为 false |
| `API_V1_PREFIX` | `/api/v1` | API 路径前缀 |
| `REDIS_HOST` | `red-xxxxx` | Redis 内部主机名（从 Redis 服务复制） |
| `REDIS_PORT` | `6379` | Redis 端口 |
| `REDIS_DB` | `0` | Redis 数据库索引 |
| `UPLOAD_DIR` | `uploads` | 上传目录 |
| `RESULT_DIR` | `results` | 结果目录 |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app` | 前端域名（逗号分隔） |

#### 敏感环境变量（重要！）

| Key | Value | 说明 |
|-----|-------|------|
| `SECRET_KEY` | `生成的强密钥` | JWT 签名密钥（见下方生成方法） |
| `ALGORITHM` | `HS256` | JWT 算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `43200` | Token 过期时间（30天） |
| `RESEND_API_KEY` | `re_xxxxx` | Resend API 密钥 |
| `FROM_EMAIL` | `support@formy.it.com` | 发件人邮箱 |

#### 生成 SECRET_KEY

在本地运行：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

复制输出的字符串作为 `SECRET_KEY`。

---

### 步骤 6: 部署 Worker（可选，用于异步任务）

1. 在 Render Dashboard 点击 **"New +"**
2. 选择 **"Background Worker"**
3. 配置：
   - **Name**: `formy-worker`
   - **Runtime**: `Docker`
   - **Docker Command**: `python run_worker_simple.py`
   - **Environment**: 与 Backend 相同的环境变量
4. 点击 **"Create Background Worker"**

---

### 步骤 7: 验证部署

1. 等待构建完成（约 3-5 分钟）
2. 部署成功后，Render 会提供一个 URL：
   ```
   https://formy-backend-xxxxx.onrender.com
   ```
3. 测试健康检查：
   ```bash
   curl https://formy-backend-xxxxx.onrender.com/health
   ```
4. 查看 API 文档：
   ```
   https://formy-backend-xxxxx.onrender.com/docs
   ```

---

## 🔐 环境变量配置

### 本地开发环境

创建 `.env` 文件（不要提交到 Git）：

```env
# 应用配置
APP_NAME=Formy API
APP_VERSION=1.0.0
DEBUG=true
API_V1_PREFIX=/api/v1

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 存储配置
UPLOAD_DIR=uploads
RESULT_DIR=results

# CORS 配置
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# JWT 配置
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# 邮件服务
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=support@formy.it.com
```

### 生产环境（Render）

- ✅ 所有配置通过 Render Dashboard 的 **Environment** 标签设置
- ✅ 不要在代码中硬编码敏感信息
- ✅ 使用 Render 的 **Secret Files** 功能存储大型配置文件

---

## 🔍 监控和日志

### 查看 Render 日志

1. 打开 Render Dashboard
2. 选择你的服务（`formy-backend`）
3. 点击 **"Logs"** 标签
4. 实时查看应用日志

### 日志级别

Dockerfile 中配置的日志级别：
```dockerfile
CMD ["gunicorn", "app.main:app", \
     "--log-level", "info"]  # 可改为: debug, info, warning, error
```

---

## ⚠️ 常见问题

### 1. 构建失败：`ModuleNotFoundError`

**原因**：依赖未正确安装

**解决**：
```bash
# 本地测试依赖安装
pip install -r requirements.txt

# 确保 requirements.txt 包含所有依赖
pip freeze > requirements.txt
```

---

### 2. Redis 连接失败

**错误信息**：
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**解决**：
- 检查 `REDIS_HOST` 和 `REDIS_PORT` 是否正确
- 在 Render 中，使用 Redis 服务的 **Internal Hostname**（不是 External URL）
- 格式：`red-xxxxx`（不包括 `redis://` 前缀）

---

### 3. CORS 错误

**错误信息**：
```
Access to fetch at 'https://backend.onrender.com/api/v1/...' from origin 'https://frontend.vercel.app' has been blocked by CORS policy
```

**解决**：
在 Render 环境变量中更新 `CORS_ORIGINS`：
```
CORS_ORIGINS=https://your-frontend.vercel.app,https://your-custom-domain.com
```

---

### 4. 图片上传失败

**原因**：Render 的免费计划不支持持久化存储

**解决方案**：
1. **推荐**：使用云存储（S3、Cloudinary、七牛云）
2. **临时方案**：使用 Render 的磁盘存储（重启后丢失）

---

### 5. Worker 不工作

**原因**：Worker 未正确启动或无法连接 Redis

**解决**：
1. 检查 Worker 日志
2. 确认 Worker 的 `REDIS_HOST` 与 Backend 相同
3. 使用相同的环境变量配置

---

## 📊 性能优化

### 1. 调整 Gunicorn Workers 数量

在 `Dockerfile` 中：
```dockerfile
CMD ["gunicorn", "app.main:app", \
     "--workers", "4"]  # 推荐: (2 x CPU核心数) + 1
```

Render 实例类型对应的 CPU：
- **Free**: 0.5 CPU → 2 workers
- **Starter**: 0.5 CPU → 2 workers
- **Standard**: 2 CPU → 5 workers
- **Pro**: 4 CPU → 9 workers

### 2. 启用 Keep-Alive

```dockerfile
CMD ["gunicorn", "app.main:app", \
     "--keep-alive", "75"]  # 保持连接 75 秒
```

### 3. 增加超时时间

```dockerfile
CMD ["gunicorn", "app.main:app", \
     "--timeout", "120"]  # AI 任务可能需要更长时间
```

---

## 🎯 部署检查清单

部署前确保：

- [ ] `Dockerfile` 已创建并测试
- [ ] `.dockerignore` 已创建
- [ ] `requirements.txt` 包含 `gunicorn`
- [ ] 健康检查端点 `/health` 正常工作
- [ ] 所有代码已推送到 GitHub
- [ ] Redis 服务已在 Render 中创建
- [ ] 环境变量已正确配置
- [ ] `SECRET_KEY` 已生成并设置
- [ ] `CORS_ORIGINS` 已设置为前端域名
- [ ] `RESEND_API_KEY` 已设置
- [ ] 本地 Docker Compose 测试通过

---

## 🚀 后续优化

1. **配置自动部署**：在 Render 中启用 GitHub 自动部署
2. **添加监控**：使用 Sentry、Datadog 等监控工具
3. **配置备份**：定期备份 Redis 数据
4. **CDN 加速**：使用 Cloudflare 加速静态资源
5. **自定义域名**：在 Render 中配置自定义域名

---

## 📚 相关资源

- Render 文档: https://render.com/docs
- Docker 文档: https://docs.docker.com
- FastAPI 部署: https://fastapi.tiangolo.com/deployment/
- Gunicorn 文档: https://docs.gunicorn.org

---

## 🎉 完成！

现在你的 Formy Backend 已经可以在 Render 上运行了！

**下一步**：更新前端的 API 基础 URL 为 Render 提供的域名。

