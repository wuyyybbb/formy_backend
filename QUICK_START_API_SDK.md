# 🚀 API SDK 快速开始

## 1️⃣ 安装依赖

```bash
cd frontend
npm install
```

这会安装 `axios@^1.6.2` 和其他依赖。

## 2️⃣ 基本使用

### 导入 API

```typescript
import { 
  uploadImage, 
  createTask, 
  getTask,
  EditMode,
  TaskStatus 
} from '@/api'
```

### 上传图片

```typescript
const handleUpload = async (file: File) => {
  try {
    const result = await uploadImage(file, 'source')
    console.log('File ID:', result.file_id)
    console.log('URL:', result.url)
  } catch (error) {
    console.error('Upload failed:', error.message)
  }
}
```

### 创建任务

```typescript
const handleGenerate = async () => {
  const task = await createTask({
    mode: EditMode.HEAD_SWAP,
    source_image: 'img_20231117_abc123',
    config: {
      target_face_image: 'img_20231117_def456'
    }
  })
  
  console.log('Task ID:', task.task_id)
}
```

### 查询任务

```typescript
const checkTask = async (taskId: string) => {
  const task = await getTask(taskId)
  
  console.log('Status:', task.status)
  console.log('Progress:', task.progress + '%')
  
  if (task.status === TaskStatus.DONE) {
    console.log('Result:', task.result?.output_image)
  }
}
```

## 3️⃣ 完整示例

```typescript
import { 
  uploadImage, 
  createTask, 
  getTask,
  EditMode,
  TaskStatus,
  getImageUrl
} from '@/api'

async function processImage(file: File) {
  // 1. 上传图片
  const uploadResult = await uploadImage(file, 'source')
  
  // 2. 创建任务
  const task = await createTask({
    mode: EditMode.HEAD_SWAP,
    source_image: uploadResult.file_id,
    config: {}
  })
  
  // 3. 轮询状态
  const interval = setInterval(async () => {
    const taskInfo = await getTask(task.task_id)
    
    console.log(`Progress: ${taskInfo.progress}%`)
    
    if (taskInfo.status === TaskStatus.DONE) {
      clearInterval(interval)
      const resultUrl = getImageUrl(taskInfo.result!.output_image!)
      console.log('Done!', resultUrl)
    }
  }, 2500)
}
```

## 4️⃣ 类型定义

所有 API 都有完整的 TypeScript 类型：

```typescript
// 自动提示和类型检查
import type { 
  UploadImageResponse,
  TaskInfo,
  TaskResult 
} from '@/api'

const result: UploadImageResponse = await uploadImage(file, 'source')
const task: TaskInfo = await getTask(taskId)
```

## 5️⃣ 错误处理

```typescript
try {
  const result = await uploadImage(file, 'source')
} catch (error) {
  // 友好的错误消息
  alert(error.message)
}
```

## 📚 详细文档

查看 `frontend/API_SDK_GUIDE.md` 获取完整文档。

## ✅ 检查清单

- [x] ✅ 已安装 axios 依赖
- [x] ✅ 已创建 Axios 客户端
- [x] ✅ 已封装所有 API 函数
- [x] ✅ 已添加完整类型定义
- [x] ✅ 已实现统一错误处理
- [x] ✅ 已提供详细文档

---

**开始使用吧！** 🎉

