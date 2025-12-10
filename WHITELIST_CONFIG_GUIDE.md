# 白名单配置说明

## 两级白名单系统

### 1. VIP 白名单（10000 积分）
**用途**: 管理员和核心用户，拥有最高积分额度
**配置方式**: 修改 Render 环境变量 `VIP_WHITELIST_EMAILS`

**当前 VIP 用户:**
- wyb3206@163.com
- wuyebei3206@gmail.com

### 2. 试用白名单（1000 积分）
**用途**: 给潜在客户、测试用户提供试用额度
**配置方式**: 修改 Render 环境变量 `TRIAL_WHITELIST_EMAILS`

**当前试用用户:**
- 553588070@qq.com

---

## 如何添加新的试用白名单用户

### 方法 1: 通过 Render Dashboard（推荐）

1. 打开 Render Dashboard
2. 进入 `formy-backend` 服务
3. 点击 `Environment` 标签
4. 找到环境变量 `TRIAL_WHITELIST_EMAILS`
5. 在现有邮箱后添加新邮箱（用逗号分隔）

**示例:**
```
553588070@qq.com,newuser@example.com,another@test.com
```

6. 点击 `Save Changes`
7. Render 会自动重启服务应用新配置

### 方法 2: 修改本地 .env 文件（本地开发）

编辑 `backend/.env` 文件：

```env
# 试用白名单用户（逗号分隔）
TRIAL_WHITELIST_EMAILS=553588070@qq.com,newuser@example.com
```

---

## 白名单特性

### VIP 白名单用户
- ✅ 注册时获得 **10000 积分**
- ✅ 每次登录自动补充到 10000 积分（如果低于此值）
- ✅ 适合长期使用

### 试用白名单用户
- ✅ 注册时获得 **1000 积分**
- ✅ 每次登录自动补充到 1000 积分（如果低于此值）
- ✅ 适合短期试用

### 普通用户
- 注册时获得 **100 积分**
- 需要充值才能获得更多积分

---

## 注意事项

1. **邮箱格式**: 必须是有效的邮箱地址（小写）
2. **分隔符**: 多个邮箱用英文逗号 `,` 分隔
3. **空格**: 可以有空格，系统会自动去除
4. **大小写**: 系统会自动转换为小写进行匹配

**正确示例:**
```
user1@gmail.com,user2@qq.com, user3@163.com
```

**错误示例:**
```
user1@gmail.com;user2@qq.com    # 不能用分号
user1@gmail.com user2@qq.com    # 不能用空格分隔
```

---

## 常见问题

### Q: 如何移除某个试用用户？
A: 从 `TRIAL_WHITELIST_EMAILS` 中删除对应邮箱即可

### Q: 可以把试用用户升级为 VIP 吗？
A: 可以，从 `TRIAL_WHITELIST_EMAILS` 中删除，添加到 `VIP_WHITELIST_EMAILS`

### Q: 白名单用户的积分会被扣除吗？
A: 会被扣除，但每次登录会自动补充到对应额度

### Q: 修改白名单配置后多久生效？
A: Render 重启后立即生效（约 1-2 分钟）

---

## 环境变量完整列表

```env
# VIP 白名单（10000 积分）
VIP_WHITELIST_EMAILS=wyb3206@163.com,wuyebei3206@gmail.com

# 试用白名单（1000 积分）
TRIAL_WHITELIST_EMAILS=553588070@qq.com

# 兼容旧配置（将被废弃）
WHITELIST_EMAILS=wyb3206@163.com,wuyebei3206@gmail.com
WHITELIST_CREDITS=10000
```

---

## 快速添加试用用户

**添加单个用户:**
```
TRIAL_WHITELIST_EMAILS=553588070@qq.com,新邮箱@example.com
```

**添加多个用户:**
```
TRIAL_WHITELIST_EMAILS=553588070@qq.com,user1@test.com,user2@test.com,user3@test.com
```
