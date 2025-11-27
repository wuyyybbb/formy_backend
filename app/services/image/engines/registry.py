"""
Engine 注册表
负责管理和注册所有 Engine，提供配置驱动的 Engine 选择

支持在配置文件中使用 ${ENV_VAR} 占位符，从环境变量读取配置。
"""
from typing import Dict, Any, Optional, Type
import yaml

from app.services.image.engines.base import EngineBase, EngineType
from app.services.image.engines.external_api import ExternalApiEngine
from app.services.image.engines.comfyui_engine import ComfyUIEngine
from app.utils.env_parser import load_yaml_with_env


class EngineRegistry:
    """Engine 注册表"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化注册表
        
        Args:
            config_path: 配置文件路径（engine_config.yml）
        """
        self.config_path = config_path or "./engine_config.yml"
        self.engines: Dict[str, EngineBase] = {}
        self.engine_classes: Dict[str, Type[EngineBase]] = {
            "external_api": ExternalApiEngine,
            "comfyui": ComfyUIEngine
        }
        self.config: Dict[str, Any] = {}
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """从 YAML 文件加载配置（支持环境变量占位符）"""
        try:
            # 使用支持环境变量的加载器
            self.config = load_yaml_with_env(self.config_path)
            print(f"[EngineRegistry] ✅ 配置加载成功: {self.config_path}")
            
            # 打印已解析的 ComfyUI URL（用于调试）
            engines = self.config.get("engines", {})
            for engine_name, engine_cfg in engines.items():
                if engine_cfg.get("type") == "comfyui":
                    comfyui_url = engine_cfg.get("config", {}).get("comfyui_url")
                    if comfyui_url:
                        print(f"[EngineRegistry] 📍 {engine_name}: {comfyui_url}")
                    
        except FileNotFoundError:
            print(f"[EngineRegistry] ❌ 配置文件不存在: {self.config_path}")
            self.config = {}
        except Exception as e:
            print(f"[EngineRegistry] ❌ 配置加载失败: {e}")
            import traceback
            traceback.print_exc()
            self.config = {}
    
    def register_engine(
        self, 
        engine_name: str, 
        engine_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        注册 Engine
        
        Args:
            engine_name: 引擎名称（唯一标识）
            engine_type: 引擎类型（external_api / comfyui）
            config: 引擎配置
            
        Returns:
            bool: 是否注册成功
        """
        try:
            # 获取引擎类
            engine_class = self.engine_classes.get(engine_type)
            if not engine_class:
                print(f"[EngineRegistry] 不支持的引擎类型: {engine_type}")
                return False
            
            # 创建引擎实例
            engine = engine_class(config=config)
            
            # 注册到字典
            self.engines[engine_name] = engine
            
            print(f"[EngineRegistry] 引擎注册成功: {engine_name} ({engine_type})")
            return True
            
        except Exception as e:
            print(f"[EngineRegistry] 引擎注册失败: {engine_name}, 错误: {e}")
            return False
    
    def get_engine(self, engine_name: str) -> Optional[EngineBase]:
        """
        获取 Engine 实例
        
        Args:
            engine_name: 引擎名称
            
        Returns:
            Optional[EngineBase]: 引擎实例，不存在返回 None
        """
        return self.engines.get(engine_name)
    
    def get_engine_for_step(self, pipeline_name: str, step_name: str) -> Optional[EngineBase]:
        """
        根据 Pipeline 和 Step 获取对应的 Engine
        
        Args:
            pipeline_name: Pipeline 名称（如 head_swap）
            step_name: 步骤名称（如 face_detection）
            
        Returns:
            Optional[EngineBase]: 引擎实例
        """
        # TODO: 从配置中查找映射关系
        # 例如：config['pipelines']['head_swap']['steps']['face_detection']['engine']
        
        try:
            pipeline_config = self.config.get("pipelines", {}).get(pipeline_name, {})
            step_config = pipeline_config.get("steps", {}).get(step_name, {})
            engine_name = step_config.get("engine")
            
            if not engine_name:
                return None
            
            return self.get_engine(engine_name)
            
        except Exception as e:
            print(f"[EngineRegistry] 获取引擎失败: {e}")
            return None
    
    def initialize_from_config(self):
        """从配置文件初始化所有 Engine"""
        engines_config = self.config.get("engines", {})
        
        for engine_name, engine_cfg in engines_config.items():
            engine_type = engine_cfg.get("type")
            engine_config = engine_cfg.get("config", {})
            
            self.register_engine(
                engine_name=engine_name,
                engine_type=engine_type,
                config=engine_config
            )
    
    def list_engines(self) -> list[str]:
        """
        列出所有已注册的 Engine
        
        Returns:
            list[str]: 引擎名称列表
        """
        return list(self.engines.keys())
    
    def health_check_all(self) -> Dict[str, bool]:
        """
        对所有 Engine 进行健康检查
        
        Returns:
            Dict[str, bool]: {引擎名称: 是否健康}
        """
        results = {}
        for engine_name, engine in self.engines.items():
            results[engine_name] = engine.health_check()
        return results


# 全局注册表实例（单例模式）
_engine_registry_instance: Optional[EngineRegistry] = None


def get_engine_registry(config_path: Optional[str] = None) -> EngineRegistry:
    """获取 Engine 注册表实例（单例）"""
    global _engine_registry_instance
    if _engine_registry_instance is None:
        _engine_registry_instance = EngineRegistry(config_path)
        _engine_registry_instance.initialize_from_config()
    return _engine_registry_instance

