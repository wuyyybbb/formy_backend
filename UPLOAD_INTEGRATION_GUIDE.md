# 图片上传功能集成指南

## ✅ 已完成的工作

### 前端（Frontend）

#### 1. API 客户端（src/api/client.ts）
- ✅ 封装 HTTP 请求
- ✅ 支持 JSON 和 FormData 请求
- ✅ 统一错误处理
- ✅ 响应解析

#### 2. 上传 API（src/api/upload.ts）
- ✅ `uploadImage(file, purpose)` 函数
- ✅ 文件类型验证
- ✅ 文件大小验证（10MB）
- ✅ 获取图片 URL 辅助函数

#### 3. 上传组件（src/components/editor/UploadArea.tsx）
- ✅ 调用真实后端 API
- ✅ 上传进度显示
- ✅ 错误提示
- ✅ 上传成功后显示图片

#### 4. 环境配置
- ✅ API 基础 URL 配置
- ✅ 开发环境代理配置

---

### 后端（Backend）

#### 1. 数据模型（app/schemas/image.py）
- ✅ `UploadImageResponse` - 上传响应模型
- ✅ `ImageInfo` - 图片信息模型

#### 2. 存储服务（app/services/storage/）
- ✅ `StorageInterface` - 存储接口
- ✅ `LocalStorage` - 本地文件系统实现
- ✅ 异步文件读写
- ✅ 文件 URL 生成

#### 3. 上传路由（app/api/v1/routes_upload.py）
- ✅ `POST /api/v1/upload` - 上传图片接口
- ✅ 文件类型验证
- ✅ 文件大小验证
- ✅ 文件保存和 URL 返回

#### 4. 主应用（app/main.py）
- ✅ FastAPI 应用初始化
- ✅ CORS 配置
- ✅ 静态文件服务（/uploads, /results）
- ✅ 路由注册

---

## 🚀 快速启动

### 1. 启动后端

```bash
# 进入后端目录
cd backend

# 安装依赖（如果还没安装）
pip install -r requirements.txt

# 启动 FastAPI 服务
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**后端将运行在**: http://localhost:8000

**API 文档**: http://localhost:8000/docs

---

### 2. 配置前端环境变量

在 `frontend/` 目录下创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

### 3. 启动前端

```bash
# 进入前端目录
cd frontend

# 安装依赖（如果还没安装）
npm install

# 启动开发服务器
npm run dev
```

**前端将运行在**: http://localhost:5173

---

## 🧪 测试上传功能

### 测试步骤

1. **访问编辑器页面**
   ```
   http://localhost:5173/editor
   ```

2. **点击上传区域**
   - 选择一张图片（JPG、PNG 或 WEBP）
   - 观察上传进度

3. **验证上传成功**
   - 图片应该显示在预览区
   - 浏览器控制台会输出上传成功信息
   - 后端控制台会显示文件保存路径

4. **检查后端文件**
   ```bash
   # 查看上传的文件
   ls backend/uploads/source/
   ls backend/uploads/reference/
   ```

5. **直接访问图片**
   ```
   http://localhost:8000/uploads/source/img_20231117_abc123.jpg
   ```

---

## 📊 完整的数据流

```
1. 用户选择图片
   ↓
2. 前端：UploadArea 组件触发 handleFileChange
   ↓
3. 前端：调用 uploadImage(file, purpose)
   ↓
4. 前端：构建 FormData，发送 POST 请求
   ↓
5. 后端：routes_upload.upload_image 接收请求
   ↓
6. 后端：验证文件类型和大小
   ↓
7. 后端：生成文件 ID 和文件名
   ↓
8. 后端：LocalStorage.save_file 保存到磁盘
   ↓
9. 后端：返回 UploadImageResponse（包含 URL）
   ↓
10. 前端：接收响应，更新 state
   ↓
11. 前端：使用返回的 URL 显示图片
```

---

## 🔍 调试技巧

### 前端调试

1. **查看网络请求**
   - 打开浏览器开发者工具 → Network 标签
   - 找到 `/api/v1/upload` 请求
   - 查看请求头、请求体、响应

2. **查看控制台日志**
   ```javascript
   console.log('图片上传成功:', result)
   console.error('图片上传失败:', error)
   ```

3. **检查 CORS 错误**
   - 如果出现跨域错误，检查后端 CORS 配置
   - 确保前端 URL 在 `settings.CORS_ORIGINS` 中

### 后端调试

1. **查看日志输出**
   ```python
   print(f"文件保存失败: {e}")
   ```

2. **访问 API 文档**
   ```
   http://localhost:8000/docs
   ```
   - 可以直接在文档中测试上传接口

3. **检查文件权限**
   ```bash
   # 确保上传目录有写权限
   chmod -R 755 backend/uploads
   ```

---

## 📁 文件结构

### 前端文件

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts          ✅ HTTP 客户端
│   │   └── upload.ts          ✅ 上传 API
│   └── components/
│       └── editor/
│           ├── UploadArea.tsx ✅ 上传组件（已更新）
│           └── ControlPanel.tsx ✅ 控制面板（已更新）
└── .env                       ⚠️ 需要手动创建
```

### 后端文件

```
backend/
├── app/
│   ├── main.py                ✅ FastAPI 入口
│   ├── api/
│   │   └── v1/
│   │       └── routes_upload.py ✅ 上传路由
│   ├── schemas/
│   │   └── image.py           ✅ 图片数据模型
│   └── services/
│       └── storage/
│           ├── interface.py   ✅ 存储接口
│           ├── local_storage.py ✅ 本地存储实现
│           └── __init__.py    ✅
└── uploads/                   📁 上传目录（自动创建）
    ├── source/                📁 原图
    └── reference/             📁 参考图
```

---

## ⚙️ 配置说明

### 前端配置（.env）

```env
# API 基础 URL
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 后端配置（app/core/config.py）

```python
# 上传目录
UPLOAD_DIR: str = "./uploads"

# 结果目录
RESULT_DIR: str = "./results"

# 最大上传大小（字节）
MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

# 允许的文件扩展名
ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".webp"}

# CORS 配置
CORS_ORIGINS: list = [
    "http://localhost:3000",
    "http://localhost:5173",
]
```

---

## 🐛 常见问题

### 1. CORS 错误

**现象**: 浏览器控制台显示跨域错误

**解决**:
```python
# backend/app/core/config.py
CORS_ORIGINS: list = [
    "http://localhost:5173",  # 添加前端 URL
]
```

### 2. 404 错误（上传接口不存在）

**现象**: 请求返回 404

**解决**:
- 确认后端服务已启动
- 检查 API 前缀配置
- 访问 http://localhost:8000/docs 查看可用接口

### 3. 文件保存失败

**现象**: 后端返回 500 错误

**解决**:
```bash
# 检查上传目录权限
chmod -R 755 backend/uploads

# 或删除重新创建
rm -rf backend/uploads
mkdir -p backend/uploads/source backend/uploads/reference
```

### 4. 图片显示不出来

**现象**: 上传成功但图片无法显示

**解决**:
- 检查返回的 URL 格式
- 确认静态文件服务已挂载
- 访问 http://localhost:8000/uploads/source/xxx.jpg 测试

### 5. 前端无法连接后端

**现象**: Network error 或 Connection refused

**解决**:
```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查端口是否被占用
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

---

## ✅ 验证清单

完成上传功能集成后，确认以下内容：

- [ ] 后端服务正常启动（http://localhost:8000）
- [ ] 前端服务正常启动（http://localhost:5173）
- [ ] 能访问 API 文档（http://localhost:8000/docs）
- [ ] 在编辑器页面能看到上传区域
- [ ] 选择图片后显示上传进度
- [ ] 上传成功后图片正常显示
- [ ] 浏览器控制台无错误
- [ ] 后端 uploads/ 目录中有保存的文件
- [ ] 能直接访问上传的图片 URL

---

## 🎯 下一步

上传功能完成后，可以继续：

1. **对接任务创建 API**
   - 创建 `/api/v1/tasks` 接口
   - 前端调用创建任务
   
2. **实现任务状态轮询**
   - 创建 `/api/v1/tasks/{task_id}` 接口
   - 前端定时查询任务状态

3. **集成 Worker**
   - Worker 消费任务队列
   - 调用 Pipeline 处理图片

4. **显示处理结果**
   - 获取结果图片 URL
   - 显示在预览区域

---

**文档更新时间**: 2025-11-17  
**状态**: 图片上传功能已完成 ✅

