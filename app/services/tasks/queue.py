"""
Redis 任务队列管理
负责任务的入队、出队操作
"""
import json
import redis
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.utils.redis_client import get_redis_client


class TaskQueue:
    """任务队列管理类"""
    
    # Redis Key 前缀
    QUEUE_KEY = "formy:task:queue"           # 任务队列（List）
    TASK_KEY_PREFIX = "formy:task:data:"     # 任务数据（Hash）
    PROCESSING_SET = "formy:task:processing" # 处理中任务集合（Set）
    
    def __init__(self):
        """初始化 Redis 连接"""
        # 使用统一的 Redis 客户端（基于 REDIS_URL）
        self.redis_client = get_redis_client()
    
    def push_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """
        推送任务到队列
        
        Args:
            task_id: 任务ID
            task_data: 任务数据
            
        Returns:
            bool: 是否成功
        """
        try:
            # 1. 存储任务数据到 Hash
            task_key = f"{self.TASK_KEY_PREFIX}{task_id}"
            self.redis_client.hset(
                task_key,
                mapping={
                    "task_id": task_id,
                    "status": "pending",
                    "data": json.dumps(task_data, ensure_ascii=False),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            # 2. 推入队列（右侧推入）
            self.redis_client.rpush(self.QUEUE_KEY, task_id)
            
            return True
        except Exception as e:
            print(f"推送任务失败: {e}")
            return False
    
    def pop_task(self, timeout: int = 5) -> Optional[str]:
        """
        从队列中弹出任务（阻塞式）
        
        Args:
            timeout: 阻塞超时时间（秒）
            
        Returns:
            Optional[str]: 任务ID，如果超时返回 None
        """
        try:
            # 从左侧弹出（FIFO）
            result = self.redis_client.blpop(self.QUEUE_KEY, timeout=timeout)
            if result:
                _, task_id = result
                # 标记为处理中
                self.redis_client.sadd(self.PROCESSING_SET, task_id)
                return task_id
            return None
        except Exception as e:
            print(f"弹出任务失败: {e}")
            return None
    
    def get_task_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务数据
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict]: 任务数据
        """
        try:
            task_key = f"{self.TASK_KEY_PREFIX}{task_id}"
            data = self.redis_client.hgetall(task_key)
            
            if not data:
                return None
            
            # 解析 JSON 数据
            if "data" in data:
                data["data"] = json.loads(data["data"])
            
            return data
        except Exception as e:
            print(f"获取任务数据失败: {e}")
            return None
    
    def update_task_status(
        self, 
        task_id: str, 
        status: str,
        progress: int = 0,
        current_step: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            progress: 进度百分比
            current_step: 当前步骤描述
            result: 结果数据（完成时）
            error: 错误信息（失败时）
            
        Returns:
            bool: 是否成功
        """
        try:
            task_key = f"{self.TASK_KEY_PREFIX}{task_id}"
            
            # 构建更新字段
            update_data = {
                "status": status,
                "progress": str(progress),
                "updated_at": datetime.now().isoformat()
            }
            
            if current_step:
                update_data["current_step"] = current_step
            
            if result:
                update_data["result"] = json.dumps(result, ensure_ascii=False)
            
            if error:
                update_data["error"] = json.dumps(error, ensure_ascii=False)
            
            # 记录完成/失败时间
            if status == "done":
                update_data["completed_at"] = datetime.now().isoformat()
            elif status == "failed":
                update_data["failed_at"] = datetime.now().isoformat()
            
            # 更新 Hash
            self.redis_client.hset(task_key, mapping=update_data)
            
            # 如果任务完成/失败/取消，从处理中集合移除
            if status in ["done", "failed", "cancelled"]:
                self.redis_client.srem(self.PROCESSING_SET, task_id)
            
            return True
        except Exception as e:
            print(f"更新任务状态失败: {e}")
            return False
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # 从队列中移除（如果还在队列中）
            self.redis_client.lrem(self.QUEUE_KEY, 0, task_id)
            
            # 更新状态为已取消
            return self.update_task_status(task_id, "cancelled")
        except Exception as e:
            print(f"取消任务失败: {e}")
            return False
    
    def get_queue_length(self) -> int:
        """获取队列长度"""
        try:
            return self.redis_client.llen(self.QUEUE_KEY)
        except Exception as e:
            print(f"获取队列长度失败: {e}")
            return 0
    
    def get_processing_count(self) -> int:
        """获取正在处理的任务数量"""
        try:
            return self.redis_client.scard(self.PROCESSING_SET)
        except Exception as e:
            print(f"获取处理中任务数量失败: {e}")
            return 0
    
    def is_task_exists(self, task_id: str) -> bool:
        """检查任务是否存在"""
        try:
            task_key = f"{self.TASK_KEY_PREFIX}{task_id}"
            return self.redis_client.exists(task_key) > 0
        except Exception as e:
            print(f"检查任务存在失败: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务数据（清理用）
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        try:
            task_key = f"{self.TASK_KEY_PREFIX}{task_id}"
            self.redis_client.delete(task_key)
            self.redis_client.srem(self.PROCESSING_SET, task_id)
            return True
        except Exception as e:
            print(f"删除任务失败: {e}")
            return False
    
    def get_all_task_ids(self, status_filter: Optional[str] = None) -> list[str]:
        """
        获取所有任务ID（支持状态筛选）
        
        Args:
            status_filter: 状态筛选（pending/processing/done/failed/cancelled）
            
        Returns:
            list[str]: 任务ID列表
        """
        try:
            # 扫描所有任务键
            pattern = f"{self.TASK_KEY_PREFIX}*"
            task_ids = []
            
            for key in self.redis_client.scan_iter(match=pattern):
                task_id = key.replace(self.TASK_KEY_PREFIX, "")
                
                # 如果有状态筛选
                if status_filter:
                    task_status = self.redis_client.hget(key, "status")
                    if task_status == status_filter:
                        task_ids.append(task_id)
                else:
                    task_ids.append(task_id)
            
            return task_ids
        except Exception as e:
            print(f"获取任务列表失败: {e}")
            return []
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            return self.redis_client.ping()
        except Exception:
            return False


# 全局队列实例（单例模式）
_task_queue_instance: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """获取任务队列实例（单例）"""
    global _task_queue_instance
    if _task_queue_instance is None:
        _task_queue_instance = TaskQueue()
    return _task_queue_instance

