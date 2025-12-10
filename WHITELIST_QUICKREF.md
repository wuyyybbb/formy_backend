# 🎯 白名单快速参考

## 当前配置状态

### 🌟 VIP 白名单（10000 积分）
- wyb3206@163.com
- wuyebei3206@gmail.com

### 🎁 试用白名单（1000 积分）  
- 553588070@qq.com

### 👥 普通用户（100 积分）
- 所有其他用户

---

## 🚀 快速添加试用用户

### 步骤 1: 生成配置
```bash
cd backend
python add_trial_user.py 新邮箱@example.com
```

### 步骤 2: 复制输出的配置
脚本会输出类似：
```
TRIAL_WHITELIST_EMAILS=553588070@qq.com,新邮箱@example.com
```

### 步骤 3: 更新 Render
1. 打开 https://dashboard.render.com
2. 选择 `formy-backend`
3. 点击 `Environment` 标签
4. 找到 `TRIAL_WHITELIST_EMAILS`
5. 粘贴新值
6. 点击 `Save Changes`

---

## 📋 Render 环境变量清单

需要在 Render 中设置这些环境变量：

```env
VIP_WHITELIST_EMAILS=wyb3206@163.com,wuyebei3206@gmail.com
VIP_WHITELIST_CREDITS=10000
TRIAL_WHITELIST_EMAILS=553588070@qq.com
TRIAL_WHITELIST_CREDITS=1000
```

---

## 🔍 验证是否生效

新用户注册后，查看 Render 日志：

- ✅ VIP 用户: `🌟 VIP白名单用户注册: xxx, 初始算力: 10000`
- ✅ 试用用户: `🎁 试用白名单用户注册: xxx, 初始算力: 1000`
- ✅ 普通用户: `✅ 普通用户注册: xxx, 初始算力: 100`

---

## 📚 详细文档

- **配置指南**: `WHITELIST_CONFIG_GUIDE.md`
- **Render 设置**: `RENDER_WHITELIST_SETUP.md`
- **管理脚本**: `add_trial_user.py`
