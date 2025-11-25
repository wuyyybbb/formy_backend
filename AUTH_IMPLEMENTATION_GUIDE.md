# 邮箱验证码登录实现指南

## 📋 概述

已成功实现完整的**邮箱验证码登录**功能，包含：
- ✅ 数据库层：User 表（Redis 存储）
- ✅ 后端层：3 个认证 API
- ✅ 邮件服务：Resend 发送验证码
- ✅ 前端层：登录弹窗组件

---

## 🏗️ 系统架构

```
用户输入邮箱
     ↓
前端：调用发送验证码 API
     ↓
后端：生成 6 位验证码
     ↓
Resend：发送邮件到用户邮箱
     ↓
用户：收到邮件，输入验证码
     ↓
前端：调用登录 API
     ↓
后端：验证验证码
     ↓
后端：获取或创建用户
     ↓
后端：生成 JWT Token
     ↓
前端：保存 Token 和用户信息
     ↓
登录成功！
```

---

## 📂 文件结构

### 后端文件

```
backend/
├── app/
│   ├── models/
│   │   └── user.py                    # 用户模型
│   ├── schemas/
│   │   └── auth.py                    # 认证 DTO
│   ├── services/
│   │   ├── auth/
│   │   │   └── auth_service.py        # 认证服务
│   │   └── email/
│   │       └── resend_service.py      # 邮件服务
│   ├── api/
│   │   └── v1/
│   │       └── routes_auth.py         # 认证路由
│   └── main.py                        # 注册路由
├── .env.example                       # 环境变量示例
└── requirements.txt                   # 添加 python-jose
```

### 前端文件

```
frontend/
└── src/
    ├── api/
    │   ├── auth.ts                    # 认证 API
    │   └── index.ts                   # 导出认证函数
    ├── components/
    │   └── auth/
    │       └── LoginModal.tsx         # 登录弹窗
    └── pages/
        └── LandingPage.tsx            # 添加登录按钮
```

---

## 🔧 后端实现

### 1. 用户模型（`backend/app/models/user.py`）

**User 表字段**：
- `user_id`: 用户唯一 ID
- `email`: 邮箱地址（唯一）
- `username`: 用户名（可选）
- `avatar`: 头像 URL（可选）
- `created_at`: 创建时间
- `last_login`: 最后登录时间
- `is_active`: 是否激活

**VerificationCode 字段**：
- `email`: 邮箱
- `code`: 6 位验证码
- `expires_at`: 过期时间
- `is_used`: 是否已使用

**存储方式**：Redis
- 用户数据：`user:email:{email}` 和 `user:id:{user_id}`
- 验证码：`verification_code:{email}`（10 分钟过期）

---

### 2. 三个 API

#### API 1: 发送验证码

**接口**：`POST /api/v1/auth/send-code`

**请求体**：
```json
{
  "email": "user@example.com"
}
```

**响应**：
```json
{
  "success": true,
  "message": "验证码已发送到 user@example.com",
  "expires_in": 600
}
```

**流程**：
1. 生成 6 位数字验证码
2. 保存到 Redis（10 分钟过期）
3. 调用 Resend API 发送邮件

---

#### API 2: 验证码登录

**接口**：`POST /api/v1/auth/login`

**请求体**：
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": "usr_123456",
    "email": "user@example.com",
    "username": "user",
    "avatar": null,
    "created_at": "2025-01-01T00:00:00",
    "last_login": "2025-01-01T00:00:00"
  }
}
```

**流程**：
1. 验证验证码（是否存在、是否过期、是否已使用）
2. 获取或创建用户（首次登录自动创建）
3. 生成 JWT Token（24 小时有效期）
4. 返回 Token 和用户信息

---

#### API 3: 获取当前用户

**接口**：`GET /api/v1/auth/me`

**请求头**：
```
Authorization: Bearer <token>
```

**响应**：
```json
{
  "user": {
    "user_id": "usr_123456",
    "email": "user@example.com",
    "username": "user",
    "avatar": null,
    "created_at": "2025-01-01T00:00:00",
    "last_login": "2025-01-01T00:00:00"
  }
}
```

**流程**：
1. 从 Authorization header 解析 Token
2. 解码并验证 JWT
3. 从 Redis 获取用户信息
4. 返回用户数据

---

### 3. 邮件服务（Resend）

**Resend 配置**：
- API Key：`RESEND_API_KEY`
- 发件人：`support@formy.it.com`

**邮件样式**：
- 深色主题（符合 Formy 品牌风格）
- 青色强调色
- 大号验证码显示
- 包含有效期提示

**邮件内容**：
```
标题：【Formy】您的验证码是 123456

正文：
  - Logo + 品牌名
  - 标题：验证码登录
  - 6 位验证码（大号、居中、青色）
  - 提示：10 分钟有效、勿告知他人
  - Footer：版权信息
```

---

## 🎨 前端实现

### 1. 登录弹窗（`LoginModal.tsx`）

**两步流程**：
1. **输入邮箱** → 发送验证码
2. **输入验证码** → 登录

**功能特性**：
- ✅ 邮箱格式验证
- ✅ 验证码倒计时（60 秒）
- ✅ 错误提示
- ✅ Loading 状态
- ✅ 支持回车键提交
- ✅ 自动聚焦
- ✅ 返回上一步
- ✅ 重新发送验证码

**UI 设计**：
- 深色主题
- 青色主色调
- 居中弹窗
- 背景模糊遮罩

---

### 2. Landing Page 集成

**功能**：
- ✅ Header 添加"登录"按钮
- ✅ 登录后显示用户信息和头像
- ✅ 用户菜单（我的工作台、退出登录）
- ✅ 自动从本地存储恢复登录状态

**用户体验**：
- 未登录：显示"登录"按钮
- 已登录：显示用户名和头像
- 点击头像：弹出用户菜单

---

### 3. 认证 API（`frontend/src/api/auth.ts`）

**API 函数**：
```typescript
sendVerificationCode(email)  // 发送验证码
loginWithCode(email, code)   // 登录
getCurrentUser()             // 获取当前用户
```

**本地存储工具**：
```typescript
saveAuthInfo(token, user)    // 保存认证信息
getToken()                   // 获取 Token
getUserInfo()                // 获取用户信息
clearAuthInfo()              // 清除认证信息
isLoggedIn()                 // 检查是否登录
```

**自动处理**：
- Token 自动添加到 Axios header
- 页面加载时自动恢复登录状态

---

## ⚙️ 配置步骤

### 1. 获取 Resend API Key

1. 访问 https://resend.com/
2. 注册账号
3. 验证域名（`formy.it.com`）
4. 创建 API Key

### 2. 配置后端环境变量

创建 `backend/.env` 文件：

```bash
# 复制示例文件
cd backend
cp .env.example .env
```

编辑 `.env` 文件，填写：

```env
# Resend 配置
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=support@formy.it.com

# JWT 密钥（生产环境必须修改！）
SECRET_KEY=your-super-secret-key-here

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 3. 安装依赖

```bash
cd backend
pip install python-jose[cryptography]
# 或
pip install -r requirements.txt
```

### 4. 重启后端

```bash
cd backend
python -m uvicorn app.main:app --reload
```

---

## 🧪 测试流程

### 测试 1: 发送验证码

**使用 curl**：
```bash
curl -X POST http://localhost:8000/api/v1/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com"}'
```

**预期结果**：
- 返回 `{"success": true, ...}`
- 收到邮件

---

### 测试 2: 登录

**使用 curl**：
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","code":"123456"}'
```

**预期结果**：
- 返回包含 `access_token` 和 `user` 的 JSON

---

### 测试 3: 获取当前用户

**使用 curl**：
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <your_token>"
```

**预期结果**：
- 返回用户信息

---

### 测试 4: 前端完整流程

1. **访问首页**
   ```
   http://localhost:5173
   ```

2. **点击"登录"按钮**
   - 弹出登录弹窗

3. **输入邮箱**
   - 点击"发送验证码"
   - 检查邮箱收到验证码

4. **输入验证码**
   - 输入 6 位验证码
   - 点击"登录"

5. **验证登录状态**
   - Header 显示用户名和头像
   - 点击头像查看菜单
   - 刷新页面，登录状态保持

---

## 🔒 安全性

### 已实现的安全措施

✅ **验证码安全**：
- 10 分钟过期
- 一次性使用（用后失效）
- Redis 自动清理

✅ **JWT Token 安全**：
- 24 小时有效期
- HMAC-SHA256 签名
- 包含用户 ID 和邮箱

✅ **传输安全**：
- 生产环境建议使用 HTTPS
- CORS 限制允许的域名

---

## 📊 数据流示例

### Redis 数据结构

**验证码**：
```
Key: verification_code:user@example.com
Value: {"code":"123456","created_at":"2025-01-01T00:00:00","is_used":false}
TTL: 600 秒
```

**用户（按邮箱）**：
```
Key: user:email:user@example.com
Value: {"user_id":"usr_123456","email":"user@example.com",...}
TTL: 无（永久）
```

**用户（按 ID）**：
```
Key: user:id:usr_123456
Value: {"user_id":"usr_123456","email":"user@example.com",...}
TTL: 无（永久）
```

---

## 🚨 常见问题

### Q1: 收不到验证码邮件？

**可能原因**：
1. `RESEND_API_KEY` 未配置或错误
2. 发件人邮箱未验证
3. 收件人邮箱在垃圾邮件中

**解决方法**：
1. 检查 `.env` 文件
2. 在 Resend 控制台验证域名
3. 查看后端日志：`✅ 验证码邮件已发送到: xxx`

---

### Q2: 登录提示"验证码错误或已过期"？

**可能原因**：
1. 验证码输入错误
2. 验证码已过期（超过 10 分钟）
3. 验证码已使用
4. Redis 未运行

**解决方法**：
1. 检查验证码是否正确
2. 重新发送验证码
3. 确保 Redis 正在运行

---

### Q3: 前端刷新后登录状态丢失？

**可能原因**：
- Token 未保存到 localStorage

**解决方法**：
- 确保调用了 `saveAuthInfo(token, user)`
- 检查浏览器控制台是否有错误

---

### Q4: API 返回 401 Unauthorized？

**可能原因**：
1. Token 未传递
2. Token 已过期
3. Token 签名错误

**解决方法**：
1. 检查请求 Header：`Authorization: Bearer <token>`
2. 重新登录获取新 Token
3. 确保前后端 `SECRET_KEY` 一致

---

## 🎯 后续优化建议

### 功能增强

- [ ] 添加第三方登录（Google、GitHub）
- [ ] 添加手机号登录
- [ ] 添加用户资料编辑
- [ ] 添加邮箱绑定/换绑
- [ ] 添加登录历史记录

### 安全增强

- [ ] 添加验证码发送频率限制（防止滥用）
- [ ] 添加 IP 黑名单
- [ ] 添加 Refresh Token 机制
- [ ] 添加设备管理（多设备登录）

### 用户体验

- [ ] 记住我（延长 Token 有效期）
- [ ] 社交账号头像
- [ ] 用户偏好设置
- [ ] 邮件通知订阅

---

## 📚 相关文档

- **Resend 文档**: https://resend.com/docs
- **FastAPI 文档**: https://fastapi.tiangolo.com/
- **JWT 规范**: https://jwt.io/

---

## ✅ 功能清单

### 后端

- [x] User 数据模型
- [x] 验证码生成和存储
- [x] Resend 邮件发送
- [x] JWT Token 生成和验证
- [x] API 1: 发送验证码
- [x] API 2: 验证码登录
- [x] API 3: 获取当前用户
- [x] 环境变量配置
- [x] 依赖项更新

### 前端

- [x] 登录弹窗组件
- [x] 邮箱输入和验证
- [x] 验证码输入
- [x] 倒计时功能
- [x] 错误提示
- [x] 认证 API 封装
- [x] 本地存储管理
- [x] Landing Page 集成
- [x] 用户菜单
- [x] 登出功能

---

**登录功能已完成！** 🎉

现在用户可以通过邮箱验证码登录 Formy 了！

