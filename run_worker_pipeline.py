"""
Pipeline Worker - 调用真实的 Pipeline 处理任务
用于生产环境，执行实际的 AI 处理
"""
import time
import signal
import sys
from typing import Optional
from pathlib import Path

from app.services.tasks.queue import get_task_queue
from app.services.tasks.manager import get_task_service
from app.schemas.task import EditMode
from app.services.image.pipelines.pose_change_pipeline import PoseChangePipeline
from app.services.image.dto import EditTaskInput


class PipelineWorker:
    """Pipeline Worker 类 - 调用真实 Pipeline"""
    
    def __init__(self):
        """初始化 Worker"""
        self.queue = get_task_queue()
        self.task_service = get_task_service()
        self.is_running = False
        self._setup_signal_handlers()
        
        # 初始化 Pipelines
        self.pose_pipeline = PoseChangePipeline()
        
        print("[Worker] Pipeline Worker 初始化完成")
    
    def _setup_signal_handlers(self):
        """设置信号处理器（优雅关闭）"""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """处理关闭信号"""
        print("\n[Worker] 接收到关闭信号，正在停止...")
        self.is_running = False
    
    def start(self):
        """启动 Worker 循环"""
        print("[Worker] Pipeline Worker 已启动，等待任务...")
        print("[Worker] 将调用真实的 ComfyUI Pipeline 处理任务")
        print("[Worker] 按 Ctrl+C 停止\n")
        
        self.is_running = True
        
        while self.is_running:
            try:
                # 从队列中获取任务（阻塞式，超时 5 秒）
                task_id = self.queue.pop_task(timeout=5)
                
                if task_id:
                    print(f"\n{'='*60}")
                    print(f"[Worker] 📥 获取到任务: {task_id}")
                    print(f"{'='*60}")
                    
                    # 立即标记任务为处理中
                    try:
                        self.queue.update_task_status(
                            task_id=task_id,
                            status="processing",
                            progress=0,
                            current_step="Worker 已接收任务，正在初始化..."
                        )
                        print(f"[Worker] ✅ 任务状态已更新为 processing")
                    except Exception as e:
                        print(f"[Worker] ⚠️  更新任务状态失败: {e}")
                    
                    # 处理任务
                    self._process_task(task_id)
                else:
                    # 超时未获取到任务，继续循环
                    continue
                    
            except Exception as e:
                # 检查是否是 Redis 超时错误（队列空闲）
                error_msg = str(e).lower()
                if 'timeout' in error_msg or 'reading from socket' in error_msg:
                    # 这只是队列暂时没有任务，不是真正的错误
                    # 静默处理，继续等待
                    time.sleep(1)
                    continue
                
                # 其他异常才是真正的错误
                print(f"[Worker] ❌ Worker 循环出错: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)
        
        print("[Worker] Pipeline Worker 已停止")
    
    def _process_task(self, task_id: str):
        """
        处理单个任务
        
        Args:
            task_id: 任务ID
        """
        try:
            # 1. 获取任务数据
            print(f"[Worker] 📋 正在获取任务数据...")
            task_data = self.queue.get_task_data(task_id)
            
            if not task_data:
                error_msg = f"任务数据不存在: {task_id}"
                print(f"[Worker] ❌ {error_msg}")
                self.task_service.fail_task(
                    task_id=task_id,
                    error_code="TASK_DATA_NOT_FOUND",
                    error_message="无法获取任务数据",
                    error_details=f"任务 {task_id} 在 Redis 中不存在"
                )
                return
            
            # 2. 解析任务信息
            input_data = task_data.get("data", {})
            mode = input_data.get("mode")
            source_image = input_data.get("source_image")
            config = input_data.get("config", {})
            
            print(f"[Worker] 📌 任务模式: {mode}")
            print(f"[Worker] 🖼️  原始图片: {source_image}")
            print(f"[Worker] ⚙️  配置: {config}")
            
            # 3. 验证必要参数
            if not mode:
                self.task_service.fail_task(
                    task_id=task_id,
                    error_code="INVALID_MODE",
                    error_message="任务模式 (mode) 缺失",
                    error_details="请求中未指定编辑模式"
                )
                print(f"[Worker] ❌ 任务模式缺失")
                return
            
            if not source_image:
                self.task_service.fail_task(
                    task_id=task_id,
                    error_code="INVALID_SOURCE_IMAGE",
                    error_message="原始图片 (source_image) 缺失",
                    error_details="请求中未指定原始图片路径"
                )
                print(f"[Worker] ❌ 原始图片缺失")
                return
            
            # 4. 更新状态为处理中（第二次更新，带更详细的信息）
            self.task_service.update_task_progress(
                task_id=task_id,
                progress=5,
                current_step=f"正在准备 {mode} 处理..."
            )
            
            # 5. 根据模式分发到对应的 Pipeline
            print(f"[Worker] 🚀 开始处理任务...")
            result = self._dispatch_to_pipeline(
                task_id=task_id,
                mode=mode,
                source_image=source_image,
                config=config
            )
            
            # 6. 标记任务完成或失败
            if result:
                self.task_service.complete_task(task_id, result)
                print(f"[Worker] ✅ 任务完成: {task_id}")
                print(f"[Worker] 📸 输出图片: {result.get('output_image')}")
                if result.get('comparison_image'):
                    print(f"[Worker] 🔀 对比图片: {result.get('comparison_image')}")
            else:
                self.task_service.fail_task(
                    task_id=task_id,
                    error_code="PROCESSING_FAILED",
                    error_message="Pipeline 处理失败",
                    error_details=f"模式 {mode} 的处理流程返回了空结果"
                )
                print(f"[Worker] ❌ 任务失败: {task_id} - Pipeline 返回空结果")
                
        except Exception as e:
            print(f"[Worker] ❌ 处理任务异常: {task_id}")
            print(f"[Worker] 💥 错误类型: {type(e).__name__}")
            print(f"[Worker] 📝 错误信息: {e}")
            import traceback
            error_traceback = traceback.format_exc()
            print(error_traceback)
            
            # 标记任务失败，包含详细的错误信息
            try:
                self.task_service.fail_task(
                    task_id=task_id,
                    error_code="INTERNAL_ERROR",
                    error_message=f"任务处理异常: {type(e).__name__}",
                    error_details=f"{str(e)}\n\n堆栈跟踪:\n{error_traceback}"
                )
            except Exception as fail_error:
                print(f"[Worker] ⚠️  无法标记任务失败: {fail_error}")
    
    def _dispatch_to_pipeline(
        self,
        task_id: str,
        mode: str,
        source_image: str,
        config: dict
    ) -> Optional[dict]:
        """
        分发任务到对应的 Pipeline
        
        Args:
            task_id: 任务ID
            mode: 编辑模式
            source_image: 原始图片
            config: 配置参数
            
        Returns:
            Optional[dict]: 处理结果（包含 output_image, thumbnail, metadata）
        """
        try:
            print(f"[Worker] 分发任务到 Pipeline - 模式: {mode}")
            
            # 根据模式调用对应的 Pipeline
            if mode == EditMode.POSE_CHANGE.value:
                return self._process_pose_change(task_id, source_image, config)
            elif mode == EditMode.HEAD_SWAP.value:
                print(f"[Worker] ⚠️  换头功能尚未实现，使用模拟处理")
                return self._process_mock(task_id, source_image, config)
            elif mode == EditMode.BACKGROUND_CHANGE.value:
                print(f"[Worker] ⚠️  换背景功能尚未实现，使用模拟处理")
                return self._process_mock(task_id, source_image, config)
            else:
                print(f"[Worker] ❌ 不支持的编辑模式: {mode}")
                return None
                
        except Exception as e:
            print(f"[Worker] ❌ Pipeline 处理失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _process_pose_change(
        self, 
        task_id: str, 
        source_image: str, 
        config: dict
    ) -> Optional[dict]:
        """
        处理换姿势任务（调用真实 Pipeline）
        
        Args:
            task_id: 任务ID
            source_image: 原始图片
            config: 配置参数
            
        Returns:
            Optional[dict]: 处理结果
        """
        print(f"[Worker] 🎨 开始执行换姿势 Pipeline...")
        
        try:
            # 构建 Pipeline 输入
            from app.schemas.image import PoseChangeConfig
            
            # 进度回调函数
            def progress_callback(progress: int, message: str):
                try:
                    self.task_service.update_task_progress(task_id, progress, message)
                    print(f"[Worker] 📊 进度: {progress}% - {message}")
                except Exception as e:
                    print(f"[Worker] ⚠️  更新进度失败: {e}")
            
            # 更新进度
            progress_callback(10, "正在准备 Pipeline 输入...")
            
            # 构建输入对象
            task_input = EditTaskInput(
                task_id=task_id,
                source_image=source_image,
                mode=EditMode.POSE_CHANGE,
                config=config,
                progress_callback=progress_callback
            )
            
            print(f"[Worker] 📦 Pipeline 输入已准备完成")
            progress_callback(15, "正在调用 ComfyUI Pipeline...")
            
            # 执行 Pipeline
            result = self.pose_pipeline.execute(task_input)
            
            # 检查结果
            if result.success:
                print(f"[Worker] ✅ Pipeline 执行成功")
                print(f"[Worker] 📸 输出图片: {result.output_image}")
                print(f"[Worker] 🖼️  缩略图: {result.thumbnail}")
                if result.comparison_image:
                    print(f"[Worker] 🔀 对比图: {result.comparison_image}")
                
                return {
                    "output_image": result.output_image,
                    "thumbnail": result.thumbnail,
                    "comparison_image": result.comparison_image,
                    "metadata": result.metadata
                }
            else:
                print(f"[Worker] ❌ Pipeline 执行失败")
                print(f"[Worker] 🔴 错误码: {result.error_code}")
                print(f"[Worker] 📝 错误信息: {result.error_message}")
                
                # 将 Pipeline 错误传递到任务状态
                self.task_service.fail_task(
                    task_id=task_id,
                    error_code=result.error_code or "PIPELINE_ERROR",
                    error_message=result.error_message or "Pipeline 执行失败",
                    error_details=f"Pipeline 返回失败结果。可能的原因：\n"
                                 f"- ComfyUI 服务不可用\n"
                                 f"- 图片格式不正确\n"
                                 f"- 配置参数错误"
                )
                return None
                
        except Exception as e:
            print(f"[Worker] ❌ Pipeline 执行异常")
            print(f"[Worker] 💥 异常类型: {type(e).__name__}")
            print(f"[Worker] 📝 异常信息: {e}")
            import traceback
            error_trace = traceback.format_exc()
            print(error_trace)
            
            # 记录详细错误
            self.task_service.fail_task(
                task_id=task_id,
                error_code="PIPELINE_EXCEPTION",
                error_message=f"Pipeline 执行异常: {type(e).__name__}",
                error_details=f"{str(e)}\n\n堆栈:\n{error_trace}"
            )
            return None
    
    def _process_mock(
        self, 
        task_id: str, 
        source_image: str, 
        config: dict
    ) -> Optional[dict]:
        """
        模拟处理（用于未实现的功能）
        
        Args:
            task_id: 任务ID
            source_image: 原始图片
            config: 配置参数
            
        Returns:
            Optional[dict]: 模拟结果
        """
        from app.services.image.image_assets import resolve_uploaded_file, copy_image_to_results
        
        print(f"[Worker] 使用模拟处理...")
        
        try:
            source_path = resolve_uploaded_file(source_image)
            output_file = copy_image_to_results(
                source_path, f"{task_id}_output{source_path.suffix.lower() or '.jpg'}"
            )
            
            return {
                "output_image": f"/results/{output_file.name}",
                "thumbnail": f"/results/{output_file.name}",
                "metadata": {
                    "width": 0,
                    "height": 0,
                    "format": "jpeg",
                    "mock": True
                }
            }
        except Exception as e:
            print(f"[Worker] 模拟处理失败: {e}")
            return None


def run_pipeline_worker():
    """运行 Pipeline Worker（入口函数）"""
    print("="*60)
    print("Formy Pipeline Worker")
    print("="*60)
    print("此 Worker 会调用真实的 Pipeline 处理任务")
    print("包括 ComfyUI 工作流调用")
    print("="*60)
    
    # 检查 Redis 连接
    queue = get_task_queue()
    if not queue.health_check():
        print("[错误] 无法连接到 Redis，请检查配置")
        sys.exit(1)
    
    print("[成功] Redis 连接正常")
    
    # 启动 Worker
    worker = PipelineWorker()
    worker.start()


if __name__ == "__main__":
    run_pipeline_worker()

