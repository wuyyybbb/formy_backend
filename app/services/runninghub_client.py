"""
RunningHub API 客户端封装

提供与 RunningHub 平台交互的统一接口。
"""

import os
from typing import Optional, List
from typing_extensions import TypedDict
import requests
from pydantic import BaseModel, Field


class UploadResourceResponse(TypedDict):
    fileId: str
    fileUrl: str
    fileName: str
    fileSize: int


class RunningHubOutputFile(BaseModel):
    fileUrl: str = Field(..., description="文件完整 URL")
    fileType: Optional[str] = Field(None, description="文件类型")
    nodeId: Optional[str] = Field(None, description="节点 ID")


class RunningHubError(Exception):
    pass


class RunningHubUploadError(RunningHubError):
    pass


class RunningHubTaskError(RunningHubError):
    pass


class RunningHubClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("RUNNINGHUB_API_KEY")
        self.base_url = (base_url or os.getenv("RUNNINGHUB_BASE_URL", "https://www.runninghub.cn")).rstrip("/")
        
        if not self.api_key:
            raise ValueError("RUNNINGHUB_API_KEY 未配置")
        
        self.session = requests.Session()
    
    def upload_resource(self, file_content: bytes, filename: str, timeout: int = 60) -> UploadResourceResponse:
        url = f"{self.base_url}/resource/openapi/upload"
        
        try:
            files = {"file": (filename, file_content)}
            data = {"apikey": self.api_key}
            
            response = self.session.post(url, files=files, data=data, timeout=timeout)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("code") != 0:
                raise RunningHubUploadError(f"上传资源失败：{result.get('message')}")
            
            data_obj = result.get("data", {})
            
            return UploadResourceResponse(
                fileId=data_obj.get("fileId", ""),
                fileUrl=data_obj.get("fileUrl", ""),
                fileName=data_obj.get("fileName", filename),
                fileSize=data_obj.get("fileSize", 0)
            )
        except requests.RequestException as e:
            raise RunningHubUploadError(f"上传请求失败：{str(e)}")
    
    def get_task_outputs(self, task_id: str, timeout: int = 30) -> List[RunningHubOutputFile]:
        url = f"{self.base_url}/task/openapi/outputs"
        
        try:
            payload = {"apikey": self.api_key, "taskId": task_id}
            
            response = self.session.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("code") != 0:
                print(f"⚠️  获取任务输出警告：{result.get('message')}")
                return []
            
            data_list = result.get("data", [])
            
            outputs = []
            for item in data_list:
                try:
                    outputs.append(RunningHubOutputFile(**item))
                except Exception as e:
                    print(f"⚠️  解析输出文件失败：{e}")
                    continue
            
            return outputs
        except requests.RequestException as e:
            raise RunningHubTaskError(f"获取任务输出请求失败：{str(e)}")


_global_client: Optional[RunningHubClient] = None


def get_runninghub_client() -> RunningHubClient:
    global _global_client
    if _global_client is None:
        _global_client = RunningHubClient()
    return _global_client


def get_task_outputs(task_id: str) -> List[RunningHubOutputFile]:
    client = get_runninghub_client()
    return client.get_task_outputs(task_id)
