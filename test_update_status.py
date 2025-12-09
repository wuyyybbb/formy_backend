#!/usr/bin/env python3
"""
Test script to verify update_task_status behavior
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables
os.environ.setdefault('DATABASE_URL', os.getenv('DATABASE_URL', 'postgresql://'))

from app.db import connect_to_db, close_db_connection, crud_tasks
from app.schemas.task import TaskStatus
import uuid

async def test_update_status():
    """Test update_task_status function"""
    
    # Connect to database
    await connect_to_db()
    
    try:
        # Create a test task first
        test_task_id = f"test_{uuid.uuid4().hex[:8]}"
        test_user_id = str(uuid.uuid4())
        
        print(f"[TEST] 创建测试任务: {test_task_id}")
        
        # Create task
        task = await crud_tasks.create_task(
            task_id=test_task_id,
            user_id=test_user_id,
            mode="HEAD_SWAP",
            status=TaskStatus.PENDING.value
        )
        print(f"[TEST] ✅ 任务已创建")
        
        # Now test update_task_status
        print(f"[TEST] 开始更新任务状态为 'done'...")
        
        result = await crud_tasks.update_task_status(
            task_id=test_task_id,
            status=TaskStatus.DONE.value,
            progress=100,
            result={"output_image": "test.jpg"}
        )
        
        print(f"[TEST] 更新返回值: {result}")
        
        # Verify the update
        task_data = await crud_tasks.get_task_by_id(test_task_id)
        if task_data:
            print(f"[TEST] ✅ 任务状态验证:")
            print(f"       - 任务ID: {task_data.get('task_id')}")
            print(f"       - 状态: {task_data.get('status')}")
            print(f"       - 进度: {task_data.get('progress')}")
        else:
            print(f"[TEST] ❌ 任务未找到")
            
    finally:
        await close_db_connection()
        print("[TEST] 数据库连接已关闭")

if __name__ == "__main__":
    asyncio.run(test_update_status())
