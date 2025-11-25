# ☁️ Render 平台快速部署指南

5 分钟将 Formy Backend 部署到 Render 生产环境！

---

## 📋 前置准备

✅ GitHub 仓库已创建: `https://github.com/wuyyybbb/formy_backend.git`  
✅ 代码已推送到 GitHub  
✅ 有 Resend API Key  
✅ 有 Render 账号（没有的话免费注册: https://render.com）

---

## 🚀 部署步骤

### 步骤 1: 推送代码到 GitHub

```bash
cd F:\formy\backend

# 检查本地提交
git log --oneline -3

# 推送到 GitHub（如果还没推送）
git push origin main

# 或使用 GitHub Desktop 推送
```

---

### 步骤 2: 登录 Render

访问: https://dashboard.render.com/

使用 GitHub 账号登录（推荐）或邮箱注册

---

### 步骤 3: 创建 Blueprint

**Blueprint 会自动创建所有服务（Backend + Redis）**

1. 点击右上角 **"New +"**
2. 选择 **"Blueprint"**
3. 点击 **"Connect a repository"**
4. 授权 GitHub（如果首次使用）
5. 在列表中找到 **`formy_backend`** 仓库
6. 点击 **"Connect"**

Render 会自动读取 `render.yaml` 并显示：

```
✅ Web Service: formy-backend (Docker)
✅ Redis:       formy-redis (Free Plan)
```

7. 点击 **"Apply"** 按钮

---

### 步骤 4: 配置环境变量

部署会自动开始，但需要配置环境变量才能正常工作。

1. 在 Dashboard 中点击 **`formy-backend`** 服务
2. 点击左侧 **"Environment"** 标签
3. 添加/修改以下变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `RESEND_API_KEY` | `re_xxxxxxxxxxxxxx` | ⚠️ 必填：你的 Resend API 密钥 |
| `FROM_EMAIL` | `support@formy.it.com` | ⚠️ 必填：发件邮箱 |
| `CORS_ORIGINS` | `https://formy-frontend.vercel.app` | ⚠️ 必填：前端域名 |
| `SECRET_KEY` | （自动生成的值） | ✅ 保持自动生成 |

4. 点击 **"Save Changes"**

5. 服务会自动重新部署（约 2-3 分钟）

---

### 步骤 5: 等待部署完成

**构建过程**（约 3-5 分钟）：

```
1. ⬇️  拉取代码...
2. 🔨 构建 Docker 镜像...
   - 安装 Python 3.10
   - 安装依赖包
   - 复制应用代码
3. 🚀 启动容器...
4. ✅ 部署完成！
```

部署完成后，你会看到：

```
✅ Live
Your service is live at https://formy-backend-xxxx.onrender.com
```

---

### 步骤 6: 验证部署

点击部署 URL 或访问以下端点：

```bash
# 健康检查
https://formy-backend-xxxx.onrender.com/health

# 预期输出
{"status": "healthy"}

# API 文档
https://formy-backend-xxxx.onrender.com/docs

# 根路径
https://formy-backend-xxxx.onrender.com/
```

---

## ✅ 完成！

恭喜！你的后端已成功部署到 Render！

**获取的服务：**

- ✅ **Backend API**: `https://formy-backend-xxxx.onrender.com`
- ✅ **Redis**: 内部 URL（自动连接）
- ✅ **HTTPS**: 自动配置的 SSL 证书
- ✅ **自动部署**: 推送代码到 GitHub 自动触发部署

---

## 🔄 更新代码

### 本地修改后推送

```bash
cd F:\formy\backend

# 修改代码...

git add .
git commit -m "Update backend"
git push origin main
```

**Render 会自动检测更新并重新部署！**

---

## 📊 监控和日志

### 查看日志

1. 在 Dashboard 中点击 **`formy-backend`** 服务
2. 点击 **"Logs"** 标签
3. 实时查看应用日志

### 查看指标

点击 **"Metrics"** 标签查看：

- CPU 使用率
- 内存使用率
- 请求数量
- 响应时间

---

## ⚠️ Render Free Plan 限制

**了解免费套餐限制**：

| 限制 | 说明 | 影响 |
|------|------|------|
| **自动休眠** | 15 分钟无活动后休眠 | 首次访问需等待 30-60 秒冷启动 |
| **月度小时数** | 750 小时/月（足够 24/7 运行） | 单个服务可持续运行 |
| **内存** | 512 MB | 够用，但不要运行大型任务 |
| **带宽** | 100 GB/月 | 通常足够 |

### 解决休眠问题

**方法 1: 使用 UptimeRobot（推荐）**

1. 注册 https://uptimerobot.com/（免费）
2. 添加监控:
   - URL: `https://formy-backend-xxxx.onrender.com/health`
   - 间隔: 5 分钟
3. 每 5 分钟自动 ping，保持服务活跃

**方法 2: 升级到付费计划**

- **Starter Plan**: $7/月
- 无休眠
- 更多资源

---

## 🔧 常见问题

### 1. 部署失败：Build Error

**检查**：

1. 查看 Logs 标签中的错误信息
2. 确认 `Dockerfile` 格式正确
3. 确认 `requirements.txt` 中的包都能安装

**解决**：

```bash
# 本地测试 Docker 构建
cd F:\formy\backend
docker build -t test .
```

---

### 2. 服务启动但无法访问

**检查**：

1. 查看 Logs，确认没有启动错误
2. 确认环境变量都已配置
3. 检查 Redis 服务是否正常

**解决**：

在 Environment 标签检查必需的环境变量：
- `REDIS_HOST`
- `SECRET_KEY`
- `RESEND_API_KEY`

---

### 3. CORS 错误

**症状**：前端请求被浏览器阻止

**解决**：

1. 进入 Environment 标签
2. 修改 `CORS_ORIGINS`:
   ```
   https://formy-frontend.vercel.app,https://yourdomain.com
   ```
3. 保存后等待重新部署

---

### 4. 邮件发送失败

**检查**：

1. `RESEND_API_KEY` 是否正确
2. `FROM_EMAIL` 是否在 Resend 中验证
3. 查看 Resend Dashboard 的日志

---

### 5. Redis 连接失败

**症状**：日志中显示 `redis.exceptions.ConnectionError`

**解决**：

1. 检查 Redis 服务是否创建成功
2. 确认 `REDIS_HOST` 环境变量正确配置
3. Render 会自动注入 Redis 连接信息

---

## 🎯 下一步

### 连接前端

在前端项目中更新 API Base URL：

```bash
# frontend/.env
VITE_API_BASE_URL=https://formy-backend-xxxx.onrender.com/api/v1
```

### 配置自定义域名（可选）

1. 在 Render Dashboard 中点击服务
2. 点击 **"Settings"** 标签
3. 找到 **"Custom Domain"** 部分
4. 添加你的域名（例如：`api.formy.it.com`）
5. 在域名 DNS 中添加 CNAME 记录

---

## 📚 相关文档

- [Render 官方文档](https://render.com/docs)
- [Docker 部署指南](backend/DOCKER_DEPLOYMENT_GUIDE.md)
- [本地 Docker 测试](backend/DOCKER_QUICK_START.md)

---

## 🎉 成功！

你的 Formy Backend 现在已经：

- ✅ 部署到云端
- ✅ 拥有 HTTPS
- ✅ 自动扩展
- ✅ 自动部署
- ✅ 24/7 在线（Free Plan 有休眠）

**开始使用你的 API 吧！** 🚀

```
API Base URL: https://formy-backend-xxxx.onrender.com
API 文档:     https://formy-backend-xxxx.onrender.com/docs
```

