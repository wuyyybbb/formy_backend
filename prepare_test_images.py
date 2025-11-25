"""
Prepare test images for local testing
Copy images from test_image folder to uploads directory with proper file_id naming
"""
import shutil
from pathlib import Path
from datetime import datetime

# Directories
TEST_IMAGE_DIR = Path("test_image")
UPLOAD_DIR = Path("uploads")
SOURCE_DIR = UPLOAD_DIR / "source"
REFERENCE_DIR = UPLOAD_DIR / "reference"

# Ensure upload directories exist
SOURCE_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

print("🖼️  Preparing test images for local testing...")
print("=" * 60)

# List all images in test_image directory
test_images = list(TEST_IMAGE_DIR.glob("*.*"))
image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
test_images = [img for img in test_images if img.suffix.lower() in image_extensions]

if not test_images:
    print(f"❌ No images found in {TEST_IMAGE_DIR}")
    print(f"   Please add test images to: {TEST_IMAGE_DIR.absolute()}")
    exit(1)

print(f"📁 Found {len(test_images)} test image(s):\n")

# Copy images with file_id naming
file_id_mapping = {}
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

for idx, img_path in enumerate(test_images, 1):
    # Generate file_id (simplified version)
    file_id = f"test_{timestamp}_{idx:03d}"
    extension = img_path.suffix.lower()
    
    # Determine subdirectory based on index (first image = source, rest = reference)
    if idx == 1:
        target_dir = SOURCE_DIR
        purpose = "source"
    else:
        target_dir = REFERENCE_DIR
        purpose = "reference"
    
    # Copy file
    target_path = target_dir / f"{file_id}{extension}"
    shutil.copyfile(img_path, target_path)
    
    # Store mapping
    file_id_mapping[img_path.name] = {
        "file_id": file_id,
        "purpose": purpose,
        "original": str(img_path),
        "copied_to": str(target_path),
        "url": f"/uploads/{purpose}/{file_id}{extension}"
    }
    
    print(f"  {idx}. {img_path.name}")
    print(f"     → file_id: {file_id}")
    print(f"     → purpose: {purpose}")
    print(f"     → path: {target_path}")
    print()

print("=" * 60)
print("✅ Test images prepared successfully!")
print()
print("📋 File ID Mapping:")
print("-" * 60)

for original_name, info in file_id_mapping.items():
    print(f"\n{original_name}:")
    print(f"  file_id:  {info['file_id']}")
    print(f"  purpose:  {info['purpose']}")
    print(f"  URL:      {info['url']}")

print()
print("=" * 60)
print("🧪 How to test:")
print()
print("1. Use the file_id values above in your API requests")
print("2. For POSE_CHANGE task, use:")
print(f"   - source_image: \"{list(file_id_mapping.values())[0]['file_id']}\"")
if len(file_id_mapping) > 1:
    print(f"   - config.pose_image: \"{list(file_id_mapping.values())[1]['file_id']}\"")
print()
print("3. Example API request (using curl or Postman):")
print("""
POST /api/v1/tasks
Headers:
  Authorization: Bearer <your_token>
  Content-Type: application/json
Body:
{
  "mode": "POSE_CHANGE",
  "source_image": "<file_id_from_above>",
  "config": {
    "pose_image": "<file_id_from_above>"
  }
}
""")
print("=" * 60)

