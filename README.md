# Formy｜形我 - AI 视觉创作工具

> 专为服装摄影师、电商从业者、品牌运营者打造的 AI 图像处理工具

## 📖 项目简介

Formy 是一个 AI 视觉创作工具，提供以下功能：
- 🔄 **AI 换头** - 智能替换人物头部
- 🎨 **AI 换背景** - 自动更换图片背景
- 💃 **AI 换姿势** - 迁移人物姿态

### 💰 套餐和算力系统

Formy 采用**算力消耗制**：
- 每个 AI 任务消耗一定算力
- 不同模式消耗不同算力（换头 48 / 换背景 36 / 换姿势 60）
- 套餐提供每月固定算力额度（STARTER 2000 / BASIC 5000 / PRO 12000 / ULTIMATE 30000）
- 算力不足时无法创建任务，需要升级套餐

**示例**：PRO 套餐（12000 算力）可处理约 250 次标准换头任务

详见：`算力扣减与AI任务集成说明.md`

---

## 🚀 如何启动项目（适合小白）

### 📋 前置要求

在开始之前，请确保你的电脑已安装：

1. **Python** （版本 3.10 或更高）
   - 下载地址: https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

2. **Node.js** （版本 16 或更高）
   - 下载地址: https://nodejs.org/
   - 选择 LTS 版本

3. **Redis** （任务队列，可选）
   - Windows 下载: https://github.com/tporadowski/redis/releases

### 📦 第一次使用：安装依赖

#### 1. 安装后端依赖

打开 **命令提示符** 或 **PowerShell**，运行：

```bash
# 进入项目根目录
cd F:\formy

# 进入后端目录
cd backend

# 安装 Python 依赖
pip install -r requirements.txt
```

等待安装完成（可能需要几分钟）。

#### 2. 安装前端依赖

在**新的**命令行窗口中，运行：

```bash
# 进入项目根目录
cd F:\formy


# 进入前端目录
cd frontend

# 安装 Node.js 依赖
npm install
```

等待安装完成（可能需要几分钟）。

---

## ▶️ 启动项目（每次使用都需要）

**重要提示**：需要同时打开 **3 个命令行窗口**，分别运行后端、Worker 和前端。

### 窗口 1：启动后端 API

1. 打开**第一个**命令行窗口
2. 运行以下命令：

```bash
cd F:\formy\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**成功标志**：看到类似以下输出
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

✅ **不要关闭这个窗口！保持运行。**

---

### 窗口 2：启动 Worker（任务处理）

1. 打开**第二个**命令行窗口
2. 运行以下命令：

```bash
cd F:\formy\backend
python run_worker_simple.py
```

**成功标志**：看到类似以下输出
```
╔══════════════════════════════════════════════════════════╗
║              Formy Worker - 简易版本                     ║
╚══════════════════════════════════════════════════════════╝

🚀 Worker 已启动，等待任务...
```

✅ **不要关闭这个窗口！保持运行。**

---

### 窗口 3：启动前端界面

1. 打开**第三个**命令行窗口
2. 运行以下命令：

```bash
cd F:\formy\frontend
npm run dev
```

**成功标志**：看到类似以下输出
```
VITE v5.0.8  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: http://192.168.x.x:5173/
```

✅ **不要关闭这个窗口！保持运行。**

---

### 🌐 打开网页

在浏览器中访问：**http://localhost:5173**

你应该能看到 Formy 的主页。

---

## 🎯 如何使用

### 完整流程（推荐）

1. **访问首页**
   - 打开 http://localhost:5173
   - 浏览品牌介绍和功能展示

2. **选择功能**
   - 点击"Get Started"或"开始创作"
   - 进入功能选择页面
   - 选择：AI 换头 / AI 换背景 / AI 换姿势

3. **开始创作**
   - 点击"开始创作"按钮
   - 进入编辑页面

4. **上传图片**
   - 上传原始图片
   - 上传参考图片（换头/换姿势需要）

5. **生成结果**
   - 点击"开始生成"
   - 等待处理（约 10-15 秒）
   - 查看结果

### 快速入口

- **首页**：http://localhost:5173
- **功能选择**：http://localhost:5173/features
- **编辑器**：http://localhost:5173/editor

---

## 🔐 登录功能配置

项目已集成**邮箱验证码登录**功能，需要配置邮件服务。

### 快速配置步骤

1. **获取 Resend API Key**
   - 访问 https://resend.com/ 注册账号（免费）
   - 创建 API Key

2. **配置环境变量**
   ```bash
   cd backend
   copy .env.example .env
   ```
   
   编辑 `.env` 文件，填写：
   ```env
   RESEND_API_KEY=re_你的API_Key
   FROM_EMAIL=support@formy.it.com
   SECRET_KEY=formy-secret-key-2025
   ```

3. **安装依赖**
   ```bash
   cd backend
   pip install python-jose[cryptography]
   ```

4. **重启后端**（如果正在运行）

5. **测试登录**
   - 访问 http://localhost:5173
   - 点击 "登录" 按钮
   - 输入邮箱，发送验证码
   - 输入验证码，登录成功！

**详细说明**：查看 `快速配置登录功能.txt` 和 `AUTH_IMPLEMENTATION_GUIDE.md`

---

## 🛑 如何停止项目

1. 在每个命令行窗口中按 **Ctrl + C**
2. 依次关闭 3 个窗口

---

## ❓ 常见问题

### Q1: 启动后端时报错 "ModuleNotFoundError"

**原因**：Python 依赖没有安装

**解决方法**：
```bash
cd F:\formy\backend
pip install -r requirements.txt
```

---

### Q2: 启动前端时报错 "npm error code ENOENT"

**原因**：Node.js 依赖没有安装

**解决方法**：
```bash
cd F:\formy\frontend
npm install
```

---

### Q3: 后端启动成功，但访问 http://localhost:8000 没反应

**检查**：
1. 确认看到 "Application startup complete." 消息
2. 在浏览器访问 http://localhost:8000/health
3. 应该看到 `{"status":"healthy"}`

**如果还是不行**：
- 检查是否有其他程序占用了 8000 端口
- 尝试重启电脑

---

### Q4: 前端打不开，显示空白页

**检查**：
1. 确认 3 个窗口都在运行
2. 刷新浏览器 (Ctrl + F5)
3. 清除浏览器缓存

---

### Q5: 上传图片后点击"生成"没反应

**检查**：
1. Worker 窗口是否正在运行？
2. 打开浏览器控制台 (F12)，看是否有错误

**解决方法**：
- 确保 Worker 正在运行（窗口 2）
- 重新启动 Worker

---

### Q6: 如何查看详细错误信息？

**方法 1 - 浏览器控制台**：
1. 按 F12 打开开发者工具
2. 切换到 "Console" 标签
3. 查看红色错误信息

**方法 2 - 后端日志**：
- 查看后端命令行窗口（窗口 1）的输出

**方法 3 - Worker 日志**：
- 查看 Worker 命令行窗口（窗口 2）的输出

---

## 📂 项目结构

```
F:\formy\
├── backend/              # 后端代码
│   ├── app/             # 应用代码
│   ├── requirements.txt # Python 依赖
│   └── run_worker_simple.py  # Worker 脚本
├── frontend/            # 前端代码
│   ├── src/            # 源代码
│   ├── package.json    # Node.js 依赖
│   └── vite.config.ts  # 配置文件
├── docs/               # 文档
└── README.md          # 本文件
```

---

## 🔧 端口说明

- **8000** - 后端 API 服务
- **5173** - 前端开发服务器

确保这两个端口没有被其他程序占用。

---

## 📱 快速启动脚本（推荐）

为了方便启动，你可以创建批处理文件：

### 创建 `start-backend.bat`

在项目根目录创建文件，内容：

```batch
@echo off
cd /d F:\formy\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
```

### 创建 `start-worker.bat`

在项目根目录创建文件，内容：

```batch
@echo off
cd /d F:\formy\backend
python run_worker_simple.py
pause
```

### 创建 `start-frontend.bat`

在项目根目录创建文件，内容：

```batch
@echo off
cd /d F:\formy\frontend
npm run dev
pause
```

**使用方法**：
1. 双击 `start-backend.bat`
2. 双击 `start-worker.bat`
3. 双击 `start-frontend.bat`
4. 打开浏览器访问 http://localhost:5173

---

## 📚 详细文档

- **API 文档**: `docs/API_SPEC.md`
- **任务系统**: `backend/TASK_SYSTEM_README.md`
- **前端 API SDK**: `frontend/API_SDK_GUIDE.md`
- **测试指南**: `POLLING_TEST_GUIDE.md`

---

## 🎓 学习资源

如果你想学习更多：

- **Python 基础**: https://www.runoob.com/python3/python3-tutorial.html
- **JavaScript 基础**: https://www.runoob.com/js/js-tutorial.html
- **FastAPI 文档**: https://fastapi.tiangolo.com/zh/
- **React 文档**: https://react.dev/

---

## 🆘 获取帮助

遇到问题？

1. 查看上面的"常见问题"部分
2. 查看详细文档
3. 检查命令行窗口的错误信息
4. 打开浏览器控制台 (F12) 查看错误

---

## 📝 开发状态

当前版本：**1.0.0**

功能状态：
- ✅ 图片上传
- ✅ 任务创建
- ✅ 任务轮询
- ✅ 进度显示
- ⚠️ AI 处理（模拟中，需接入真实引擎）

---

## 📄 许可证

本项目仅供学习和研究使用。

---

**祝你使用愉快！** 🎉

如有问题，请查看上方的"常见问题"部分或相关文档。



