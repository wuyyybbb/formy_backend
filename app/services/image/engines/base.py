"""
Engine 基类
定义所有 Engine 的通用接口
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum


class EngineType(str, Enum):
    """引擎类型枚举"""
    EXTERNAL_API = "external_api"      # 闭源 API 调用
    COMFYUI = "comfyui"                # ComfyUI 工作流
    LOCAL_MODEL = "local_model"        # 本地模型
    RUNNINGHUB = "runninghub"          # RunningHub 云端工作流


class EngineBase(ABC):
    """Engine 基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 Engine
        
        Args:
            config: 引擎配置
        """
        self.config = config or {}
        self.engine_type: Optional[EngineType] = None
        self.engine_name: str = self.__class__.__name__
    
    @abstractmethod
    def execute(self, input_data: Any, **kwargs) -> Any:
        """
        执行引擎处理（抽象方法，子类必须实现）
        
        Args:
            input_data: 输入数据
            **kwargs: 其他参数
            
        Returns:
            Any: 处理结果
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """
        验证输入数据（抽象方法，子类必须实现）
        
        Args:
            input_data: 输入数据
            
        Returns:
            bool: 是否有效
        """
        pass
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: 引擎是否可用
        """
        # TODO: 子类可重写以实现具体的健康检查逻辑
        return True
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.config.get(key, default)
    
    def _log(self, message: str, level: str = "INFO"):
        """
        记录日志
        
        Args:
            message: 日志信息
            level: 日志级别
        """
        # TODO: 接入实际的日志系统
        print(f"[{level}] [{self.engine_name}] {message}")

