# Render 环境变量配置 - 白名单系统

## 🎯 需要在 Render Dashboard 添加的环境变量

### 1. VIP 白名单（10000 积分）

**变量名**: `VIP_WHITELIST_EMAILS`  
**值**: `wyb3206@163.com,wuyebei3206@gmail.com`

### 2. 试用白名单（1000 积分）

**变量名**: `TRIAL_WHITELIST_EMAILS`  
**值**: `553588070@qq.com`

### 3. VIP 积分额度

**变量名**: `VIP_WHITELIST_CREDITS`  
**值**: `10000`

### 4. 试用积分额度

**变量名**: `TRIAL_WHITELIST_CREDITS`  
**值**: `1000`

---

## 📝 操作步骤

### 在 Render Dashboard 中配置

1. 登录 Render Dashboard: https://dashboard.render.com
2. 选择 `formy-backend` 服务
3. 点击左侧菜单 `Environment`
4. 点击 `Add Environment Variable` 按钮
5. 添加以下环境变量：

| Key | Value |
|-----|-------|
| `VIP_WHITELIST_EMAILS` | `wyb3206@163.com,wuyebei3206@gmail.com` |
| `VIP_WHITELIST_CREDITS` | `10000` |
| `TRIAL_WHITELIST_EMAILS` | `553588070@qq.com` |
| `TRIAL_WHITELIST_CREDITS` | `1000` |

6. 点击 `Save Changes`
7. Render 会自动重启服务（约 1-2 分钟）

---

## 🔄 如何添加新的试用用户

### 方法 1: 使用脚本生成配置（推荐）

```bash
# 查看当前配置
python add_trial_user.py

# 添加单个用户
python add_trial_user.py newuser@example.com

# 添加多个用户
python add_trial_user.py user1@test.com user2@test.com user3@test.com
```

脚本会自动生成新的环境变量值，你只需要复制粘贴到 Render Dashboard。

### 方法 2: 手动编辑

1. 打开 Render Dashboard
2. 找到环境变量 `TRIAL_WHITELIST_EMAILS`
3. 在现有值后添加新邮箱（用逗号分隔）

**示例:**
```
当前值: 553588070@qq.com
新值: 553588070@qq.com,newuser@example.com,another@test.com
```

4. 保存并等待服务重启

---

## ✅ 验证配置是否生效

### 1. 查看 Render 日志

服务重启后，查看日志中是否有类似信息：

```
🎁 试用白名单用户注册: newuser@example.com, 初始算力: 1000
```

### 2. 测试登录

使用新添加的试用邮箱登录，检查是否获得 1000 积分。

---

## 🎨 白名单等级说明

| 等级 | 初始积分 | 登录补充 | 适用场景 |
|------|---------|---------|---------|
| 🌟 VIP | 10000 | 自动补充到 10000 | 管理员、核心用户 |
| 🎁 试用 | 1000 | 自动补充到 1000 | 潜在客户、测试用户 |
| 👥 普通 | 100 | 无 | 普通注册用户 |

---

## 📌 注意事项

1. **邮箱必须小写**: 系统会自动转换，但建议统一使用小写
2. **逗号分隔**: 多个邮箱用英文逗号 `,` 分隔
3. **无需重启代码**: 只需在 Render 中更新环境变量即可
4. **立即生效**: 更新后新用户注册或登录时立即获得对应积分

---

## 🔧 常见问题

### Q: 如何移除某个试用用户？
**A**: 从 `TRIAL_WHITELIST_EMAILS` 中删除对应邮箱，保存即可

### Q: 可以临时禁用某个白名单用户吗？
**A**: 可以，从对应的白名单环境变量中移除该邮箱

### Q: 白名单用户的积分用完了怎么办？
**A**: 再次登录会自动补充到对应额度

### Q: 可以修改积分额度吗？
**A**: 可以，修改 `VIP_WHITELIST_CREDITS` 或 `TRIAL_WHITELIST_CREDITS` 的值

---

## 📞 技术支持

如有问题，请联系：
- 📧 Email: wuyebei3206@gmail.com
- 📝 查看配置指南: `WHITELIST_CONFIG_GUIDE.md`
