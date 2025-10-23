"""
Contrast Manager
Ensures WCAG-compliant accessibility and optimal visual hierarchy
"""
from typing import Tuple, Dict, Any, Optional, List
from dataclasses import dataclass
import colorsys
from app.infra.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ContrastResult:
    """Result of contrast check"""
    ratio: float
    passes_aa: bool  # WCAG AA (4.5:1 for normal text, 3:1 for large)
    passes_aaa: bool  # WCAG AAA (7:1 for normal text, 4.5:1 for large)
    recommendation: Optional[str] = None


class ContrastManager:
    """
    Manages color contrast and accessibility

    Features:
    - WCAG AA/AAA contrast ratio calculation
    - Automatic color adjustments for readability
    - Dynamic overlay opacity
    - Color harmony validation
    """

    # WCAG contrast thresholds
    WCAG_AA_NORMAL = 4.5  # Normal text
    WCAG_AA_LARGE = 3.0   # Large text (18pt+ or 14pt+ bold)
    WCAG_AAA_NORMAL = 7.0
    WCAG_AAA_LARGE = 4.5

    def __init__(self):
        """Initialize contrast manager"""
        pass

    def calculate_contrast_ratio(
        self,
        foreground: str,
        background: str
    ) -> float:
        """
        Calculate WCAG contrast ratio between two colors

        Args:
            foreground: Foreground color (hex)
            background: Background color (hex)

        Returns:
            Contrast ratio (1-21)
        """
        fg_rgb = self._hex_to_rgb(foreground)
        bg_rgb = self._hex_to_rgb(background)

        fg_lum = self._relative_luminance(fg_rgb)
        bg_lum = self._relative_luminance(bg_rgb)

        lighter = max(fg_lum, bg_lum)
        darker = min(fg_lum, bg_lum)

        ratio = (lighter + 0.05) / (darker + 0.05)
        return round(ratio, 2)

    def check_contrast(
        self,
        foreground: str,
        background: str,
        is_large_text: bool = False
    ) -> ContrastResult:
        """
        Check if color combination meets WCAG standards

        Args:
            foreground: Foreground color (hex)
            background: Background color (hex)
            is_large_text: Whether text is large (18pt+ or 14pt+ bold)

        Returns:
            ContrastResult
        """
        ratio = self.calculate_contrast_ratio(foreground, background)

        aa_threshold = self.WCAG_AA_LARGE if is_large_text else self.WCAG_AA_NORMAL
        aaa_threshold = self.WCAG_AAA_LARGE if is_large_text else self.WCAG_AAA_NORMAL

        passes_aa = ratio >= aa_threshold
        passes_aaa = ratio >= aaa_threshold

        # Generate recommendation
        recommendation = None
        if not passes_aa:
            recommendation = f"Contrast too low ({ratio}:1). Need {aa_threshold}:1 for WCAG AA. Consider darker foreground or lighter background."
        elif not passes_aaa:
            recommendation = f"Passes WCAG AA but not AAA ({ratio}:1). Consider improving to {aaa_threshold}:1 for better accessibility."

        return ContrastResult(
            ratio=ratio,
            passes_aa=passes_aa,
            passes_aaa=passes_aaa,
            recommendation=recommendation
        )

    def ensure_readable_text(
        self,
        text_color: str,
        background_color: str,
        min_ratio: float = WCAG_AA_NORMAL,
        prefer_lighter: bool = True
    ) -> str:
        """
        Adjust text color to meet minimum contrast ratio

        Args:
            text_color: Original text color (hex)
            background_color: Background color (hex)
            min_ratio: Minimum contrast ratio to achieve
            prefer_lighter: If True, try lightening text first, else darken

        Returns:
            Adjusted text color (hex)
        """
        current_ratio = self.calculate_contrast_ratio(text_color, background_color)

        if current_ratio >= min_ratio:
            return text_color  # Already good

        logger.info(f"Adjusting text color for contrast: {current_ratio:.2f} → {min_ratio}")

        # Convert to HSL for easier adjustment
        text_rgb = self._hex_to_rgb(text_color)
        h, s, l = colorsys.rgb_to_hls(*[x/255 for x in text_rgb])

        # Try adjusting lightness
        step = 0.05 if prefer_lighter else -0.05
        max_iterations = 20

        for _ in range(max_iterations):
            # Adjust lightness
            l = max(0, min(1, l + step))

            # Convert back to RGB
            adjusted_rgb = colorsys.hls_to_rgb(h, l, s)
            adjusted_rgb = tuple(int(x * 255) for x in adjusted_rgb)
            adjusted_hex = self._rgb_to_hex(adjusted_rgb)

            # Check new contrast
            new_ratio = self.calculate_contrast_ratio(adjusted_hex, background_color)

            if new_ratio >= min_ratio:
                logger.info(f"✅ Achieved contrast: {new_ratio:.2f}")
                return adjusted_hex

            # If we hit bounds, reverse direction
            if l == 0 or l == 1:
                step = -step

        # If still can't achieve, use pure white or black
        white_ratio = self.calculate_contrast_ratio("#FFFFFF", background_color)
        black_ratio = self.calculate_contrast_ratio("#000000", background_color)

        if white_ratio >= black_ratio:
            logger.warning("Using white for contrast")
            return "#FFFFFF"
        else:
            logger.warning("Using black for contrast")
            return "#000000"

    def calculate_overlay_opacity(
        self,
        background_brightness: float,
        target_contrast: float = WCAG_AA_NORMAL
    ) -> float:
        """
        Calculate optimal overlay opacity for text on images

        Args:
            background_brightness: Average brightness of background (0-1)
            target_contrast: Target contrast ratio

        Returns:
            Opacity value (0-1)
        """
        # Brighter backgrounds need darker overlays
        if background_brightness > 0.7:
            # Very bright - need significant darkening
            opacity = 0.6 + (background_brightness - 0.7) * 0.5
        elif background_brightness > 0.4:
            # Medium - moderate overlay
            opacity = 0.3 + (background_brightness - 0.4) * 0.5
        else:
            # Dark - minimal overlay or none
            opacity = max(0, background_brightness * 0.3)

        opacity = min(0.8, max(0, opacity))  # Clamp to 0-0.8

        logger.info(f"Calculated overlay opacity: {opacity:.2f} for brightness {background_brightness:.2f}")
        return opacity

    def suggest_color_adjustments(
        self,
        foreground: str,
        background: str,
        is_large_text: bool = False
    ) -> Dict[str, Any]:
        """
        Suggest color adjustments to improve contrast

        Args:
            foreground: Foreground color (hex)
            background: Background color (hex)
            is_large_text: Whether text is large

        Returns:
            Dict with suggestions
        """
        result = self.check_contrast(foreground, background, is_large_text)

        if result.passes_aa:
            return {
                "status": "good",
                "current_ratio": result.ratio,
                "message": "Contrast meets WCAG AA standards"
            }

        # Generate alternative colors
        adjusted_fg = self.ensure_readable_text(
            foreground,
            background,
            min_ratio=self.WCAG_AA_LARGE if is_large_text else self.WCAG_AA_NORMAL
        )

        return {
            "status": "needs_adjustment",
            "current_ratio": result.ratio,
            "message": result.recommendation,
            "suggested_foreground": adjusted_fg,
            "suggested_background": background  # Could also adjust background
        }

    def validate_palette(
        self,
        colors: Dict[str, str],
        background: str = "#FFFFFF"
    ) -> Dict[str, ContrastResult]:
        """
        Validate entire color palette against a background

        Args:
            colors: Dict of color names to hex values
            background: Background color to test against

        Returns:
            Dict of color names to ContrastResult
        """
        results = {}

        for name, color in colors.items():
            result = self.check_contrast(color, background, is_large_text=False)
            results[name] = result

            if not result.passes_aa:
                logger.warning(f"Color '{name}' ({color}) fails WCAG AA on {background}")

        return results

    def get_text_shadow_for_contrast(
        self,
        text_color: str,
        background_color: str
    ) -> Optional[str]:
        """
        Suggest text shadow CSS for additional contrast

        Args:
            text_color: Text color (hex)
            background_color: Background color (hex)

        Returns:
            CSS text-shadow value or None
        """
        ratio = self.calculate_contrast_ratio(text_color, background_color)

        if ratio >= self.WCAG_AA_NORMAL:
            return None  # No shadow needed

        # Determine shadow color (opposite of text)
        text_brightness = self._get_brightness(text_color)

        if text_brightness > 0.5:
            # Light text → dark shadow
            shadow_color = "rgba(0, 0, 0, 0.7)"
        else:
            # Dark text → light shadow
            shadow_color = "rgba(255, 255, 255, 0.7)"

        # CSS text-shadow
        return f"2px 2px 4px {shadow_color}"

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to hex"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    def _relative_luminance(self, rgb: Tuple[int, int, int]) -> float:
        """
        Calculate relative luminance for WCAG formula
        https://www.w3.org/TR/WCAG20/#relativeluminancedef
        """
        r, g, b = [x / 255.0 for x in rgb]

        # Apply gamma correction
        def adjust(c):
            if c <= 0.03928:
                return c / 12.92
            else:
                return ((c + 0.055) / 1.055) ** 2.4

        r = adjust(r)
        g = adjust(g)
        b = adjust(b)

        # Calculate luminance
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _get_brightness(self, hex_color: str) -> float:
        """Get perceived brightness (0-1)"""
        rgb = self._hex_to_rgb(hex_color)
        # Perceived brightness formula
        brightness = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
        return brightness

    def analyze_color_harmony(
        self,
        colors: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze if colors work well together

        Args:
            colors: List of hex colors

        Returns:
            Harmony analysis
        """
        if len(colors) < 2:
            return {"status": "insufficient_colors"}

        # Convert to HSL
        hsl_colors = []
        for color in colors:
            rgb = self._hex_to_rgb(color)
            h, l, s = colorsys.rgb_to_hls(*[x/255 for x in rgb])
            hsl_colors.append((h * 360, s, l))  # Convert hue to degrees

        # Check hue relationships
        hues = [h for h, s, l in hsl_colors]

        # Complementary (opposite hues)
        is_complementary = any(
            abs(hues[i] - hues[j]) > 150 and abs(hues[i] - hues[j]) < 210
            for i in range(len(hues)) for j in range(i+1, len(hues))
        )

        # Analogous (similar hues)
        is_analogous = all(
            abs(hues[i] - hues[j]) < 30
            for i in range(len(hues)) for j in range(i+1, len(hues))
        )

        # Triadic (120° apart)
        is_triadic = len(hues) == 3 and all(
            90 < abs(hues[i] - hues[j]) < 150
            for i in range(len(hues)) for j in range(i+1, len(hues))
        )

        harmony_type = "unknown"
        if is_complementary:
            harmony_type = "complementary"
        elif is_analogous:
            harmony_type = "analogous"
        elif is_triadic:
            harmony_type = "triadic"

        return {
            "harmony_type": harmony_type,
            "is_harmonious": harmony_type != "unknown",
            "hues": hues
        }


# Singleton instance
contrast_manager = ContrastManager()
