# RESEND_API_KEY 配置问题排查指南

## 🔍 **当前错误**

**错误信息**:
```
发送邮件失败,请检查 RESEND_API_KEY 配置
```

**后端返回**: 500 Internal Server Error

---

## 🎯 **可能的原因**

### **1. API Key 值不完整（最常见）**

从您的截图看，Render 环境变量中显示：
```
RESEND_API_KEY: re_UyKQVkQT_6JNjQvf9Nb4a
```

**问题**: Resend API Key 通常是 **51 个字符**，格式为 `re_` + 48个字符。

**检查方法**:
1. 在 Render Dashboard 中点击环境变量
2. 查看完整的 API Key 值
3. 确认是否完整（应该以 `re_` 开头，总共约 51 个字符）

---

### **2. 环境变量格式问题**

**可能的问题**:
- 值前后有空格
- 值被引号包裹（不需要引号）
- 值中有换行符

**正确格式**:
```
RESEND_API_KEY=re_UyKQVkQT_6JNjQvf9Nb4a...（完整密钥）
```

**错误格式**:
```
RESEND_API_KEY="re_UyKQVkQT..."  ❌ 不要加引号
RESEND_API_KEY= re_UyKQVkQT...   ❌ 不要有前导空格
```

---

### **3. 后端服务未重新加载环境变量**

**问题**: 修改环境变量后，后端服务可能还在使用旧的配置。

**解决方法**:
1. 在 Render Dashboard 中，找到后端服务
2. 点击 **"Manual Deploy"** → **"Deploy latest commit"**
3. 等待重新部署完成（2-3分钟）

---

### **4. API Key 权限问题**

**检查方法**:
1. 登录 Resend Dashboard: https://resend.com/
2. 进入 **API Keys** 页面
3. 查看您的 API Key 权限：
   - ✅ **Full access** - 应该可以
   - ✅ **Sending access** - 应该可以
   - ❌ **Read only** - 无法发送邮件

---

### **5. API Key 已过期或被删除**

**检查方法**:
1. 登录 Resend Dashboard
2. 查看 API Key 状态：
   - ✅ **Active** - 正常
   - ❌ **Revoked** - 已撤销
   - ❌ **Expired** - 已过期

---

## ✅ **排查步骤（按顺序）**

### **步骤 1: 检查 Render 环境变量**

1. 登录 Render Dashboard: https://dashboard.render.com/
2. 进入后端服务 **formy_backend**
3. 点击 **"Environment"** 标签
4. 找到 **RESEND_API_KEY** 环境变量
5. 点击 **"Show value"** 或 **"Edit"** 查看完整值

**检查项**:
- [ ] 值是否完整（约 51 个字符）
- [ ] 是否以 `re_` 开头
- [ ] 没有前后空格
- [ ] 没有引号包裹

---

### **步骤 2: 验证 API Key 在 Resend 中有效**

1. 访问: https://resend.com/
2. 登录您的账号
3. 进入 **API Keys** 页面
4. 找到对应的 API Key（名称：Onboarding）
5. 检查：
   - [ ] 状态是 **Active**
   - [ ] 权限是 **Full access** 或 **Sending access**
   - [ ] 创建时间正确

---

### **步骤 3: 检查后端日志**

1. 在 Render Dashboard 中，点击 **"Logs"** 标签
2. 查看最新的日志，寻找：

**✅ 正常日志**:
```
🔧 邮件服务初始化:
   - API Key: 已配置
   - API Key 长度: 51 字符
   - API Key 预览: re_UyKQVkQ...vf9Nb4a
   - From Email: onboarding@resend.dev
```

**❌ 异常日志**:
```
🔧 邮件服务初始化:
   - API Key: ❌ 未配置
   ⚠️  警告: RESEND_API_KEY 未设置
```

或

```
⚠️  警告: RESEND_API_KEY 格式可能不正确（应该以 're_' 开头）
```

或

```
❌ Resend API 返回错误:
   - 状态码: 401
   - 错误信息: Invalid API key
   ⚠️  API Key 无效或已过期
```

---

### **步骤 4: 重新部署后端服务**

如果环境变量已正确配置，但日志显示未配置：

1. 在 Render Dashboard 中
2. 点击 **"Manual Deploy"** → **"Deploy latest commit"**
3. 等待部署完成
4. 再次查看日志

---

### **步骤 5: 测试 API Key（高级）**

使用 curl 或 Postman 测试 API Key：

```bash
curl -X POST https://api.resend.com/emails \
  -H "Authorization: Bearer re_YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "onboarding@resend.dev",
    "to": ["your@email.com"],
    "subject": "Test Email",
    "html": "<p>Test</p>"
  }'
```

**✅ 成功响应**:
```json
{
  "id": "email-id-here"
}
```

**❌ 失败响应**:
```json
{
  "message": "Invalid API key"
}
```

---

## 🔧 **修复方法**

### **方法 1: 重新复制 API Key**

1. 登录 Resend Dashboard
2. 进入 **API Keys** 页面
3. 如果 API Key 已存在，可以：
   - 点击 **"..."** → **"Delete"** 删除旧的
   - 点击 **"+ Create API key"** 创建新的
4. **立即复制** 完整的 API Key（只显示一次！）
5. 在 Render 中更新环境变量

### **方法 2: 更新 Render 环境变量**

1. 在 Render Dashboard 中
2. 进入后端服务 → **Environment**
3. 找到 **RESEND_API_KEY**
4. 点击 **"Edit"**
5. 粘贴完整的 API Key（确保没有空格）
6. 点击 **"Save Changes"**
7. **重新部署服务**

### **方法 3: 检查环境变量格式**

确保格式正确：

```bash
# ✅ 正确
RESEND_API_KEY=re_UyKQVkQT_6JNjQvf9Nb4a...（完整51字符）

# ❌ 错误 - 有引号
RESEND_API_KEY="re_UyKQVkQT_6JNjQvf9Nb4a..."

# ❌ 错误 - 有空格
RESEND_API_KEY= re_UyKQVkQT_6JNjQvf9Nb4a...

# ❌ 错误 - 不完整
RESEND_API_KEY=re_UyKQVkQT_6JNjQvf9Nb4a（缺少字符）
```

---

## 📊 **常见错误对照表**

| 后端日志 | 原因 | 解决方法 |
|---------|------|---------|
| `API Key: ❌ 未配置` | 环境变量未设置或为空 | 在 Render 中添加/更新 RESEND_API_KEY |
| `格式可能不正确` | API Key 不以 `re_` 开头 | 检查是否复制完整 |
| `状态码: 401` | API Key 无效或过期 | 在 Resend 创建新的 API Key |
| `状态码: 403` | API Key 权限不足 | 检查权限是否为 Full/Sending access |
| `状态码: 422` | 邮箱地址格式错误 | 检查收件人邮箱格式 |
| `网络请求失败` | 网络问题 | 检查 Render 服务网络连接 |

---

## 🧪 **快速诊断命令**

在 Render 后端 Logs 中，应该看到：

```bash
# 启动时的日志
🔧 邮件服务初始化:
   - API Key: 已配置
   - API Key 长度: 51 字符
   - API Key 预览: re_UyKQVkQ...vf9Nb4a
   - From Email: onboarding@resend.dev

# 发送邮件时的日志
📤 正在发送邮件到 wyb3206@163.com...
✅ 验证码邮件已发送到: wyb3206@163.com
```

如果看到：
```bash
⚠️  警告: RESEND_API_KEY 未设置
```
→ 环境变量未配置或未加载

如果看到：
```bash
❌ Resend API 返回错误:
   - 状态码: 401
```
→ API Key 无效，需要重新创建

---

## ✅ **验证修复成功**

修复后，测试发送验证码：

1. 刷新前端页面
2. 输入邮箱地址
3. 点击"发送验证码"
4. ✅ 应该看到切换到验证码输入界面
5. ✅ 检查邮箱收到验证码（可能在垃圾箱）

---

## 🆘 **仍然无法解决？**

### 收集以下信息：

1. **Render 后端日志**（最近 50 行）
   - 特别是邮件服务初始化和发送邮件的日志

2. **Resend Dashboard 截图**
   - API Keys 页面
   - 显示 API Key 状态和权限

3. **Render 环境变量截图**
   - 显示 RESEND_API_KEY 的配置（隐藏敏感部分）

4. **错误信息**
   - 前端显示的错误
   - 浏览器控制台的错误

---

## 📝 **最佳实践**

1. **API Key 管理**:
   - 为生产环境创建独立的 API Key
   - 定期轮换 API Key（每 3-6 个月）
   - 不要将 API Key 提交到 Git

2. **环境变量配置**:
   - 使用 Render 的环境变量功能（不要硬编码）
   - 修改后记得重新部署
   - 定期检查环境变量是否正确

3. **监控和日志**:
   - 定期查看后端日志
   - 监控邮件发送成功率
   - 设置告警（如果邮件发送失败率过高）

---

**更新时间**: 2025-11-20  
**问题**: RESEND_API_KEY 配置后仍报错  
**核心原因**: 环境变量格式、完整性或服务未重新加载

