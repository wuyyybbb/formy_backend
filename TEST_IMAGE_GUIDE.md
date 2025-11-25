# 本地测试图片使用指南

本指南说明如何使用 `test_image` 目录进行本地测试，无需通过前端上传图片。

## 📁 目录结构

```
backend/
├── test_image/               # 测试图片目录
│   ├── person1.jpg          # 原图
│   ├── pose_reference.jpg   # 姿势参考图
│   └── ...                  # 更多测试图片
├── uploads/                 # 上传图片存储（生产环境）
│   ├── source/
│   ├── reference/
│   └── other/
├── results/                 # 处理结果输出
└── prepare_test_images.py  # 测试图片准备脚本
```

## 🚀 使用方法

### **方法 1：直接使用完整路径（最简单）**

修改后的 `resolve_uploaded_file()` 函数现在支持三种输入：

1. **标准 file_id**（生产环境）
   ```python
   source_image = "img_abc123"
   # 会在 uploads/source/, uploads/reference/ 搜索 img_abc123.*
   ```

2. **完整文件路径**（测试用）
   ```python
   source_image = "F:/formy/backend/test_image/person1.jpg"
   # 直接使用该文件
   ```

3. **test_image 目录的文件名**（测试用）
   ```python
   source_image = "person1.jpg"
   # 会在 test_image/ 目录搜索 person1.jpg
   ```

### **方法 2：运行本地测试脚本**

#### **步骤 1：准备测试图片**

```bash
# 在 backend 目录下创建 test_image 文件夹（已创建）
cd F:\formy\backend\test_image

# 确保至少有 2 张图片：
# - 图片 1：原图（要改变姿势的人）
# - 图片 2：姿势参考图（目标姿势）
```

#### **步骤 2：运行测试脚本**

```bash
cd F:\formy\backend
python test_pose_change_local.py
```

**输出示例：**
```
================================================================================
📁 Available Test Images
================================================================================

  1. person1.jpg (2048 KB)
  2. pose_reference.jpg (1536 KB)

🎯 Using:
   Source: person1.jpg
   Pose:   pose_reference.jpg

================================================================================
🧪 Testing POSE_CHANGE Pipeline Locally
================================================================================

📸 Source Image:  test_image\person1.jpg
🕺 Pose Reference: test_image\pose_reference.jpg

✅ Test images found

🔧 Initializing PoseChangePipeline...
✅ Pipeline initialized

🚀 Starting pose transfer...
--------------------------------------------------------------------------------
[Pipeline] Step 1: Loading images...
[Pipeline] Step 2: Calling ComfyUI Engine...
[Pipeline] Step 3: Saving results...

================================================================================
📊 Result Summary
================================================================================

✅ Status: SUCCESS

📁 Output Image:      results/test_local_pose_change_output.jpg
🖼️  Thumbnail:         results/test_local_pose_change_thumbnail.jpg
📊 Comparison Image:  results/test_local_pose_change_comparison.jpg

⏱️  Processing Time: 45.23s

================================================================================
```

### **方法 3：通过 API 测试（使用文件名）**

创建任务时，直接使用 test_image 目录里的文件名：

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "POSE_CHANGE",
    "source_image": "person1.jpg",
    "config": {
      "pose_image": "pose_reference.jpg"
    }
  }'
```

或使用完整路径：

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "POSE_CHANGE",
    "source_image": "F:/formy/backend/test_image/person1.jpg",
    "config": {
      "pose_image": "F:/formy/backend/test_image/pose_reference.jpg"
    }
  }'
```

### **方法 4：准备标准格式的测试图片**

如果你想使用标准的 file_id 格式：

```bash
cd F:\formy\backend
python prepare_test_images.py
```

**输出示例：**
```
🖼️  Preparing test images for local testing...
============================================================
📁 Found 2 test image(s):

  1. person1.jpg
     → file_id: test_20241201_001
     → purpose: source
     → path: uploads\source\test_20241201_001.jpg

  2. pose_reference.jpg
     → file_id: test_20241201_002
     → purpose: reference
     → path: uploads\reference\test_20241201_002.jpg

============================================================
✅ Test images prepared successfully!

📋 File ID Mapping:
------------------------------------------------------------

person1.jpg:
  file_id:  test_20241201_001
  purpose:  source
  URL:      /uploads/source/test_20241201_001.jpg

pose_reference.jpg:
  file_id:  test_20241201_002
  purpose:  reference
  URL:      /uploads/reference/test_20241201_002.jpg

============================================================
🧪 How to test:

1. Use the file_id values above in your API requests
2. For POSE_CHANGE task, use:
   - source_image: "test_20241201_001"
   - config.pose_image: "test_20241201_002"
```

然后使用生成的 file_id 创建任务：

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "POSE_CHANGE",
    "source_image": "test_20241201_001",
    "config": {
      "pose_image": "test_20241201_002"
    }
  }'
```

## 🔧 技术实现

### **resolve_uploaded_file() 函数**

位置：`backend/app/services/image/image_assets.py`

**搜索顺序：**
1. 检查是否是完整路径（存在且是文件）
2. 在 `uploads/source/`, `uploads/reference/`, `uploads/other/` 搜索 `{file_id}.*`
3. 在 `uploads/` 递归搜索 `{file_id}.*`
4. 在 `test_image/` 搜索完整文件名
5. 在 `test_image/` 搜索 `{file_id}.*`

**示例：**
```python
from app.services.image.image_assets import resolve_uploaded_file

# 标准 file_id
path = resolve_uploaded_file("img_abc123")
# → F:/formy/backend/uploads/source/img_abc123.jpg

# 完整路径
path = resolve_uploaded_file("F:/formy/backend/test_image/test.jpg")
# → F:/formy/backend/test_image/test.jpg

# test_image 文件名
path = resolve_uploaded_file("test.jpg")
# → F:/formy/backend/test_image/test.jpg
```

## 📝 注意事项

1. **生产环境 vs 测试环境**
   - 生产环境：只使用 `uploads/` 目录
   - 测试环境：可以使用 `test_image/` 目录

2. **文件格式**
   - 支持：JPG, JPEG, PNG, WEBP
   - 建议分辨率：1024x1024 或更高

3. **Worker 环境**
   - 如果 Worker 在单独的服务上运行，需要将 test_image 同步到 Worker 服务器
   - 或者使用 `prepare_test_images.py` 将图片复制到 uploads 目录

4. **文件权限**
   - 确保 Worker 有读取 test_image 目录的权限

## 🎯 推荐工作流

**本地开发测试：**
```bash
# 1. 添加测试图片到 test_image/
# 2. 运行本地测试脚本
python test_pose_change_local.py

# 3. 或通过 API 测试（使用文件名）
POST /api/v1/tasks
{
  "source_image": "person1.jpg",
  "config": {"pose_image": "pose_reference.jpg"}
}
```

**部署到 Render 前测试：**
```bash
# 1. 使用 prepare_test_images.py 生成标准 file_id
python prepare_test_images.py

# 2. 使用生成的 file_id 测试
POST /api/v1/tasks
{
  "source_image": "test_20241201_001",
  "config": {"pose_image": "test_20241201_002"}
}

# 3. 确认成功后再部署到 Render
```

## 🐛 故障排查

**问题：FileNotFoundError**
```python
FileNotFoundError: 未找到对应文件: person1.jpg
```

**解决：**
1. 检查 test_image 目录是否存在
2. 检查文件名拼写是否正确
3. 尝试使用完整路径

**问题：图片加载失败**
```python
Error: 加载图片失败: cannot identify image file
```

**解决：**
1. 确认图片格式是否支持（JPG/PNG/WEBP）
2. 确认图片文件是否损坏
3. 使用 PIL 测试图片：
   ```python
   from PIL import Image
   Image.open("test_image/person1.jpg").show()
   ```

## ✅ 完成！

现在你可以：
- ✅ 直接使用 test_image 目录的图片测试
- ✅ 无需通过前端上传
- ✅ 支持完整路径、文件名、file_id 三种方式
- ✅ 一键运行本地测试脚本

