"""
Local test script for POSE_CHANGE pipeline using test_image directory
Run this script to test pose transfer without frontend upload
"""
import sys
import os

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    # Try to set UTF-8 encoding for Windows console
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

print("=" * 80)
print("🚀 SCRIPT START - test_pose_change_local.py")
print("=" * 80)
print()

import json
from pathlib import Path

print("[1/5] ✅ Standard library imports completed")
print(f"      Current working directory: {Path.cwd()}")
print(f"      Script location: {Path(__file__).parent.absolute()}")
print()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))
print(f"[2/5] ✅ Added to sys.path: {Path(__file__).parent}")
print(f"      sys.path: {sys.path[:3]}...")  # Show first 3 entries
print()

print("[3/5] 🔄 Importing app modules...")
try:
    from app.services.image.pipelines.pose_change_pipeline import PoseChangePipeline
    print("      ✅ PoseChangePipeline imported")
except Exception as e:
    print(f"      ❌ Failed to import PoseChangePipeline: {e}")
    raise

try:
    from app.services.image.dto import EditTaskInput
    print("      ✅ EditTaskInput imported")
except Exception as e:
    print(f"      ❌ Failed to import EditTaskInput: {e}")
    raise

try:
    from app.services.image.enums import EditMode
    print("      ✅ EditMode imported")
except Exception as e:
    print(f"      ❌ Failed to import EditMode: {e}")
    raise

print("[4/5] ✅ All app module imports completed")
print()

def list_test_images():
    """List available test images"""
    print("[list_test_images] Searching for test images...")
    test_dir = Path("test_image")
    print(f"[list_test_images] Test directory path: {test_dir.absolute()}")
    print(f"[list_test_images] Directory exists: {test_dir.exists()}")
    
    if not test_dir.exists():
        print(f"❌ Test image directory not found: {test_dir.absolute()}")
        print(f"   Please create it and add test images.")
        return []
    
    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    print(f"[list_test_images] Supported extensions: {image_extensions}")
    
    all_files = list(test_dir.iterdir())
    print(f"[list_test_images] Total files in directory: {len(all_files)}")
    
    images = [img for img in all_files if img.suffix.lower() in image_extensions]
    print(f"[list_test_images] Image files found: {len(images)}")
    for img in images:
        print(f"[list_test_images]   - {img.name} ({img.stat().st_size} bytes)")
    
    return images

def test_pose_change(source_image_path: str, pose_image_path: str):
    """
    Test pose change pipeline locally
    
    Args:
        source_image_path: Path to source image
        pose_image_path: Path to pose reference image
    """
    print()
    print("=" * 80)
    print("🧪 Testing POSE_CHANGE Pipeline Locally")
    print("=" * 80)
    print()
    print(f"[test_pose_change] Function called with:")
    print(f"  📸 Source Image:  {source_image_path}")
    print(f"  🕺 Pose Reference: {pose_image_path}")
    print()
    
    # Verify files exist
    print("[test_pose_change] Step 1: Verifying file existence...")
    source_path = Path(source_image_path)
    pose_path = Path(pose_image_path)
    
    print(f"[test_pose_change]   Source exists: {source_path.exists()}")
    print(f"[test_pose_change]   Source absolute: {source_path.absolute()}")
    
    if not source_path.exists():
        print(f"❌ Source image not found: {source_image_path}")
        return
    
    print(f"[test_pose_change]   Pose exists: {pose_path.exists()}")
    print(f"[test_pose_change]   Pose absolute: {pose_path.absolute()}")
    
    if not pose_path.exists():
        print(f"❌ Pose image not found: {pose_image_path}")
        return
    
    print("✅ Test images found")
    print()
    
    # Create pipeline
    print("[test_pose_change] Step 2: Initializing PoseChangePipeline...")
    try:
        pipeline = PoseChangePipeline()
        print("[test_pose_change] ✅ PoseChangePipeline instance created")
    except Exception as e:
        print(f"[test_pose_change] ❌ Failed to create pipeline: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Create task input
    print("[test_pose_change] Step 3: Creating EditTaskInput...")
    print("[test_pose_change]   Preparing task data...")
    print(f"[test_pose_change]   - task_id: test_local_pose_change")
    print(f"[test_pose_change]   - mode: POSE_CHANGE")
    print(f"[test_pose_change]   - source_image: {source_image_path}")
    print(f"[test_pose_change]   - config.pose_image: {pose_image_path}")
    
    try:
        task_input = EditTaskInput(
            task_id="test_local_pose_change",
            mode=EditMode.POSE_CHANGE,  # ← Required field!
            source_image=source_image_path,  # Use full path directly
            config={
                "pose_image": pose_image_path,  # Use full path directly
                "preserve_face": True,
                "smoothness": 0.7
            },
            progress_callback=None
        )
        print("[test_pose_change] ✅ EditTaskInput created successfully:")
        print(f"[test_pose_change]   task_id: {task_input.task_id}")
        print(f"[test_pose_change]   mode: {task_input.mode}")
        print(f"[test_pose_change]   source_image: {task_input.source_image}")
        print(f"[test_pose_change]   config: {task_input.config}")
    except Exception as e:
        print(f"[test_pose_change] ❌ Failed to create task input: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    print("[test_pose_change] Step 4: Executing pipeline...")
    print("🚀 Starting pose transfer...")
    print("-" * 80)
    
    # Execute pipeline
    print("[test_pose_change] Calling pipeline.execute()...")
    try:
        result = pipeline.execute(task_input)
        print("[test_pose_change] ✅ pipeline.execute() returned")
        print(f"[test_pose_change]   result.success: {result.success}")
        
        print()
        print("=" * 80)
        print("📊 Result Summary")
        print("=" * 80)
        print()
        
        if result.success:
            print("✅ Status: SUCCESS")
            print()
            print(f"📁 Output Image:      {result.output_image}")
            print(f"🖼️  Thumbnail:         {result.thumbnail}")
            if result.comparison_image:
                print(f"📊 Comparison Image:  {result.comparison_image}")
            print()
            
            if result.metadata:
                print("📋 Metadata:")
                for key, value in result.metadata.items():
                    print(f"   {key}: {value}")
            print()
            
            print(f"⏱️  Processing Time: {result.processing_time:.2f}s")
            
        else:
            print("❌ Status: FAILED")
            print()
            print(f"🚫 Error Code:    {result.error_code}")
            print(f"💬 Error Message: {result.error_message}")
            # Note: error_details is not in EditTaskResult schema
        
        print()
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ Execution Failed")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("[5/5] 📋 Entering main() function")
    print()
    
    # List available test images
    print("[main] Calling list_test_images()...")
    images = list_test_images()
    print(f"[main] list_test_images() returned {len(images)} image(s)")
    print()
    
    if not images:
        print("[main] No images found - displaying usage instructions")
        print()
        print("=" * 80)
        print("📝 Usage Instructions")
        print("=" * 80)
        print()
        print("1. Create test_image directory:")
        print("   mkdir test_image")
        print()
        print("2. Add at least 2 test images:")
        print("   - Image 1: Source image (person to change pose)")
        print("   - Image 2: Pose reference (target pose)")
        print()
        print("3. Run this script again:")
        print("   python test_pose_change_local.py")
        print()
        return
    
    print()
    print("=" * 80)
    print("📁 Available Test Images")
    print("=" * 80)
    print()
    for idx, img in enumerate(images, 1):
        print(f"  {idx}. {img.name} ({img.stat().st_size // 1024} KB)")
    print()
    
    if len(images) < 2:
        print("[main] Warning: Only 1 image found, need at least 2")
        print("⚠️  Warning: Need at least 2 images for pose change test")
        print("   - Image 1: Source image")
        print("   - Image 2: Pose reference")
        print()
        return
    
    # Use first two images by default
    source_image = str(images[0])
    pose_image = str(images[1])
    
    print("[main] Selected images:")
    print(f"[main]   Source: {source_image}")
    print(f"[main]   Pose:   {pose_image}")
    print()
    
    print("🎯 Using:")
    print(f"   Source: {images[0].name}")
    print(f"   Pose:   {images[1].name}")
    print()
    
    # Run test
    print("[main] Calling test_pose_change()...")
    test_pose_change(source_image, pose_image)
    print()
    print("[main] test_pose_change() completed")
    print()
    print("=" * 80)
    print("✅ SCRIPT END - test_pose_change_local.py")
    print("=" * 80)

if __name__ == "__main__":
    print()
    print("[__main__] Script is being run directly")
    print("[__main__] Calling main()...")
    print()
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("[__main__] ⚠️  Script interrupted by user (Ctrl+C)")
        print()
    except Exception as e:
        print()
        print()
        print("[__main__] ❌ Unhandled exception in main():")
        print(f"[__main__]    {type(e).__name__}: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("=" * 80)
        print("❌ SCRIPT FAILED")
        print("=" * 80)

