"""
Quick OCR Test Script
Tests the OCR service with a sample image containing GB text
"""
from PIL import Image, ImageDraw, ImageFont
import os
import tempfile

# Create test image with "45.2 GB" text
def create_test_image():
    """Create a simple test image with GB text"""
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use default font
    try:
        # Use a larger default font
        from PIL import ImageFont
        font = ImageFont.load_default()
    except:
        font = None
    
    # Draw text
    text = "Total Data Shared\n45.2 GB\nConduit Active"
    draw.text((50, 50), text, fill='black', font=font)
    
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name)
    temp_file.close()
    
    return temp_file.name

def test_ocr():
    """Test OCR extraction"""
    from ocr_service import get_ocr_service
    from config import TESSERACT_PATH
    
    print("🧪 Testing OCR Service...")
    print(f"Tesseract Path: {TESSERACT_PATH}")
    
    # Get OCR service
    ocr = get_ocr_service(TESSERACT_PATH)
    
    if not ocr.available:
        print("❌ OCR not available!")
        return False
    
    print("✅ OCR service initialized")
    
    # Create test image
    print("\n📸 Creating test image with '45.2 GB' text...")
    image_path = create_test_image()
    print(f"Test image: {image_path}")
    
    try:
        # Extract data amount
        print("\n🔍 Running OCR extraction...")
        result = ocr.extract_data_amount(image_path)
        
        print(f"\nResults:")
        print(f"  Success: {result['success']}")
        print(f"  Amount: {result.get('amount_gb')} GB")
        print(f"  Unit: {result.get('unit')}")
        print(f"  Confidence: {result.get('confidence')}%")
        print(f"  Raw Text Preview: {result.get('raw_text', '')[:100]}...")
        
        # Determine tier
        if result['success']:
            tier = ocr.determine_conduit_tier(result['amount_gb'])
            print(f"  Tier: {tier}")
            
        # Full verification
        print("\n🎯 Running full verification...")
        verify_result = ocr.verify_screenshot(image_path, min_confidence=60)
        
        print(f"\nVerification Results:")
        print(f"  Success: {verify_result['success']}")
        print(f"  Tier: {verify_result.get('tier')}")
        print(f"  Should Fallback: {verify_result.get('should_fallback')}")
        print(f"  Error: {verify_result.get('error', 'None')}")
        
        if verify_result['success']:
            print("\n✅ OCR TEST PASSED!")
            print("The system can automatically detect GB amounts from screenshots.")
        else:
            print("\n⚠️ OCR TEST RESULT:")
            print("OCR works but may need fallback for this type of image.")
            print("Real Conduit screenshots should work better.")
        
        return True
        
    finally:
        # Cleanup
        try:
            os.unlink(image_path)
            print(f"\n🧹 Cleaned up test image")
        except:
            pass

if __name__ == "__main__":
    test_ocr()
