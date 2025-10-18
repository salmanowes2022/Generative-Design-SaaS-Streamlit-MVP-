"""
OCR Validator
Blocks AI-generated backgrounds that accidentally contain text
Fast OCR check before accepting any background image
"""
from typing import Tuple, Dict, Any, Optional
from PIL import Image
import pytesseract
import io
import requests
from app.infra.logging import get_logger

logger = get_logger(__name__)


class OCRValidator:
    """Fast OCR gate to reject backgrounds with accidental text"""

    def __init__(self, confidence_threshold: int = 60, min_text_length: int = 3):
        """
        Initialize OCR validator

        Args:
            confidence_threshold: Minimum OCR confidence to consider text real (0-100)
            min_text_length: Minimum characters to reject (filters noise)
        """
        self.confidence_threshold = confidence_threshold
        self.min_text_length = min_text_length

    def validate_background(self, image_url: str) -> Dict[str, Any]:
        """
        Validate that background has no text

        Args:
            image_url: URL of generated background image

        Returns:
            {
                "passed": bool,
                "has_text": bool,
                "detected_text": str,
                "confidence": float,
                "reason": str
            }
        """
        try:
            # Download image
            logger.info(f"Downloading image from {image_url[:50]}...")
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            # Open as PIL Image
            image = Image.open(io.BytesIO(response.content))

            # Run OCR
            has_text, detected_text, confidence = self.has_text(image)

            if has_text:
                logger.warning(f"OCR gate FAILED: Detected text '{detected_text}' with {confidence}% confidence")
                return {
                    "passed": False,
                    "has_text": True,
                    "detected_text": detected_text,
                    "confidence": confidence,
                    "reason": f"Background contains text: '{detected_text}'"
                }

            logger.info("OCR gate PASSED: No text detected")
            return {
                "passed": True,
                "has_text": False,
                "detected_text": "",
                "confidence": 0.0,
                "reason": "Clean background, no text detected"
            }

        except Exception as e:
            logger.error(f"OCR validation error: {str(e)}")
            # On error, allow image through (fail open)
            # We don't want OCR errors to block generation
            return {
                "passed": True,
                "has_text": False,
                "detected_text": "",
                "confidence": 0.0,
                "reason": f"OCR check failed, allowing image: {str(e)}"
            }

    def has_text(self, image: Image.Image) -> Tuple[bool, str, float]:
        """
        Run Tesseract OCR on image to detect text

        Args:
            image: PIL Image

        Returns:
            (has_text, detected_text, confidence)
        """
        try:
            # Resize for faster OCR (max 1024px on longest side)
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Convert to RGB if needed
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')

            # Run Tesseract with detailed output
            ocr_data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                config='--psm 11'  # Sparse text mode
            )

            # Filter high-confidence text
            detected_words = []
            confidences = []

            for i, conf in enumerate(ocr_data['conf']):
                # Skip low confidence detections
                if int(conf) < self.confidence_threshold:
                    continue

                word = ocr_data['text'][i].strip()

                # Skip empty or very short words (noise)
                if len(word) < self.min_text_length:
                    continue

                detected_words.append(word)
                confidences.append(int(conf))

            # Calculate results
            if detected_words:
                detected_text = ' '.join(detected_words)
                avg_confidence = sum(confidences) / len(confidences)
                logger.info(f"OCR detected text: '{detected_text}' (confidence: {avg_confidence:.1f}%)")
                return True, detected_text, avg_confidence

            logger.debug("No text detected in image")
            return False, "", 0.0

        except Exception as e:
            logger.error(f"Tesseract OCR error: {str(e)}")
            # On OCR failure, assume no text (fail open)
            return False, "", 0.0

    def validate_with_retry(
        self,
        image_url: str,
        max_attempts: int = 3,
        regenerate_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Validate background with automatic regeneration on text detection

        Args:
            image_url: URL of generated background
            max_attempts: Maximum regeneration attempts
            regenerate_callback: Function to call to regenerate image (returns new URL)

        Returns:
            {
                "passed": bool,
                "final_url": str,
                "attempts": int,
                "validation_results": List[Dict]
            }
        """
        validation_results = []
        current_url = image_url

        for attempt in range(max_attempts):
            logger.info(f"OCR validation attempt {attempt + 1}/{max_attempts}")

            result = self.validate_background(current_url)
            validation_results.append(result)

            if result["passed"]:
                return {
                    "passed": True,
                    "final_url": current_url,
                    "attempts": attempt + 1,
                    "validation_results": validation_results
                }

            # Text detected, need to regenerate
            if attempt < max_attempts - 1 and regenerate_callback:
                logger.warning(f"Text detected, regenerating... (attempt {attempt + 1})")
                try:
                    current_url = regenerate_callback()
                    logger.info(f"Regenerated new image: {current_url[:50]}...")
                except Exception as e:
                    logger.error(f"Regeneration failed: {str(e)}")
                    break
            else:
                logger.error(f"Max attempts reached or no regenerate callback")
                break

        # Failed all attempts
        return {
            "passed": False,
            "final_url": current_url,
            "attempts": len(validation_results),
            "validation_results": validation_results
        }


# Global OCR validator instance
ocr_validator = OCRValidator(confidence_threshold=60, min_text_length=3)
