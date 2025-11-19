# Render 快速部署指南

## 🚀 5 分钟部署到 Render

### 前置准备

1. ✅ GitHub 账号
2. ✅ Render 账号（用 GitHub 登录即可）
3. ✅ Resend API Key（用于发送邮件）

---

## 📝 部署步骤

### 第 1 步：推送代码到 GitHub（如果还没推送）

```bash
cd F:\formy\backend
git add .
git commit -m "Add Docker configuration for Render"
git push origin main
```

---

### 第 2 步：创建 Redis 服务

1. 登录 https://render.com
2. 点击 **"New +"** → 选择 **"Redis"**
3. 配置：
   ```
   Name: formy-redis
   Plan: Starter ($7/月)
   Region: Oregon (US West)
   ```
4. 点击 **"Create Redis"**
5. **记下 Internal Connection String**：`red-xxxxxxxxxxxxx`（只要这部分）

---

### 第 3 步：部署 Backend API

1. 点击 **"New +"** → 选择 **"Web Service"**
2. 选择仓库 **"formy_backend"**
3. 配置：
   ```
   Name: formy-backend
   Region: Oregon (US West)
   Branch: main
   Runtime: Docker
   Instance Type: Starter ($7/月)
   ```
4. 点击 **"Create Web Service"**（先不要着急，还需要配置环境变量）

---

### 第 4 步：配置环境变量（重要！）

在创建服务后，点击 **"Environment"** 标签，添加以下变量：

#### 基础配置（必需）

```env
APP_NAME=Formy API
APP_VERSION=1.0.0
DEBUG=false
API_V1_PREFIX=/api/v1
```

#### Redis 配置（必需）

```env
REDIS_HOST=red-xxxxxxxxxxxxx    # ← 替换为你的 Redis Internal Hostname
REDIS_PORT=6379
REDIS_DB=0
```

#### 存储配置（必需）

```env
UPLOAD_DIR=uploads
RESULT_DIR=results
```

#### CORS 配置（必需）

```env
CORS_ORIGINS=https://your-frontend-url.vercel.app
```
**⚠️ 记得替换为你的前端实际域名！**

#### JWT 配置（必需，敏感）

```env
SECRET_KEY=生成的密钥    # ← 见下方生成方法
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

**生成 SECRET_KEY：**
在本地 PowerShell 中运行：
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
复制输出的字符串。

#### 邮件配置（必需，敏感）

```env
RESEND_API_KEY=re_xxxxxxxxxxxxx    # ← 从 Resend 获取
FROM_EMAIL=support@formy.it.com
```

---

### 第 5 步：保存并部署

1. 点击 **"Save Changes"**
2. Render 会自动开始构建和部署
3. 等待 3-5 分钟

---

### 第 6 步：验证部署

部署成功后，Render 会给你一个 URL，类似：
```
https://formy-backend-xxxxx.onrender.com
```

**测试健康检查：**
```bash
curl https://formy-backend-xxxxx.onrender.com/health
```

**查看 API 文档：**
浏览器打开：
```
https://formy-backend-xxxxx.onrender.com/docs
```

---

## ✅ 完成！

你的后端已经在 Render 上运行了！

### 下一步：

1. **更新前端 API URL**：
   ```typescript
   // frontend/.env.production
   VITE_API_BASE_URL=https://formy-backend-xxxxx.onrender.com/api/v1
   ```

2. **更新 CORS 配置**：
   在 Render 环境变量中，将前端 Vercel URL 添加到 `CORS_ORIGINS`

3. **测试登录功能**：
   确保 Resend 邮件能正常发送

---

## 🔧 常见问题

### Q1: 构建失败了怎么办？

查看 Render 的 **"Logs"** 标签，找到错误信息。常见原因：
- 依赖安装失败 → 检查 `requirements.txt`
- Dockerfile 语法错误 → 本地测试 `docker build .`

### Q2: 无法连接 Redis？

检查 `REDIS_HOST` 是否正确：
- ✅ 正确：`red-xxxxxxxxxxxxx`
- ❌ 错误：`redis://red-xxxxxxxxxxxxx:6379`（不要包含协议和端口）

### Q3: CORS 错误？

确保 `CORS_ORIGINS` 包含你的前端域名（不要有尾随斜杠）：
- ✅ 正确：`https://formy-frontend.vercel.app`
- ❌ 错误：`https://formy-frontend.vercel.app/`

### Q4: Render 免费计划够用吗？

❌ **不推荐免费计划**，因为：
- 15 分钟无请求后自动休眠
- 首次唤醒需要 30-60 秒
- 用户体验极差

✅ **推荐 Starter 计划**（$7/月）：
- 始终在线
- 更好的性能
- 适合生产环境

---

## 💰 预计成本

| 服务 | 计划 | 月费 |
|------|------|------|
| **Backend API** | Starter | $7 |
| **Redis** | Starter | $7 |
| **Worker**（可选） | Starter | $7 |
| **总计** | - | **$14-21/月** |

---

## 📞 需要帮助？

- Render 文档: https://render.com/docs
- 查看完整部署指南: `DOCKER_DEPLOY_GUIDE.md`

