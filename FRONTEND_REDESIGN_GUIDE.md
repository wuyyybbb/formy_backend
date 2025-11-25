# 前端页面重新设计说明

## 📋 概述

前端已重新设计为 **3 个独立页面**，提供更清晰的用户流程。

---

## 🎯 页面结构

### 1. Landing Page（首页）- `/`

**功能**：品牌展示、价值传递、视觉冲击

**文件**：`frontend/src/pages/LandingPage.tsx`

**特点**：
- ✅ 参考 `reference/1.jpg` 设计风格
- ✅ 大标题："Autonomous, Local, Cost-competitive"
- ✅ 服装产品展示区（带浮动动画）
- ✅ 核心价值展示：10x 速度、80% 成本降低、24/7 服务
- ✅ 三大功能预览卡片
- ✅ CTA 按钮："开始创作" → 跳转到功能选择页

**访问地址**：http://localhost:5173/

---

### 2. Feature Selection Page（功能选择）- `/features`

**功能**：让用户选择 AI 功能（换头 / 换背景 / 换姿势）

**文件**：`frontend/src/pages/FeatureSelection.tsx`

**特点**：
- ✅ 三个功能卡片展示
- ✅ 点击选中功能（视觉高亮）
- ✅ 每个功能有详细说明和特性列表
- ✅ 选中后点击"开始创作"按钮
- ✅ 带有使用提示

**访问地址**：http://localhost:5173/features

**交互流程**：
```
用户访问 /features
  ↓
浏览三个功能卡片
  ↓
点击选择一个功能（卡片高亮）
  ↓
点击"开始创作"按钮
  ↓
跳转到 /editor?mode=XXX
```

---

### 3. Editor Page（编辑工作区）- `/editor`

**功能**：上传图片、调整参数、生成结果（原有功能保留）

**文件**：`frontend/src/pages/Editor.tsx`

**特点**：
- ✅ 支持从 URL 参数接收模式：`/editor?mode=HEAD_SWAP`
- ✅ 左侧控制面板（PC）/ 底部控制（移动端）
- ✅ 右侧预览面板（PC）/ 顶部预览（移动端）
- ✅ 实时进度显示
- ✅ 任务轮询
- ✅ 结果展示

**访问地址**：
- 直接访问：http://localhost:5173/editor（默认换头模式）
- 带参数：http://localhost:5173/editor?mode=HEAD_SWAP
- 带参数：http://localhost:5173/editor?mode=BACKGROUND_CHANGE
- 带参数：http://localhost:5173/editor?mode=POSE_CHANGE

**交互流程**：
```
用户进入编辑页面
  ↓
上传原始图片
  ↓
上传参考图片（如需要）
  ↓
调整参数（可选）
  ↓
点击"开始生成"
  ↓
显示进度（实时轮询）
  ↓
显示结果
```

---

## 🔄 完整用户流程

```
访问首页 (/)
  ↓
查看品牌介绍和功能展示
  ↓
点击"Get Started" 或 "开始创作"
  ↓
进入功能选择页面 (/features)
  ↓
选择一个功能（换头/换背景/换姿势）
  ↓
点击"开始创作"
  ↓
进入编辑页面 (/editor?mode=XXX)
  ↓
上传图片 → 生成 → 查看结果
```

---

## 📂 文件清单

### 新建文件
- `frontend/src/pages/LandingPage.tsx` - 首页（新）
- `frontend/src/pages/FeatureSelection.tsx` - 功能选择页（新）

### 修改文件
- `frontend/src/App.tsx` - 更新路由
- `frontend/src/pages/Editor.tsx` - 添加 URL 参数支持

### 保留文件
- `frontend/src/pages/Home.tsx` - 旧首页（已不再使用）
- 其他组件文件保持不变

---

## 🎨 设计亮点

### 首页（Landing Page）
1. **视觉冲击**
   - 大标题使用渐变色（青色到蓝色）
   - 浮动动画的产品展示
   - 科技感背景网格

2. **价值传递**
   - 三个数据指标：10x、80%、24/7
   - 清晰的功能卡片
   - 强有力的 CTA

3. **专业感**
   - 参考 Silana 风格
   - 黑色主题 + 青色点缀
   - 现代科技风

### 功能选择页
1. **清晰的选择**
   - 三个功能平铺展示
   - 点击选中有明显反馈
   - 详细的功能说明

2. **引导提示**
   - 底部有使用提示
   - 告诉用户每个功能适合什么场景

3. **流畅体验**
   - 选中后按钮高亮
   - 一键进入编辑页面

### 编辑页面
1. **保留原有功能**
   - 所有编辑功能完整保留
   - 轮询和进度显示正常工作

2. **URL 参数支持**
   - 从功能选择页带入模式
   - 页面加载时自动切换到对应模式

---

## 🔧 技术实现

### URL 参数传递

**功能选择页 → 编辑页**：
```typescript
// FeatureSelection.tsx
navigate(`/editor?mode=${selectedFeature}`)
```

**编辑页接收参数**：
```typescript
// Editor.tsx
const [searchParams] = useSearchParams()
const modeFromUrl = searchParams.get('mode')
```

### 路由配置

```typescript
// App.tsx
<Routes>
  <Route path="/" element={<LandingPage />} />
  <Route path="/features" element={<FeatureSelection />} />
  <Route path="/editor" element={<Editor />} />
</Routes>
```

---

## 📱 响应式设计

### 所有页面都支持
- ✅ 桌面端（PC）
- ✅ 平板端
- ✅ 移动端

### 适配要点
- 首页：产品展示区在移动端换行
- 功能选择：卡片在移动端变为单列
- 编辑页：保持原有的响应式布局

---

## 🎨 颜色方案

保持原有的设计系统：

- **主色调**：`text-primary` (青色 #00D9FF)
- **辅助色**：`text-accent` (橙色)
- **背景色**：
  - `bg-dark` - 主背景
  - `bg-dark-card` - 卡片背景
  - `bg-dark-border` - 边框

---

## 🚀 使用方法

### 启动项目

1. 确保后端和 Worker 正在运行
2. 启动前端：
   ```bash
   cd frontend
   npm run dev
   ```
3. 访问 http://localhost:5173

### 测试流程

1. **测试首页**
   - 访问 http://localhost:5173/
   - 查看品牌展示
   - 点击"Get Started"

2. **测试功能选择**
   - 应该自动跳转到 /features
   - 点击三个功能卡片
   - 观察选中效果
   - 点击"开始创作"

3. **测试编辑页**
   - 应该跳转到 /editor?mode=XXX
   - 观察顶部模式标签是否正确
   - 上传图片并生成

---

## 📝 开发注意事项

### 如果要修改首页
编辑：`frontend/src/pages/LandingPage.tsx`

### 如果要修改功能选择页
编辑：`frontend/src/pages/FeatureSelection.tsx`

### 如果要修改编辑页
编辑：`frontend/src/pages/Editor.tsx`

### 添加新页面
1. 在 `frontend/src/pages/` 创建新文件
2. 在 `frontend/src/App.tsx` 添加路由

---

## 🎯 后续优化建议

### 首页
- [ ] 添加真实的服装展示图片（替换占位符）
- [ ] 添加视频演示
- [ ] 添加用户评价
- [ ] 添加案例展示

### 功能选择页
- [ ] 添加每个功能的示例图片
- [ ] 添加功能对比表格
- [ ] 添加价格信息（如需要）

### 编辑页
- [ ] 添加历史记录
- [ ] 添加收藏功能
- [ ] 添加分享功能
- [ ] 添加下载功能

---

## 🆘 常见问题

### Q: 首页显示空白？
A: 确保前端服务正在运行，刷新浏览器（Ctrl + F5）

### Q: 功能选择页跳转失败？
A: 检查路由配置，确保 `/features` 路径正确

### Q: 编辑页没有自动切换模式？
A: 检查 URL 是否包含 `?mode=XXX` 参数

### Q: 样式显示不正常？
A: 确保 Tailwind CSS 正常工作，重启前端服务

---

## 📚 相关文档

- **API 文档**：`frontend/API_SDK_GUIDE.md`
- **启动指南**：`README.md`
- **设计规范**：`fronted_style_guide.md`

---

**新设计已完成！** 🎉

现在你有了一个完整的三页面流程，用户体验更加清晰流畅。

