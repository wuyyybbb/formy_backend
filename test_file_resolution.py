"""
测试文件路径解析
"""
import sys
import os
from pathlib import Path

# 确保可以导入 app 模块
sys.path.insert(0, str(Path(__file__).parent))

# 模拟不同工作目录的情况
print("=" * 80)
print("测试 file_id 解析功能")
print("=" * 80)

# 测试 1: 从 backend 目录运行
print("\n测试 1: 从 backend 目录运行")
print(f"当前工作目录: {os.getcwd()}")
os.chdir(Path(__file__).parent)
print(f"更改后工作目录: {os.getcwd()}")

try:
    from app.services.image.image_assets import resolve_uploaded_file
    
    # 列出实际存在的文件
    uploads_dir = Path("uploads/source")
    if uploads_dir.exists():
        files = list(uploads_dir.glob("*"))
        print(f"\n📂 uploads/source 中的文件:")
        for f in files:
            print(f"  - {f.name}")
        
        if files:
            # 测试第一个文件
            file_name = files[0].name
            file_id = file_name.rsplit(".", 1)[0]  # 去掉扩展名
            print(f"\n🔍 尝试查找 file_id: {file_id}")
            
            result = resolve_uploaded_file(file_id)
            print(f"✅ 成功找到文件: {result}")
    else:
        print(f"❌ uploads/source 目录不存在")
        
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 测试 2: 从其他目录运行（模拟 worker 场景）
print("\n" + "=" * 80)
print("测试 2: 从项目根目录运行（模拟 worker 场景）")
print("=" * 80)

os.chdir(Path(__file__).parent.parent)
print(f"当前工作目录: {os.getcwd()}")

# 重新导入（避免缓存）
import importlib
try:
    import app.services.image.image_assets as img_assets
    importlib.reload(img_assets)
    from app.services.image.image_assets import resolve_uploaded_file
    
    # 列出实际存在的文件
    uploads_dir = Path("backend/uploads/source")
    if uploads_dir.exists():
        files = list(uploads_dir.glob("*"))
        print(f"\n📂 backend/uploads/source 中的文件:")
        for f in files[:3]:  # 只显示前3个
            print(f"  - {f.name}")
        
        if files:
            # 测试第一个文件
            file_name = files[0].name
            file_id = file_name.rsplit(".", 1)[0]  # 去掉扩展名
            print(f"\n🔍 尝试查找 file_id: {file_id}")
            
            result = resolve_uploaded_file(file_id)
            print(f"✅ 成功找到文件: {result}")
    else:
        print(f"❌ backend/uploads/source 目录不存在")
        
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ 测试完成")
print("=" * 80)
