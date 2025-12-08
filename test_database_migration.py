"""
数据库迁移测试脚本
用于验证任务系统从 Redis 迁移到 PostgreSQL 是否成功
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.db import connect_to_db, close_db_connection, get_pool
from app.db.crud_tasks import (
    create_task,
    get_task_by_id,
    get_tasks_by_user,
    update_task_status,
    count_tasks_by_user
)
from app.schemas.task import TaskStatus, EditMode


async def test_database_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("1. 测试数据库连接")
    print("=" * 60)
    
    try:
        await connect_to_db()
        pool = get_pool()
        
        if pool:
            print("✅ 数据库连接成功")
            
            # 测试查询
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    print("✅ 数据库查询测试通过")
                else:
                    print("❌ 数据库查询测试失败")
                    return False
            
            return True
        else:
            print("❌ 数据库连接池未初始化")
            return False
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


async def test_tasks_table_exists():
    """测试 tasks 表是否存在"""
    print("\n" + "=" * 60)
    print("2. 测试 tasks 表是否存在")
    print("=" * 60)
    
    try:
        pool = get_pool()
        if not pool:
            print("❌ 数据库连接池未初始化")
            return False
        
        async with pool.acquire() as conn:
            # 检查表是否存在
            exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'tasks'
                )
                """
            )
            
            if exists:
                print("✅ tasks 表存在")
                
                # 检查表结构
                columns = await conn.fetch(
                    """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'tasks'
                    ORDER BY ordinal_position
                    """
                )
                
                print(f"\n表结构（共 {len(columns)} 列）：")
                for col in columns:
                    print(f"  - {col['column_name']}: {col['data_type']}")
                
                return True
            else:
                print("❌ tasks 表不存在")
                print("\n请在 Supabase 中运行建表 SQL:")
                print("  文件位置: backend/database_schema/tasks_table.sql")
                return False
                
    except Exception as e:
        print(f"❌ 检查表结构失败: {e}")
        return False


async def test_create_task():
    """测试创建任务"""
    print("\n" + "=" * 60)
    print("3. 测试创建任务")
    print("=" * 60)
    
    try:
        # 创建测试任务
        task_info = await create_task(
            task_id="test_task_001",
            user_id="test_user_001",
            mode=EditMode.HEAD_SWAP.value,
            source_image="test_source.jpg",
            reference_image="test_reference.jpg",
            config={"quality": "high", "size": "1024x1024"},
            credits_consumed=10
        )
        
        print(f"✅ 任务创建成功: {task_info.task_id}")
        print(f"  - 用户: {task_info.task_id}")
        print(f"  - 状态: {task_info.status.value}")
        print(f"  - 模式: {task_info.mode.value}")
        print(f"  - 算力: {task_info.credits_consumed}")
        
        return task_info.task_id
        
    except Exception as e:
        print(f"❌ 创建任务失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_get_task(task_id: str):
    """测试获取任务"""
    print("\n" + "=" * 60)
    print("4. 测试获取任务")
    print("=" * 60)
    
    try:
        task_info = await get_task_by_id(task_id)
        
        if task_info:
            print(f"✅ 任务查询成功: {task_info.task_id}")
            print(f"  - 状态: {task_info.status.value}")
            print(f"  - 进度: {task_info.progress}%")
            print(f"  - 创建时间: {task_info.created_at}")
            return True
        else:
            print(f"❌ 任务不存在: {task_id}")
            return False
            
    except Exception as e:
        print(f"❌ 查询任务失败: {e}")
        return False


async def test_update_task_status(task_id: str):
    """测试更新任务状态"""
    print("\n" + "=" * 60)
    print("5. 测试更新任务状态")
    print("=" * 60)
    
    try:
        # 更新为处理中
        success = await update_task_status(
            task_id=task_id,
            status=TaskStatus.PROCESSING.value,
            progress=50,
            current_step="正在处理图片..."
        )
        
        if success:
            print(f"✅ 状态更新成功: {task_id}")
            
            # 验证更新
            task_info = await get_task_by_id(task_id)
            if task_info:
                print(f"  - 新状态: {task_info.status.value}")
                print(f"  - 进度: {task_info.progress}%")
                print(f"  - 当前步骤: {task_info.current_step}")
                return True
        else:
            print(f"❌ 状态更新失败: {task_id}")
            return False
            
    except Exception as e:
        print(f"❌ 更新任务状态失败: {e}")
        return False


async def test_get_tasks_by_user(user_id: str):
    """测试获取用户任务列表"""
    print("\n" + "=" * 60)
    print("6. 测试获取用户任务列表")
    print("=" * 60)
    
    try:
        tasks = await get_tasks_by_user(
            user_id=user_id,
            page=1,
            page_size=10
        )
        
        print(f"✅ 查询成功，找到 {len(tasks)} 个任务")
        
        for i, task in enumerate(tasks, 1):
            print(f"\n  任务 {i}:")
            print(f"    - ID: {task.task_id}")
            print(f"    - 状态: {task.status.value}")
            print(f"    - 模式: {task.mode.value}")
            print(f"    - 创建时间: {task.created_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ 查询任务列表失败: {e}")
        return False


async def test_count_tasks(user_id: str):
    """测试统计任务数量"""
    print("\n" + "=" * 60)
    print("7. 测试统计任务数量")
    print("=" * 60)
    
    try:
        total_count = await count_tasks_by_user(user_id)
        processing_count = await count_tasks_by_user(
            user_id,
            status_filter=TaskStatus.PROCESSING.value
        )
        
        print(f"✅ 统计成功")
        print(f"  - 总任务数: {total_count}")
        print(f"  - 处理中: {processing_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 统计失败: {e}")
        return False


async def cleanup_test_data(task_id: str):
    """清理测试数据"""
    print("\n" + "=" * 60)
    print("8. 清理测试数据")
    print("=" * 60)
    
    try:
        pool = get_pool()
        if not pool:
            print("❌ 数据库连接池未初始化")
            return False
        
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM tasks WHERE task_id = $1",
                task_id
            )
        
        print(f"✅ 测试数据已清理: {task_id}")
        return True
        
    except Exception as e:
        print(f"❌ 清理测试数据失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 开始数据库迁移测试")
    print("=" * 60)
    
    results = []
    task_id = None
    
    try:
        # 1. 测试数据库连接
        result = await test_database_connection()
        results.append(("数据库连接", result))
        if not result:
            print("\n❌ 数据库连接失败，跳过后续测试")
            return False
        
        # 2. 测试表是否存在
        result = await test_tasks_table_exists()
        results.append(("tasks 表存在", result))
        if not result:
            print("\n❌ tasks 表不存在，请先运行建表 SQL")
            return False
        
        # 3. 测试创建任务
        task_id = await test_create_task()
        results.append(("创建任务", task_id is not None))
        if not task_id:
            print("\n❌ 创建任务失败，跳过后续测试")
            return False
        
        # 4. 测试获取任务
        result = await test_get_task(task_id)
        results.append(("获取任务", result))
        
        # 5. 测试更新任务状态
        result = await test_update_task_status(task_id)
        results.append(("更新任务状态", result))
        
        # 6. 测试获取用户任务列表
        result = await test_get_tasks_by_user("test_user_001")
        results.append(("获取任务列表", result))
        
        # 7. 测试统计任务数量
        result = await test_count_tasks("test_user_001")
        results.append(("统计任务数量", result))
        
        # 8. 清理测试数据
        if task_id:
            result = await cleanup_test_data(task_id)
            results.append(("清理测试数据", result))
        
    finally:
        # 关闭数据库连接
        await close_db_connection()
    
    # 打印测试总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 60)
    
    return passed == total


async def main():
    """主函数"""
    try:
        success = await run_all_tests()
        
        if success:
            print("\n🎉 所有测试通过！数据库迁移成功！")
            sys.exit(0)
        else:
            print("\n⚠️  部分测试失败，请检查错误信息")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Formy 数据库迁移测试")
    print("=" * 60)
    print("\n请确保已配置以下环境变量：")
    print("  - DATABASE_URL: PostgreSQL 连接字符串")
    print("\n" + "=" * 60)
    
    asyncio.run(main())
