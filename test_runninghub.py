"""
RunningHub Engine 测试脚本
用于验证 RunningHub 配置和连接
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.image.engines.registry import get_engine_registry


def test_runninghub_config():
    """测试 RunningHub 配置"""
    print("=" * 60)
    print("🔍 RunningHub Engine 配置测试")
    print("=" * 60)
    
    try:
        # 1. 加载 Engine Registry
        print("\n[1] 加载 Engine Registry...")
        config_path = Path(__file__).parent / "engine_config.yml"
        registry = get_engine_registry(str(config_path))
        print("✅ Engine Registry 加载成功")
        
        # 2. 列出所有已注册的 Engine
        print("\n[2] 已注册的 Engine:")
        engines = registry.list_engines()
        for engine_name in engines:
            print(f"   - {engine_name}")
        
        # 3. 获取 RunningHub Engine
        print("\n[3] 获取 RunningHub Engine...")
        runninghub_engine = registry.get_engine('runninghub_pose_transfer')
        
        if not runninghub_engine:
            print("❌ RunningHub Engine 未找到！")
            print("   请检查 engine_config.yml 中的配置")
            return False
        
        print(f"✅ RunningHub Engine 已加载")
        print(f"   引擎类型: {runninghub_engine.engine_type}")
        
        # 4. 显示配置信息
        print("\n[4] RunningHub 配置信息:")
        print(f"   API Key: {runninghub_engine.api_key[:10]}...{runninghub_engine.api_key[-10:]}")
        print(f"   Workflow ID: {runninghub_engine.workflow_id}")
        print(f"   API Base URL: {runninghub_engine.api_base_url}")
        print(f"   Timeout: {runninghub_engine.timeout} 秒")
        print(f"   Poll Interval: {runninghub_engine.poll_interval} 秒")
        
        # 5. 健康检查
        print("\n[5] 执行健康检查...")
        print("   正在连接 RunningHub API...")
        
        is_healthy = runninghub_engine.health_check()
        
        if is_healthy:
            print("✅ RunningHub Engine 健康检查通过！")
            print("   API 连接正常，可以开始使用")
        else:
            print("❌ RunningHub Engine 健康检查失败！")
            print("   可能原因：")
            print("   - API Key 无效")
            print("   - Workflow ID 不存在")
            print("   - 网络连接问题")
            print("   - RunningHub 服务不可用")
        
        # 6. 测试 Pipeline 配置
        print("\n[6] 测试 Pipeline 配置...")
        pose_engine = registry.get_engine_for_step("pose_change", "pose_transfer")
        
        if pose_engine:
            print("✅ pose_change Pipeline 已正确配置 RunningHub Engine")
        else:
            print("⚠️  pose_change Pipeline 未找到对应的 Engine")
        
        # 7. 总结
        print("\n" + "=" * 60)
        if is_healthy:
            print("🎉 RunningHub 集成测试通过！")
            print("=" * 60)
            print("\n✅ 您现在可以：")
            print("   1. 启动后端服务")
            print("   2. 通过前端上传图片")
            print("   3. 选择姿势迁移功能")
            print("   4. 等待 RunningHub 处理并返回结果")
            print("\n📚 更多信息请查看: RUNNINGHUB_DEPLOYMENT_GUIDE.md")
        else:
            print("⚠️  RunningHub 配置需要检查")
            print("=" * 60)
            print("\n🔧 请检查：")
            print("   1. engine_config.yml 中的 API Key 是否正确")
            print("   2. Workflow ID 是否正确")
            print("   3. 网络连接是否正常")
            print("   4. RunningHub 服务是否可用")
        print()
        
        return is_healthy
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pose_change_pipeline():
    """测试 Pose Change Pipeline"""
    print("\n" + "=" * 60)
    print("🔍 测试 Pose Change Pipeline")
    print("=" * 60)
    
    try:
        from app.services.image.pipelines.pose_change_pipeline import PoseChangePipeline
        
        print("\n[1] 初始化 Pipeline...")
        pipeline = PoseChangePipeline()
        
        if pipeline.comfyui_engine:
            print(f"✅ Pipeline 已成功绑定引擎")
            print(f"   引擎类型: {type(pipeline.comfyui_engine).__name__}")
            return True
        else:
            print("❌ Pipeline 未找到可用引擎")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n")
    print("🚀 RunningHub 集成测试")
    print()
    
    # 测试配置
    config_ok = test_runninghub_config()
    
    # 测试 Pipeline
    pipeline_ok = test_pose_change_pipeline()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    print(f"   配置测试: {'✅ 通过' if config_ok else '❌ 失败'}")
    print(f"   Pipeline 测试: {'✅ 通过' if pipeline_ok else '❌ 失败'}")
    print()
    
    if config_ok and pipeline_ok:
        print("🎉 所有测试通过！RunningHub 已就绪！")
        sys.exit(0)
    else:
        print("⚠️  部分测试失败，请检查配置")
        sys.exit(1)
