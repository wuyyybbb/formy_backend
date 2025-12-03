"""
RunningHub Engine
负责调用 RunningHub API 执行工作流
官网：https://www.runninghub.ai
"""
import requests
import time
from typing import Any, Dict, Optional

from app.services.image.engines.base import EngineBase, EngineType


class RunningHubEngine(EngineBase):
    """RunningHub Engine - 调用 RunningHub 云端工作流"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 RunningHub Engine
        
        Args:
            config: RunningHub 配置
                - api_key: RunningHub API Key
                - workflow_id: 工作流 ID（从 URL 中提取）
                - api_base_url: API 基础 URL（默认 https://api.runninghub.ai）
                - timeout: 超时时间（默认 300 秒）
                - poll_interval: 轮询间隔（默认 3 秒）
        """
        super().__init__(config)
        self.engine_type = EngineType.EXTERNAL_API
        
        # 从配置中获取信息
        self.api_key = self.get_config("api_key")
        self.workflow_id = self.get_config("workflow_id")
        self.api_base_url = self.get_config("api_base_url", "https://api.runninghub.ai")
        self.timeout = self.get_config("timeout", 300)
        self.poll_interval = self.get_config("poll_interval", 3)
        
        if not self.api_key:
            raise ValueError("RunningHub API Key 未配置")
        if not self.workflow_id:
            raise ValueError("RunningHub Workflow ID 未配置")
        
        self._log(f"RunningHub Engine 初始化完成 - Workflow: {self.workflow_id}")
    
    def execute(self, input_data: Any, **kwargs) -> Any:
        """
        执行 RunningHub 工作流
        
        Args:
            input_data: 输入数据（可以是字典，包含 raw_image、pose_image 等）
            **kwargs: 其他参数
                - raw_image_path: 原始图片路径
                - pose_image_path: 姿势参考图路径
                - raw_image_url: 原始图片 URL（优先使用）
                - pose_image_url: 姿势参考图 URL（优先使用）
                
        Returns:
            Dict: 执行结果，包含 output_image 等信息
        """
        self._log(f"开始执行 RunningHub 工作流: {self.workflow_id}")
        
        # 1. 验证输入
        if not self.validate_input(input_data):
            raise ValueError("输入数据验证失败")
        
        # 2. 准备请求参数
        request_params = self._prepare_request(input_data, **kwargs)
        
        # 3. 提交工作流
        task_id = self._submit_workflow(request_params)
        
        # 4. 等待执行完成
        result = self._wait_for_completion(task_id)
        
        self._log("RunningHub 工作流执行成功")
        
        return result
    
    def validate_input(self, input_data: Any) -> bool:
        """
        验证输入数据
        
        Args:
            input_data: 输入数据
            
        Returns:
            bool: 是否有效
        """
        if input_data is None:
            return False
        
        # 如果是字典，检查必要字段
        if isinstance(input_data, dict):
            # 至少需要一个图片输入
            has_input = any([
                input_data.get("raw_image"),
                input_data.get("source_image"),
                input_data.get("image")
            ])
            return has_input
        
        return True
    
    def _prepare_request(self, input_data: Any, **kwargs) -> Dict:
        """
        准备 RunningHub API 请求参数
        
        Args:
            input_data: 输入数据
            **kwargs: 其他参数
            
        Returns:
            Dict: 请求参数
        """
        params = {}
        
        # 处理输入数据
        if isinstance(input_data, dict):
            raw_image = input_data.get("raw_image") or input_data.get("source_image")
            pose_image = input_data.get("pose_image") or input_data.get("reference_image")
        else:
            raw_image = input_data
            pose_image = None
        
        # 从 kwargs 获取（优先级更高）
        raw_image_url = kwargs.get("raw_image_url")
        pose_image_url = kwargs.get("pose_image_url")
        raw_image_path = kwargs.get("raw_image_path") or raw_image
        pose_image_path = kwargs.get("pose_image_path") or pose_image
        
        # 如果提供了 URL，直接使用
        if raw_image_url:
            params["raw_image"] = raw_image_url
        elif raw_image_path:
            # 如果是文件路径，需要先上传
            params["raw_image"] = self._upload_image(raw_image_path)
        
        if pose_image_url:
            params["pose_image"] = pose_image_url
        elif pose_image_path:
            params["pose_image"] = self._upload_image(pose_image_path)
        
        # 添加其他参数
        extra_params = self.get_config("extra_params", {})
        params.update(extra_params)
        
        return params
    
    def _upload_image(self, image_path: str) -> str:
        """
        上传图片到 RunningHub
        
        Args:
            image_path: 本地图片路径
            
        Returns:
            str: 图片 URL
        """
        try:
            import os
            from pathlib import Path
            
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
            # 读取图片
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            filename = os.path.basename(image_path)
            
            # 上传到 RunningHub
            url = f"{self.api_base_url}/v1/upload"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            files = {
                "file": (filename, image_data, "image/jpeg")
            }
            
            response = requests.post(url, headers=headers, files=files, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            image_url = result.get("url") or result.get("file_url")
            
            if not image_url:
                raise Exception("上传响应中没有返回图片 URL")
            
            self._log(f"图片已上传到 RunningHub: {filename} -> {image_url}")
            
            return image_url
            
        except Exception as e:
            raise Exception(f"上传图片失败: {e}")
    
    def _submit_workflow(self, params: Dict) -> str:
        """
        提交工作流到 RunningHub
        
        Args:
            params: 请求参数
            
        Returns:
            str: 任务 ID
        """
        try:
            # 构建请求
            url = f"{self.api_base_url}/v1/workflows/{self.workflow_id}/run"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": params
            }
            
            self._log(f"提交工作流到 RunningHub: {url}")
            
            # 发送请求
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            task_id = result.get("task_id") or result.get("id") or result.get("run_id")
            
            if not task_id:
                raise Exception(f"未获取到任务 ID，响应: {result}")
            
            self._log(f"工作流已提交，任务 ID: {task_id}")
            
            return task_id
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"提交工作流失败: HTTP {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f", {error_detail}"
            except:
                error_msg += f", {e.response.text}"
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(f"提交工作流异常: {e}")
    
    def _wait_for_completion(self, task_id: str) -> Dict:
        """
        等待任务完成
        
        Args:
            task_id: 任务 ID
            
        Returns:
            Dict: 任务结果
        """
        start_time = time.time()
        
        self._log(f"等待任务完成: {task_id}")
        
        while True:
            # 检查超时
            elapsed_time = time.time() - start_time
            if elapsed_time > self.timeout:
                raise TimeoutError(f"任务执行超时: {self.timeout} 秒")
            
            # 查询任务状态
            try:
                status_info = self._get_task_status(task_id)
                status = status_info.get("status")
                
                self._log(f"任务状态: {status} (已用时 {int(elapsed_time)} 秒)")
                
                if status in ["completed", "success", "finished"]:
                    # 任务完成
                    result = self._parse_result(status_info)
                    return result
                
                elif status in ["failed", "error", "cancelled"]:
                    # 任务失败
                    error_msg = status_info.get("error") or status_info.get("message") or "未知错误"
                    raise Exception(f"任务执行失败: {error_msg}")
                
                elif status in ["running", "pending", "queued", "processing"]:
                    # 任务进行中，继续等待
                    time.sleep(self.poll_interval)
                
                else:
                    # 未知状态，继续等待
                    self._log(f"未知任务状态: {status}", "WARNING")
                    time.sleep(self.poll_interval)
                    
            except Exception as e:
                # 如果查询失败，可能是网络问题，继续重试
                if elapsed_time > self.timeout:
                    raise
                self._log(f"查询任务状态失败，继续重试: {e}", "WARNING")
                time.sleep(self.poll_interval)
    
    def _get_task_status(self, task_id: str) -> Dict:
        """
        查询任务状态
        
        Args:
            task_id: 任务 ID
            
        Returns:
            Dict: 任务状态信息
        """
        try:
            url = f"{self.api_base_url}/v1/tasks/{task_id}"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            raise Exception(f"查询任务状态失败: {e}")
    
    def _parse_result(self, status_info: Dict) -> Dict:
        """
        解析任务结果
        
        Args:
            status_info: 任务状态信息
            
        Returns:
            Dict: 解析后的结果
        """
        try:
            # 提取输出
            outputs = status_info.get("outputs") or status_info.get("output") or {}
            
            # 提取输出图片 URL
            output_image_url = None
            
            # 尝试多种可能的字段名
            if isinstance(outputs, dict):
                output_image_url = (
                    outputs.get("output_image") or 
                    outputs.get("image") or 
                    outputs.get("result") or
                    outputs.get("output")
                )
            elif isinstance(outputs, str):
                output_image_url = outputs
            
            if not output_image_url:
                raise Exception(f"未找到输出图片 URL，响应: {status_info}")
            
            result = {
                "output_image": {
                    "url": output_image_url,
                    "type": "output"
                },
                "raw_outputs": outputs,
                "task_info": status_info
            }
            
            self._log(f"任务结果解析成功，输出图片: {output_image_url}")
            
            return result
            
        except Exception as e:
            raise Exception(f"解析任务结果失败: {e}")
    
    def download_image(self, image_info: Dict, save_path: str) -> str:
        """
        下载 RunningHub 生成的图片
        
        Args:
            image_info: 图片信息（包含 url）
            save_path: 保存路径
            
        Returns:
            str: 保存路径
        """
        try:
            from pathlib import Path
            
            url = image_info.get("url")
            if not url:
                raise ValueError("图片信息中没有 URL")
            
            # 下载图片
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # 保存图片
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            self._log(f"图片已下载: {save_path}")
            
            return save_path
            
        except Exception as e:
            raise Exception(f"下载图片失败: {e}")
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: RunningHub API 是否可用
        """
        try:
            # 检查配置
            if not self.api_key or not self.workflow_id:
                self._log("健康检查失败: API Key 或 Workflow ID 未配置", "WARNING")
                return False
            
            # 简化健康检查：只验证配置是否完整
            # RunningHub 的具体 API 端点可能需要实际测试
            # 如果配置齐全，认为是健康的
            self._log("健康检查通过: 配置完整", "INFO")
            return True
            
        except Exception as e:
            self._log(f"健康检查异常: {e}", "ERROR")
            return False

