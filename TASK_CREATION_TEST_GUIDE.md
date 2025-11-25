# 任务创建功能测试指南

## 🎯 功能概述

本次实现了 **POST /tasks** 任务创建功能，前端 Editor 页面的"生成"按钮已经绑定真实的 API 调用逻辑。

## ✅ 已实现的功能

### 后端
1. ✅ **POST /api/v1/tasks** - 创建任务接口
2. ✅ **GET /api/v1/tasks/{task_id}** - 查询任务详情
3. ✅ **GET /api/v1/tasks** - 获取任务列表
4. ✅ **POST /api/v1/tasks/{task_id}/cancel** - 取消任务
5. ✅ 任务路由已注册到 FastAPI 应用

### 前端
1. ✅ **createTask API 函数** - `frontend/src/api/tasks.ts`
2. ✅ **任务状态管理** - Editor 页面中的 task_id、taskStatus、sourceFileId、referenceFileId
3. ✅ **生成按钮逻辑** - 真实调用 createTask API
4. ✅ **图片上传改进** - UploadArea 组件返回 file_id 和 imageUrl
5. ✅ **移动端支持** - MobileControls 组件也支持真实上传

## 🧪 测试步骤

### 1. 确保后端正在运行

```bash
cd F:\formy\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**确认后端启动成功**：
- 访问 http://localhost:8000/health 应该返回 `{"status":"healthy"}`
- 访问 http://localhost:8000/docs 可以看到 API 文档

### 2. 启动前端

打开**新的终端**：

```bash
cd F:\formy\frontend
npm run dev
```

前端应该运行在 http://localhost:5173

### 3. 测试任务创建流程

#### 步骤 A：上传图片
1. 打开浏览器访问 http://localhost:5173/editor
2. 点击"原始图片"上传区域，选择一张图片
3. 等待上传完成（会显示加载动画）
4. 上传成功后，图片应该显示在上传区域

#### 步骤 B：上传参考图（根据模式）
- **HEAD_SWAP（换头）**：需要上传参考头像
- **BACKGROUND_CHANGE（换背景）**：需要上传背景图片
- **POSE_CHANGE（换姿势）**：需要上传目标姿势图

#### 步骤 C：点击"开始生成"按钮
1. 点击底部的"开始生成"按钮
2. 观察按钮变为"处理中..."并显示加载动画
3. 打开浏览器控制台（F12），应该能看到：
   ```
   图片上传成功: {file_id: "img_20231117_xxx", ...}
   任务创建成功: {task_id: "task_20231117_xxx", status: "pending", ...}
   ```

#### 步骤 D：验证后端
1. 在后端终端中，应该能看到任务创建的日志
2. 访问 http://localhost:8000/docs
3. 尝试调用 `GET /api/v1/tasks/{task_id}`，使用控制台中的 task_id
4. 应该能获取到任务信息

### 4. 测试不同模式

切换到不同的模式标签，测试：
- **AI 换头** (HEAD_SWAP)
- **AI 换背景** (BACKGROUND_CHANGE)
- **AI 换姿势** (POSE_CHANGE)

每个模式都应该能够正常创建任务。

### 5. 测试错误处理

#### 测试 A：未上传图片就点击生成
- **预期**：弹出提示 "请先上传原始图片"

#### 测试 B：HEAD_SWAP 模式下只上传原图
- **预期**：弹出提示 "此模式需要上传参考图片"

#### 测试 C：关闭后端后尝试上传/生成
- **预期**：显示错误提示

## 📊 验证任务系统是否工作

### 方法 1：使用 API 文档测试
1. 访问 http://localhost:8000/docs
2. 找到 `POST /api/v1/tasks`
3. 点击 "Try it out"
4. 输入请求体：
   ```json
   {
     "mode": "HEAD_SWAP",
     "source_image": "img_20231117_abc123",
     "config": {
       "target_face_image": "img_20231117_def456"
     }
   }
   ```
5. 点击 "Execute"
6. 应该收到响应，包含 task_id

### 方法 2：使用 curl 命令
```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "HEAD_SWAP",
    "source_image": "img_20231117_abc123",
    "config": {}
  }'
```

### 方法 3：查询任务列表
```bash
curl http://localhost:8000/api/v1/tasks
```

## 🔍 调试技巧

### 前端调试
1. 打开浏览器开发者工具（F12）
2. 切换到 Console 标签
3. 观察上传和任务创建的日志
4. 切换到 Network 标签
5. 观察 API 请求和响应

### 后端调试
1. 查看后端终端的日志输出
2. 如果有错误，会显示完整的堆栈跟踪
3. 检查 Redis 连接状态（如果配置了 Redis）

## 📝 当前限制

### 注意事项
1. ⚠️ **任务不会真正执行** - Worker 还没有启动，任务创建后会停留在 "pending" 状态
2. ⚠️ **没有实时状态更新** - 前端还没有轮询机制，需要手动刷新任务状态
3. ⚠️ **结果显示是模拟的** - 目前显示原图作为结果预览

### 下一步工作
- 启动 Worker 进程来真正处理任务
- 实现前端轮询机制（自动查询任务状态）
- 接入真实的 AI Pipeline（换头/换背景/换姿势）

## ✨ 成功标志

如果看到以下情况，说明功能正常：

✅ 图片能够成功上传到后端
✅ 前端获取到 file_id
✅ 点击"开始生成"按钮后，控制台显示 task_id
✅ 后端 API 文档中能查询到创建的任务
✅ 任务状态为 "pending"
✅ 任务记录包含正确的 mode、source_image、config

## 🚀 下一步计划

1. **启动 Worker** - 让任务真正被处理
2. **实现状态轮询** - 前端定时查询任务状态
3. **显示处理进度** - 进度条和当前步骤
4. **显示最终结果** - 处理完成后显示输出图片
5. **任务列表页面** - 查看所有任务历史

---

**测试愉快！** 🎉

如果遇到任何问题，请检查：
1. 后端和前端是否都在运行
2. 浏览器控制台是否有错误信息
3. 后端终端是否有错误日志

