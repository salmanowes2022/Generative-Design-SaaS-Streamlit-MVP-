"""
Validator v2
Comprehensive brand compliance validation with color science
- ΔE (CIE2000) color matching
- WCAG contrast ratios
- Policy checks
- On-brand scoring (0-100)
"""
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image
import io
import requests
import numpy as np
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from app.core.brand_brain import BrandTokens, BrandPolicies
from app.infra.logging import get_logger

logger = get_logger(__name__)


class ValidatorV2:
    """Brand compliance validator with color science and scoring"""

    # Scoring weights
    WEIGHT_COLOR = 0.40
    WEIGHT_CONTRAST = 0.30
    WEIGHT_POLICY = 0.30

    # Thresholds
    DELTA_E_EXCELLENT = 5.0  # ΔE < 5 is excellent match
    DELTA_E_GOOD = 10.0      # ΔE < 10 is good match
    DELTA_E_ACCEPTABLE = 20.0  # ΔE < 20 is acceptable
    WCAG_AA_NORMAL = 4.5     # WCAG AA for normal text
    WCAG_AA_LARGE = 3.0      # WCAG AA for large text
    WCAG_AAA_NORMAL = 7.0    # WCAG AAA for normal text

    def validate_asset(
        self,
        image_url: str,
        tokens: BrandTokens,
        policies: Optional[BrandPolicies] = None,
        text_on_image: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of asset against brand

        Args:
            image_url: URL of asset to validate
            tokens: Brand design tokens
            policies: Brand policies (optional)
            text_on_image: Text overlaid on image for contrast checking (optional)

        Returns:
            {
                "on_brand_score": int (0-100),
                "passed": bool,
                "color_validation": Dict,
                "contrast_validation": Dict,
                "policy_validation": Dict,
                "reasons": List[str],
                "suggestions": List[str]
            }
        """
        try:
            # Download image
            logger.info(f"Validating asset from {image_url[:50]}...")
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))

            # Run validations
            color_result = self.validate_colors(image, tokens)
            contrast_result = self.validate_contrast(image, tokens, text_on_image)
            policy_result = self.validate_policies(text_on_image, policies) if policies else {"score": 100, "violations": []}

            # Calculate weighted score
            on_brand_score = int(
                color_result["score"] * self.WEIGHT_COLOR +
                contrast_result["score"] * self.WEIGHT_CONTRAST +
                policy_result["score"] * self.WEIGHT_POLICY
            )

            # Collect reasons and suggestions
            reasons = []
            suggestions = []

            if color_result["score"] < 70:
                reasons.append(f"Color match: {color_result['score']}/100 (ΔE: {color_result['avg_delta_e']:.1f})")
                suggestions.append(color_result.get("suggestion", "Use brand colors more prominently"))

            if contrast_result["score"] < 70:
                reasons.append(f"Contrast: {contrast_result['score']}/100")
                if contrast_result.get("violations"):
                    reasons.extend(contrast_result["violations"])
                suggestions.append("Ensure text meets WCAG AA contrast requirements")

            if policy_result["score"] < 100:
                reasons.extend(policy_result["violations"])
                suggestions.append("Review text against brand voice guidelines")

            # Determine pass/fail
            passed = on_brand_score >= 70

            logger.info(f"Validation complete: Score {on_brand_score}/100, Passed: {passed}")

            return {
                "on_brand_score": on_brand_score,
                "passed": passed,
                "color_validation": color_result,
                "contrast_validation": contrast_result,
                "policy_validation": policy_result,
                "reasons": reasons if reasons else ["All brand guidelines met"],
                "suggestions": suggestions
            }

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return {
                "on_brand_score": 50,
                "passed": False,
                "color_validation": {"score": 0, "error": str(e)},
                "contrast_validation": {"score": 0},
                "policy_validation": {"score": 0},
                "reasons": [f"Validation error: {str(e)}"],
                "suggestions": ["Re-generate asset"]
            }

    def validate_colors(self, image: Image.Image, tokens: BrandTokens) -> Dict[str, Any]:
        """
        Validate color palette using ΔE (CIE2000)

        Args:
            image: PIL Image
            tokens: Brand design tokens with color palette

        Returns:
            {
                "score": int (0-100),
                "avg_delta_e": float,
                "color_matches": List[Dict],
                "dominant_colors": List[str],
                "suggestion": str
            }
        """
        try:
            # Extract dominant colors from image
            dominant_colors = self._extract_dominant_colors(image, n_colors=5)

            # Get brand colors
            brand_colors = []
            if tokens.color.get("primary"):
                brand_colors.append(tokens.color["primary"])
            if tokens.color.get("secondary"):
                brand_colors.append(tokens.color["secondary"])
            if tokens.color.get("accent"):
                brand_colors.append(tokens.color["accent"])

            if not brand_colors:
                logger.warning("No brand colors defined, skipping color validation")
                return {"score": 100, "avg_delta_e": 0.0, "color_matches": [], "dominant_colors": dominant_colors}

            # Calculate ΔE for each dominant color vs each brand color
            color_matches = []
            min_delta_es = []

            for dom_color in dominant_colors:
                best_match = None
                min_delta_e = float('inf')

                for brand_color in brand_colors:
                    delta_e = self._calculate_delta_e(dom_color, brand_color)
                    if delta_e < min_delta_e:
                        min_delta_e = delta_e
                        best_match = brand_color

                color_matches.append({
                    "image_color": dom_color,
                    "brand_color": best_match,
                    "delta_e": min_delta_e,
                    "match_quality": self._delta_e_to_quality(min_delta_e)
                })
                min_delta_es.append(min_delta_e)

            # Calculate average ΔE (lower is better)
            avg_delta_e = sum(min_delta_es) / len(min_delta_es)

            # Convert ΔE to score (0-100)
            if avg_delta_e < self.DELTA_E_EXCELLENT:
                score = 100
            elif avg_delta_e < self.DELTA_E_GOOD:
                score = 90 - int((avg_delta_e - self.DELTA_E_EXCELLENT) * 2)
            elif avg_delta_e < self.DELTA_E_ACCEPTABLE:
                score = 70 - int((avg_delta_e - self.DELTA_E_GOOD) * 2)
            else:
                score = max(0, 50 - int(avg_delta_e - self.DELTA_E_ACCEPTABLE))

            suggestion = ""
            if score < 70:
                suggestion = f"Use brand colors {', '.join(brand_colors[:3])} more prominently"

            return {
                "score": score,
                "avg_delta_e": round(avg_delta_e, 2),
                "color_matches": color_matches,
                "dominant_colors": dominant_colors,
                "suggestion": suggestion
            }

        except Exception as e:
            logger.error(f"Color validation error: {str(e)}")
            return {"score": 50, "error": str(e), "dominant_colors": []}

    def validate_contrast(
        self,
        image: Image.Image,
        tokens: BrandTokens,
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate WCAG contrast ratios

        Args:
            image: PIL Image
            tokens: Brand design tokens
            text: Text overlay (optional)

        Returns:
            {
                "score": int (0-100),
                "ratios": List[Dict],
                "violations": List[str],
                "meets_wcag_aa": bool
            }
        """
        if not text:
            # No text, perfect contrast score
            return {"score": 100, "ratios": [], "violations": [], "meets_wcag_aa": True}

        try:
            # Get text color from tokens
            text_color = tokens.color.get("text", "#000000")

            # Sample background colors from image
            bg_colors = self._sample_background_colors(image)

            # Calculate contrast ratios
            ratios = []
            violations = []

            for bg_color in bg_colors:
                ratio = self._calculate_contrast_ratio(text_color, bg_color)
                ratios.append({
                    "background": bg_color,
                    "text": text_color,
                    "ratio": round(ratio, 2)
                })

                # Check WCAG AA compliance
                if ratio < self.WCAG_AA_NORMAL:
                    violations.append(
                        f"Low contrast {ratio:.1f}:1 on {bg_color} "
                        f"(need {self.WCAG_AA_NORMAL}:1 for WCAG AA)"
                    )

            # Calculate score
            avg_ratio = sum(r["ratio"] for r in ratios) / len(ratios)
            meets_wcag_aa = avg_ratio >= self.WCAG_AA_NORMAL

            if meets_wcag_aa:
                score = 100
            elif avg_ratio >= self.WCAG_AA_LARGE:
                score = 80
            else:
                score = max(0, int(avg_ratio / self.WCAG_AA_NORMAL * 70))

            return {
                "score": score,
                "ratios": ratios,
                "violations": violations,
                "meets_wcag_aa": meets_wcag_aa
            }

        except Exception as e:
            logger.error(f"Contrast validation error: {str(e)}")
            return {"score": 50, "error": str(e), "ratios": [], "violations": [], "meets_wcag_aa": False}

    def validate_policies(self, text: Optional[str], policies: Optional[BrandPolicies]) -> Dict[str, Any]:
        """
        Validate text against brand policies

        Args:
            text: Text to validate
            policies: Brand policies

        Returns:
            {
                "score": int (0-100),
                "violations": List[str]
            }
        """
        if not text or not policies:
            return {"score": 100, "violations": []}

        violations = []
        text_lower = text.lower()

        # Check forbidden terms
        if policies.forbid:
            for term in policies.forbid:
                if term.lower() in text_lower:
                    violations.append(f"Contains forbidden term: '{term}'")

        # Calculate score (10 points deducted per violation)
        score = max(0, 100 - len(violations) * 10)

        return {
            "score": score,
            "violations": violations
        }

    # Helper methods

    def _extract_dominant_colors(self, image: Image.Image, n_colors: int = 5) -> List[str]:
        """Extract dominant colors from image using k-means clustering"""
        try:
            # Resize for performance
            img = image.copy()
            img.thumbnail((200, 200))
            img = img.convert('RGB')

            # Get pixel data
            pixels = np.array(img).reshape(-1, 3)

            # Simple histogram-based approach (faster than k-means)
            # Quantize to 32 colors and find most common
            quantized = (pixels // 32) * 32
            unique, counts = np.unique(quantized, axis=0, return_counts=True)

            # Sort by count and take top n_colors
            sorted_indices = np.argsort(counts)[::-1]
            top_colors = unique[sorted_indices[:n_colors]]

            # Convert to hex
            hex_colors = [
                f"#{r:02x}{g:02x}{b:02x}"
                for r, g, b in top_colors
            ]

            return hex_colors

        except Exception as e:
            logger.error(f"Color extraction error: {str(e)}")
            return []

    def _sample_background_colors(self, image: Image.Image, n_samples: int = 3) -> List[str]:
        """Sample background colors from different regions of image"""
        try:
            img = image.convert('RGB')
            w, h = img.size

            # Sample from different regions
            regions = [
                (w // 4, h // 4),      # Top-left
                (3 * w // 4, h // 4),  # Top-right
                (w // 2, h // 2),      # Center
            ]

            colors = []
            for x, y in regions:
                r, g, b = img.getpixel((x, y))
                colors.append(f"#{r:02x}{g:02x}{b:02x}")

            return colors

        except Exception as e:
            logger.error(f"Background sampling error: {str(e)}")
            return ["#ffffff"]

    def _calculate_delta_e(self, color1: str, color2: str) -> float:
        """
        Calculate ΔE (CIE2000) between two hex colors

        Args:
            color1: Hex color #RRGGBB
            color2: Hex color #RRGGBB

        Returns:
            Delta E value (0 = identical, >50 = very different)
        """
        try:
            # Convert hex to RGB
            rgb1 = self._hex_to_rgb(color1)
            rgb2 = self._hex_to_rgb(color2)

            # Convert to Lab color space
            srgb1 = sRGBColor(rgb1[0] / 255.0, rgb1[1] / 255.0, rgb1[2] / 255.0)
            srgb2 = sRGBColor(rgb2[0] / 255.0, rgb2[1] / 255.0, rgb2[2] / 255.0)

            lab1 = convert_color(srgb1, LabColor)
            lab2 = convert_color(srgb2, LabColor)

            # Calculate ΔE using CIE2000
            delta_e = delta_e_cie2000(lab1, lab2)

            return float(delta_e)

        except Exception as e:
            logger.error(f"Delta E calculation error: {str(e)}")
            return 100.0  # Return high value on error

    def _calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """
        Calculate WCAG contrast ratio between two colors

        Args:
            color1: Hex color #RRGGBB
            color2: Hex color #RRGGBB

        Returns:
            Contrast ratio (1.0 to 21.0)
        """
        try:
            # Calculate relative luminance
            L1 = self._relative_luminance(color1)
            L2 = self._relative_luminance(color2)

            # WCAG formula
            lighter = max(L1, L2)
            darker = min(L1, L2)
            ratio = (lighter + 0.05) / (darker + 0.05)

            return ratio

        except Exception as e:
            logger.error(f"Contrast ratio error: {str(e)}")
            return 1.0

    def _relative_luminance(self, hex_color: str) -> float:
        """Calculate relative luminance for WCAG contrast"""
        try:
            r, g, b = self._hex_to_rgb(hex_color)

            # Normalize to 0-1
            r, g, b = r / 255.0, g / 255.0, b / 255.0

            # Apply gamma correction
            def gamma(c):
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

            r, g, b = gamma(r), gamma(g), gamma(b)

            # Calculate luminance
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        except Exception as e:
            logger.error(f"Luminance calculation error: {str(e)}")
            return 0.5

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _delta_e_to_quality(self, delta_e: float) -> str:
        """Convert ΔE value to human-readable quality"""
        if delta_e < self.DELTA_E_EXCELLENT:
            return "excellent"
        elif delta_e < self.DELTA_E_GOOD:
            return "good"
        elif delta_e < self.DELTA_E_ACCEPTABLE:
            return "acceptable"
        else:
            return "poor"


# Global validator instance
validator_v2 = ValidatorV2()
