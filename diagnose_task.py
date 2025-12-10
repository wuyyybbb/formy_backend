#!/usr/bin/env python3
"""
快速诊断脚本 - 检查任务状态和队列
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

async def diagnose_task(task_id: str):
    """诊断任务状态"""
    print(f"\n{'='*60}")
    print(f"📊 诊断任务: {task_id}")
    print(f"{'='*60}\n")
    
    # 1. 检查数据库中的任务
    print("1️⃣ 检查数据库...")
    try:
        from app.db import connect_to_db, crud_tasks
        await connect_to_db()
        
        task = await crud_tasks.get_task_by_id(task_id)
        if task:
            print(f"   ✅ 任务存在于数据库")
            print(f"   - 状态: {task.get('status')}")
            print(f"   - 进度: {task.get('progress')}%")
            print(f"   - 模式: {task.get('mode')}")
            print(f"   - 源图片: {task.get('source_image')}")
            print(f"   - 参考图片: {task.get('reference_image')}")
            print(f"   - 创建时间: {task.get('created_at')}")
            print(f"   - 更新时间: {task.get('updated_at')}")
        else:
            print(f"   ❌ 任务不存在于数据库")
            return
    except Exception as e:
        print(f"   ❌ 数据库查询失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 检查 Redis 队列
    print("\n2️⃣ 检查 Redis 队列...")
    try:
        from app.services.tasks.queue import get_task_queue
        queue = get_task_queue()
        
        # 检查队列长度
        import redis
        r = redis.from_url(os.getenv("REDIS_URL"))
        queue_key = "formy:task:queue"
        queue_length = r.llen(queue_key)
        print(f"   - 队列长度: {queue_length}")
        
        # 检查任务是否在队列中
        task_data = queue.get_task_data(task_id)
        if task_data:
            print(f"   ✅ 任务在 Redis 中")
            print(f"   - 数据: {task_data}")
        else:
            print(f"   ❌ 任务不在 Redis 中")
            
        # 查看队列内容
        if queue_length > 0:
            print(f"\n   📋 队列中的任务:")
            tasks_in_queue = r.lrange(queue_key, 0, -1)
            for i, task_json in enumerate(tasks_in_queue):
                print(f"   {i+1}. {task_json.decode('utf-8')[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Redis 查询失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 检查文件是否存在
    print("\n3️⃣ 检查文件...")
    try:
        from app.services.image.image_assets import resolve_uploaded_file
        
        if task.get('source_image'):
            try:
                source_path = resolve_uploaded_file(task.get('source_image'))
                if source_path.exists():
                    file_size = source_path.stat().st_size
                    print(f"   ✅ 源图片存在: {source_path} ({file_size} bytes)")
                else:
                    print(f"   ❌ 源图片不存在: {source_path}")
            except Exception as e:
                print(f"   ❌ 解析源图片失败: {e}")
        
        if task.get('reference_image'):
            try:
                ref_path = resolve_uploaded_file(task.get('reference_image'))
                if ref_path.exists():
                    file_size = ref_path.stat().st_size
                    print(f"   ✅ 参考图片存在: {ref_path} ({file_size} bytes)")
                else:
                    print(f"   ❌ 参考图片不存在: {ref_path}")
            except Exception as e:
                print(f"   ❌ 解析参考图片失败: {e}")
                
    except Exception as e:
        print(f"   ❌ 文件检查失败: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ 诊断完成")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python diagnose_task.py <task_id>")
        print("示例: python diagnose_task.py task_1765269501_jabe1d")
        sys.exit(1)
    
    task_id = sys.argv[1]
    asyncio.run(diagnose_task(task_id))
