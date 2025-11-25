# 算力扣减与 AI 任务集成说明

## ✅ 完成内容

已实现算力扣减功能，让套餐与 AI 任务调用真正关联起来。用户的套餐算力会直接限制他们能调用多少次 AI 功能。

---

## 📁 文件结构

```
backend/
├── app/
│   ├── config/
│   │   └── credits_cost.py          # 算力消耗配置
│   ├── schemas/
│   │   └── task.py                  # TaskInfo 添加 credits_consumed 字段
│   └── api/v1/
│       └── routes_tasks.py          # 任务创建添加算力检查和扣除
└── test_credits_integration.py      # 算力扣减集成测试
```

---

## 🎯 核心实现

### 1. 算力消耗配置（`backend/app/config/credits_cost.py`）

定义不同任务类型和配置下的算力消耗：

#### 基础算力消耗（按模式）

| 模式 | 算力消耗 | 说明 |
|------|---------|------|
| **HEAD_SWAP** | 40 | AI 换头 |
| **BACKGROUND_CHANGE** | 30 | AI 换背景 |
| **POSE_CHANGE** | 50 | AI 换姿势（最复杂） |

#### 质量加成（乘数）

| 质量 | 乘数 | 说明 |
|------|------|------|
| **standard** | 1.0x | 标准质量 |
| **high** | 1.5x | 高清 |
| **ultra** | 2.0x | 超高清 |

#### 尺寸加成（乘数）

| 尺寸 | 乘数 | 说明 |
|------|------|------|
| **small** | 1.0x | 小图 |
| **medium** | 1.2x | 中图 |
| **large** | 1.5x | 大图 |
| **xlarge** | 2.0x | 超大图 |

#### 算力计算公式

```
总算力 = 基础算力 × 质量乘数 × 尺寸乘数
```

**示例**：
- HEAD_SWAP + 标准 + 中图 = 40 × 1.0 × 1.2 = **48 算力**
- BACKGROUND_CHANGE + 高清 + 大图 = 30 × 1.5 × 1.5 = **68 算力**
- POSE_CHANGE + 超高清 + 超大图 = 50 × 2.0 × 2.0 = **200 算力**

---

### 2. 任务创建流程（`backend/app/api/v1/routes_tasks.py`）

更新了 `POST /api/v1/tasks` 接口，添加算力检查和扣除逻辑：

#### 流程图

```
用户请求创建任务
       ↓
验证用户登录（token）
       ↓
计算所需算力
       ↓
检查用户算力是否足够
       ↓
   [足够？]
   ↙     ↘
 是        否
 ↓         ↓
预扣算力   返回 402 错误
 ↓         (CREDIT_NOT_ENOUGH)
创建任务
 ↓
[成功？]
 ↙    ↘
是     否
↓      ↓
返回   返还算力
任务   返回 500 错误
```

#### 关键代码逻辑

```python
@router.post("/tasks", response_model=TaskInfo)
async def create_task(
    request: TaskCreateRequest,
    current_user_id: str = Depends(get_current_user_id)  # 需要登录
):
    # 1. 计算所需算力
    required_credits = calculate_task_credits(
        mode=request.mode,
        quality=request.config.get('quality', 'standard'),
        size=request.config.get('size', 'medium')
    )
    
    # 2. 检查算力是否足够
    user_billing = billing_service.get_user_billing_info(current_user_id)
    if user_billing.current_credits < required_credits:
        # 返回 402 错误
        raise HTTPException(status_code=402, detail={
            "error": "CREDIT_NOT_ENOUGH",
            "message": "算力不足",
            "required": required_credits,
            "current": user_billing.current_credits,
            "deficit": required_credits - user_billing.current_credits
        })
    
    # 3. 预扣除算力
    billing_service.consume_credits(current_user_id, required_credits)
    
    # 4. 创建任务
    task_info = task_service.create_task(request)
    task_info.credits_consumed = required_credits  # 记录消耗
    
    return task_info
```

---

### 3. 错误处理

#### 算力不足错误（402 Payment Required）

当用户算力不足时，返回详细错误信息：

```json
{
  "detail": {
    "error": "CREDIT_NOT_ENOUGH",
    "message": "算力不足。需要 48 算力，当前剩余 30 算力",
    "required": 48,
    "current": 30,
    "deficit": 18
  }
}
```

**前端可以根据这个错误**：
1. 显示算力不足提示
2. 引导用户升级套餐
3. 显示还需要多少算力（deficit）

---

## 📊 不同套餐的使用次数

假设使用标准配置（HEAD_SWAP + 标准 + 中图 = 48 算力/次）：

| 套餐 | 月度算力 | 标准任务次数 | 价格 |
|------|---------|-------------|------|
| **STARTER** | 2000 | ~41 次 | ¥49 |
| **BASIC** | 5000 | ~104 次 | ¥99 |
| **PRO** | 12000 | ~250 次 | ¥199 |
| **ULTIMATE** | 30000 | ~625 次 | ¥399 |

---

## 🧪 测试指南

### 方法 1: 自动化测试脚本（推荐）

```bash
cd backend
python test_credits_integration.py
```

**测试场景**：

#### 场景 1: 算力充足 → 任务创建成功
1. 切换到 PRO 套餐（12000 算力）
2. 创建 HEAD_SWAP 任务
3. ✅ 任务创建成功，算力被扣除

#### 场景 2: 算力不足 → 任务创建失败
1. 切换到 STARTER 套餐（2000 算力）
2. 消耗算力到只剩 30
3. 尝试创建任务（需要 48 算力）
4. ✅ 返回 402 错误，提示算力不足

#### 场景 3: 不同模式消耗不同算力
1. 切换到 ULTIMATE 套餐（30000 算力）
2. 分别创建 HEAD_SWAP、BACKGROUND_CHANGE、POSE_CHANGE
3. ✅ 每个任务消耗不同算力：48、36、60

---

### 方法 2: 手动测试

#### Step 1: 登录获取 token

```powershell
$email = "test@example.com"

# 发送验证码
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/send-code" -Method Post -Body (@{email=$email} | ConvertTo-Json) -ContentType "application/json"

# 登录
$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method Post -Body (@{email=$email;code="YOUR_CODE"} | ConvertTo-Json) -ContentType "application/json"
$token = $loginResponse.access_token
$headers = @{Authorization="Bearer $token"}
```

#### Step 2: 切换套餐

```powershell
# 切换到 PRO 套餐
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/billing/change_plan" -Method Post -Headers $headers -Body (@{plan_id="pro"} | ConvertTo-Json) -ContentType "application/json"
```

#### Step 3: 查看当前算力

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/billing/me" -Method Get -Headers $headers | ConvertTo-Json
```

#### Step 4: 创建任务（测试算力扣除）

```powershell
$taskData = @{
    mode = "HEAD_SWAP"
    source_image = "test_image_123"
    config = @{
        quality = "standard"
        size = "medium"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tasks" -Method Post -Headers $headers -Body $taskData -ContentType "application/json" | ConvertTo-Json
```

#### Step 5: 再次查看算力（应该减少了）

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/billing/me" -Method Get -Headers $headers | ConvertTo-Json
```

#### Step 6: 测试算力不足

```powershell
# 消耗大部分算力，只剩 30
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/billing/consume_credits?amount=11970" -Method Post -Headers $headers

# 尝试创建任务（需要 48，但只剩 30）
try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tasks" -Method Post -Headers $headers -Body $taskData -ContentType "application/json"
} catch {
    # 应该返回 402 错误
    $_.Exception.Response.StatusCode
    $_.ErrorDetails.Message | ConvertFrom-Json | ConvertTo-Json -Depth 10
}
```

---

## 🎨 前端集成建议

### 1. 创建任务前显示算力消耗

```typescript
// 计算任务所需算力（前端估算）
function estimateCredits(mode: string, quality: string, size: string): number {
  const baseCosts = {
    'HEAD_SWAP': 40,
    'BACKGROUND_CHANGE': 30,
    'POSE_CHANGE': 50
  }
  
  const qualityMult = {
    'standard': 1.0,
    'high': 1.5,
    'ultra': 2.0
  }
  
  const sizeMult = {
    'small': 1.0,
    'medium': 1.2,
    'large': 1.5,
    'xlarge': 2.0
  }
  
  const base = baseCosts[mode] || 40
  const qMult = qualityMult[quality] || 1.0
  const sMult = sizeMult[size] || 1.2
  
  return Math.floor(base * qMult * sMult)
}

// 在生成按钮上显示
<button
  onClick={handleGenerate}
  className="btn-primary"
>
  生成（消耗 {estimateCredits(mode, quality, size)} 算力）
</button>
```

### 2. 处理算力不足错误

```typescript
import { createTask } from '../api/tasks'
import { getMyBillingInfo, changePlan } from '../api/billing'

async function handleGenerate() {
  try {
    const task = await createTask({
      mode: currentMode,
      source_image: sourceImageId,
      config: { quality, size }
    })
    
    // 任务创建成功
    setTaskId(task.task_id)
    console.log(`消耗了 ${task.credits_consumed} 算力`)
    
  } catch (error) {
    if (error.response?.status === 402) {
      // 算力不足
      const detail = error.response.data.detail
      
      // 显示错误提示
      alert(`算力不足！\n需要: ${detail.required}\n当前: ${detail.current}\n还差: ${detail.deficit}`)
      
      // 引导用户升级套餐
      const upgrade = confirm('是否升级套餐？')
      if (upgrade) {
        navigate('/pricing')  // 跳转到价格页
      }
    } else {
      console.error('创建任务失败:', error)
    }
  }
}
```

### 3. 实时显示剩余算力

```typescript
import { useEffect, useState } from 'react'
import { getMyBillingInfo } from '../api/billing'

export function CreditsDisplay() {
  const [credits, setCredits] = useState(0)
  const [total, setTotal] = useState(0)
  
  useEffect(() => {
    // 获取算力信息
    getMyBillingInfo().then(data => {
      setCredits(data.current_credits)
      setTotal(data.monthly_credits)
    })
  }, [])
  
  const percentage = total > 0 ? (credits / total) * 100 : 0
  
  return (
    <div className="credits-display">
      <div className="flex justify-between mb-2">
        <span className="text-sm text-text-secondary">剩余算力</span>
        <span className="text-sm font-semibold text-primary">
          {credits} / {total}
        </span>
      </div>
      
      {/* 进度条 */}
      <div className="w-full bg-dark-border rounded-full h-2">
        <div
          className="bg-primary h-2 rounded-full transition-all"
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
      
      {/* 警告提示 */}
      {percentage < 20 && (
        <div className="text-xs text-accent mt-2">
          ⚠️ 算力即将用尽，建议升级套餐
        </div>
      )}
    </div>
  )
}
```

---

## 📋 算力消耗速查表

### 标准质量 + 中等尺寸（最常用）

| 模式 | 算力消耗 |
|------|---------|
| AI 换头 | 48 |
| AI 换背景 | 36 |
| AI 换姿势 | 60 |

### 高清质量 + 大尺寸

| 模式 | 算力消耗 |
|------|---------|
| AI 换头 | 90 |
| AI 换背景 | 68 |
| AI 换姿势 | 113 |

### 超高清 + 超大尺寸（最高配置）

| 模式 | 算力消耗 |
|------|---------|
| AI 换头 | 160 |
| AI 换背景 | 120 |
| AI 换姿势 | 200 |

---

## 🔧 未来扩展

### 1. 动态定价
根据市场情况动态调整算力消耗：
```python
# 从数据库或配置中心读取最新价格
def get_dynamic_credits_cost(mode: str) -> int:
    return db.query(PricingConfig).filter_by(mode=mode).first().cost
```

### 2. 算力包
允许用户购买额外算力包：
```python
class CreditPackage:
    package_id: str
    credits: int  # 额外算力
    price: int    # 价格
    expires_in: int  # 有效期（天）
```

### 3. 使用记录
详细记录每次算力消耗：
```python
class CreditUsageLog:
    log_id: str
    user_id: str
    task_id: str
    credits_consumed: int
    balance_before: int
    balance_after: int
    created_at: datetime
```

### 4. 算力预警
当算力低于阈值时发送通知：
```python
async def check_credit_alert(user_id: str):
    billing = billing_service.get_user_billing_info(user_id)
    if billing.credits_usage_percentage > 80:
        # 发送邮件或推送通知
        await send_alert_email(billing.email, "算力即将用尽")
```

---

## ✅ 验证清单

- [x] 创建算力消耗配置（`credits_cost.py`）
- [x] 定义基础算力消耗（按模式）
- [x] 定义质量和尺寸加成
- [x] 实现算力计算函数
- [x] 更新任务创建接口，添加用户认证
- [x] 添加算力检查逻辑
- [x] 添加算力预扣除逻辑
- [x] 实现算力不足错误处理（402）
- [x] 实现创建失败时算力返还
- [x] 在 TaskInfo 中添加 `credits_consumed` 字段
- [x] 创建集成测试脚本
- [x] 编写详细文档

---

## 🎉 完成！

算力扣减功能已成功集成！现在：

1. ✅ **套餐直接限制 AI 调用次数**
   - 用户算力不足时无法创建任务
   - 返回明确的错误信息

2. ✅ **不同任务消耗不同算力**
   - 换头（40）< 换背景（30）< 换姿势（50）
   - 支持质量和尺寸加成

3. ✅ **算力自动扣除**
   - 任务创建成功后自动扣除
   - 创建失败时自动返还

4. ✅ **完整的错误处理**
   - 402 错误码表示算力不足
   - 详细的错误信息包含缺口算力

**立即测试**：
```bash
cd backend
python test_credits_integration.py
```

套餐和 AI 调用已真正关联！💰✨

