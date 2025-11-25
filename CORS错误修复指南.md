# CORS 错误修复指南

## 🔍 **当前错误**

**错误信息**:
```
Access to XMLHttpRequest at 'https://formy-backend.onrender.com/api/v1/auth/send-code' 
from origin 'https://formy-frontend-fulshxgny-wuyebeis-projects.vercel.app' 
has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**Network 面板显示**:
- OPTIONS 请求返回 **400 Bad Request**
- 请求被 CORS 策略阻止

---

## 🎯 **问题原因**

### **核心问题**:
1. **前端使用 Vercel 预览域名**: `https://formy-frontend-fulshxgny-wuyebeis-projects.vercel.app`
2. **后端 CORS 只允许生产域名**: `https://formy-frontend.vercel.app`
3. **Vercel 预览域名每次部署都会变化**，无法预先配置

---

## ✅ **解决方案**

### **方案 1: 更新后端 CORS 配置（已修复）**

后端代码已更新，支持所有 Vercel 域名：

```python
# backend/app/main.py
app.add_middleware(
    StarletteCORSMiddleware,
    # 使用正则表达式匹配所有 Vercel 域名
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+|https://formy-frontend\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**支持的范围**:
- ✅ 所有 `*.vercel.app` 域名（包括预览域名）
- ✅ 所有 `localhost` 端口（开发环境）
- ✅ 生产域名 `formy-frontend.vercel.app`

---

### **方案 2: 配置前端环境变量（Vercel）**

#### 步骤 1: 登录 Vercel Dashboard
访问: https://vercel.com/dashboard

#### 步骤 2: 进入项目设置
1. 找到 **formy_frontend** 项目
2. 点击项目进入详情
3. 点击 **"Settings"** 标签
4. 点击左侧 **"Environment Variables"**

#### 步骤 3: 添加环境变量
点击 **"Add New"**，添加：

```bash
Name: VITE_API_BASE_URL
Value: https://formy-backend.onrender.com/api/v1
Environment: Production, Preview, Development (全选)
```

#### 步骤 4: 重新部署
1. 点击 **"Deployments"** 标签
2. 找到最新的部署
3. 点击 **"..."** → **"Redeploy"**
4. 等待部署完成（2-3分钟）

---

### **方案 3: 更新 Render 环境变量（如果使用）**

虽然代码已支持通配符，但为了兼容，也可以在 Render 环境变量中添加：

```bash
CORS_ORIGINS=https://formy-frontend.vercel.app,https://*.vercel.app,http://localhost:5173
```

**注意**: 由于使用了正则表达式，这个环境变量实际上不会被使用，但保留也无妨。

---

## 🚀 **立即修复步骤**

### **步骤 1: 推送后端代码**

```bash
cd backend
git add app/main.py app/core/config.py
git commit -m "Fix CORS: Support Vercel preview domains"
git push origin main
```

### **步骤 2: 等待 Render 自动部署**
- Render 会自动检测代码更新
- 等待 2-3 分钟部署完成

### **步骤 3: 配置 Vercel 环境变量**
1. Vercel Dashboard → formy_frontend → Settings → Environment Variables
2. 添加: `VITE_API_BASE_URL = https://formy-backend.onrender.com/api/v1`
3. 重新部署前端

### **步骤 4: 测试**
1. 刷新前端页面
2. 点击"发送验证码"
3. ✅ 应该不再出现 CORS 错误

---

## 🧪 **验证修复**

### 1. 检查后端 CORS 响应头

在浏览器控制台执行：

```javascript
fetch('https://formy-backend.onrender.com/api/v1/auth/send-code', {
  method: 'OPTIONS',
  headers: {
    'Origin': 'https://formy-frontend-fulshxgny-wuyebeis-projects.vercel.app',
    'Access-Control-Request-Method': 'POST',
    'Access-Control-Request-Headers': 'content-type'
  }
})
.then(response => {
  console.log('Status:', response.status);
  console.log('CORS Headers:', {
    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
  });
})
.catch(error => console.error('Error:', error));
```

**✅ 成功响应**:
```
Status: 200
CORS Headers: {
  'Access-Control-Allow-Origin': 'https://formy-frontend-fulshxgny-wuyebeis-projects.vercel.app',
  'Access-Control-Allow-Methods': '*',
  'Access-Control-Allow-Headers': '*'
}
```

### 2. 检查前端请求

在浏览器 Network 面板：
- ✅ OPTIONS 请求返回 **200**（不是 400）
- ✅ POST 请求成功发送
- ✅ 收到验证码响应

---

## 📋 **完整配置检查清单**

### 后端（Render）
- [ ] 代码已更新（支持 Vercel 预览域名）
- [ ] 已推送到 GitHub
- [ ] Render 自动部署完成
- [ ] 后端日志无错误

### 前端（Vercel）
- [ ] 环境变量 `VITE_API_BASE_URL` 已配置
- [ ] 值为: `https://formy-backend.onrender.com/api/v1`
- [ ] 已重新部署
- [ ] 前端可以正常访问

### 测试
- [ ] 浏览器控制台无 CORS 错误
- [ ] Network 面板 OPTIONS 请求返回 200
- [ ] 可以成功发送验证码
- [ ] 收到验证码邮件

---

## 🔍 **常见问题**

### Q1: 为什么 Vercel 预览域名会变化？
**A**: Vercel 为每次 Pull Request 或分支部署创建唯一的预览域名，格式为：
```
https://<project-name>-<hash>-<username>.vercel.app
```

### Q2: 可以只配置生产域名吗？
**A**: 可以，但这样预览环境无法使用。推荐使用通配符支持所有 Vercel 域名。

### Q3: 开发环境也需要配置吗？
**A**: 不需要，代码中已包含 `http://localhost:\d+` 支持所有本地端口。

### Q4: 为什么 OPTIONS 请求返回 400？
**A**: 因为后端 CORS 配置不允许该域名，现在已修复。

### Q5: 如何确认 CORS 配置生效？
**A**: 查看 Network 面板的 Response Headers，应该包含：
```
Access-Control-Allow-Origin: https://formy-frontend-fulshxgny-wuyebeis-projects.vercel.app
Access-Control-Allow-Methods: *
Access-Control-Allow-Headers: *
```

---

## 📊 **修复前后对比**

| 项目 | 修复前 | 修复后 |
|------|--------|--------|
| **CORS 支持** | ❌ 只支持生产域名 | ✅ 支持所有 Vercel 域名 |
| **OPTIONS 请求** | ❌ 返回 400 | ✅ 返回 200 |
| **预览环境** | ❌ 无法使用 | ✅ 完全支持 |
| **开发环境** | ✅ 支持 | ✅ 支持 |

---

## 🎉 **修复完成后的效果**

1. ✅ 所有 Vercel 预览域名都可以访问后端
2. ✅ 生产域名正常工作
3. ✅ 本地开发环境正常工作
4. ✅ 不再出现 CORS 错误
5. ✅ 验证码功能完全正常

---

## 📞 **需要帮助？**

如果修复后仍有问题：

1. **检查后端日志**: Render Dashboard → Logs
2. **检查前端环境变量**: Vercel Dashboard → Settings → Environment Variables
3. **检查浏览器控制台**: F12 → Console/Network
4. **验证后端部署**: 访问 `https://formy-backend.onrender.com/docs`

---

**更新时间**: 2025-11-20  
**问题**: CORS 错误阻止前端访问后端  
**解决方案**: 使用正则表达式支持所有 Vercel 域名
