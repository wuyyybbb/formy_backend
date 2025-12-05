"""
任务相关的数据传输对象（DTO）
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 待处理（已入队）
    PROCESSING = "processing"    # 处理中
    DONE = "done"               # 完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消


class EditMode(str, Enum):
    """编辑模式枚举"""
    HEAD_SWAP = "HEAD_SWAP"                    # 换头
    BACKGROUND_CHANGE = "BACKGROUND_CHANGE"    # 换背景
    POSE_CHANGE = "POSE_CHANGE"                # 换姿势


class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    mode: EditMode = Field(..., description="编辑模式")
    source_image: str = Field(..., description="原始图片 file_id")
    config: Dict[str, Any] = Field(default_factory=dict, description="模式相关配置参数")


class TaskResult(BaseModel):
    """任务结果"""
    output_image: Optional[str] = Field(None, description="输出图片路径")
    thumbnail: Optional[str] = Field(None, description="缩略图路径")
    comparison_image: Optional[str] = Field(None, description="对比图路径")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class TaskError(BaseModel):
    """任务错误信息"""
    code: str = Field(..., description="错误码")
    message: str = Field(..., description="错误信息")
    details: Optional[str] = Field(None, description="详细错误描述")


class TaskInfo(BaseModel):
    """任务信息"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    mode: EditMode = Field(..., description="编辑模式")
    progress: int = Field(0, ge=0, le=100, description="进度百分比")
    current_step: Optional[str] = Field(None, description="当前步骤描述")
    
    # 输入信息
    source_image: str = Field(..., description="原始图片 file_id")
    reference_image: Optional[str] = Field(None, description="参考图片 file_id（换头/换背景/换姿势）")
    config: Dict[str, Any] = Field(default_factory=dict, description="配置参数")
    
    # 结果信息
    result: Optional[TaskResult] = Field(None, description="任务结果")
    error: Optional[TaskError] = Field(None, description="错误信息")
    
    # 算力信息
    credits_consumed: Optional[int] = Field(None, description="消耗的算力")
    
    # 时间信息
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    failed_at: Optional[datetime] = Field(None, description="失败时间")
    processing_time: Optional[float] = Field(None, description="处理耗时（秒）")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: list[TaskInfo] = Field(default_factory=list, description="任务列表")
    pagination: Optional[Dict[str, Any]] = Field(None, description="分页信息")


class TaskSummary(BaseModel):
    """任务摘要（列表显示用）"""
    task_id: str
    status: TaskStatus
    mode: EditMode
    thumbnail: Optional[str] = None
    progress: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

