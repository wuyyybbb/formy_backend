# 前端 API SDK 封装完成总结

## ✅ 完成内容

已使用 **Axios** 完成前端 API SDK 封装，提供统一、类型安全的 API 调用接口。

## 📦 实现的文件

### 核心文件

1. **`frontend/src/api/client.ts`** - Axios 客户端配置
   - 基于 Axios 创建 HTTP 客户端
   - 请求/响应拦截器
   - 统一错误处理
   - 30 秒超时设置
   - 支持认证 Token（预留）

2. **`frontend/src/api/upload.ts`** - 图片上传 API
   - `uploadImage(file, purpose)` - 上传图片
   - `getImageUrl(url)` - 获取完整图片 URL
   - 文件类型验证
   - 文件大小验证（10MB）

3. **`frontend/src/api/tasks.ts`** - 任务管理 API
   - `createTask(request)` - 创建任务
   - `getTask(taskId)` - 获取任务详情
   - `listTasks(params)` - 获取任务列表
   - `cancelTask(taskId)` - 取消任务
   - 完整的类型定义

4. **`frontend/src/api/index.ts`** - 统一入口
   - 导出所有 API 函数
   - 导出所有类型定义
   - 提供命名空间（可选）

5. **`frontend/package.json`** - 依赖配置
   - 添加 `axios@^1.6.2` 依赖

### 文档

6. **`frontend/API_SDK_GUIDE.md`** - 详细使用指南
   - API 参考文档
   - 完整示例代码
   - React 组件集成示例
   - 最佳实践

7. **`API_SDK_SUMMARY.md`** - 本文档

## 🎯 核心 API

### 图片上传

```typescript
import { uploadImage, getImageUrl } from '@/api'

// 上传图片
const result = await uploadImage(file, 'source')
// 返回: { file_id, filename, size, url, uploaded_at }

// 获取完整 URL
const imageUrl = getImageUrl(result.url)
```

### 任务管理

```typescript
import { createTask, getTask, EditMode, TaskStatus } from '@/api'

// 创建任务
const task = await createTask({
  mode: EditMode.HEAD_SWAP,
  source_image: sourceFileId,
  config: { target_face_image: referenceFileId }
})

// 查询任务
const taskInfo = await getTask(task.task_id)

// 检查状态
if (taskInfo.status === TaskStatus.DONE) {
  console.log('完成！', taskInfo.result)
}
```

## 🔧 技术特性

### Axios 配置

- **baseURL**: 从环境变量读取，默认 `http://localhost:8000/api/v1`
- **timeout**: 30 秒
- **请求拦截器**: 可添加认证 Token
- **响应拦截器**: 
  - 自动解析 `response.data`
  - 统一错误处理
  - 友好的错误消息

### 类型安全

所有 API 都有完整的 TypeScript 类型定义：

```typescript
// 枚举
export enum TaskStatus { PENDING, PROCESSING, DONE, FAILED, CANCELLED }
export enum EditMode { HEAD_SWAP, BACKGROUND_CHANGE, POSE_CHANGE }

// 接口
export interface UploadImageResponse { file_id, filename, size, url, uploaded_at }
export interface CreateTaskRequest { mode, source_image, config }
export interface TaskInfo { task_id, status, progress, result, error, ... }
export interface TaskResult { output_image, thumbnail, metadata }
export interface TaskError { code, message, details }
```

### 错误处理

统一的错误处理机制：

```typescript
try {
  const result = await uploadImage(file, 'source')
} catch (error) {
  // error.message 包含友好的错误消息
  console.error(error.message)
}
```

**错误消息示例**：
- `"不支持的文件格式，请上传 JPG、PNG 或 WEBP 格式的图片"`
- `"图片大小不能超过 10MB"`
- `"网络连接失败，请检查网络"`
- `"请求失败 (404)"`

## 📊 使用方式

### 方式 1：从统一入口导入（推荐）

```typescript
import { 
  uploadImage, 
  createTask, 
  getTask,
  EditMode,
  TaskStatus 
} from '@/api'
```

### 方式 2：从各自模块导入

```typescript
import { uploadImage } from '@/api/upload'
import { createTask } from '@/api/tasks'
```

### 方式 3：使用命名空间

```typescript
import { ImageAPI, TaskAPI } from '@/api'

ImageAPI.uploadImage(...)
TaskAPI.createTask(...)
```

## 🔄 与旧代码的兼容性

已更新的文件：
- ✅ `frontend/src/api/client.ts` - 从 fetch 迁移到 axios
- ✅ `frontend/src/api/upload.ts` - 更新为使用 axios
- ✅ `frontend/src/api/tasks.ts` - 更新为使用 axios

**无需修改使用 API 的代码**，因为：
- 函数签名保持一致
- 返回值类型保持一致
- 错误处理方式保持一致

## 📝 下一步

### 安装依赖

```bash
cd frontend
npm install
```

这会自动安装 axios。

### 开发建议

1. **使用类型注解**
   ```typescript
   import type { TaskInfo } from '@/api'
   const task: TaskInfo = await getTask(taskId)
   ```

2. **环境变量配置**
   
   创建 `.env` 文件：
   ```bash
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   ```

3. **添加认证（如需要）**
   
   修改 `client.ts` 的请求拦截器：
   ```typescript
   const token = localStorage.getItem('auth_token')
   if (token) {
     config.headers.Authorization = `Bearer ${token}`
   }
   ```

## 🎉 优势

### 相比之前的 fetch 实现

1. **更简洁的 API**
   ```typescript
   // 之前（fetch）
   const response = await apiClient.postFormData('/upload', formData)
   
   // 现在（axios）
   return await apiClient.post('/upload', formData, {
     headers: { 'Content-Type': 'multipart/form-data' }
   })
   ```

2. **自动 JSON 解析**
   - Axios 自动解析 JSON 响应
   - 自动设置 Content-Type

3. **拦截器支持**
   - 请求拦截：添加认证、日志等
   - 响应拦截：统一错误处理

4. **更好的错误处理**
   - 友好的错误消息
   - 自动区分网络错误和服务器错误

5. **TypeScript 支持更好**
   - Axios 有完整的 TypeScript 类型定义
   - 更好的代码提示

## 📚 参考文档

- **使用指南**: `frontend/API_SDK_GUIDE.md`
- **后端 API 规范**: `docs/API_SPEC.md`
- **Axios 官方文档**: https://axios-http.com/

---

## 🚀 快速验证

创建一个测试文件验证 API：

```typescript
// frontend/src/test-api.ts
import { uploadImage, createTask, getTask, EditMode } from '@/api'

async function testAPI() {
  console.log('测试 API...')
  
  // 测试上传（需要真实文件）
  // const result = await uploadImage(file, 'source')
  // console.log('上传成功:', result)
  
  // 测试创建任务（需要真实 file_id）
  // const task = await createTask({
  //   mode: EditMode.HEAD_SWAP,
  //   source_image: 'img_xxx',
  //   config: {}
  // })
  // console.log('任务创建:', task)
  
  // 测试查询任务（需要真实 task_id）
  // const taskInfo = await getTask('task_xxx')
  // console.log('任务信息:', taskInfo)
}

testAPI()
```

---

**API SDK 封装完成！** ✨

现有的代码可以继续使用，无需修改。新代码可以使用更简洁的 axios 风格。

