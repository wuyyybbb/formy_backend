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
from app.schemas.task import EditMode, TaskStatus
from app.services.image.pipelines.pose_change_pipeline import PoseChangePipeline
from app.services.image.pipelines.head_swap_pipeline import HeadSwapPipeline
from app.services.image.pipelines.background_pipeline import BackgroundPipeline
from app.services.image.dto import EditTaskInput
from app.core.error_codes import TaskErrorCode, create_error


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
        self.head_swap_pipeline = HeadSwapPipeline()
        self.background_pipeline = BackgroundPipeline()
        
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
        print("[Worker] 会调用真实的 Pipeline 处理任务（RunningHub / ComfyUI）")
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
            # 获取任务数据（从队列获取原始数据）
            task_data = self.queue.get_task_data(task_id)
            
            if not task_data:
                print(f"[Worker] ❌ 任务不存在: {task_id}")
                return
            
            # 提取任务参数（任务数据保存在 "data" 字段中）
            input_data = task_data.get("data", {})
            mode = input_data.get("mode")
            source_image = input_data.get("source_image")
            config = input_data.get("config", {})
            
            print(f"[Worker] 📋 任务模式: {mode}")
            print(f"[Worker] 🖼️  原始图片: {source_image}")
            print(f"[Worker] ⚙️  配置: {config}")
            
            # 分发到对应的 Pipeline
            result = self._dispatch_to_pipeline(
                task_id=task_id,
                mode=mode,
                source_image=source_image,
                config=config
            )
            
            if result:
                # 标记任务完成
                print(f"[Worker] ✅ 任务处理完成")
                print(f"[Worker] 📸 输出图片: {result.get('output_image')}")
                print(f"[Worker] 📸 对比图: {result.get('comparison_image')}")
                print(f"[Worker] 📸 缩略图: {result.get('thumbnail')}")
                print(f"[Worker] 📋 完整结果: {result}")
                
                try:
                    success = self.task_service.complete_task(
                        task_id=task_id,
                        result=result  # 传入完整的 result 字典
                    )
                    print(f"[Worker] ✅ 任务状态已更新为 completed, 结果: {success}")
                except Exception as e:
                    print(f"[Worker] ❌ 更新任务状态失败: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
            else:
                # Pipeline 返回 None，表示失败（错误已在 Pipeline 中记录）
                print(f"[Worker] ❌ 任务处理失败")
                
                # 如果任务状态还不是 failed，标记为失败
                task_info = self.task_service.get_task(task_id)
                if task_info and task_info.status != TaskStatus.FAILED:
                    self.task_service.fail_task(
                        task_id=task_id,
                        error_code="PIPELINE_ERROR",
                        error_message="Pipeline 处理失败",
                        error_details="Pipeline 返回空结果"
                    )
                
                print(f"[Worker] 任务失败: {task_id}")
                
        except Exception as e:
            print(f"[Worker] 处理任务异常: {task_id}, 错误: {e}")
            
            # 标记任务失败
            self.task_service.fail_task(
                task_id=task_id,
                error_code="INTERNAL_ERROR",
                error_message="任务处理过程中发生异常",
                error_details=str(e)
            )
    
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
                return self._process_head_swap(task_id, source_image, config)
            elif mode == EditMode.BACKGROUND_CHANGE.value:
                return self._process_background_change(task_id, source_image, config)
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
        """处理换姿势任务（调用真实 Pipeline）"""
        print(f"[Worker] 🎨 开始执行换姿势 Pipeline...")
        
        try:
            # 进度回调函数
            def progress_callback(progress: int, message: str):
                try:
                    self.task_service.update_task_progress(task_id, progress, message)
                    print(f"[Worker] 📊 进度: {progress}% - {message}")
                except Exception as e:
                    print(f"[Worker] ⚠️  更新进度失败: {e}")
            
            # 构建输入对象
            task_input = EditTaskInput(
                task_id=task_id,
                source_image=source_image,
                mode=EditMode.POSE_CHANGE,
                config=config,
                progress_callback=progress_callback
            )
            
            # 执行 Pipeline
            result = self.pose_pipeline.execute(task_input)
            
            # 检查结果
            if result.success:
                return {
                    "output_image": result.output_image,
                    "thumbnail": result.thumbnail,
                    "comparison_image": result.comparison_image,
                    "metadata": result.metadata
                }
            else:
                return None
                
        except Exception as e:
            print(f"[Worker] ❌ Pipeline 执行异常: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _process_head_swap(
        self, 
        task_id: str, 
        source_image: str, 
        config: dict
    ) -> Optional[dict]:
        """处理换头任务（调用真实 Pipeline）"""
        print(f"[Worker] 🎭 开始执行换头 Pipeline...")
        
        try:
            # 进度回调函数
            def progress_callback(progress: int, message: str):
                try:
                    self.task_service.update_task_progress(task_id, progress, message)
                    print(f"[Worker] 📊 进度: {progress}% - {message}")
                except Exception as e:
                    print(f"[Worker] ⚠️  更新进度失败: {e}")
            
            # 构建输入对象
            task_input = EditTaskInput(
                task_id=task_id,
                source_image=source_image,
                mode=EditMode.HEAD_SWAP,
                config=config,
                progress_callback=progress_callback
            )
            
            # 执行 Pipeline
            result = self.head_swap_pipeline.execute(task_input)
            
            # 检查结果
            if result.success:
                return {
                    "output_image": result.output_image,
                    "thumbnail": result.thumbnail,
                    "comparison_image": result.comparison_image,
                    "metadata": result.metadata
                }
            else:
                return None
                
        except Exception as e:
            print(f"[Worker] ❌ Pipeline 执行异常: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _process_background_change(
        self, 
        task_id: str, 
        source_image: str, 
        config: dict
    ) -> Optional[dict]:
        """处理换背景任务（调用真实 Pipeline）"""
        print(f"[Worker] 🌄 开始执行换背景 Pipeline...")
        
        try:
            # 进度回调函数
            def progress_callback(progress: int, message: str):
                try:
                    self.task_service.update_task_progress(task_id, progress, message)
                    print(f"[Worker] 📊 进度: {progress}% - {message}")
                except Exception as e:
                    print(f"[Worker] ⚠️  更新进度失败: {e}")
            
            # 构建输入对象
            task_input = EditTaskInput(
                task_id=task_id,
                source_image=source_image,
                mode=EditMode.BACKGROUND_CHANGE,
                config=config,
                progress_callback=progress_callback
            )
            
            # 执行 Pipeline
            result = self.background_pipeline.execute(task_input)
            
            print(f"[Worker] 🔍 Pipeline 返回结果: success={result.success}")
            print(f"[Worker] 🔍 result.output_image: {result.output_image}")
            print(f"[Worker] 🔍 result.comparison_image: {result.comparison_image}")
            
            # 检查结果
            if result.success:
                return {
                    "output_image": result.output_image,
                    "thumbnail": result.thumbnail,
                    "comparison_image": result.comparison_image,
                    "metadata": result.metadata
                }
            else:
                print(f"[Worker] ❌ Pipeline 返回失败: {result.error_message}")
                return None
                
        except Exception as e:
            print(f"[Worker] ❌ Pipeline 执行异常: {e}")
            import traceback
            traceback.print_exc()
            return None


def run_pipeline_worker():
    """运行 Pipeline Worker（入口函数）"""
    print("="*60)
    print("Formy Pipeline Worker")
    print("="*60)
    
    worker = PipelineWorker()
    worker.start()


if __name__ == "__main__":
    run_pipeline_worker()

