"""
Logo Engine v2
Intelligent logo placement with luminance-based variant selection
- Samples background luminance at logo position
- Selects optimal logo variant (light/dark/full-color)
- Enforces safe zones and scale constraints
"""
from typing import Dict, Any, Optional, Tuple, List
from PIL import Image, ImageDraw
import io
import requests
import numpy as np
from app.core.brand_brain import BrandTokens
from app.infra.logging import get_logger

logger = get_logger(__name__)


class LogoEngine:
    """Intelligent logo placement with luminance-based variant selection"""

    # Luminance thresholds for variant selection
    LUMINANCE_DARK_THRESHOLD = 0.3   # Use light logo on dark backgrounds
    LUMINANCE_LIGHT_THRESHOLD = 0.7  # Use dark logo on light backgrounds

    # Position mappings
    POSITION_COORDS = {
        "top-left": (0.05, 0.05),
        "top-right": (0.95, 0.05),
        "top-center": (0.5, 0.05),
        "bottom-left": (0.05, 0.95),
        "bottom-right": (0.95, 0.95),
        "bottom-center": (0.5, 0.95),
        "center": (0.5, 0.5)
    }

    def apply_logo(
        self,
        background_url: str,
        logo_variants: Dict[str, str],
        tokens: BrandTokens,
        position: Optional[str] = None,
        scale_override: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Apply logo to background with intelligent variant selection

        Args:
            background_url: URL of background image
            logo_variants: Dict with keys: "light", "dark", "full_color"
            tokens: Brand tokens with logo rules
            position: Logo position override (default: use tokens.logo.allowed_positions[0])
            scale_override: Logo scale override (default: use tokens.logo.min_px)

        Returns:
            {
                "success": bool,
                "image": Image.Image,
                "variant_used": str,
                "position": str,
                "luminance": float,
                "safe_zone_respected": bool
            }
        """
        try:
            # Download background
            logger.info(f"Applying logo to background {background_url[:50]}...")
            response = requests.get(background_url, timeout=10)
            response.raise_for_status()
            background = Image.open(io.BytesIO(response.content)).convert('RGBA')

            # Determine position
            if not position:
                allowed_positions = tokens.logo.get("allowed_positions", ["top-right"])
                position = allowed_positions[0]

            # Calculate logo placement coordinates
            bg_width, bg_height = background.size
            position_ratio = self.POSITION_COORDS.get(position, (0.95, 0.05))
            safe_zone_px = tokens.logo.get("safe_zone_px", 0)

            # Sample background luminance at logo position
            luminance = self._sample_luminance(background, position_ratio, safe_zone_px)
            logger.info(f"Background luminance at {position}: {luminance:.2f}")

            # Select optimal logo variant
            variant_used = self._select_variant(luminance, logo_variants)
            logger.info(f"Selected logo variant: {variant_used}")

            # Download logo
            logo_url = logo_variants.get(variant_used)
            if not logo_url:
                logger.error(f"Logo variant '{variant_used}' not available")
                # Fallback to any available variant
                for v in ["full_color", "dark", "light"]:
                    if v in logo_variants and logo_variants[v]:
                        logo_url = logo_variants[v]
                        variant_used = v
                        break

            if not logo_url:
                raise ValueError("No logo variants available")

            logo_response = requests.get(logo_url, timeout=10)
            logo_response.raise_for_status()
            logo = Image.open(io.BytesIO(logo_response.content)).convert('RGBA')

            # Calculate logo size
            min_px = tokens.logo.get("min_px", 100)
            logo_width = scale_override if scale_override else min_px

            # Maintain aspect ratio
            aspect_ratio = logo.height / logo.width
            logo_height = int(logo_width * aspect_ratio)

            # Resize logo
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

            # Calculate final position with safe zone
            x, y = self._calculate_final_position(
                bg_width, bg_height,
                logo_width, logo_height,
                position_ratio,
                safe_zone_px
            )

            # Check if safe zone is respected
            safe_zone_respected = self._check_safe_zone(
                x, y, logo_width, logo_height,
                bg_width, bg_height,
                safe_zone_px
            )

            # Composite logo onto background
            background.paste(logo, (x, y), logo)

            logger.info(f"Logo applied successfully at ({x}, {y}) with size {logo_width}x{logo_height}")

            return {
                "success": True,
                "image": background,
                "variant_used": variant_used,
                "position": position,
                "luminance": round(luminance, 2),
                "safe_zone_respected": safe_zone_respected,
                "coordinates": (x, y),
                "size": (logo_width, logo_height)
            }

        except Exception as e:
            logger.error(f"Logo application error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "variant_used": None,
                "position": position,
                "luminance": 0.0,
                "safe_zone_respected": False
            }

    def _sample_luminance(
        self,
        image: Image.Image,
        position_ratio: Tuple[float, float],
        safe_zone_px: int
    ) -> float:
        """
        Sample average luminance at logo position

        Args:
            image: Background image
            position_ratio: (x_ratio, y_ratio) in 0-1 range
            safe_zone_px: Safe zone padding in pixels

        Returns:
            Average luminance (0.0 = black, 1.0 = white)
        """
        try:
            # Convert to RGB for luminance calculation
            img_rgb = image.convert('RGB')
            width, height = img_rgb.size

            # Calculate sample region (logo bounding box + safe zone)
            x_center = int(position_ratio[0] * width)
            y_center = int(position_ratio[1] * height)

            # Sample region size (estimate based on safe zone)
            sample_size = max(safe_zone_px * 2, 100)

            # Calculate sample bounds
            x1 = max(0, x_center - sample_size // 2)
            y1 = max(0, y_center - sample_size // 2)
            x2 = min(width, x_center + sample_size // 2)
            y2 = min(height, y_center + sample_size // 2)

            # Crop sample region
            sample = img_rgb.crop((x1, y1, x2, y2))

            # Convert to numpy array
            pixels = np.array(sample)

            # Calculate relative luminance (WCAG formula)
            # Y = 0.2126*R + 0.7152*G + 0.0722*B
            r = pixels[:, :, 0] / 255.0
            g = pixels[:, :, 1] / 255.0
            b = pixels[:, :, 2] / 255.0

            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

            # Return average luminance
            avg_luminance = float(np.mean(luminance))

            return avg_luminance

        except Exception as e:
            logger.error(f"Luminance sampling error: {str(e)}")
            return 0.5  # Default to medium luminance

    def _select_variant(self, luminance: float, logo_variants: Dict[str, str]) -> str:
        """
        Select optimal logo variant based on background luminance

        Args:
            luminance: Background luminance (0.0-1.0)
            logo_variants: Available logo variants

        Returns:
            Variant name: "light", "dark", or "full_color"
        """
        # Dark background → use light logo
        if luminance < self.LUMINANCE_DARK_THRESHOLD:
            if "light" in logo_variants and logo_variants["light"]:
                return "light"

        # Light background → use dark logo
        elif luminance > self.LUMINANCE_LIGHT_THRESHOLD:
            if "dark" in logo_variants and logo_variants["dark"]:
                return "dark"

        # Medium luminance or no specific variant → use full color
        if "full_color" in logo_variants and logo_variants["full_color"]:
            return "full_color"

        # Fallback to any available variant
        for variant in ["dark", "light", "full_color"]:
            if variant in logo_variants and logo_variants[variant]:
                return variant

        return "full_color"

    def _calculate_final_position(
        self,
        bg_width: int,
        bg_height: int,
        logo_width: int,
        logo_height: int,
        position_ratio: Tuple[float, float],
        safe_zone_px: int
    ) -> Tuple[int, int]:
        """
        Calculate final logo position with safe zone

        Args:
            bg_width: Background width
            bg_height: Background height
            logo_width: Logo width
            logo_height: Logo height
            position_ratio: (x_ratio, y_ratio) in 0-1 range
            safe_zone_px: Safe zone padding

        Returns:
            (x, y) top-left corner of logo
        """
        # Calculate base position
        x_ratio, y_ratio = position_ratio

        # Handle anchor points
        if x_ratio <= 0.1:  # Left aligned
            x = safe_zone_px
        elif x_ratio >= 0.9:  # Right aligned
            x = bg_width - logo_width - safe_zone_px
        else:  # Center aligned
            x = int(x_ratio * bg_width - logo_width / 2)

        if y_ratio <= 0.1:  # Top aligned
            y = safe_zone_px
        elif y_ratio >= 0.9:  # Bottom aligned
            y = bg_height - logo_height - safe_zone_px
        else:  # Center aligned
            y = int(y_ratio * bg_height - logo_height / 2)

        # Clamp to image bounds
        x = max(safe_zone_px, min(x, bg_width - logo_width - safe_zone_px))
        y = max(safe_zone_px, min(y, bg_height - logo_height - safe_zone_px))

        return (x, y)

    def _check_safe_zone(
        self,
        x: int,
        y: int,
        logo_width: int,
        logo_height: int,
        bg_width: int,
        bg_height: int,
        safe_zone_px: int
    ) -> bool:
        """
        Check if logo respects safe zone constraints

        Args:
            x, y: Logo position
            logo_width, logo_height: Logo dimensions
            bg_width, bg_height: Background dimensions
            safe_zone_px: Required safe zone padding

        Returns:
            True if safe zone is respected
        """
        # Check all edges
        left_ok = x >= safe_zone_px
        right_ok = x + logo_width <= bg_width - safe_zone_px
        top_ok = y >= safe_zone_px
        bottom_ok = y + logo_height <= bg_height - safe_zone_px

        return all([left_ok, right_ok, top_ok, bottom_ok])

    def create_preview_with_safe_zone(
        self,
        background_url: str,
        tokens: BrandTokens,
        position: Optional[str] = None
    ) -> Image.Image:
        """
        Create preview showing safe zone guidelines

        Args:
            background_url: URL of background image
            tokens: Brand tokens with logo rules
            position: Logo position

        Returns:
            Image with safe zone overlay
        """
        try:
            # Download background
            response = requests.get(background_url, timeout=10)
            response.raise_for_status()
            background = Image.open(io.BytesIO(response.content)).convert('RGBA')

            # Create overlay
            overlay = Image.new('RGBA', background.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Draw safe zone
            safe_zone_px = tokens.logo.get("safe_zone_px", 0)
            if safe_zone_px > 0:
                width, height = background.size
                # Draw safe zone rectangle
                draw.rectangle(
                    [safe_zone_px, safe_zone_px, width - safe_zone_px, height - safe_zone_px],
                    outline=(255, 0, 0, 128),
                    width=3
                )

            # Draw position markers
            if position:
                position_ratio = self.POSITION_COORDS.get(position, (0.5, 0.5))
                x = int(position_ratio[0] * background.width)
                y = int(position_ratio[1] * background.height)

                # Draw crosshair
                marker_size = 20
                draw.line([(x - marker_size, y), (x + marker_size, y)], fill=(255, 0, 0, 255), width=2)
                draw.line([(x, y - marker_size), (x, y + marker_size)], fill=(255, 0, 0, 255), width=2)

            # Composite overlay
            background.paste(overlay, (0, 0), overlay)

            return background

        except Exception as e:
            logger.error(f"Preview creation error: {str(e)}")
            return None


# Global logo engine instance
logo_engine = LogoEngine()
