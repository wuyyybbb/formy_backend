# Formy API 规范文档

## 概述

Formy 后端 API 基于 FastAPI 构建，提供服装图像 AI 编辑能力。

- **Base URL**: `http://localhost:8000`
- **API Version**: `v1`
- **API Prefix**: `/api/v1`

---

## 认证方式（可选）

当前版本支持两种模式：
- **无认证模式**：直接调用接口（开发阶段）
- **Token 认证**：Bearer Token（生产环境推荐）

```http
Authorization: Bearer <your_token>
```

---

## 📌 核心接口

### 1. 上传图片

**功能**：上传服装模特图片或参考图片

**请求**

```http
POST /api/v1/upload
Content-Type: multipart/form-data
```

**表单参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件（支持 jpg/jpeg/png/webp） |
| purpose | string | 否 | 用途标识：`source`（原图）/ `reference`（参考图）|

**响应示例**

```json
{
  "success": true,
  "data": {
    "file_id": "img_20231117_abc123",
    "filename": "model.jpg",
    "size": 2048576,
    "url": "/uploads/img_20231117_abc123.jpg",
    "uploaded_at": "2025-11-17T10:30:00Z"
  }
}
```

**错误响应**

```json
{
  "success": false,
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "不支持的文件格式，仅支持 jpg/jpeg/png/webp"
  }
}
```

---

### 2. 创建编辑任务

**功能**：创建 AI 图像编辑任务（换头/换背景/换姿势）

**请求**

```http
POST /api/v1/tasks
Content-Type: application/json
```

**请求体**

```json
{
  "mode": "HEAD_SWAP",
  "source_image": "img_20231117_abc123",
  "config": {
    "reference_image": "img_20231117_def456",
    "quality": "high",
    "preserve_details": true
  }
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| mode | string | 是 | 编辑模式：`HEAD_SWAP` / `BACKGROUND_CHANGE` / `POSE_CHANGE` |
| source_image | string | 是 | 原始图片的 file_id |
| config | object | 是 | 模式相关配置参数 |

**config 参数详解**

#### HEAD_SWAP（换头）模式

```json
{
  "reference_image": "img_xxx",      // 参考头像图片 file_id
  "quality": "high",                 // 质量：low / medium / high
  "preserve_details": true,          // 保留细节
  "blend_strength": 0.8              // 融合强度 0.0-1.0
}
```

#### BACKGROUND_CHANGE（换背景）模式

```json
{
  "background_type": "custom",       // 背景类型：custom / preset / remove
  "background_image": "img_yyy",     // 背景图片 file_id（background_type=custom 时必填）
  "background_preset": "studio_white", // 预设背景（background_type=preset 时使用）
  "edge_blur": 2,                    // 边缘羽化程度 0-10
  "color_match": true                // 颜色匹配
}
```

#### POSE_CHANGE（换姿势）模式

```json
{
  "target_pose": "standing_front",   // 目标姿势（预设姿势库）
  "pose_reference": "img_zzz",       // 或提供参考姿势图片 file_id
  "preserve_face": true,             // 保持面部不变
  "smoothness": 0.7                  // 平滑度 0.0-1.0
}
```

**响应示例**

```json
{
  "success": true,
  "data": {
    "task_id": "task_20231117_xyz789",
    "status": "pending",
    "mode": "HEAD_SWAP",
    "created_at": "2025-11-17T10:35:00Z",
    "estimated_time": 30
  }
}
```

**任务状态说明**

| 状态 | 说明 |
|------|------|
| pending | 待处理（已入队） |
| processing | 处理中 |
| done | 完成 |
| failed | 失败 |
| cancelled | 已取消 |

---

### 3. 查询任务状态

**功能**：查询任务处理进度和结果

**请求**

```http
GET /api/v1/tasks/{task_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| task_id | string | 任务 ID |

**响应示例 - 处理中**

```json
{
  "success": true,
  "data": {
    "task_id": "task_20231117_xyz789",
    "status": "processing",
    "mode": "HEAD_SWAP",
    "progress": 65,
    "current_step": "正在进行头部融合...",
    "created_at": "2025-11-17T10:35:00Z",
    "updated_at": "2025-11-17T10:35:25Z"
  }
}
```

**响应示例 - 完成**

```json
{
  "success": true,
  "data": {
    "task_id": "task_20231117_xyz789",
    "status": "done",
    "mode": "HEAD_SWAP",
    "progress": 100,
    "result": {
      "output_image": "/results/task_20231117_xyz789_output.jpg",
      "thumbnail": "/results/task_20231117_xyz789_thumb.jpg",
      "metadata": {
        "width": 1024,
        "height": 1536,
        "format": "jpeg",
        "size": 3145728
      }
    },
    "created_at": "2025-11-17T10:35:00Z",
    "completed_at": "2025-11-17T10:35:45Z",
    "processing_time": 45
  }
}
```

**响应示例 - 失败**

```json
{
  "success": true,
  "data": {
    "task_id": "task_20231117_xyz789",
    "status": "failed",
    "mode": "HEAD_SWAP",
    "error": {
      "code": "ENGINE_ERROR",
      "message": "AI 模型处理失败，请稍后重试",
      "details": "Face detection failed: No face found in reference image"
    },
    "created_at": "2025-11-17T10:35:00Z",
    "failed_at": "2025-11-17T10:35:15Z"
  }
}
```

---

### 4. 获取任务列表

**功能**：获取用户的任务历史记录

**请求**

```http
GET /api/v1/tasks
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| status | string | 否 | all | 筛选状态：all / pending / processing / done / failed |
| mode | string | 否 | all | 筛选模式：all / HEAD_SWAP / BACKGROUND_CHANGE / POSE_CHANGE |
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |
| sort | string | 否 | created_desc | 排序：created_desc / created_asc / updated_desc |

**响应示例**

```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "task_id": "task_20231117_xyz789",
        "status": "done",
        "mode": "HEAD_SWAP",
        "thumbnail": "/results/task_20231117_xyz789_thumb.jpg",
        "created_at": "2025-11-17T10:35:00Z",
        "completed_at": "2025-11-17T10:35:45Z"
      },
      {
        "task_id": "task_20231117_xyz788",
        "status": "processing",
        "mode": "BACKGROUND_CHANGE",
        "progress": 45,
        "created_at": "2025-11-17T10:30:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "page_size": 20,
      "total_items": 45,
      "total_pages": 3
    }
  }
}
```

---

### 5. 取消任务

**功能**：取消正在排队或处理中的任务

**请求**

```http
DELETE /api/v1/tasks/{task_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| task_id | string | 任务 ID |

**响应示例**

```json
{
  "success": true,
  "data": {
    "task_id": "task_20231117_xyz789",
    "status": "cancelled",
    "message": "任务已成功取消"
  }
}
```

---

### 6. 下载结果图片

**功能**：下载任务生成的结果图片

**请求**

```http
GET /api/v1/results/{filename}
```

**说明**：直接返回图片文件流，可在浏览器中预览或下载

---

## 🔐 认证接口（可选）

### 7. 用户注册

**请求**

```http
POST /api/v1/auth/register
Content-Type: application/json
```

**请求体**

```json
{
  "username": "fashion_designer",
  "email": "designer@example.com",
  "password": "secure_password_123"
}
```

**响应示例**

```json
{
  "success": true,
  "data": {
    "user_id": "user_abc123",
    "username": "fashion_designer",
    "email": "designer@example.com",
    "created_at": "2025-11-17T10:00:00Z"
  }
}
```

---

### 8. 用户登录

**请求**

```http
POST /api/v1/auth/login
Content-Type: application/json
```

**请求体**

```json
{
  "email": "designer@example.com",
  "password": "secure_password_123"
}
```

**响应示例**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "user_id": "user_abc123",
      "username": "fashion_designer",
      "email": "designer@example.com"
    }
  }
}
```

---

### 9. 获取用户信息

**请求**

```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

**响应示例**

```json
{
  "success": true,
  "data": {
    "user_id": "user_abc123",
    "username": "fashion_designer",
    "email": "designer@example.com",
    "created_at": "2025-11-17T10:00:00Z",
    "stats": {
      "total_tasks": 128,
      "completed_tasks": 115,
      "storage_used": "2.5GB"
    }
  }
}
```

---

## 📊 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": { /* 具体数据 */ }
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "用户友好的错误信息",
    "details": "详细的错误描述（可选）"
  }
}
```

---

## ⚠️ 错误码说明

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| INVALID_REQUEST | 400 | 请求参数错误 |
| INVALID_FILE_TYPE | 400 | 不支持的文件类型 |
| FILE_TOO_LARGE | 400 | 文件大小超过限制（10MB） |
| UNAUTHORIZED | 401 | 未授权（需要登录）|
| FORBIDDEN | 403 | 无权限访问 |
| TASK_NOT_FOUND | 404 | 任务不存在 |
| FILE_NOT_FOUND | 404 | 文件不存在 |
| MODE_NOT_SUPPORTED | 422 | 不支持的编辑模式 |
| ENGINE_ERROR | 500 | AI 引擎处理错误 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| SERVICE_UNAVAILABLE | 503 | 服务暂时不可用 |

---

## 📝 使用示例

### 完整工作流示例（JavaScript）

```javascript
// 1. 上传原始图片
const uploadSource = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('purpose', 'source');
  
  const response = await fetch('http://localhost:8000/api/v1/upload', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  return result.data.file_id;
};

// 2. 上传参考图片（换头模式需要）
const uploadReference = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('purpose', 'reference');
  
  const response = await fetch('http://localhost:8000/api/v1/upload', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  return result.data.file_id;
};

// 3. 创建编辑任务
const createTask = async (sourceId, referenceId) => {
  const response = await fetch('http://localhost:8000/api/v1/tasks', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      mode: 'HEAD_SWAP',
      source_image: sourceId,
      config: {
        reference_image: referenceId,
        quality: 'high',
        preserve_details: true,
        blend_strength: 0.8
      }
    })
  });
  
  const result = await response.json();
  return result.data.task_id;
};

// 4. 轮询任务状态
const pollTaskStatus = async (taskId) => {
  const interval = setInterval(async () => {
    const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId}`);
    const result = await response.json();
    
    const task = result.data;
    
    if (task.status === 'done') {
      clearInterval(interval);
      console.log('任务完成！', task.result.output_image);
      // 显示结果图片
      showResult(task.result.output_image);
    } else if (task.status === 'failed') {
      clearInterval(interval);
      console.error('任务失败：', task.error.message);
    } else {
      console.log(`处理中... ${task.progress}%`);
    }
  }, 2000); // 每2秒查询一次
};

// 完整流程
const processImage = async (sourceFile, referenceFile) => {
  try {
    // 上传图片
    const sourceId = await uploadSource(sourceFile);
    const referenceId = await uploadReference(referenceFile);
    
    // 创建任务
    const taskId = await createTask(sourceId, referenceId);
    
    // 轮询状态
    await pollTaskStatus(taskId);
  } catch (error) {
    console.error('处理失败：', error);
  }
};
```

---

## 🔧 限制说明

| 项目 | 限制 |
|------|------|
| 图片大小 | 最大 10MB |
| 图片格式 | jpg, jpeg, png, webp |
| 图片分辨率 | 建议 512x512 ~ 2048x2048 |
| 并发任务数 | 每用户最多 3 个 |
| 任务保留时间 | 完成后保留 7 天 |
| 请求频率 | 100 次/分钟 |

---

## 📌 WebSocket 实时更新（可选扩展）

对于不想轮询的客户端，可以使用 WebSocket 接收任务状态实时更新。

**连接地址**

```
ws://localhost:8000/api/v1/ws/tasks/{task_id}
```

**接收消息格式**

```json
{
  "type": "status_update",
  "data": {
    "task_id": "task_20231117_xyz789",
    "status": "processing",
    "progress": 75,
    "current_step": "正在进行图像融合..."
  }
}
```

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2025-11-17 | 初始版本 |

---

**更新日志**：本文档将随 API 实现不断完善更新。

