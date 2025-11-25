# Render Redis 配置指南

## 🎯 问题描述

**错误信息**:
```
发送验证码失败: Redis连接失败, 请检查配置. Error 111 connecting to localhost:6379. Connection refused.
```

**原因**: Render 后端环境没有配置 Redis 连接信息，默认连接 `localhost:6379` 失败。

---

## ✅ 解决方案（两种方式）

### **方式 A：使用 Render 自带的 Redis（推荐，免费）**

#### 1. 创建 Redis 实例

1. 登录 Render Dashboard: https://dashboard.render.com/
2. 点击右上角 **"New +"** 按钮
3. 选择 **"Redis"**
4. 配置：
   ```
   Name: formy-redis
   Region: 选择与后端相同的区域（如 Oregon (US West)）
   Plan: Free（免费版，足够开发使用）
   ```
5. 点击 **"Create Redis"**
6. 等待部署完成（约 1-2 分钟）

#### 2. 获取 Redis 连接信息

创建完成后，在 Redis 实例页面找到：

- **Internal Redis URL**: `redis://red-xxxxxxxxxxxxx:6379`
- **External Redis URL**: `redis://red-xxxxxxxxxxxxx.oregon-postgres.render.com:6379`

**推荐使用 Internal Redis URL**（更快，免费）

#### 3. 配置后端环境变量

1. 进入后端服务 **"formy_backend"**
2. 点击左侧 **"Environment"** 标签
3. 点击 **"Add Environment Variable"**
4. 添加以下变量：

```bash
# Redis 配置（使用 REDIS_URL，最简单）
REDIS_URL=redis://red-xxxxxxxxxxxxx:6379

# 或者分别配置（二选一）
REDIS_HOST=red-xxxxxxxxxxxxx.oregon-postgres.render.com
REDIS_PORT=6379
# REDIS_PASSWORD=密码（如果有的话）
```

#### 4. 重新部署后端

- 环境变量更新后，Render 会自动重启服务
- 或手动点击 **"Manual Deploy"** → **"Deploy latest commit"**

#### 5. 验证配置

查看后端部署日志，应该看到：
```
✅ Redis 连接成功！
```

---

### **方式 B：使用外部 Redis 服务**

如果不想用 Render 的 Redis，可以使用：

#### 1. Redis Cloud（推荐）
- 网站: https://redis.com/try-free/
- 免费额度: 30MB，足够开发使用
- 全球节点，速度快

#### 2. Upstash（推荐）
- 网站: https://upstash.com/
- 免费额度: 10,000 命令/天
- 自动扩展，支持 REST API

#### 配置步骤：
1. 注册并创建 Redis 实例
2. 获取连接 URL
3. 在 Render 后端环境变量中设置 `REDIS_URL`

---

## 📋 完整的环境变量清单

在 Render 后端服务中配置以下所有环境变量：

```bash
# Redis 配置（必须）
REDIS_URL=redis://red-xxxxxxxxxxxxx:6379

# 邮件服务配置（必须）
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=onboarding@resend.dev

# CORS 配置（必须）
CORS_ORIGINS=https://formy-frontend.vercel.app,http://localhost:5173

# JWT 配置（必须，生成一个随机密钥）
SECRET_KEY=your-super-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 应用配置（可选）
DEBUG=False
APP_NAME=Formy
```

---

## 🔐 获取 RESEND_API_KEY

登录功能还需要邮件服务，请按以下步骤获取：

### 1. 注册 Resend
- 访问: https://resend.com/
- 使用 GitHub 账号登录
- 免费版：3,000 封邮件/月

### 2. 创建 API Key
1. 进入 Dashboard
2. 点击 **"API Keys"**
3. 点击 **"Create API Key"**
4. 名称: `formy-production`
5. 权限: **"Sending access"**
6. 复制生成的 API Key（格式：`re_xxxxx`）

### 3. 配置到 Render
在后端环境变量中添加：
```bash
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxx
```

---

## 🧪 测试步骤

### 1. 检查后端日志

在 Render 后端服务的 **"Logs"** 标签页，查看启动日志：

**✅ 成功的日志**:
```bash
✅ Redis 连接成功！
🔧 邮件服务初始化:
   - API Key: 已配置
   - From Email: onboarding@resend.dev
```

**❌ 失败的日志**:
```bash
❌ Redis 连接失败: Connection refused
📋 当前配置:
   REDIS_HOST: localhost
   REDIS_PORT: 6379
🔧 解决方案:
   1. 在 Render 创建 Redis 实例
   2. 在环境变量中设置 REDIS_URL
```

### 2. 测试登录功能

1. 访问前端: https://formy-frontend.vercel.app
2. 点击右上角 **"登录"** 按钮
3. 输入邮箱: `your@email.com`
4. 点击 **"发送验证码"**
5. ✅ 应该看到切换到验证码输入界面
6. 检查邮箱，输入验证码
7. ✅ 登录成功

---

## ⚠️ 常见问题

### Q1: Redis 连接超时
**现象**: `Timeout connecting to Redis`

**解决**:
1. 检查 Redis 实例是否在运行
2. 检查 REDIS_URL 是否正确
3. 使用 Internal Redis URL 而不是 External

### Q2: 验证码邮件没收到
**原因**: RESEND_API_KEY 未配置或无效

**解决**:
1. 检查环境变量中的 `RESEND_API_KEY`
2. 登录 Resend 查看 API Key 状态
3. 查看后端日志确认邮件是否发送成功

### Q3: CORS 错误
**现象**: 前端请求被阻止

**解决**:
在后端环境变量中设置：
```bash
CORS_ORIGINS=https://formy-frontend.vercel.app,http://localhost:5173
```

---

## 📸 配置截图示例

### Render Redis 实例页面
```
Name: formy-redis
Status: Available
Plan: Free
Internal Redis URL: redis://red-xxxxx:6379  ← 复制这个
```

### Render 后端环境变量页面
```
Environment Variables:
  REDIS_URL = redis://red-xxxxx:6379
  RESEND_API_KEY = re_xxxxx
  CORS_ORIGINS = https://formy-frontend.vercel.app
  SECRET_KEY = your-secret-key
```

---

## 🎉 配置完成检查清单

- [ ] Render Redis 实例已创建
- [ ] REDIS_URL 已添加到后端环境变量
- [ ] RESEND_API_KEY 已配置
- [ ] CORS_ORIGINS 包含前端域名
- [ ] SECRET_KEY 已设置（不使用默认值）
- [ ] 后端服务已重新部署
- [ ] 后端日志显示 "✅ Redis 连接成功"
- [ ] 前端可以发送验证码
- [ ] 邮件可以正常接收
- [ ] 登录功能正常工作

---

## 📞 需要帮助？

如果配置后仍有问题：

1. **查看后端日志**: Render Dashboard → formy_backend → Logs
2. **查看前端错误**: 浏览器 F12 → Console/Network 标签
3. **检查环境变量**: Render Dashboard → Environment → 确认所有变量已设置

---

**更新时间**: 2025-11-20  
**作者**: Cursor AI Assistant

