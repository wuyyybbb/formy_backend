"""
任务管理服务
提供任务创建、查询、取消等业务逻辑
"""
import json
import asyncio
from typing import Optional, List
from datetime import datetime

from app.schemas.task import (
    TaskStatus, 
    EditMode, 
    TaskCreateRequest, 
    TaskInfo,
    TaskResult,
    TaskError,
    TaskSummary
)
from app.services.tasks.queue import get_task_queue
from app.utils.id_generator import generate_task_id
from app.db import crud_tasks


class TaskService:
    """任务管理服务类"""
    
    def __init__(self):
        """初始化任务服务"""
        self.queue = get_task_queue()
    
    async def create_task(
        self, 
        request: TaskCreateRequest,
        user_id: Optional[str] = None,
        credits_consumed: Optional[int] = None
    ) -> TaskInfo:
        """
        创建新任务
        
        Args:
            request: 任务创建请求
            user_id: 用户ID（用于失败退款）
            credits_consumed: 消耗的积分（用于失败退款）
            
        Returns:
            TaskInfo: 任务信息
        """
        # 1. 生成任务ID
        task_id = generate_task_id()
        
        # 2. 构建任务数据
        # 从 config 中提取 reference_image（不同模式使用不同字段名）
        reference_image = None
        if request.mode == EditMode.HEAD_SWAP:
            # 换头：使用 reference_image, target_face_image, 或 cloth_image
            reference_image = (request.config.get("reference_image") or 
                             request.config.get("target_face_image") or 
                             request.config.get("cloth_image"))
        elif request.mode == EditMode.BACKGROUND_CHANGE:
            # 换背景：使用 background_image 或 bg_image
            reference_image = (request.config.get("background_image") or 
                             request.config.get("bg_image"))
        elif request.mode == EditMode.POSE_CHANGE:
            # 换姿势：使用 pose_reference 或 pose_image
            reference_image = (request.config.get("pose_reference") or 
                             request.config.get("pose_image"))
        
        # 3. 写入数据库（持久化存储）
        task_info = await crud_tasks.create_task(
            task_id=task_id,
            user_id=user_id,
            mode=request.mode.value,
            source_image=request.source_image,
            reference_image=reference_image,
            config=request.config,
            credits_consumed=credits_consumed
        )
        
        # 4. 推入 Redis 队列（用于 worker 处理）
        task_data = {
            "mode": request.mode.value,
            "source_image": request.source_image,
            "reference_image": reference_image,
            "config": request.config,
            "user_id": user_id,
            "credits_consumed": credits_consumed
        }
        
        success = self.queue.push_task(task_id, task_data)
        
        if not success:
            raise Exception("Failed to create task: cannot push to queue")
        
        # 5. 返回任务信息
        return task_info
    
    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """
        获取任务详情
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskInfo]: 任务信息，不存在返回 None
        """
        # 从数据库获取任务数据
        task_info = await crud_tasks.get_task_by_id(task_id)
        return task_info
    
    async def get_task_list(
        self, 
        user_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        mode_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[TaskSummary]:
        """
        获取任务列表
        
        Args:
            user_id: 用户ID（必需，用于过滤任务）
            status_filter: 状态筛选
            mode_filter: 模式筛选
            page: 页码
            page_size: 每页数量
            
        Returns:
            List[TaskSummary]: 任务摘要列表
        """
        if not user_id:
            raise ValueError("user_id 是必需的，用于过滤任务")
        
        # 从数据库获取任务列表
        task_infos = await crud_tasks.get_tasks_by_user(
            user_id=user_id,
            status_filter=status_filter,
            mode_filter=mode_filter,
            page=page,
            page_size=page_size
        )
        
        # 转换为任务摘要
        tasks = []
        for task_info in task_infos:
            tasks.append(TaskSummary(
                task_id=task_info.task_id,
                status=task_info.status,
                mode=task_info.mode,
                thumbnail=task_info.result.thumbnail if task_info.result else None,
                progress=task_info.progress,
                created_at=task_info.created_at,
                completed_at=task_info.completed_at
            ))
        
        return tasks
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        # 更新数据库状态为已取消
        success = await crud_tasks.update_task_status(
            task_id=task_id,
            status=TaskStatus.CANCELLED.value
        )
        
        # 同时更新 Redis（用于兼容性）
        self.queue.cancel_task(task_id)
        
        return success
    
    async def update_task_progress(
        self, 
        task_id: str, 
        progress: int,
        current_step: Optional[str] = None
    ) -> bool:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比（0-100）
            current_step: 当前步骤描述
            
        Returns:
            bool: 是否成功
        """
        # 更新数据库
        success = await crud_tasks.update_task_status(
            task_id=task_id,
            status=TaskStatus.PROCESSING.value,
            progress=progress,
            current_step=current_step
        )
        
        # 同时更新 Redis（用于兼容性，可选）
        self.queue.update_task_status(
            task_id=task_id,
            status="processing",
            progress=progress,
            current_step=current_step
        )
        
        return success
    
    async def complete_task(
        self, 
        task_id: str, 
        result: dict
    ) -> bool:
        """
        标记任务完成（异步版本）
        
        Args:
            task_id: 任务ID
            result: 结果数据（包含 output_image, thumbnail, metadata）
            
        Returns:
            bool: 是否成功
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 更新数据库
                print(f"[TaskService] 📝 开始标记任务为完成: {task_id}（尝试 {attempt + 1}/{max_retries}）")
                success = await crud_tasks.update_task_status(
                    task_id=task_id,
                    status=TaskStatus.DONE.value,
                    progress=100,
                    result=result
                )
                print(f"[TaskService] 📊 update_task_status 返回值: {success}")
                
                # 同时更新 Redis（用于兼容性，可选）
                try:
                    self.queue.update_task_status(
                        task_id=task_id,
                        status="done",
                        progress=100,
                        result=result
                    )
                except Exception as redis_error:
                    print(f"[TaskService] ⚠️  更新 Redis 失败: {redis_error}")
                    # Redis 失败不影响主流程
                
                print(f"[TaskService] {'✅' if success else '❌'} 任务完成标记: {success}")
                return success
                
            except Exception as e:
                error_msg = str(e).lower()
                is_connection_error = any(keyword in error_msg for keyword in [
                    'connection', 'reset', 'closed', 'timeout', 'pool'
                ])
                
                if is_connection_error and attempt < max_retries - 1:
                    import asyncio
                    wait_time = (attempt + 1) * 2  # 2, 4, 6 秒
                    print(f"[TaskService] ⚠️  数据库连接错误，{wait_time}秒后重试（{attempt + 1}/{max_retries}）: {e}")
                    await asyncio.sleep(wait_time)
                    
                    # 尝试重新初始化数据库连接
                    try:
                        from app.db import connect_to_db
                        await connect_to_db()
                        print(f"[TaskService] ✅ 数据库连接已重新建立")
                    except Exception as reconnect_error:
                        print(f"[TaskService] ❌ 重新连接失败: {reconnect_error}")
                    continue
                else:
                    print(f"[TaskService] ❌ 标记任务完成失败（最终失败）: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
        
        return False
    
    async def fail_task(
        self, 
        task_id: str,
        user_id: Optional[str] = None,
        credits_consumed: Optional[int] = None,
        error_code: str = "UNKNOWN_ERROR",
        error_message: str = "未知错误",
        error_details: Optional[str] = None
    ) -> bool:
        """
        标记任务失败（异步版本）
        
        Args:
            task_id: 任务ID
            user_id: 用户ID（用于退款）
            credits_consumed: 消耗的积分（用于退款）
            error_code: 错误码
            error_message: 错误信息
            error_details: 错误详情
            
        Returns:
            bool: 是否成功
        """
        # 🔒 先执行退款（在重试循环外，防止重复退款）
        refund_success = False
        if user_id and credits_consumed:
            try:
                refund_success = await self._refund_credits_async(task_id, user_id, credits_consumed)
                if not refund_success:
                    print(f"[TaskService] ⚠️  退款失败，但继续更新任务状态")
            except Exception as refund_error:
                print(f"[TaskService] ❌ 退款异常: {refund_error}")
                # 退款失败不应阻止任务状态更新，继续执行
        
        # 更新任务状态（带重试）
        max_retries = 3
        for attempt in range(max_retries):
            try:
                error = {
                    "code": error_code,
                    "message": error_message,
                    "details": error_details
                }
                
                # 更新数据库（带重试）
                success = await crud_tasks.update_task_status(
                    task_id=task_id,
                    status=TaskStatus.FAILED.value,
                    error=error
                )
                
                # 同时更新 Redis（用于兼容性，可选）
                try:
                    self.queue.update_task_status(
                        task_id=task_id,
                        status="failed",
                        error=error
                    )
                except Exception as redis_error:
                    print(f"[TaskService] ⚠️  更新 Redis 失败: {redis_error}")
                    # Redis 失败不影响主流程
                
                print(f"[TaskService] ✅ 任务已标记为失败（尝试 {attempt + 1}/{max_retries}）")
                return success
                
            except Exception as e:
                error_msg = str(e).lower()
                is_connection_error = any(keyword in error_msg for keyword in [
                    'connection', 'reset', 'closed', 'timeout', 'pool'
                ])
                
                if is_connection_error and attempt < max_retries - 1:
                    import asyncio
                    wait_time = (attempt + 1) * 2  # 2, 4, 6 秒
                    print(f"[TaskService] ⚠️  数据库连接错误，{wait_time}秒后重试（{attempt + 1}/{max_retries}）: {e}")
                    await asyncio.sleep(wait_time)
                    
                    # 尝试重新初始化数据库连接
                    try:
                        from app.db import connect_to_db
                        await connect_to_db()
                        print(f"[TaskService] ✅ 数据库连接已重新建立")
                    except Exception as reconnect_error:
                        print(f"[TaskService] ❌ 重新连接失败: {reconnect_error}")
                    continue
                else:
                    print(f"[TaskService] ❌ 标记任务失败时出错（最终失败）: {e}")
                    import traceback
                    traceback.print_exc()
                    # 不再抛出异常，避免 Worker 崩溃
                    return False
        
        return False
    
    async def _refund_credits_async(self, task_id: str, user_id: str, credits: int) -> bool:
        """
        异步退款功能
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            credits: 退款积分数
            
        Returns:
            bool: 是否成功
        """
        try:
            from app.services.billing import billing_service
            success = billing_service.add_credits(user_id, credits)
            
            if success:
                print(f"[TaskService] ✅ 已为用户 {user_id} 退款 {credits} 积分（任务 {task_id} 失败）")
            else:
                print(f"[TaskService] ❌ 为用户 {user_id} 退款 {credits} 积分失败")
            
            return success
        except Exception as e:
            print(f"[TaskService] ❌ 退款异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def refund_credits_for_failed_task(self, task_id: str) -> bool:
        """
        Refund credits for a failed task
        
        Policy: Full refund for all failed tasks
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功退款
        """
        try:
            # Get task data from database
            task_info = asyncio.run(crud_tasks.get_task_by_id(task_id))
            if not task_info:
                print(f"[Refund] Task {task_id} not found, cannot refund")
                return False
            
            # Get user_id and credits_consumed from task info
            # Note: We need to get user_id from database
            # For now, try to get from Redis for backward compatibility
            task_data = self.queue.get_task_data(task_id)
            if task_data:
                input_data = task_data.get("data", {})
                if isinstance(input_data, str):
                    import json
                    input_data = json.loads(input_data)
                user_id = input_data.get("user_id")
            else:
                # If Redis data not available, we can't refund (need user_id)
                print(f"[Refund] Task {task_id} missing user data in Redis")
                return False
            
            credits_consumed = task_info.credits_consumed
            
            if not user_id or not credits_consumed:
                print(f"[Refund] Task {task_id} missing user_id or credits_consumed")
                return False
            
            # Refund credits
            from app.services.billing import billing_service
            success = billing_service.add_credits(user_id, credits_consumed)
            
            if success:
                print(f"[Refund] ✓ Refunded {credits_consumed} credits to user {user_id} for failed task {task_id}")
            else:
                print(f"[Refund] ✗ Failed to refund credits for task {task_id}")
            
            return success
            
        except Exception as e:
            print(f"[Refund] Error refunding credits for task {task_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_queue_stats(self) -> dict:
        """
        获取队列统计信息
        
        Returns:
            dict: 统计信息
        """
        return {
            "pending": self.queue.get_queue_length(),
            "processing": self.queue.get_processing_count(),
            "total_tasks": len(self.queue.get_all_task_ids())
        }
    
    def _parse_task_info(self, task_data: dict) -> TaskInfo:
        """
        解析任务数据为 TaskInfo 对象
        
        Args:
            task_data: Redis 中存储的任务数据
            
        Returns:
            TaskInfo: 任务信息对象
        """
        # 解析任务输入数据
        input_data = task_data.get("data", {})
        if isinstance(input_data, str):
            input_data = json.loads(input_data)
        
        # 解析结果数据
        result = None
        if "result" in task_data:
            result_data = task_data["result"]
            if isinstance(result_data, str):
                result_data = json.loads(result_data)
            result = TaskResult(**result_data)
        
        # 解析错误信息
        error = None
        if "error" in task_data:
            error_data = task_data["error"]
            if isinstance(error_data, str):
                error_data = json.loads(error_data)
            error = TaskError(**error_data)
        
        # 构建 TaskInfo
        return TaskInfo(
            task_id=task_data["task_id"],
            status=TaskStatus(task_data.get("status", "pending")),
            mode=EditMode(input_data.get("mode", "HEAD_SWAP")),
            progress=int(task_data.get("progress", 0)),
            current_step=task_data.get("current_step"),
            source_image=input_data.get("source_image", ""),
            reference_image=input_data.get("reference_image"),  # 添加参考图片
            config=input_data.get("config", {}),
            result=result,
            error=error,
            created_at=datetime.fromisoformat(task_data["created_at"]),
            updated_at=datetime.fromisoformat(task_data["updated_at"]) if "updated_at" in task_data else None,
            completed_at=datetime.fromisoformat(task_data["completed_at"]) if "completed_at" in task_data else None,
            failed_at=datetime.fromisoformat(task_data["failed_at"]) if "failed_at" in task_data else None
        )


# 全局服务实例（单例模式）
_task_service_instance: Optional[TaskService] = None


def get_task_service() -> TaskService:
    """获取任务服务实例（单例）"""
    global _task_service_instance
    if _task_service_instance is None:
        _task_service_instance = TaskService()
    return _task_service_instance

