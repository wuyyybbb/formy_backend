# ⚡ 快速修复 CORS 错误 - 3 个步骤

## ❌ 问题
前端访问后端时出现 CORS 错误：`Missing Header: Access-Control-Allow-Origin`

---

## ✅ 解决方法（3 分钟）

### 步骤 1: 登录 Render

访问: https://dashboard.render.com/

点击 **`formy-backend`** 服务

---

### 步骤 2: 添加环境变量

1. 点击左侧 **"Environment"** 标签

2. 找到或新建 `CORS_ORIGINS` 变量

3. 设置值为：
   ```
   https://formy-frontend.vercel.app,http://localhost:3000,http://localhost:5173
   ```

4. 点击 **"Save Changes"**

> **重要**: 
> - 多个域名用**逗号**分隔
> - **不要有空格**
> - 必须包含 `https://`

---

### 步骤 3: 重新部署

1. 返回服务主页

2. 点击 **"Manual Deploy"**

3. 选择 **"Deploy latest commit"**

4. 等待 3-5 分钟

---

## 🧪 验证

访问前端：https://formy-frontend.vercel.app/

尝试上传图片，应该**不再有 CORS 错误**！✅

---

## 📝 Render 环境变量配置

| 变量名 | 值 |
|--------|-----|
| `CORS_ORIGINS` | `https://formy-frontend.vercel.app,http://localhost:3000,http://localhost:5173` |

---

## 🚨 如果还有问题

1. 确认环境变量已保存
2. 确认已重新部署
3. 清除浏览器缓存（Ctrl + Shift + R）
4. 查看 Render Logs 确认部署成功

---

**完整指南**: 查看 `CORS错误修复指南.md`

---

**3 步骤完成，CORS 错误解决！** 🎉

