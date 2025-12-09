"""
任务 CRUD 操作（使用 asyncpg 连接 Supabase PostgreSQL）
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncpg
from app.db import get_pool
from app.schemas.task import TaskStatus, EditMode, TaskInfo, TaskResult, TaskError


async def create_task(
    task_id: str,
    user_id: str,
    mode: str,
    source_image: str,
    reference_image: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    credits_consumed: Optional[int] = None
) -> TaskInfo:
    """
    创建新任务
    
    Args:
        task_id: 任务ID
        user_id: 用户ID
        mode: 编辑模式（HEAD_SWAP/BACKGROUND_CHANGE/POSE_CHANGE）
        source_image: 源图片 file_id
        reference_image: 参考图片 file_id（可选）
        config: 配置参数（可选）
        credits_consumed: 消耗的算力（可选）
        
    Returns:
        TaskInfo: 创建的任务对象
        
    Raises:
        Exception: 数据库连接错误或任务已存在
    """
    pool = get_pool()
    if not pool:
        raise Exception("数据库连接池未初始化")
    
    now = datetime.utcnow()
    
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO tasks (
                task_id,
                user_id,
                status,
                mode,
                progress,
                source_image,
                reference_image,
                config,
                credits_consumed,
                created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
            )
            """,
            task_id,
            user_id,
            TaskStatus.PENDING.value,
            mode,
            0,  # progress
            source_image,
            reference_image,
            json.dumps(config, default=str) if config else None,
            credits_consumed,
            now
        )
    
    # 返回创建的任务对象
    return TaskInfo(
        task_id=task_id,
        status=TaskStatus.PENDING,
        mode=EditMode(mode),
        progress=0,
        source_image=source_image,
        reference_image=reference_image,
        config=config or {},
        credits_consumed=credits_consumed,
        created_at=now
    )


async def get_task_by_id(task_id: str) -> Optional[TaskInfo]:
    """
    根据任务ID获取任务详情
    
    Args:
        task_id: 任务ID
        
    Returns:
        Optional[TaskInfo]: 任务对象，如果不存在则返回 None
        
    Raises:
        Exception: 数据库连接错误
    """
    pool = get_pool()
    if not pool:
        raise Exception("数据库连接池未初始化")
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 
                task_id,
                user_id,
                status,
                mode,
                progress,
                current_step,
                source_image,
                reference_image,
                config,
                result,
                error,
                credits_consumed,
                created_at,
                updated_at,
                completed_at,
                failed_at,
                processing_time
            FROM tasks
            WHERE task_id = $1
            """,
            task_id
        )
        
        if not row:
            return None
        
        # 将数据库行转换为 TaskInfo 对象
        return _row_to_task_info(row)


async def get_tasks_by_user(
    user_id: str,
    status_filter: Optional[str] = None,
    mode_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> List[TaskInfo]:
    """
    获取用户的任务列表（按创建时间倒序）
    
    Args:
        user_id: 用户ID
        status_filter: 状态筛选（可选）
        mode_filter: 模式筛选（可选）
        page: 页码（从1开始）
        page_size: 每页数量
        
    Returns:
        List[TaskInfo]: 任务列表
        
    Raises:
        Exception: 数据库连接错误
    """
    pool = get_pool()
    if not pool:
        raise Exception("数据库连接池未初始化")
    
    # 构建查询条件
    conditions = ["user_id = $1"]
    params = [user_id]
    param_idx = 2
    
    if status_filter:
        conditions.append(f"status = ${param_idx}")
        params.append(status_filter)
        param_idx += 1
    
    if mode_filter:
        conditions.append(f"mode = ${param_idx}")
        params.append(mode_filter)
        param_idx += 1
    
    where_clause = " AND ".join(conditions)
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT 
                task_id,
                user_id,
                status,
                mode,
                progress,
                current_step,
                source_image,
                reference_image,
                config,
                result,
                error,
                credits_consumed,
                created_at,
                updated_at,
                completed_at,
                failed_at,
                processing_time
            FROM tasks
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """,
            *params,
            page_size,
            offset
        )
        
        # 将数据库行转换为 TaskInfo 对象
        return [_row_to_task_info(row) for row in rows]


async def update_task_status(
    task_id: str,
    status: str,
    progress: Optional[int] = None,
    current_step: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[Dict[str, Any]] = None,
    processing_time: Optional[float] = None
) -> bool:
    """
    更新任务状态
    
    Args:
        task_id: 任务ID
        status: 新状态
        progress: 进度（可选）
        current_step: 当前步骤（可选）
        result: 结果数据（可选）
        error: 错误信息（可选）
        processing_time: 处理耗时（可选）
        
    Returns:
        bool: 是否成功
        
    Raises:
        Exception: 数据库连接错误
    """
    pool = get_pool()
    if not pool:
        raise Exception("数据库连接池未初始化")
    
    now = datetime.utcnow()
    
    # 构建更新字段
    update_fields = ["status = $2", "updated_at = $3"]
    params = [task_id, status, now]
    param_idx = 4
    
    if progress is not None:
        update_fields.append(f"progress = ${param_idx}")
        params.append(progress)
        param_idx += 1
    
    if current_step is not None:
        update_fields.append(f"current_step = ${param_idx}")
        params.append(current_step)
        param_idx += 1
    
    if result is not None:
        update_fields.append(f"result = ${param_idx}")
        params.append(json.dumps(result, default=str))
        param_idx += 1
    
    if error is not None:
        update_fields.append(f"error = ${param_idx}")
        params.append(json.dumps(error, default=str))
        param_idx += 1
    
    if processing_time is not None:
        update_fields.append(f"processing_time = ${param_idx}")
        params.append(processing_time)
        param_idx += 1
    
    # 根据状态设置时间戳
    if status == TaskStatus.DONE.value:
        update_fields.append(f"completed_at = ${param_idx}")
        params.append(now)
        param_idx += 1
    elif status == TaskStatus.FAILED.value:
        update_fields.append(f"failed_at = ${param_idx}")
        params.append(now)
        param_idx += 1
    
    set_clause = ", ".join(update_fields)
    
    async with pool.acquire() as conn:
        result = await conn.execute(
            f"""
            UPDATE tasks
            SET {set_clause}
            WHERE task_id = $1
            """,
            *params
        )
        
        # 检查是否有行被更新
        return result == "UPDATE 1"


async def delete_task(task_id: str) -> bool:
    """
    删除任务（物理删除）
    
    Args:
        task_id: 任务ID
        
    Returns:
        bool: 是否成功
        
    Raises:
        Exception: 数据库连接错误
    """
    pool = get_pool()
    if not pool:
        raise Exception("数据库连接池未初始化")
    
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM tasks
            WHERE task_id = $1
            """,
            task_id
        )
        
        # 检查是否有行被删除
        return result == "DELETE 1"


async def count_tasks_by_user(
    user_id: str,
    status_filter: Optional[str] = None,
    mode_filter: Optional[str] = None
) -> int:
    """
    统计用户的任务数量
    
    Args:
        user_id: 用户ID
        status_filter: 状态筛选（可选）
        mode_filter: 模式筛选（可选）
        
    Returns:
        int: 任务数量
        
    Raises:
        Exception: 数据库连接错误
    """
    pool = get_pool()
    if not pool:
        raise Exception("数据库连接池未初始化")
    
    # 构建查询条件
    conditions = ["user_id = $1"]
    params = [user_id]
    param_idx = 2
    
    if status_filter:
        conditions.append(f"status = ${param_idx}")
        params.append(status_filter)
        param_idx += 1
    
    if mode_filter:
        conditions.append(f"mode = ${param_idx}")
        params.append(mode_filter)
        param_idx += 1
    
    where_clause = " AND ".join(conditions)
    
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            f"""
            SELECT COUNT(*)
            FROM tasks
            WHERE {where_clause}
            """,
            *params
        )
        
        return count or 0


def _row_to_task_info(row: asyncpg.Record) -> TaskInfo:
    """
    将数据库行转换为 TaskInfo 对象
    
    Args:
        row: 数据库行记录
        
    Returns:
        TaskInfo: 任务对象
    """
    # 解析 config（JSON）
    config = {}
    if row['config']:
        if isinstance(row['config'], str):
            config = json.loads(row['config'])
        else:
            config = row['config']
    
    # 解析 result（JSON）
    result = None
    if row['result']:
        result_data = row['result']
        if isinstance(result_data, str):
            result_data = json.loads(result_data)
        result = TaskResult(**result_data)
    
    # 解析 error（JSON）
    error = None
    if row['error']:
        error_data = row['error']
        if isinstance(error_data, str):
            error_data = json.loads(error_data)
        error = TaskError(**error_data)
    
    # 构建 TaskInfo
    return TaskInfo(
        task_id=row['task_id'],
        status=TaskStatus(row['status']),
        mode=EditMode(row['mode']),
        progress=row['progress'],
        current_step=row['current_step'],
        source_image=row['source_image'],
        reference_image=row['reference_image'],
        config=config,
        result=result,
        error=error,
        credits_consumed=row['credits_consumed'],
        created_at=row['created_at'],
        updated_at=row['updated_at'],
        completed_at=row['completed_at'],
        failed_at=row['failed_at'],
        processing_time=row['processing_time']
    )

