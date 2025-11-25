"""
Local test script for POSE_CHANGE pipeline using test_image directory
Run this script to test pose transfer without frontend upload
"""
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.image.pipelines.pose_change_pipeline import PoseChangePipeline
from app.services.image.dto import EditTaskInput

def list_test_images():
    """List available test images"""
    test_dir = Path("test_image")
    if not test_dir.exists():
        print(f"❌ Test image directory not found: {test_dir.absolute()}")
        print(f"   Please create it and add test images.")
        return []
    
    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    images = [img for img in test_dir.iterdir() if img.suffix.lower() in image_extensions]
    return images

def test_pose_change(source_image_path: str, pose_image_path: str):
    """
    Test pose change pipeline locally
    
    Args:
        source_image_path: Path to source image
        pose_image_path: Path to pose reference image
    """
    print("=" * 80)
    print("🧪 Testing POSE_CHANGE Pipeline Locally")
    print("=" * 80)
    print()
    print(f"📸 Source Image:  {source_image_path}")
    print(f"🕺 Pose Reference: {pose_image_path}")
    print()
    
    # Verify files exist
    if not Path(source_image_path).exists():
        print(f"❌ Source image not found: {source_image_path}")
        return
    
    if not Path(pose_image_path).exists():
        print(f"❌ Pose image not found: {pose_image_path}")
        return
    
    print("✅ Test images found")
    print()
    
    # Create pipeline
    print("🔧 Initializing PoseChangePipeline...")
    pipeline = PoseChangePipeline()
    
    # Create task input
    task_input = EditTaskInput(
        task_id="test_local_pose_change",
        source_image=source_image_path,  # Use full path directly
        config={
            "pose_image": pose_image_path,  # Use full path directly
            "preserve_face": True,
            "smoothness": 0.7
        },
        progress_callback=None
    )
    
    print("✅ Pipeline initialized")
    print()
    print("🚀 Starting pose transfer...")
    print("-" * 80)
    
    # Execute pipeline
    try:
        result = pipeline.execute(task_input)
        
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
            if result.error_details:
                print(f"📝 Error Details: {result.error_details}")
        
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
    # List available test images
    images = list_test_images()
    
    if not images:
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
        print("⚠️  Warning: Need at least 2 images for pose change test")
        print("   - Image 1: Source image")
        print("   - Image 2: Pose reference")
        print()
        return
    
    # Use first two images by default
    source_image = str(images[0])
    pose_image = str(images[1])
    
    print("🎯 Using:")
    print(f"   Source: {images[0].name}")
    print(f"   Pose:   {images[1].name}")
    print()
    
    # Run test
    test_pose_change(source_image, pose_image)

if __name__ == "__main__":
    main()

