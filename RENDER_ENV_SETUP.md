# Render 环境变量配置指南

## 重要：JWT 密钥配置

**必须确保 `JWT_SECRET` 和 `SECRET_KEY` 设置为相同的值**，否则会导致登录签名和验签失败。

### 必需的环境变量

在 Render 控制台的 Environment Variables 中设置以下变量：

```env
# JWT 核心密钥（登录签名和验签使用同一个密钥）
JWT_SECRET=formy_super_secret_2025
SECRET_KEY=formy_super_secret_2025

# token 有效期（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 加密算法
ALGORITHM=HS256

# Redis（使用 Render Key Value Redis 内网地址）
REDIS_URL=redis://your-redis-instance:6379

# 允许跨域
CORS_ORIGINS=https://formy-frontend.vercel.app,http://localhost:3000,http://localhost:5173

# Resend API Key（用于发送验证码）
RESEND_API_KEY=your_resend_api_key_here
```

## 配置步骤

1. 登录 Render 控制台
2. 进入你的后端服务（Backend Service）
3. 点击左侧菜单的 **Environment**
4. 添加或更新以下环境变量：
   - `JWT_SECRET` = `formy_super_secret_2025`
   - `SECRET_KEY` = `formy_super_secret_2025`
   - `ACCESS_TOKEN_EXPIRE_MINUTES` = `1440`
   - `ALGORITHM` = `HS256`
   - `REDIS_URL` = （从 Render Redis 实例获取）
   - `CORS_ORIGINS` = `https://formy-frontend.vercel.app,http://localhost:3000,http://localhost:5173`
   - `RESEND_API_KEY` = （从 Resend 控制台获取）

## 注意事项

⚠️ **关键点**：
- `JWT_SECRET` 和 `SECRET_KEY` **必须完全相同**，否则会导致：
  - 登录时签名的 token 无法被 `/tasks` 等接口验证
  - 出现 "用户信息不存在" 或 "无效的令牌" 错误

## 验证配置

配置完成后，重启 Render 服务，然后：
1. 尝试登录，获取 token
2. 使用该 token 调用 `/tasks` 接口
3. 如果仍然出现 401 错误，检查：
   - 两个密钥是否完全一致（包括大小写、空格）
   - 是否已重启服务使配置生效

