"""
OCR Service for Emirates ID and Passport processing
"""
import re
from typing import Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Lazy imports for CV2 and PIL to avoid import errors at startup
CV2_AVAILABLE = False
PIL_AVAILABLE = False
NUMPY_AVAILABLE = False
TESSERACT_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
    NUMPY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OpenCV or NumPy not available: {e}")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PIL not available: {e}")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Tesseract not available: {e}")


class OCRService:
    """
    Service for processing Emirates ID and Passport OCR
    """

    def __init__(self):
        """Initialize OCR service"""
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            logger.warning("OpenCV or NumPy is not available. OCR functionality will be limited.")
        if not PIL_AVAILABLE:
            logger.warning("PIL is not available. OCR functionality will be limited.")
        if not TESSERACT_AVAILABLE:
            logger.warning("Tesseract is not available. OCR functionality will be limited.")

    def preprocess_image(self, image_path: str):
        """
        Preprocess image for better OCR accuracy

        Args:
            image_path: Path to the image file

        Returns:
            Preprocessed image as numpy array
        """
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            raise RuntimeError("OpenCV and NumPy are required for image preprocessing but are not available")

        # Read image
        img = cv2.imread(image_path)

        if img is None:
            raise ValueError(f"Could not read image from {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply adaptive thresholding for better text extraction
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Apply morphological operations to remove noise
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)

        return processed

    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract all text from image using Tesseract OCR

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text as string
        """
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            raise RuntimeError("OpenCV and NumPy are required but not available")
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL is required but not available")
        if not TESSERACT_AVAILABLE:
            logger.error("Tesseract is not available. Cannot perform OCR.")
            raise RuntimeError("Tesseract OCR is not installed. Please install tesseract-ocr system package.")

        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path)

            # Convert back to PIL Image for pytesseract
            pil_img = Image.fromarray(processed_img)

            # Extract text with English and Arabic language support
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(pil_img, config=custom_config, lang='eng+ara')

            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            raise

    def parse_emirates_id(self, text: str) -> Dict[str, any]:
        """
        Parse Emirates ID specific fields from extracted text

        Args:
            text: Extracted text from OCR

        Returns:
            Dictionary with parsed Emirates ID fields
        """
        result = {
            "full_name": None,
            "emirates_id": None,
            "nationality": None,
            "date_of_birth": None,
            "sex": None,
            "expiry": None,
            "confidence": 0.0
        }

        # Clean text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = ' '.join(text.split())  # Remove extra whitespace

        confidence_scores = []

        # Extract Emirates ID number (784-XXXX-XXXXXXX-X format)
        # Pattern: 784 followed by 12 digits, may have dashes or spaces
        eid_patterns = [
            r'784[-\s]?\d{4}[-\s]?\d{7}[-\s]?\d',  # With separators
            r'784\d{12}',  # Without separators
            r'(?:ID|IDN|Card No|Number)[\s:]*([0-9]{15})',  # After ID label
        ]

        for pattern in eid_patterns:
            match = re.search(pattern, text)
            if match:
                eid = match.group(0) if not match.groups() else match.group(1)
                # Normalize format
                eid = re.sub(r'[^\d]', '', eid)  # Remove non-digits
                if len(eid) == 15 and eid.startswith('784'):
                    result["emirates_id"] = f"{eid[:3]}-{eid[3:7]}-{eid[7:14]}-{eid[14]}"
                    confidence_scores.append(0.9)
                    break

        # Extract Name (usually after "Name" or before "Nationality")
        name_patterns = [
            r'(?:Name|Full Name)[\s:]*([A-Z][a-zA-Z\s]{2,50})(?:Nationality|Sex|DOB)',
            r'([A-Z][A-Z\s]{10,50})(?:Nationality|UNITED ARAB EMIRATES)',
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and not any(char.isdigit() for char in name):
                    result["full_name"] = ' '.join(name.split())
                    confidence_scores.append(0.8)
                    break

        # Extract Nationality
        nationality_patterns = [
            r'(?:Nationality|National)[\s:]*([A-Za-z\s]{3,30})(?:Date|DOB|Sex)',
            r'(United Arab Emirates|UAE|India|Pakistan|Bangladesh|Philippines|Egypt)',
        ]

        for pattern in nationality_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nationality = match.group(1).strip()
                result["nationality"] = nationality
                confidence_scores.append(0.8)
                break

        # Extract Date of Birth (DD/MM/YYYY or DD-MM-YYYY or YYYY-MM-DD)
        dob_patterns = [
            r'(?:DOB|Date of Birth|Birth)[\s:]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'(\d{2}[/-]\d{2}[/-]\d{4})',
        ]

        for pattern in dob_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Try parsing date
                    for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                        try:
                            date_obj = datetime.strptime(match, fmt)
                            # Validate reasonable birth year (1920-2024)
                            if 1920 <= date_obj.year <= 2024:
                                result["date_of_birth"] = date_obj.strftime('%Y-%m-%d')
                                confidence_scores.append(0.85)
                                break
                        except ValueError:
                            continue
                    if result["date_of_birth"]:
                        break
                except Exception:
                    continue
            if result["date_of_birth"]:
                break

        # Extract Gender/Sex
        sex_patterns = [
            r'(?:Sex|Gender)[\s:]*([MFmf])',
            r'\b([MF])\b(?:ale)?',
        ]

        for pattern in sex_patterns:
            match = re.search(pattern, text)
            if match:
                sex = match.group(1).upper()
                if sex in ['M', 'F']:
                    result["sex"] = sex
                    confidence_scores.append(0.9)
                    break

        # Extract Expiry Date
        expiry_patterns = [
            r'(?:Expiry|Exp|Valid Until)[\s:]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'(?:Expiry|Exp)[\s:]*(\d{2}[/-]\d{2}[/-]\d{4})',
        ]

        for pattern in expiry_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                        try:
                            date_obj = datetime.strptime(match, fmt)
                            # Expiry should be in future or recent past
                            if 2020 <= date_obj.year <= 2040:
                                result["expiry"] = date_obj.strftime('%Y-%m-%d')
                                confidence_scores.append(0.85)
                                break
                        except ValueError:
                            continue
                    if result["expiry"]:
                        break
                except Exception:
                    continue
            if result["expiry"]:
                break

        # Calculate overall confidence
        if confidence_scores:
            result["confidence"] = sum(confidence_scores) / len(confidence_scores)

        # Add field-level confidence
        result["field_confidence"] = {
            "emirates_id": 0.9 if result["emirates_id"] else 0.0,
            "full_name": 0.8 if result["full_name"] else 0.0,
            "nationality": 0.8 if result["nationality"] else 0.0,
            "date_of_birth": 0.85 if result["date_of_birth"] else 0.0,
            "sex": 0.9 if result["sex"] else 0.0,
            "expiry": 0.85 if result["expiry"] else 0.0,
        }

        return result

    def validate_image_quality(self, image_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image quality for OCR processing

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            return False, "OpenCV and NumPy are required but not available"

        try:
            img = cv2.imread(image_path)

            if img is None:
                return False, "Could not read image file"

            # Check image size (minimum 300x200 pixels)
            height, width = img.shape[:2]
            if width < 300 or height < 200:
                return False, f"Image too small ({width}x{height}). Minimum size: 300x200 pixels"

            # Check if image is too large (> 10MB or > 4000x4000)
            if width > 4000 or height > 4000:
                return False, f"Image too large ({width}x{height}). Maximum size: 4000x4000 pixels"

            # Check brightness (average pixel value)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray)
            if avg_brightness < 30:
                return False, "Image too dark. Please use better lighting"
            if avg_brightness > 225:
                return False, "Image overexposed. Please reduce lighting"

            # Check blur (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 100:
                return False, "Image too blurry. Please hold camera steady"

            return True, None

        except Exception as e:
            return False, f"Image validation error: {str(e)}"

    def process_emirates_id(self, image_path: str) -> Dict[str, any]:
        """
        Complete Emirates ID processing pipeline

        Args:
            image_path: Path to the Emirates ID image

        Returns:
            Dictionary with extracted data and metadata
        """
        result = {
            "success": False,
            "data": None,
            "error": None,
            "raw_text": None,
            "image_quality": None
        }

        try:
            # Step 1: Validate image quality
            is_valid, error_msg = self.validate_image_quality(image_path)
            if not is_valid:
                result["error"] = error_msg
                result["image_quality"] = {"valid": False, "message": error_msg}
                return result

            result["image_quality"] = {"valid": True, "message": "Image quality is good"}

            # Step 2: Extract text from image
            raw_text = self.extract_text_from_image(image_path)
            result["raw_text"] = raw_text

            if not raw_text or len(raw_text) < 10:
                result["error"] = "Could not extract text from image. Please ensure the Emirates ID is clearly visible"
                return result

            # Step 3: Parse Emirates ID fields
            parsed_data = self.parse_emirates_id(raw_text)

            # Step 4: Validate critical fields
            if not parsed_data.get("emirates_id"):
                result["error"] = "Could not extract Emirates ID number. Please retake photo"
                result["data"] = parsed_data  # Still return partial data
                return result

            result["success"] = True
            result["data"] = parsed_data

            return result

        except Exception as e:
            logger.error(f"Error processing Emirates ID: {str(e)}")
            result["error"] = f"Processing error: {str(e)}"
            return result


# Singleton instance
_ocr_service = None


def get_ocr_service() -> OCRService:
    """Get singleton OCR service instance"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
