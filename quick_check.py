import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db import connect_to_db, crud_tasks
from app.services.tasks.queue import get_task_queue
import os

async def check_task(task_id):
    await connect_to_db()
    
    # 1. 检查数据库
    print(f"\n=== 检查任务: {task_id} ===\n")
    task = await crud_tasks.get_task_by_id(task_id)
    
    if task:
        print(f"✅ 任务存在于数据库")
        print(f"   状态: {task.get('status')}")
        print(f"   模式: {task.get('mode')}")
        print(f"   源图片: {task.get('source_image')}")
        print(f"   参考图片: {task.get('reference_image')}")
        print(f"   配置: {task.get('config')}")
    else:
        print(f"❌ 任务不存在")
        return
    
    # 2. 检查 Redis 队列
    print(f"\n=== 检查 Redis 队列 ===\n")
    queue = get_task_queue()
    task_data = queue.get_task_data(task_id)
    
    if task_data:
        print(f"✅ 任务在 Redis 中")
        print(f"   数据: {task_data}")
    else:
        print(f"❌ 任务不在 Redis 队列中")
    
    # 3. 检查队列长度
    import redis
    r = redis.from_url(os.getenv("REDIS_URL"))
    queue_length = r.llen("formy:task:queue")
    print(f"\n队列长度: {queue_length}")

if __name__ == "__main__":
    asyncio.run(check_task("task_1765331734_nNhz21"))
