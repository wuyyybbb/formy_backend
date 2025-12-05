"""
图像处理相关的数据传输对象
"""
from typing import Optional, Dict, Any, Callable
from pydantic import BaseModel, Field

from app.services.image.enums import EditMode, ImageQuality


class EditTaskInput(BaseModel):
    """图像编辑任务输入"""
    task_id: str = Field(..., description="任务ID")
    mode: EditMode = Field(..., description="编辑模式")
    source_image: str = Field(..., description="原始图片路径")
    config: Dict[str, Any] = Field(default_factory=dict, description="配置参数")
    
    # 进度回调（运行时传入，不序列化）
    progress_callback: Optional[Callable[[int, str], None]] = Field(
        None, 
        description="进度回调函数",
        exclude=True
    )


class HeadSwapConfig(BaseModel):
    """换头配置"""
    reference_image: str = Field(..., description="参考头像图片路径")
    quality: ImageQuality = Field(ImageQuality.HIGH, description="质量等级")
    preserve_details: bool = Field(True, description="保留细节")
    blend_strength: float = Field(0.8, ge=0.0, le=1.0, description="融合强度")


class BackgroundChangeConfig(BaseModel):
    """换背景配置"""
    background_type: str = Field(default="custom", description="背景类型: custom/preset/remove")
    background_image: Optional[str] = Field(None, description="自定义背景图片路径")
    background_preset: Optional[str] = Field(None, description="预设背景名称")
    edge_blur: int = Field(2, ge=0, le=10, description="边缘羽化程度")
    color_match: bool = Field(True, description="颜色匹配")


class PoseChangeConfig(BaseModel):
    """换姿势配置"""
    target_pose: Optional[str] = Field(None, description="目标姿势（预设）")
    pose_reference: Optional[str] = Field(None, description="姿势参考图片路径")
    preserve_face: bool = Field(True, description="保持面部不变")
    smoothness: float = Field(0.7, ge=0.0, le=1.0, description="平滑度")


class EditTaskResult(BaseModel):
    """图像编辑任务结果"""
    success: bool = Field(..., description="是否成功")
    output_image: Optional[str] = Field(None, description="输出图片路径")
    thumbnail: Optional[str] = Field(None, description="缩略图路径")
    comparison_image: Optional[str] = Field(None, description="对比图路径")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    error_code: Optional[str] = Field(None, description="错误码")
    error_message: Optional[str] = Field(None, description="错误信息")
    processing_time: Optional[float] = Field(None, description="处理耗时（秒）")


class IntermediateResult(BaseModel):
    """中间结果（Pipeline 步骤间传递）"""
    image_data: Optional[Any] = Field(None, description="图像数据")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    step_name: Optional[str] = Field(None, description="步骤名称")

