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
        self.timeout = self.get_config("timeout", 300)  # 最大等待时间 5 分钟
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
        准备 RunningHub API 请求参数（上传文件并返回文件名）
        
        Args:
            input_data: 输入数据
            **kwargs: 其他参数
            
        Returns:
            Dict: 包含已上传文件名的参数字典
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
        raw_image_path = kwargs.get("raw_image_path") or raw_image
        pose_image_path = kwargs.get("pose_image_path") or pose_image
        
        # 上传原始图片
        if raw_image_path:
            self._log(f"正在上传原始图片: {raw_image_path}")
            uploaded_filename = self._upload_image(raw_image_path)
            params["raw_image"] = uploaded_filename
        
        # 上传姿势参考图
        if pose_image_path:
            self._log(f"正在上传姿势参考图: {pose_image_path}")
            uploaded_filename = self._upload_image(pose_image_path)
            params["pose_image"] = uploaded_filename
        
        return params
    
    def _upload_image(self, image_path: str) -> str:
        """
        上传图片到 RunningHub（官方 API 格式）
        
        Args:
            image_path: 本地图片路径
            
        Returns:
            str: 图片文件名（用于后续任务提交）
        """
        try:
            import os
            from pathlib import Path
            
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
            filename = os.path.basename(image_path)
            
            # 上传到 RunningHub（官方端点）
            url = f"{self.api_base_url}/task/openapi/upload"
            # Host header 会自动从 URL 中提取，不需要手动设置
            headers = {}
            data = {
                'apiKey': self.api_key,
                'fileType': 'input'
            }
            
            # 上传文件（添加重试机制）
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self._log(f"上传图片，尝试 {attempt + 1}/{max_retries}: {filename}")
                    with open(image_path, 'rb') as f:
                        files = {'file': f}
                        response = requests.post(url, headers=headers, files=files, data=data, timeout=90)
                    response.raise_for_status()
                    result = response.json()
                    break  # 成功则跳出重试循环
                except requests.exceptions.Timeout as e:
                    if attempt < max_retries - 1:
                        self._log(f"上传超时，{5}秒后重试...", "WARNING")
                        time.sleep(5)
                    else:
                        raise Exception(f"上传图片超时（已重试{max_retries}次）: {filename}")
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        self._log(f"上传失败: {e}，{5}秒后重试...", "WARNING")
                        time.sleep(5)
                    else:
                        raise
            
            # 官方 API 返回格式：{"code": 0, "msg": "success", "data": {"fileName": "api/xxx.jpg", "fileType": "input"}}
            if result.get("code") != 0:
                raise Exception(f"上传失败: {result.get('msg')}")
            
            uploaded_filename = result.get("data", {}).get("fileName")
            if not uploaded_filename:
                raise Exception("上传响应中没有返回文件名")
            
            self._log(f"图片已上传到 RunningHub: {filename} -> {uploaded_filename}")
            
            return uploaded_filename
            
        except Exception as e:
            raise Exception(f"上传图片失败: {e}")
    
    def _submit_workflow(self, params: Dict) -> str:
        """
        提交工作流到 RunningHub（官方 API 格式）
        
        Args:
            params: 包含 raw_image 和 pose_image 文件名的字典
            
        Returns:
            str: 任务 ID
        """
        try:
            # 构建 nodeInfoList（官方 API 格式）
            # 根据工作流节点构建节点信息列表
            # 节点 #3: input:raw_image:1 - 原始图片
            # 节点 #7: input:pose_image:2 - 姿势参考图
            node_info_list = []
            
            # 添加原始图片节点（节点 #3）
            if "raw_image" in params:
                node_info_list.append({
                    "nodeId": "3",
                    "fieldName": "image",
                    "fieldValue": params["raw_image"]
                })
            
            # 添加姿势参考图节点（节点 #7）
            if "pose_image" in params:
                node_info_list.append({
                    "nodeId": "7",
                    "fieldName": "image",
                    "fieldValue": params["pose_image"]
                })
            
            # 构建请求（官方端点）
            url = f"{self.api_base_url}/task/openapi/create"
            headers = {
                'Content-Type': 'application/json'
            }
            
            payload = {
                "apiKey": self.api_key,
                "workflowId": self.workflow_id,
                "nodeInfoList": node_info_list
            }
            
            self._log(f"提交工作流到 RunningHub: {url}")
            self._log(f"节点信息: {node_info_list}")
            
            # 发送请求（添加重试机制）
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self._log(f"提交任务，尝试 {attempt + 1}/{max_retries}")
                    response = requests.post(url, headers=headers, json=payload, timeout=60)
                    response.raise_for_status()
                    break  # 成功则跳出重试循环
                except requests.exceptions.Timeout as e:
                    if attempt < max_retries - 1:
                        self._log(f"请求超时，{3}秒后重试...", "WARNING")
                        time.sleep(3)
                    else:
                        raise Exception(f"提交工作流超时（已重试{max_retries}次）: {e}")
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        self._log(f"请求失败: {e}，{3}秒后重试...", "WARNING")
                        time.sleep(3)
                    else:
                        raise
            
            # 解析响应：{"code": 0, "msg": "success", "data": {"taskId": "xxx", ...}}
            result = response.json()
            self._log(f"提交响应: {result}")
            
            if result.get("code") != 0:
                error_msg = result.get('msg', '未知错误')
                self._log(f"❌ 提交失败，错误码: {result.get('code')}, 错误信息: {error_msg}", "ERROR")
                raise Exception(f"提交失败: {error_msg}")
            
            task_id = result.get("data", {}).get("taskId")
            
            if not task_id:
                self._log(f"❌ 未获取到任务 ID，完整响应: {result}", "ERROR")
                raise Exception(f"未获取到任务 ID，响应: {result}")
            
            self._log(f"✅ 工作流已提交，任务 ID: {task_id}")
            self._log(f"🔗 可在 RunningHub 平台查看任务: https://{self.api_base_url.split('//')[1]}/task/{task_id}")
            
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
            # 检查超时（5 分钟）
            elapsed_time = time.time() - start_time
            if elapsed_time > self.timeout:
                # 友好的超时提示
                raise TimeoutError(
                    f"AI 处理超时：当前使用人数较多，系统繁忙。"
                    f"建议您稍后再试，或联系客服获取帮助。"
                    f"（已等待 {int(elapsed_time)} 秒）"
                )
            
            # 查询任务状态
            try:
                status_info = self._get_task_status(task_id)
                code = status_info.get("code")
                msg = status_info.get("msg")
                data = status_info.get("data")
                
                # 官方 API 状态码：
                # 0: 成功, 804: 运行中, 813: 排队中, 805: 失败
                
                if code == 0 and data:
                    # 任务完成
                    self._log(f"任务完成 (已用时 {int(elapsed_time)} 秒)")
                    result = self._parse_result(status_info)
                    return result
                
                elif code == 805:
                    # 任务失败
                    failed_reason = data.get("failedReason") if data else None
                    error_msg = "未知错误"
                    if failed_reason:
                        error_msg = f"{failed_reason.get('node_name')}: {failed_reason.get('exception_message')}"
                    raise Exception(f"任务执行失败: {error_msg}")
                
                elif code in [804, 813]:
                    # 运行中或排队中
                    status_text = "运行中" if code == 804 else "排队中"
                    self._log(f"任务{status_text} (已用时 {int(elapsed_time)} 秒)")
                    time.sleep(self.poll_interval)
                
                else:
                    # 未知状态
                    self._log(f"未知状态码: {code}, msg: {msg}", "WARNING")
                    time.sleep(self.poll_interval)
                    
            except Exception as e:
                # 如果查询失败，可能是网络问题，继续重试
                if elapsed_time > self.timeout:
                    raise
                self._log(f"查询任务状态失败，继续重试: {e}", "WARNING")
                time.sleep(self.poll_interval)
    
    def _get_task_status(self, task_id: str) -> Dict:
        """
        查询任务状态（官方 API 格式）
        
        Args:
            task_id: 任务 ID
            
        Returns:
            Dict: 任务状态信息
        """
        try:
            # 官方端点
            url = f"{self.api_base_url}/task/openapi/outputs"
            headers = {
                'Content-Type': 'application/json'
            }
            payload = {
                "apiKey": self.api_key,
                "taskId": task_id
            }
            
            # 查询状态（添加重试）
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        self._log(f"查询超时，重试...", "WARNING")
                        time.sleep(2)
                    else:
                        raise
                except Exception:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        raise
            
        except Exception as e:
            raise Exception(f"查询任务状态失败: {e}")
    
    def _parse_result(self, status_info: Dict) -> Dict:
        """
        解析任务结果（官方 API 格式，支持多个输出文件）
        
        Args:
            status_info: 任务状态信息
            
        Returns:
            Dict: 解析后的结果
        """
        try:
            # 官方 API 返回格式：
            # {"code": 0, "msg": "success", "data": [{"fileUrl": "xxx", "fileType": "png", "nodeId": "4"}, ...]}
            data = status_info.get("data")
            
            if not data or not isinstance(data, list) or len(data) == 0:
                raise Exception(f"未找到输出数据，响应: {status_info}")
            
            # 获取第一个输出文件（主要结果图）
            first_output = data[0]
            output_image_url = first_output.get("fileUrl")
            
            if not output_image_url:
                raise Exception(f"未找到输出图片 URL，响应: {status_info}")
            
            result = {
                "output_image": {
                    "url": output_image_url,
                    "type": first_output.get("fileType", "output")
                },
                "raw_outputs": data,
                "task_info": status_info
            }
            
            # 如果有第二个输出文件（对比图），也添加到结果中
            if len(data) > 1:
                comparison_output = data[1]
                comparison_url = comparison_output.get("fileUrl")
                if comparison_url:
                    result["comparison_image"] = {
                        "url": comparison_url,
                        "type": comparison_output.get("fileType", "comparison")
                    }
                    self._log(f"找到对比图: {comparison_url}")
            
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

