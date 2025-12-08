# 🚀 数据库迁移快速开始指南

## 1️⃣ 在 Supabase 创建 tasks 表

### 步骤：

1. **登录 Supabase Dashboard**
   - 访问: https://supabase.com/dashboard
   - 选择你的项目

2. **打开 SQL Editor**
   - 左侧菜单 → SQL Editor
   - 点击 "New Query"

3. **复制并运行建表 SQL**
   - 打开文件: `backend/database_schema/tasks_table.sql`
   - 复制全部内容
   - 粘贴到 SQL Editor
   - 点击 "Run" 或按 `Ctrl+Enter`

4. **验证表创建成功**
   ```sql
   -- 运行此查询验证
   SELECT * FROM tasks LIMIT 1;
   ```
   如果没有报错，说明表创建成功！

---

## 2️⃣ 配置环境变量

### Render 配置（生产环境）

1. **进入 Render Dashboard**
   - 选择你的 Web Service (formy_backend)

2. **添加/更新环境变量**
   ```
   DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
   
   > 💡 从 Supabase Dashboard → Settings → Database → Connection String (Pooler) 获取

3. **保存并重启服务**
   - 点击 "Save Changes"
   - Render 会自动重新部署

### 本地开发配置

创建/更新 `.env` 文件：

```bash
# backend/.env
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
REDIS_URL=your_redis_url
JWT_SECRET_KEY=your_jwt_secret
```

---

## 3️⃣ 测试数据库连接

### 在本地测试：

```bash
# 进入 backend 目录
cd backend

# 运行测试脚本
python test_database_migration.py
```

### 预期输出：

```
============================================================
🧪 开始数据库迁移测试
============================================================

============================================================
1. 测试数据库连接
============================================================
[DB] 🔗 使用 DATABASE_URL 连接数据库...
[DB] ✅ PostgreSQL 连接池创建成功
✅ 数据库连接成功
✅ 数据库查询测试通过

============================================================
2. 测试 tasks 表是否存在
============================================================
✅ tasks 表存在

... (更多测试)

============================================================
📊 测试总结
============================================================
✅ 通过 - 数据库连接
✅ 通过 - tasks 表存在
✅ 通过 - 创建任务
✅ 通过 - 获取任务
✅ 通过 - 更新任务状态
✅ 通过 - 获取任务列表
✅ 通过 - 统计任务数量
✅ 通过 - 清理测试数据

============================================================
测试结果: 8/8 通过
============================================================

🎉 所有测试通过！数据库迁移成功！
```

---

## 4️⃣ 在线验证

### 测试 API 端点：

```bash
# 替换为你的实际 URL 和 token
export API_URL="https://your-backend.onrender.com"
export TOKEN="your_jwt_token"

# 1. 创建任务
curl -X POST "$API_URL/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "HEAD_SWAP",
    "source_image": "file_test123",
    "config": {}
  }'

# 2. 获取任务列表
curl -X GET "$API_URL/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN"

# 3. 获取任务历史
curl -X GET "$API_URL/api/v1/tasks/history" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 5️⃣ 前端验证

### 前端历史功能测试：

1. **登录前端应用**
   - 访问: https://your-frontend.vercel.app

2. **创建一个测试任务**
   - 上传图片
   - 点击"生成"按钮

3. **查看历史记录**
   - 点击"历史"或"History"
   - 应该能看到刚创建的任务
   - 点击历史记录应该能回填图片

---

## ✅ 验证清单

### 数据库层面
- [ ] Supabase 中 tasks 表创建成功
- [ ] 表结构包含所有必需字段
- [ ] 索引创建成功

### 后端层面
- [ ] DATABASE_URL 环境变量配置正确
- [ ] 数据库连接池初始化成功
- [ ] 测试脚本全部通过
- [ ] API 端点正常工作

### 前端层面
- [ ] 创建任务成功
- [ ] 查询任务状态正常
- [ ] 历史记录显示正常
- [ ] 点击历史能回填图片

---

## 🔧 常见问题

### Q1: 数据库连接失败
```
[DB] ❌ 创建数据库连接池失败: ...
```

**解决方案：**
1. 检查 `DATABASE_URL` 格式是否正确
2. 确认 Supabase 项目在线
3. 检查网络连接

### Q2: tasks 表不存在
```
❌ tasks 表不存在
```

**解决方案：**
1. 确认已在 Supabase 运行建表 SQL
2. 刷新 Supabase Table Editor 查看表
3. 检查 SQL 是否有错误

### Q3: 权限错误
```
permission denied for table tasks
```

**解决方案：**
1. 检查数据库用户权限
2. 在 Supabase SQL Editor 运行：
   ```sql
   GRANT ALL ON tasks TO postgres;
   ```

### Q4: 任务创建成功但历史不显示
```
任务创建成功，但 GET /api/v1/tasks 返回空列表
```

**解决方案：**
1. 检查任务的 user_id 是否正确
2. 确认前端传递的 token 正确
3. 查看后端日志是否有错误

---

## 📝 代码变更总结

### 新增文件
- `backend/database_schema/tasks_table.sql` - 建表 SQL
- `backend/app/db/crud_tasks.py` - 任务 CRUD 操作
- `backend/test_database_migration.py` - 测试脚本
- `backend/DATABASE_MIGRATION_GUIDE.md` - 详细迁移指南

### 更新文件
- `backend/app/services/tasks/manager.py` - 使用数据库
- `backend/app/api/v1/routes_tasks.py` - 优化查询逻辑

### 架构变更
- **数据存储**: Redis → PostgreSQL（持久化）
- **任务队列**: 保持 Redis（高性能）
- **查询性能**: 支持复杂筛选和分页

---

## 🎯 下一步

### 1. 数据分析
现在任务数据在 PostgreSQL 中，可以进行：
- 用户行为分析
- 任务成功率统计
- 性能指标监控

### 2. 功能扩展
- [ ] 任务搜索功能
- [ ] 导出任务记录
- [ ] 批量操作任务

### 3. 性能优化
- [ ] 添加数据库连接池监控
- [ ] 优化查询性能
- [ ] 添加缓存层

---

## 📞 获取帮助

如果遇到问题：
1. 查看 `DATABASE_MIGRATION_GUIDE.md` 详细文档
2. 检查后端日志
3. 运行测试脚本诊断问题

---

**祝贺你完成数据库迁移！** 🎉

