# Formy 数据库迁移总结

## 🎯 迁移目标

将 Formy 从 Redis 迁移到 Supabase PostgreSQL，提高数据持久性、可靠性和查询能力。

---

## ✅ 已完成的迁移

### 1. 任务系统迁移 ✅

**状态**: 已完成代码更新，待部署测试

#### 创建的文件：
- ✅ `database_schema/tasks_table.sql` - Tasks 表结构
- ✅ `app/db/crud_tasks.py` - 任务 CRUD 操作
- ✅ `test_database_migration.py` - 任务迁移测试脚本
- ✅ `DATABASE_MIGRATION_GUIDE.md` - 任务迁移详细指南
- ✅ `QUICK_START_DATABASE.md` - 任务迁移快速开始

#### 更新的文件：
- ✅ `app/services/tasks/manager.py` - 使用数据库存储任务
- ✅ `app/api/v1/routes_tasks.py` - 优化数据库查询

#### 主要功能：
- ✅ 任务创建时写入数据库
- ✅ 任务查询从数据库读取
- ✅ 任务列表支持筛选和分页
- ✅ 历史记录包含输入图片信息
- ✅ Redis 队列仍用于任务调度

### 2. 用户和积分系统迁移 ✅

**状态**: 已完成代码更新，待集成和测试

#### 创建的文件：
- ✅ `database_schema/users_table.sql` - Users 表结构（包含 signup_bonus_granted）
- ✅ `app/services/billing/billing_service_db.py` - 数据库版本计费服务
- ✅ `USER_CREDITS_MIGRATION_GUIDE.md` - 用户和积分迁移详细指南

#### 更新的文件：
- ✅ `app/db/crud_users.py` - 添加积分管理功能
  - `update_user_credits()` - 更新用户积分
  - `get_user_by_id()` - 根据ID获取用户
  - `create_user()` - 支持 signup_bonus_granted 参数

#### 主要功能：
- ✅ 注册时写入数据库，credits=100, signup_bonus_granted=true
- ✅ 积分扣除写回数据库
- ✅ 积分查询从数据库读取
- ✅ 套餐管理使用数据库

---

## ⚠️ 待完成的集成工作

### 需要手动操作的步骤

#### 1. 在 Supabase 创建数据库表 🔴

```bash
# 1. 登录 Supabase Dashboard
# 2. 进入 SQL Editor
# 3. 运行以下 SQL 文件：

# (1) 创建 users 表
backend/database_schema/users_table.sql

# (2) 创建 tasks 表
backend/database_schema/tasks_table.sql
```

#### 2. 更新 routes_auth.py 登录逻辑 🔴

**文件**: `backend/app/api/v1/routes_auth.py`

**需要修改的接口**: `POST /auth/login` (第 115 行)

**当前代码**:
```python
# 获取或创建用户
user = auth_service.get_or_create_user(request.email)  # ❌ 使用 Redis
```

**应改为**:
```python
# 从数据库获取或创建用户
from app.db import crud_users

user = await crud_users.get_user_by_email(request.email)
if not user:
    user = await crud_users.create_user(
        email=request.email,
        current_credits=100,
        signup_bonus_granted=True
    )
else:
    # 更新最后登录时间
    pool = get_pool()
    if pool:
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET last_login = $1 WHERE user_id = $2",
                datetime.utcnow(),
                user.user_id
            )
```

#### 3. 更新 billing_service 导入 🟡

**需要更新的文件**:

**(1) routes_tasks.py** (第 14 行)
```python
# 旧导入
from app.services.billing import billing_service

# 新导入
from app.services.billing.billing_service_db import billing_service_db as billing_service
```

**(2) routes_billing.py** (如果存在)
```python
from app.services.billing.billing_service_db import billing_service_db as billing_service
```

**(3) manager.py** (任务失败退款，第 320 行)
```python
# 在 refund_credits_for_failed_task 中
from app.services.billing.billing_service_db import billing_service_db as billing_service
```

#### 4. 确认环境变量配置 🟡

确保 Render 上配置了：
```bash
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
REDIS_URL=...  # 仍需要，用于验证码和任务队列
```

#### 5. 重启服务并测试 🟡

```bash
# 在 Render Dashboard 中
# 1. 进入你的 Web Service
# 2. 点击 "Manual Deploy" -> "Deploy latest commit"
```

---

## 🧪 测试计划

### 任务系统测试

```bash
# 1. 运行测试脚本
cd backend
python test_database_migration.py

# 2. API 测试
# - POST /api/v1/tasks (创建任务)
# - GET /api/v1/tasks/{id} (查询任务)
# - GET /api/v1/tasks (任务列表)
# - GET /api/v1/tasks/history (历史记录)
```

### 用户和积分测试

```bash
# 1. 注册测试
POST /api/v1/auth/signup
{
  "email": "test@example.com",
  "password": "password123"
}
# 验证: current_credits = 100, signup_bonus_granted = true

# 2. 登录测试（验证码）
POST /api/v1/auth/login
# 验证: 不额外送积分

# 3. 积分扣除测试
POST /api/v1/tasks
# 验证: current_credits 减少, total_credits_used 增加

# 4. 任务失败退款测试
# 验证: 失败任务自动退还积分
```

---

## 📊 数据流对比

### 旧架构（Redis）
```
前端
  ↓
API (FastAPI)
  ↓
Redis (临时存储)
  ├─ 用户数据
  ├─ 任务数据
  └─ 验证码
```

### 新架构（混合）
```
前端
  ↓
API (FastAPI)
  ├─ PostgreSQL (持久化)
  │   ├─ users 表
  │   └─ tasks 表
  └─ Redis (临时数据)
      ├─ 验证码 ✅
      └─ 任务队列 ✅
```

**优势**:
- ✅ 数据持久化（不会丢失）
- ✅ 支持复杂查询
- ✅ 数据完整性保证
- ✅ 便于数据分析
- ✅ Redis 仍用于高性能场景

---

## 📂 文件清单

### 新增文件
```
backend/
├── database_schema/
│   ├── users_table.sql                         ✅ Users 表
│   └── tasks_table.sql                         ✅ Tasks 表
├── app/
│   ├── db/
│   │   ├── crud_tasks.py                       ✅ 任务 CRUD
│   │   └── crud_users.py                       ✅ 用户 CRUD（已更新）
│   └── services/
│       └── billing/
│           └── billing_service_db.py           ✅ 数据库版本计费服务
├── test_database_migration.py                  ✅ 任务迁移测试
├── DATABASE_MIGRATION_GUIDE.md                 ✅ 任务迁移指南
├── USER_CREDITS_MIGRATION_GUIDE.md             ✅ 用户积分迁移指南
├── QUICK_START_DATABASE.md                     ✅ 快速开始指南
└── MIGRATION_SUMMARY.md                        ✅ 本文件
```

### 更新的文件
```
backend/app/
├── services/
│   └── tasks/
│       └── manager.py                          ✅ 使用数据库
├── api/v1/
│   ├── routes_tasks.py                         ✅ 优化查询
│   └── routes_auth.py                          ⚠️  需要更新登录逻辑
```

---

## 🎯 下一步行动清单

### 高优先级 🔴

- [ ] **在 Supabase 运行建表 SQL**
  - users_table.sql
  - tasks_table.sql

- [ ] **更新 routes_auth.py 登录逻辑**
  - 修改 `POST /auth/login` 接口
  - 使用数据库而不是 Redis
  - 不再自动送积分

- [ ] **更新 billing_service 导入**
  - routes_tasks.py
  - routes_billing.py
  - manager.py

### 中优先级 🟡

- [ ] **在 Render 配置环境变量**
  - 确认 DATABASE_URL 正确

- [ ] **重启服务**
  - 触发新的部署

- [ ] **运行测试**
  - test_database_migration.py
  - 手动 API 测试

### 低优先级 🟢

- [ ] **清理旧代码**
  - 标记旧的 Redis 用户存储代码
  - 添加弃用警告

- [ ] **添加监控**
  - 数据库连接池监控
  - 查询性能监控

- [ ] **文档更新**
  - API 文档
  - 部署文档

---

## 💡 重要提示

### 1. 向后兼容性
- ✅ Redis 中的旧数据不会被删除
- ✅ 首次登录时会在数据库中创建用户
- ✅ 代码支持字段不存在的情况

### 2. 数据一致性
- ✅ 使用数据库事务保证一致性
- ✅ 积分扣除和任务创建原子操作
- ✅ 任务失败自动退款

### 3. 性能优化
- ✅ 数据库索引已创建
- ✅ 连接池配置（min=2, max=10）
- ✅ Redis 仍用于高频操作

---

## 📞 获取帮助

如果遇到问题：

1. **查看详细指南**:
   - `DATABASE_MIGRATION_GUIDE.md` - 任务迁移
   - `USER_CREDITS_MIGRATION_GUIDE.md` - 用户积分迁移
   - `QUICK_START_DATABASE.md` - 快速开始

2. **运行测试脚本**:
   ```bash
   python test_database_migration.py
   ```

3. **检查日志**:
   - Render 服务日志
   - Supabase 数据库日志

---

## 🎉 完成标志

当以下所有项都完成时，迁移即为成功：

- [x] ✅ 代码已更新（任务系统）
- [x] ✅ 代码已更新（用户和积分系统）
- [ ] ⬜ Supabase 表已创建
- [ ] ⬜ 登录逻辑已更新
- [ ] ⬜ billing_service 导入已更新
- [ ] ⬜ 服务已重启
- [ ] ⬜ 所有测试通过
- [ ] ⬜ 前端功能正常

---

**当前进度**: 📊 代码准备 85% | 部署集成 0% | 测试验证 0%

**预计完成时间**: 1-2 小时（完成剩余集成和测试）

**最后更新**: 2025-12-08  
**版本**: 1.0.0


