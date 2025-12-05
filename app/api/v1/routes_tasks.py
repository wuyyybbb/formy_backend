"""
任务相关路由
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from app.schemas.task import (
    TaskCreateRequest,
    TaskInfo,
    TaskListResponse,
    TaskStatus
)
from app.services.tasks.manager import TaskService
from app.services.billing import billing_service
from app.services.auth.auth_service import get_current_user_id
from app.api.v1.routes_auth import get_current_user
from app.config.credits_cost import calculate_task_credits
from app.models.user import User

router = APIRouter()

# 全局任务服务实例
_task_service: Optional[TaskService] = None


def get_task_service() -> TaskService:
    """获取任务服务实例（单例）"""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service


@router.post("/tasks", response_model=TaskInfo)
async def create_task(
    request: TaskCreateRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    创建新任务（需要登录）
    
    流程：
    1. 检查用户算力是否足够
    2. 预扣除算力
    3. 创建任务
    4. 如果创建失败，返还算力
    
    Args:
        request: 任务创建请求
        current_user_id: 当前用户ID（从 token 获取）
        
    Returns:
        TaskInfo: 任务信息
        
    Raises:
        402: 算力不足
        500: 创建失败
    """
    try:
        # 1. 计算所需算力
        required_credits = calculate_task_credits(
            mode=request.mode,
            quality=getattr(request.config, 'quality', 'standard') if request.config else 'standard',
            size=getattr(request.config, 'size', 'medium') if request.config else 'medium'
        )
        
        print(f"用户 {current_user_id} 创建任务，需要 {required_credits} 算力")
        
        # 2. 检查用户算力
        user_billing = billing_service.get_user_billing_info(current_user_id)
        if not user_billing:
            raise HTTPException(
                status_code=404,
                detail="用户信息不存在，请先登录"
            )
        
        if user_billing.current_credits < required_credits:
            raise HTTPException(
                status_code=402,  # Payment Required
                detail={
                    "error": "CREDIT_NOT_ENOUGH",
                    "message": f"算力不足。需要 {required_credits} 算力，当前剩余 {user_billing.current_credits} 算力",
                    "required": required_credits,
                    "current": user_billing.current_credits,
                    "deficit": required_credits - user_billing.current_credits
                }
            )
        
        # 3. 预扣除算力
        consume_success = billing_service.consume_credits(current_user_id, required_credits)
        if not consume_success:
            raise HTTPException(
                status_code=500,
                detail="算力扣除失败"
            )
        
        print(f"✓ 算力扣除成功，剩余 {user_billing.current_credits - required_credits} 算力")
        
        # 4. 创建任务 - 传递 user_id 和消耗的积分
        task_service = get_task_service()
        task_info = task_service.create_task(
            request, 
            user_id=current_user_id,
            credits_consumed=required_credits
        )
        
        # 在任务信息中记录消耗的算力（可选）
        task_info.credits_consumed = required_credits
        
        print(f"✓ Task created successfully: {task_info.task_id}, Credits: {required_credits}")
        
        return task_info
        
    except HTTPException:
        # 如果是 HTTP 异常，直接抛出
        raise
    except Exception as e:
        # 其他异常，尝试返还算力
        print(f"❌ 创建任务失败: {e}")
        
        # 如果已经扣除了算力，尝试返还
        try:
            if 'required_credits' in locals() and 'consume_success' in locals() and consume_success:
                billing_service.add_credits(current_user_id, required_credits)
                print(f"✓ 算力已返还")
        except:
            pass
        
        raise HTTPException(
            status_code=500,
            detail=f"创建任务失败: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=TaskInfo)
async def get_task(
    task_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    获取任务详情（需要登录，只能访问自己的任务）
    
    Args:
        task_id: 任务ID
        current_user_id: 当前用户ID（从 token 获取）
        
    Returns:
        TaskInfo: 任务信息
        
    Raises:
        404: 任务不存在
        403: 无权访问该任务（不属于当前用户）
    """
    task_service = get_task_service()
    task_info = task_service.get_task(task_id)
    
    if not task_info:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )
    
    # 检查任务是否属于当前用户
    # 从任务数据中获取 user_id
    task_data = task_service.queue.get_task_data(task_id)
    if task_data:
        # 注意：任务数据保存在 "data" 字段中，不是 "input"
        input_data = task_data.get("data", {})
        if isinstance(input_data, str):
            import json
            input_data = json.loads(input_data)
        
        task_user_id = input_data.get("user_id")
        
        # 如果任务有 user_id，检查权限
        if task_user_id is not None:
            if task_user_id != current_user_id:
                print(f"⚠️  权限检查失败: 任务 {task_id} 属于用户 {task_user_id}, 当前用户 {current_user_id}")
                raise HTTPException(
                    status_code=403,
                    detail="无权访问该任务"
                )
        else:
            # 旧任务没有 user_id，向后兼容：允许访问
            print(f"ℹ️  旧任务（无 user_id）: {task_id}, 允许访问（向后兼容）")
    else:
        # task_data 不存在，但 task_info 存在，可能是旧数据格式
        # 为了安全，仍然允许访问（向后兼容）
        print(f"ℹ️  任务数据不存在: {task_id}, 但任务信息存在，允许访问（向后兼容）")
    
    return task_info


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(None, description="状态筛选"),
    mode: Optional[str] = Query(None, description="模式筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    获取任务列表（需要登录，只返回当前用户的任务）
    
    Args:
        status: 状态筛选
        mode: 模式筛选
        page: 页码
        page_size: 每页数量
        current_user_id: 当前用户ID（从 token 获取）
        
    Returns:
        TaskListResponse: 任务列表（仅当前用户的任务）
    """
    try:
        task_service = get_task_service()
        tasks = task_service.get_task_list(
            user_id=current_user_id,  # 只返回当前用户的任务
            status_filter=status,
            mode_filter=mode,
            page=page,
            page_size=page_size
        )
        
        # 将 TaskSummary 转换为 TaskInfo（简化版）
        task_infos = []
        for task_summary in tasks:
            # 获取完整任务信息
            full_task = task_service.get_task(task_summary.task_id)
            if full_task:
                task_infos.append(full_task)
        
        return TaskListResponse(
            tasks=task_infos,
            pagination={
                "page": page,
                "page_size": page_size,
                "total": len(task_infos)
            }
        )
        
    except Exception as e:
        print(f"获取任务列表失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.get("/tasks/history", response_model=TaskListResponse)
async def get_task_history(
    mode: Optional[str] = Query(None, description="任务模式筛选（HEAD_SWAP/BACKGROUND_CHANGE/POSE_CHANGE）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user)
):
    """
    获取任务历史记录（需要登录，只返回当前用户的任务）
    
    返回的任务信息包含输入图字段（source_image, reference_image），
    方便前端点击历史时恢复输入图片。
    
    Args:
        mode: 任务模式筛选（可选）
        page: 页码
        page_size: 每页数量
        current_user: 当前用户（从 token 获取）
        
    Returns:
        TaskListResponse: 任务列表（包含输入图字段）
    """
    try:
        task_service = get_task_service()
        user_id = current_user.user_id
        
        # 获取任务列表（只返回当前用户的任务）
        tasks = task_service.get_task_list(
            user_id=user_id,
            status_filter=None,  # 历史记录不筛选状态
            mode_filter=mode,
            page=page,
            page_size=page_size
        )
        
        # 将 TaskSummary 转换为 TaskInfo（包含完整的输入图信息）
        task_infos = []
        for task_summary in tasks:
            # 获取完整任务信息（包含 source_image, reference_image）
            full_task = task_service.get_task(task_summary.task_id)
            if full_task:
                # 确保输入图字段存在
                # TaskInfo 已经包含了 source_image 和 reference_image
                task_infos.append(full_task)
        
        return TaskListResponse(
            tasks=task_infos,
            pagination={
                "page": page,
                "page_size": page_size,
                "total": len(task_infos)
            }
        )
        
    except Exception as e:
        print(f"获取任务历史失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"获取任务历史失败: {str(e)}"
        )


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    取消任务（需要登录，只能取消自己的任务）
    
    Args:
        task_id: 任务ID
        current_user_id: 当前用户ID（从 token 获取）
        
    Returns:
        dict: 操作结果
        
    Raises:
        404: 任务不存在
        403: 无权取消该任务（不属于当前用户）
    """
    try:
        task_service = get_task_service()
        
        # 检查任务是否属于当前用户
        task_data = task_service.queue.get_task_data(task_id)
        if not task_data:
            raise HTTPException(
                status_code=404,
                detail=f"任务不存在: {task_id}"
            )
        
        # 注意：任务数据保存在 "data" 字段中，不是 "input"
        input_data = task_data.get("data", {})
        if isinstance(input_data, str):
            import json
            input_data = json.loads(input_data)
        
        task_user_id = input_data.get("user_id")
        
        # 如果任务有 user_id，检查权限
        if task_user_id is not None:
            if task_user_id != current_user_id:
                print(f"⚠️  取消任务权限检查失败: 任务 {task_id} 属于用户 {task_user_id}, 当前用户 {current_user_id}")
                raise HTTPException(
                    status_code=403,
                    detail="无权取消该任务"
                )
        else:
            # 旧任务没有 user_id，向后兼容：允许取消
            print(f"ℹ️  取消旧任务（无 user_id）: {task_id}, 允许取消（向后兼容）")
        
        success = task_service.cancel_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"任务无法取消: {task_id}"
            )
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "任务已取消"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"取消任务失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"取消任务失败: {str(e)}"
        )

