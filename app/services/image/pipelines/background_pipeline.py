"""
换背景 Pipeline
负责 AI 换背景的完整流程
"""
from typing import Optional
from pathlib import Path

from app.services.image.pipelines.base import PipelineBase
from app.services.image.dto import EditTaskInput, EditTaskResult, BackgroundChangeConfig
from app.services.image.enums import ProcessingStep
from app.services.image.engines.registry import get_engine_registry
from app.services.image.image_assets import resolve_uploaded_file, copy_image_to_results
from app.core.config import settings
from app.core.error_codes import TaskErrorCode


class BackgroundPipeline(PipelineBase):
    """换背景 Pipeline"""
    
    def __init__(self):
        """初始化换背景 Pipeline"""
        super().__init__()
        # 获取 Engine 注册表
        self.engine_registry = get_engine_registry()
        # 获取换背景 Engine（优先使用 RunningHub）
        self.runninghub_engine = self.engine_registry.get_engine_for_step("background_change", "background_change")
        if not self.runninghub_engine:
            # 如果配置中没有，尝试直接获取 RunningHub Engine
            self.runninghub_engine = self.engine_registry.get_engine("runninghub_background_change")
        if not self.runninghub_engine:
            raise ValueError("换背景引擎未配置，请在 engine_config.yml 中配置 runninghub_background_change")
    
    def execute(self, task_input: EditTaskInput) -> EditTaskResult:
        """
        执行换背景流程
        
        Args:
            task_input: 任务输入
            
        Returns:
            EditTaskResult: 任务结果
        """
        self._start_timer()
        self.progress_callback = task_input.progress_callback
        
        try:
            # 1. 验证输入
            if not self.validate_input(task_input):
                return self._create_error_result(
                    "输入参数验证失败",
                    error_code=TaskErrorCode.INVALID_REQUEST.value
                )
            
            # 2. 解析配置
            config = self._parse_config(task_input.config)
            
            # 3. 执行换背景流程
            result = self._run_background_change_workflow(
                task_input.task_id,
                task_input.source_image,
                config
            )
            
            return result
            
        except Exception as e:
            self._log_step(ProcessingStep.COMPLETE, f"执行失败: {e}")
            return self._create_error_result(
                str(e),
                error_code=TaskErrorCode.PIPELINE_ERROR.value
            )
    
    def validate_input(self, task_input: EditTaskInput) -> bool:
        """
        验证输入参数
        
        Args:
            task_input: 任务输入
            
        Returns:
            bool: 是否有效
        """
        # 检查源图片是否存在
        try:
            source_path = resolve_uploaded_file(task_input.source_image)
            if not source_path.exists():
                self._log_step(ProcessingStep.LOAD_IMAGE, f"源图片不存在: {task_input.source_image}")
                return False
        except Exception as e:
            self._log_step(ProcessingStep.LOAD_IMAGE, f"无法解析源图片: {e}")
            return False
        
        # 检查配置中是否有背景图
        config = task_input.config or {}
        bg_image_id = config.get("bg_image") or config.get("background_image")
        if not bg_image_id:
            self._log_step(ProcessingStep.LOAD_IMAGE, "缺少背景图片")
            return False
        
        # 检查背景图是否存在
        try:
            bg_path = resolve_uploaded_file(bg_image_id)
            if not bg_path.exists():
                self._log_step(ProcessingStep.LOAD_IMAGE, f"背景图片不存在: {bg_image_id}")
                return False
        except Exception as e:
            self._log_step(ProcessingStep.LOAD_IMAGE, f"无法解析背景图片: {e}")
            return False
        
        # 检查 Engine 是否可用
        if not self.runninghub_engine:
            self._log_step(ProcessingStep.COMPLETE, "换背景 Engine 未配置（需要 RunningHub）")
            return False
        
        return True
    
    def _parse_config(self, config: dict) -> BackgroundChangeConfig:
        """
        解析配置
        
        Args:
            config: 配置字典
            
        Returns:
            BackgroundChangeConfig: 配置对象
        """
        # 从配置中提取背景图
        bg_image_id = config.get("bg_image") or config.get("background_image")
        
        return BackgroundChangeConfig(
            background_image=bg_image_id,
            background_type=config.get("background_type", "custom")
        )
    
    def _run_background_change_workflow(
        self,
        task_id: str,
        source_image: str,
        config: BackgroundChangeConfig
    ) -> EditTaskResult:
        """
        运行换背景工作流
        
        Args:
            task_id: 任务ID
            source_image: 原始图片 file_id（模特图片）
            config: 换背景配置
            
        Returns:
            EditTaskResult: 结果
        """
        # Step 1: 解析图片路径 (10%)
        self._update_progress(10, "正在加载图片...")
        self._log_step(ProcessingStep.LOAD_IMAGE, f"加载原始图片: {source_image}")
        
        try:
            model_image_path = resolve_uploaded_file(source_image)
            bg_image_path = resolve_uploaded_file(config.background_image)
            
            # 🔍 详细日志：确认图片路径
            print(f"[BackgroundPipeline] 🔍 输入参数:")
            print(f"  - source_image (file_id): {source_image}")
            print(f"  - background_image (file_id): {config.background_image}")
            print(f"[BackgroundPipeline] 🔍 解析后的本地路径:")
            print(f"  - model_image_path: {model_image_path}")
            print(f"  - bg_image_path: {bg_image_path}")
            
            # 验证文件是否存在
            import os
            if not os.path.exists(model_image_path):
                print(f"[BackgroundPipeline] ❌ 模特图片不存在: {model_image_path}")
            else:
                print(f"[BackgroundPipeline] ✅ 模特图片存在，大小: {os.path.getsize(model_image_path)} bytes")
            
            if not os.path.exists(bg_image_path):
                print(f"[BackgroundPipeline] ❌ 背景图片不存在: {bg_image_path}")
            else:
                print(f"[BackgroundPipeline] ✅ 背景图片存在，大小: {os.path.getsize(bg_image_path)} bytes")
                
        except Exception as e:
            return self._create_error_result(
                f"加载图片失败: {e}",
                error_code=TaskErrorCode.IMAGE_LOAD_FAILED.value
            )
        
        # Step 2: 调用 RunningHub Engine (30%)
        self._update_progress(30, "正在调用 AI 引擎...")
        self._log_step(ProcessingStep.APPLY_BACKGROUND, "开始换背景处理")
        
        try:
            # 准备输入数据（换背景工作流使用 model_image 和 bg_image）
            input_data = {
                "model_image": str(model_image_path),  # 模特图片
                "bg_image": str(bg_image_path)  # 输入背景图片
            }
            
            print(f"[BackgroundPipeline] 🔍 传递给 RunningHub Engine 的输入数据:")
            print(f"  - model_image: {input_data['model_image']}")
            print(f"  - bg_image: {input_data['bg_image']}")
            
            # 执行工作流
            result = self.runninghub_engine.execute(input_data)
            
        except Exception as e:
            # 打印详细错误信息
            import traceback
            error_trace = traceback.format_exc()
            self._log_step(ProcessingStep.COMPLETE, f"AI 引擎执行失败: {e}")
            print(f"[BackgroundPipeline] 详细错误信息:\n{error_trace}")
            
            # 根据异常类型选择错误码
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                error_code = TaskErrorCode.COMFYUI_CONNECTION_TIMEOUT
            elif "connection" in error_msg:
                error_code = TaskErrorCode.COMFYUI_NOT_AVAILABLE
            else:
                error_code = TaskErrorCode.COMFYUI_PROCESSING_FAILED
            
            return self._create_error_result(
                f"换背景处理失败: {e}",
                error_code=error_code.value
            )
        
        # Step 3: 下载并保存结果图片 (80%)
        self._update_progress(80, "正在保存结果...")
        self._log_step(ProcessingStep.COMPLETE, "保存结果图片")
        
        try:
            # 下载输出图片
            output_image_info = result.get("output_image")
            comparison_image_info = result.get("comparison_image")
            
            if not output_image_info:
                return self._create_error_result(
                    "未获取到输出图片",
                    error_code=TaskErrorCode.COMFYUI_RESULT_NOT_FOUND.value
                )
            
            # 下载输出图片
            output_url = output_image_info.get("url")
            if not output_url:
                return self._create_error_result(
                    "输出图片 URL 为空",
                    error_code=TaskErrorCode.COMFYUI_RESULT_NOT_FOUND.value
                )
            
            # 下载图片到本地
            import requests
            import io
            from app.utils.image_io import save_image, create_thumbnail
            from PIL import Image
            
            response = requests.get(output_url, timeout=60)
            response.raise_for_status()
            
            # 保存输出图片
            output_filename = f"{task_id}_output.jpg"
            output_path = Path(settings.RESULT_DIR) / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 从响应中读取图片并保存
            output_img = Image.open(io.BytesIO(response.content))
            save_image(output_img, str(output_path), format="JPEG", quality=95)
            
            # 下载对比图片（如果有）
            comparison_path = None
            comparison_filename = None
            if comparison_image_info:
                self._log_step(ProcessingStep.COMPLETE, f"找到对比图信息: {comparison_image_info}")
                comparison_url = comparison_image_info.get("url")
                if comparison_url:
                    try:
                        self._log_step(ProcessingStep.COMPLETE, f"开始下载对比图: {comparison_url}")
                        comp_response = requests.get(comparison_url, timeout=60)
                        comp_response.raise_for_status()
                        comparison_filename = f"{task_id}_comparison.jpg"
                        comparison_path = Path(settings.RESULT_DIR) / comparison_filename
                        comp_img = Image.open(io.BytesIO(comp_response.content))
                        save_image(comp_img, str(comparison_path), format="JPEG", quality=95)
                        self._log_step(ProcessingStep.COMPLETE, f"对比图已保存: /results/{comparison_filename}")
                    except Exception as e:
                        self._log_step(ProcessingStep.COMPLETE, f"下载对比图片失败: {e}")
            else:
                self._log_step(ProcessingStep.COMPLETE, "未找到对比图信息")
            
            # 生成缩略图
            thumbnail_path = None
            try:
                thumbnail = create_thumbnail(output_img, (256, 256))
                thumbnail_filename = f"{task_id}_thumb.jpg"
                thumbnail_path_obj = Path(settings.RESULT_DIR) / thumbnail_filename
                save_image(thumbnail, str(thumbnail_path_obj), format="JPEG", quality=85)
                thumbnail_path = f"/results/{thumbnail_filename}"
            except Exception as e:
                self._log_step(ProcessingStep.COMPLETE, f"生成缩略图失败: {e}")
            
            # Step 4: 完成 (100%)
            self._update_progress(100, "处理完成")
            
            return self._create_success_result(
                output_image=f"/results/{output_filename}",
                thumbnail=thumbnail_path,
                comparison_image=f"/results/{comparison_filename}" if comparison_filename else None,
                metadata={
                    "width": output_img.width,
                    "height": output_img.height,
                    "background_type": config.background_type
                }
            )
            
        except Exception as e:
            self._log_step(ProcessingStep.COMPLETE, f"保存结果失败: {e}")
            return self._create_error_result(
                f"保存结果失败: {e}",
                error_code=TaskErrorCode.COMFYUI_RESULT_NOT_FOUND.value
            )
    

