"""
OCR Service for Conduit Screenshot Verification
Extracts data amount (GB) from Psiphon/Conduit screenshots
"""
import re
import logging
from typing import Optional, Dict, Tuple
from PIL import Image, ImageEnhance, ImageFilter
import os

logger = logging.getLogger(__name__)

# Try to import pytesseract
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logger.warning("pytesseract not imported - OCR will be disabled")


class OCRService:
    """OCR service for extracting data amounts from screenshots"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize OCR service
        
        Args:
            tesseract_path: Path to tesseract executable (optional)
        """
        self.available = PYTESSERACT_AVAILABLE
        
        if tesseract_path and PYTESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        if not self.available:
            logger.warning("⚠️ OCR service unavailable - Tesseract not installed")
    
    def preprocess_image(self, image_path: str) -> Image.Image:
        """
        Preprocess image for better OCR accuracy
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Open image
            img = Image.open(image_path)
            
            # Convert to grayscale
            img = img.convert('L')
            
            # Increase contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # Sharpen
            img = img.filter(ImageFilter.SHARPEN)
            
            # Increase brightness slightly
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.2)
            
            return img
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            # Return original if preprocessing fails
            return Image.open(image_path)
    
    def clean_ocr_text(self, text: str) -> str:
        """
        Clean OCR output text - fix common OCR errors
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        # Common OCR character mistakes
        text = text.replace('O', '0')  # Letter O → Zero
        text = text.replace('o', '0')  # Lowercase o → Zero
        text = text.replace('l', '1')  # Lowercase L → One
        text = text.replace('I', '1')  # Capital I → One
        text = text.replace('S', '5')  # S → 5 (common in poor OCR)
        text = text.replace(',', '.')  # Comma decimals to periods
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def extract_data_amount(self, image_path: str) -> Dict[str, any]:
        """
        Extract data amount (GB/MB/TB) from screenshot
        
        Args:
            image_path: Path to screenshot file
            
        Returns:
            Dict with:
                - success (bool): Whether extraction succeeded
                - amount_gb (float): Amount in GB (None if failed)
                - unit (str): Original unit ('GB', 'MB', 'TB')
                - confidence (int): OCR confidence 0-100
                - raw_text (str): Raw OCR text for debugging
        """
        if not self.available:
            return {
                'success': False,
                'amount_gb': None,
                'unit': None,
                'confidence': 0,
                'raw_text': '',
                'error': 'OCR not available - Tesseract not installed'
            }
        
        try:
            # Preprocess image
            img = self.preprocess_image(image_path)
            
            # Perform OCR with confidence data
            ocr_data = pytesseract.image_to_data(
                img,
                lang='eng',  # Psiphon uses English UI
                output_type=pytesseract.Output.DICT
            )
            
            # Extract full text
            raw_text = pytesseract.image_to_string(img, lang='eng')
            
            # Clean text
            cleaned_text = self.clean_ocr_text(raw_text)
            
            # Calculate average confidence (for words with confidence > 0)
            confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) // len(confidences) if confidences else 0
            
            logger.info(f"OCR extracted text: {cleaned_text[:100]}...")
            logger.info(f"OCR confidence: {avg_confidence}%")
            
            # Extract GB/MB/TB values
            amount_gb, unit = self._extract_gb_value(cleaned_text)
            
            if amount_gb is not None:
                return {
                    'success': True,
                    'amount_gb': amount_gb,
                    'unit': unit,
                    'confidence': avg_confidence,
                    'raw_text': raw_text[:500]  # Truncate for logging
                }
            else:
                return {
                    'success': False,
                    'amount_gb': None,
                    'unit': None,
                    'confidence': avg_confidence,
                    'raw_text': raw_text[:500],
                    'error': 'Could not extract data amount from text'
                }
                
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}", exc_info=True)
            return {
                'success': False,
                'amount_gb': None,
                'unit': None,
                'confidence': 0,
                'raw_text': '',
                'error': str(e)
            }
    
    def _extract_gb_value(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Extract GB value from text using regex patterns
        
        Args:
            text: Cleaned OCR text
            
        Returns:
            Tuple of (amount_in_gb, original_unit) or (None, None)
        """
        # Pattern 1: Match GB values
        gb_pattern = r'(\d+(?:\.\d+)?)\s*(?:GB|gb|Gb|gB)'
        match = re.search(gb_pattern, text, re.IGNORECASE)
        if match:
            try:
                gb_value = float(match.group(1))
                logger.info(f"Found GB value: {gb_value} GB")
                return gb_value, 'GB'
            except ValueError:
                pass
        
        # Pattern 2: Match MB values (convert to GB)
        mb_pattern = r'(\d+(?:\.\d+)?)\s*(?:MB|mb|Mb|mB)'
        match = re.search(mb_pattern, text, re.IGNORECASE)
        if match:
            try:
                mb_value = float(match.group(1))
                gb_value = mb_value / 1024
                logger.info(f"Found MB value: {mb_value} MB = {gb_value:.2f} GB")
                return gb_value, 'MB'
            except ValueError:
                pass
        
        # Pattern 3: Match TB values (convert to GB)
        tb_pattern = r'(\d+(?:\.\d+)?)\s*(?:TB|tb|Tb|tB)'
        match = re.search(tb_pattern, text, re.IGNORECASE)
        if match:
            try:
                tb_value = float(match.group(1))
                gb_value = tb_value * 1024
                logger.info(f"Found TB value: {tb_value} TB = {gb_value:.2f} GB")
                return gb_value, 'TB'
            except ValueError:
                pass
        
        # Pattern 4: Look for keywords + numbers (e.g., "Total: 45.2 GB")
        keyword_pattern = r'(?:total|shared|sent|uploaded|data|traffic|bandwidth)[:\s]+(\d+(?:\.\d+)?)\s*(?:GB|MB|TB)'
        match = re.search(keyword_pattern, text, re.IGNORECASE)
        if match:
            # Retry extraction with the matched segment
            return self._extract_gb_value(match.group(0))
        
        logger.warning("No data amount found in OCR text")
        return None, None
    
    def determine_conduit_tier(self, gb_amount: float) -> Optional[str]:
        """
        Determine Conduit tier based on GB amount
        
        Args:
            gb_amount: Amount in GB
            
        Returns:
            Tier name ('1-10', '11-50', etc.) or None
        """
        if gb_amount is None or gb_amount < 1:
            return None
        
        # Based on CONDUIT_TIERS in config.py
        if 1 <= gb_amount <= 10:
            return '1-10'
        elif 11 <= gb_amount <= 50:
            return '11-50'
        elif 51 <= gb_amount <= 100:
            return '51-100'
        elif 101 <= gb_amount <= 500:
            return '101-500'
        elif gb_amount > 500:
            return '500+'
        
        return None
    
    def verify_screenshot(self, image_path: str, min_confidence: int = 60) -> Dict[str, any]:
        """
        Complete verification workflow for Conduit screenshot
        
        Args:
            image_path: Path to screenshot
            min_confidence: Minimum confidence threshold (0-100)
            
        Returns:
            Dict with:
                - success (bool): Whether verification succeeded
                - tier (str): Tier name or None
                - amount_gb (float): Amount in GB or None
                - confidence (int): OCR confidence
                - should_fallback (bool): Whether to show manual selection
        """
        # Extract data amount
        result = self.extract_data_amount(image_path)
        
        if not result['success']:
            return {
                'success': False,
                'tier': None,
                'amount_gb': None,
                'confidence': result.get('confidence', 0),
                'should_fallback': True,
                'error': result.get('error', 'Unknown error')
            }
        
        # Check confidence threshold
        if result['confidence'] < min_confidence:
            logger.warning(f"OCR confidence too low: {result['confidence']}% < {min_confidence}%")
            return {
                'success': False,
                'tier': None,
                'amount_gb': result['amount_gb'],
                'confidence': result['confidence'],
                'should_fallback': True,
                'error': f"Low confidence: {result['confidence']}%"
            }
        
        # Determine tier
        tier = self.determine_conduit_tier(result['amount_gb'])
        
        if tier is None:
            return {
                'success': False,
                'tier': None,
                'amount_gb': result['amount_gb'],
                'confidence': result['confidence'],
                'should_fallback': True,
                'error': 'Invalid data amount'
            }
        
        return {
            'success': True,
            'tier': tier,
            'amount_gb': result['amount_gb'],
            'confidence': result['confidence'],
            'should_fallback': False
        }


# Global OCR service instance
_ocr_service = None

def get_ocr_service(tesseract_path: Optional[str] = None) -> OCRService:
    """
    Get global OCR service instance (singleton)
    
    Args:
        tesseract_path: Path to tesseract executable
        
    Returns:
        OCRService instance
    """
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService(tesseract_path)
    return _ocr_service
