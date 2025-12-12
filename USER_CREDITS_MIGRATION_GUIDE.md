# 用户和积分系统数据库迁移指南

## 📋 概述

本次迁移将用户数据和积分系统从 Redis 迁移到 Supabase PostgreSQL。

### 迁移范围
- ✅ **用户基本信息** - 从 Redis 迁移到 PostgreSQL
- ✅ **积分管理** - 从 Redis 迁移到 PostgreSQL  
- ✅ **注册逻辑** - 写入数据库，credits=100, signup_bonus_granted=true
- ⚠️ **登录逻辑** - 需要更新，不再自动送积分
- ⚠️ **验证码** - 保持使用 Redis（临时数据）

---

## 🗃️ 数据库表结构

### Users 表

已创建完整的 users 表 SQL：`backend/database_schema/users_table.sql`

**关键字段：**
- `user_id` - 用户ID（主键）
- `email` - 邮箱（唯一）
- `current_credits` - 当前积分
- `total_credits_used` - 累计使用积分
- `signup_bonus_granted` - 注册奖励是否已发放
- `current_plan_id` - 当前套餐ID
- `plan_renew_at` - 套餐续费时间

---

## 🚀 已完成的工作

### 1. 数据库表和 CRUD 操作

#### ✅ 创建 users 表 SQL
**文件**: `backend/database_schema/users_table.sql`
- 完整的用户表结构
- 包含 `signup_bonus_granted` 字段
- 自动更新 `updated_at` 的触发器

#### ✅ 更新 crud_users.py
**文件**: `backend/app/db/crud_users.py`

新增/更新的函数：
- `create_user()` - 支持 `signup_bonus_granted` 参数，默认 credits=100
- `update_user_credits()` - 更新用户积分（增加/扣除）
- `get_user_by_id()` - 根据用户ID获取用户

### 2. 计费服务（数据库版本）

#### ✅ 创建 billing_service_db.py
**文件**: `backend/app/services/billing/billing_service_db.py`

使用数据库的新版本计费服务：
- `get_user()` - 从数据库获取用户
- `get_user_billing_info()` - 获取计费信息
- `consume_credits()` - 扣除积分（写回数据库）
- `add_credits()` - 增加积分（写回数据库）
- `change_plan()` - 切换套餐
- `check_and_renew_plan()` - 自动续费

### 3. 注册逻辑

#### ✅ 已更新注册接口
**文件**: `backend/app/api/v1/routes_auth.py`

`POST /auth/signup` 已经使用数据库：
- 调用 `crud_users.create_user()`
- 初始 `current_credits=100`
- 设置 `signup_bonus_granted=true`

---

## ⚠️ 待完成的工作

### 1. 更新登录逻辑

#### 问题
**文件**: `backend/app/services/auth/auth_service.py`

当前 `get_or_create_user()` 函数：
- 使用 Redis 存储用户
- 每次登录都可能送积分（白名单用户）
- 需要改为仅查询数据库

#### 需要修改
```python
# 旧代码（使用 Redis）
def get_or_create_user(self, email: str) -> User:
    user_key = f"user:email:{email}"
    user_data_str = self.redis_client.get(user_key)
    # ...自动送积分逻辑...
```

**改为：**
```python
# 新代码（使用数据库）
async def get_or_create_user_db(self, email: str) -> User:
    from app.db import crud_users
    
    # 从数据库获取用户
    user = await crud_users.get_user_by_email(email)
    
    if user:
        # 更新最后登录时间
        # 不再自动送积分！
        return user
    else:
        # 创建新用户（初始100积分）
        user = await crud_users.create_user(
            email=email,
            current_credits=100,
            signup_bonus_granted=True
        )
        return user
```

### 2. 更新所有使用 billing_service 的地方

#### 需要替换的导入
```python
# 旧导入
from app.services.billing import billing_service

# 新导入
from app.services.billing.billing_service_db import billing_service_db as billing_service
```

**需要更新的文件：**
- `backend/app/api/v1/routes_tasks.py` - 创建任务时扣积分
- `backend/app/api/v1/routes_billing.py` - 查询积分信息
- `backend/app/services/tasks/manager.py` - 失败退款

### 3. 更新 routes_auth.py 登录接口

#### `POST /auth/login` (验证码登录)

**当前代码：**
```python
# 使用 auth_service.get_or_create_user() (Redis)
user = auth_service.get_or_create_user(request.email)
```

**应改为：**
```python
# 使用数据库查询
from app.db import crud_users

user = await crud_users.get_user_by_email(request.email)
if not user:
    # 首次登录，创建用户
    user = await crud_users.create_user(
        email=request.email,
        current_credits=100,
        signup_bonus_granted=True
    )
else:
    # 更新最后登录时间
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET last_login = $1 WHERE user_id = $2",
            datetime.utcnow(),
            user.user_id
        )
```

---

## 📝 具体步骤

### Step 1: 在 Supabase 创建 users 表

```bash
# 1. 登录 Supabase Dashboard
# 2. 选择你的项目
# 3. 进入 SQL Editor
# 4. 运行 backend/database_schema/users_table.sql
```

**验证：**
```sql
SELECT * FROM users LIMIT 1;
SELECT column_name FROM information_schema.columns WHERE table_name = 'users';
```

### Step 2: 更新 billing_service 导入

**文件列表：**

1. **routes_tasks.py**
   ```python
   # 第 14 行
   from app.services.billing.billing_service_db import billing_service_db as billing_service
   ```

2. **routes_billing.py**（如果存在）
   ```python
   from app.services.billing.billing_service_db import billing_service_db as billing_service
   ```

3. **manager.py**（任务管理器）
   ```python
   # 在 refund_credits_for_failed_task 中
   from app.services.billing.billing_service_db import billing_service_db as billing_service
   ```

### Step 3: 更新登录逻辑

**文件**: `backend/app/api/v1/routes_auth.py`

更新 `POST /auth/login` (验证码登录):

```python
@router.post("/auth/login", response_model=LoginResponse)
async def login_with_code(request: LoginRequest):
    """
    验证码登录（使用 PostgreSQL）
    """
    try:
        from app.db import crud_users
        from app.db import get_pool
        
        auth_service = get_auth_service()
        
        # 验证验证码
        if not auth_service.verify_code(request.email, request.code):
            raise HTTPException(
                status_code=400,
                detail="验证码错误或已过期"
            )
        
        # 从数据库获取或创建用户
        user = await crud_users.get_user_by_email(request.email)
        
        if not user:
            # 首次登录，创建用户（100积分）
            user = await crud_users.create_user(
                email=request.email,
                current_credits=100,
                signup_bonus_granted=True
            )
            print(f"✓ 新用户注册: {request.email}, 初始积分: 100")
        else:
            # 已有用户，更新最后登录时间
            pool = get_pool()
            if pool:
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE users
                        SET last_login = $1
                        WHERE user_id = $2
                        """,
                        datetime.utcnow(),
                        user.user_id
                    )
            print(f"✓ 用户登录: {request.email}")
        
        # 创建访问令牌
        access_token = auth_service.create_access_token(user)
        
        # 返回用户信息和令牌
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserInfo(
                user_id=user.user_id,
                email=user.email,
                username=user.username,
                avatar=user.avatar,
                created_at=user.created_at.isoformat(),
                last_login=user.last_login.isoformat() if user.last_login else None
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"登录失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"登录失败: {str(e)}"
        )
```

### Step 4: 重启服务

```bash
# 在 Render Dashboard 中
# 1. 进入你的 Web Service
# 2. 点击 "Manual Deploy" -> "Deploy latest commit"
```

---

## 🧪 测试清单

### 1. 用户注册测试

```bash
# POST /api/v1/auth/signup
{
  "email": "test@example.com",
  "password": "password123"
}

# 预期：
# - 用户创建成功
# - current_credits = 100
# - signup_bonus_granted = true
# - 返回 JWT token
```

**验证数据库：**
```sql
SELECT user_id, email, current_credits, signup_bonus_granted 
FROM users 
WHERE email = 'test@example.com';
```

### 2. 用户登录测试（验证码）

```bash
# 1. POST /api/v1/auth/send-code
{
  "email": "test@example.com"
}

# 2. POST /api/v1/auth/login
{
  "email": "test@example.com",
  "code": "123456"
}

# 预期：
# - 登录成功
# - 返回 JWT token
# - 不会额外送积分
```

### 3. 用户登录测试（密码）

```bash
# POST /api/v1/auth/login-password-db
{
  "email": "test@example.com",
  "password": "password123"
}

# 预期：
# - 登录成功
# - 返回 JWT token
# - 更新 last_login
```

### 4. 积分扣除测试

```bash
# POST /api/v1/tasks
Authorization: Bearer <token>
{
  "mode": "HEAD_SWAP",
  "source_image": "file_xxx",
  "config": {}
}

# 预期：
# - 任务创建成功
# - 积分扣除（例如 -10）
# - current_credits 减少
# - total_credits_used 增加
```

**验证数据库：**
```sql
SELECT 
    user_id, 
    email, 
    current_credits, 
    total_credits_used 
FROM users 
WHERE email = 'test@example.com';

-- 应该看到：
-- current_credits = 90 (100 - 10)
-- total_credits_used = 10
```

### 5. 积分增加测试

```bash
# POST /api/v1/billing/add-credits (如果有这个接口)
Authorization: Bearer <token>
{
  "amount": 50
}

# 预期：
# - current_credits 增加 50
# - total_credits_used 不变
```

---

## ⚠️ 注意事项

### 1. 向后兼容性

- Redis 中的旧用户数据不会自动迁移
- 首次使用新系统登录时会在数据库中创建用户
- 建议保留 Redis 一段时间（用于验证码）

### 2. 白名单用户

**原来的逻辑：**
- 每次登录都检查白名单
- 白名单用户自动补充到 100000 积分

**新的逻辑（需要实现）：**
- 注册时检查白名单，给予特殊积分
- 登录时不再自动补充

**建议实现：**
```python
# 在 create_user 时
is_whitelist = settings.is_whitelisted(email)
initial_credits = settings.WHITELIST_CREDITS if is_whitelist else 100

user = await crud_users.create_user(
    email=email,
    current_credits=initial_credits,
    signup_bonus_granted=True
)
```

### 3. 数据一致性

- 积分扣除使用数据库事务
- 任务创建失败时会自动退款
- 使用 `update_user_credits()` 统一管理积分变更

---

## 📊 迁移架构对比

### 旧架构（Redis）
```
登录/注册
    ↓
auth_service.get_or_create_user()
    ↓
Redis (user:email:xxx)
    ↓
自动送积分（白名单）
```

### 新架构（PostgreSQL）
```
登录/注册
    ↓
crud_users.get_user_by_email()
    ↓
PostgreSQL (users 表)
    ↓
仅注册时送 100 积分
```

---

## 🔧 故障排查

### 问题：users 表不存在

```
[DB] ❌ 创建数据库连接池失败: relation "users" does not exist
```

**解决方案：**
1. 确认已在 Supabase 运行 `users_table.sql`
2. 刷新 Supabase Table Editor 查看表
3. 检查表名是否正确（小写 `users`）

### 问题：signup_bonus_granted 字段不存在

```
⚠️  更新 signup_bonus_granted 失败（可能字段不存在）
```

**解决方案：**
1. 检查 `users_table.sql` 是否包含该字段
2. 重新运行建表 SQL
3. 或手动添加字段：
   ```sql
   ALTER TABLE users ADD COLUMN signup_bonus_granted BOOLEAN NOT NULL DEFAULT FALSE;
   ```

### 问题：积分扣除失败

```
[Billing] ✗ 积分扣除失败: user=usr_xxx, amount=10
```

**解决方案：**
1. 检查用户是否存在
2. 检查 current_credits 是否足够
3. 查看数据库日志

---

## 📚 相关文档

- [数据库迁移指南](DATABASE_MIGRATION_GUIDE.md)
- [Supabase 文档](https://supabase.com/docs)
- [asyncpg 文档](https://magicstack.github.io/asyncpg/)
- [套餐配置](app/config/plans.py)

---

**最后更新**: 2025-12-08  
**版本**: 1.0.0


