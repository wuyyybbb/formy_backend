"""
快速检查 Redis 队列状态
"""
import redis
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 连接 Redis（使用 Render 的环境变量名）
redis_url = os.getenv("UPSTASH_REDIS_URL") or os.getenv("REDIS_URL")
if not redis_url or redis_url == "redis://localhost:6379":
    print("⚠️  请设置 UPSTASH_REDIS_URL 环境变量")
    print("或者直接在代码中提供 Upstash Redis URL")
    exit(1)
print(f"Redis URL: {redis_url[:30]}...")

r = redis.from_url(redis_url)

# 检查队列
queue_key = "formy:task:queue"
queue_length = r.llen(queue_key)
print(f"\n队列长度: {queue_length}")

if queue_length > 0:
    # 查看队列中的任务
    print(f"\n队列中的任务 ID:")
    tasks = r.lrange(queue_key, 0, -1)
    for i, task_id in enumerate(tasks, 1):
        task_id_str = task_id.decode('utf-8')
        print(f"  {i}. {task_id_str}")
        
        # 查看任务数据
        task_key = f"formy:task:data:{task_id_str}"
        task_data = r.hgetall(task_key)
        if task_data:
            print(f"     状态: {task_data.get(b'status', b'unknown').decode('utf-8')}")
            data_str = task_data.get(b'data', b'{}').decode('utf-8')
            data = json.loads(data_str)
            print(f"     模式: {data.get('mode', 'unknown')}")
            print(f"     原图: {data.get('source_image', 'N/A')}")
            print(f"     参考图: {data.get('reference_image', 'N/A')}")
else:
    print("\n队列为空")

# 检查处理中的任务
processing_set = "formy:task:processing"
processing_count = r.scard(processing_set)
print(f"\n处理中的任务数: {processing_count}")

if processing_count > 0:
    processing_tasks = r.smembers(processing_set)
    for task_id in processing_tasks:
        print(f"  - {task_id.decode('utf-8')}")
