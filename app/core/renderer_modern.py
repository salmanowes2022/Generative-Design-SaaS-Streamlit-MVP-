"""
Modern Design Renderer - Beautiful, Professional Layouts
Creates human-quality designs with proper typography, spacing, and visual hierarchy
"""
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dataclasses import dataclass
import io
import requests

from app.core.schemas_v2 import BrandTokensV2
from app.core.chat_agent_planner import DesignPlan
from app.infra.logging import get_logger

logger = get_logger(__name__)


class ModernRenderer:
    """
    Modern design renderer with beautiful layouts

    Features:
    - Large, readable typography (48-96px headlines)
    - Proper spacing and visual hierarchy
    - Beautiful gradients with brand colors
    - Professional composition
    - Instagram/social media optimized
    """

    def __init__(self, tokens: BrandTokensV2):
        """Initialize renderer with brand tokens"""
        self.tokens = tokens
        logger.info("🎨 Modern renderer initialized")

    def render_design(
        self,
        plan: DesignPlan,
        background_url: Optional[str] = None,
        logo_url: Optional[str] = None,
        product_image_url: Optional[str] = None
    ) -> Image.Image:
        """
        Render beautiful, professional design

        Args:
            plan: Design plan with content
            background_url: Optional background image (not used - we use gradients)
            logo_url: Optional logo
            product_image_url: Optional product image

        Returns:
            PIL Image with professional design
        """
        logger.info(f"Rendering modern design: {plan.headline}")

        # Get canvas size
        width, height = self._get_canvas_size(plan.aspect_ratio)

        # Create gradient background
        canvas = self._create_gradient_background(width, height, plan.palette_mode)

        # Add content with modern layout
        canvas = self._add_modern_layout(canvas, plan, logo_url)

        logger.info("✅ Modern design rendered")
        return canvas

    def _get_canvas_size(self, aspect_ratio: str) -> Tuple[int, int]:
        """Get canvas dimensions"""
        sizes = {
            "1x1": (1080, 1080),    # Instagram square
            "4x5": (1080, 1350),    # Instagram portrait
            "9x16": (1080, 1920),   # Instagram story
            "16x9": (1920, 1080),   # Landscape
        }
        return sizes.get(aspect_ratio, (1080, 1080))

    def _create_gradient_background(
        self,
        width: int,
        height: int,
        palette_mode: str
    ) -> Image.Image:
        """Create beautiful gradient background using FULL brand palette"""
        # Get ALL brand colors
        primary = self.tokens.colors.primary.hex
        secondary = self.tokens.colors.secondary.hex
        accent = self.tokens.colors.accent.hex

        # Select gradient colors based on palette mode
        if palette_mode == 'vibrant':
            start = primary
            end = accent  # Primary → Accent for vibrant contrast
        elif palette_mode == 'secondary':
            start = secondary
            end = primary  # Secondary → Primary
        elif palette_mode == 'accent':
            start = accent
            end = secondary  # Accent → Secondary
        elif palette_mode == 'mono':
            # Use primary color in monochrome gradient
            start = primary
            end = self._darken_color(primary, 0.3)  # Darker version
        else:  # 'primary' or default
            start = primary
            end = secondary  # Primary → Secondary

        logger.info(f"Creating gradient: {start} → {end} (mode: {palette_mode})")

        # Create canvas
        canvas = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(canvas)

        # Draw diagonal gradient
        start_rgb = self._hex_to_rgb(start)
        end_rgb = self._hex_to_rgb(end)

        for y in range(height):
            for x in range(width):
                # Diagonal gradient ratio
                ratio = (x / width + y / height) / 2

                # Interpolate colors
                r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
                g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
                b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)

                canvas.putpixel((x, y), (r, g, b))

        return canvas

    def _add_modern_layout(
        self,
        canvas: Image.Image,
        plan: DesignPlan,
        logo_url: Optional[str]
    ) -> Image.Image:
        """Add modern, centered layout with large typography AND logo"""
        width, height = canvas.size
        draw = ImageDraw.Draw(canvas)

        # ADD LOGO if provided
        if logo_url:
            try:
                canvas = self._add_logo(canvas, logo_url, plan.logo_position)
                logger.info(f"✅ Logo added at position {plan.logo_position}")
            except Exception as e:
                logger.warning(f"Could not add logo: {e}")

        # Calculate vertical rhythm
        center_y = height // 2

        # HEADLINE - Large, centered, bold
        headline_size = 96  # Large and readable
        headline_font = self._get_font('Inter', headline_size, bold=True)

        # Wrap headline to 2 lines max
        headline_wrapped = self._wrap_text_smart(plan.headline, headline_font, width * 0.8)

        # Draw headline with background
        headline_bbox = draw.multiline_textbbox((0, 0), headline_wrapped, font=headline_font, align='center')
        headline_w = headline_bbox[2] - headline_bbox[0]
        headline_h = headline_bbox[3] - headline_bbox[1]

        headline_x = (width - headline_w) // 2
        headline_y = center_y - headline_h - 60  # Above center

        # White semi-transparent background
        padding = 50
        bg_box = [
            headline_x - padding,
            headline_y - padding,
            headline_x + headline_w + padding,
            headline_y + headline_h + padding
        ]

        # NO WHITE BACKGROUND - Draw text directly on gradient
        draw = ImageDraw.Draw(canvas)

        # Draw headline text (white for visibility on dark gradient)
        draw.multiline_text(
            (headline_x, headline_y),
            headline_wrapped,
            font=headline_font,
            fill=(255, 255, 255),  # White text
            align='center',
            stroke_width=2,
            stroke_fill=(0, 0, 0)  # Black outline for readability
        )

        # SUBHEAD - Medium size, centered
        if plan.subhead:
            subhead_size = 42
            subhead_font = self._get_font('Inter', subhead_size, bold=False)

            # Wrap subhead
            subhead_wrapped = self._wrap_text_smart(plan.subhead, subhead_font, width * 0.7)

            subhead_bbox = draw.multiline_textbbox((0, 0), subhead_wrapped, font=subhead_font, align='center')
            subhead_w = subhead_bbox[2] - subhead_bbox[0]
            subhead_h = subhead_bbox[3] - subhead_bbox[1]

            subhead_x = (width - subhead_w) // 2
            subhead_y = center_y + 40  # Below center

            # Background for subhead
            sub_padding = 40
            sub_bg_box = [
                subhead_x - sub_padding,
                subhead_y - sub_padding,
                subhead_x + subhead_w + sub_padding,
                subhead_y + subhead_h + sub_padding
            ]

            # NO WHITE BACKGROUND - Draw subheader directly on gradient
            draw.multiline_text(
                (subhead_x, subhead_y),
                subhead_wrapped,
                font=subhead_font,
                fill=(255, 255, 255),  # White text
                align='center',
                stroke_width=1,
                stroke_fill=(0, 0, 0)  # Black outline
            )

        # CTA BUTTON - Bottom center, prominent
        cta_size = 36
        cta_font = self._get_font('Inter', cta_size, bold=True)

        cta_bbox = draw.textbbox((0, 0), plan.cta_text, font=cta_font)
        cta_w = cta_bbox[2] - cta_bbox[0]
        cta_h = cta_bbox[3] - cta_bbox[1]

        # Button dimensions
        button_padding_x = 80
        button_padding_y = 30
        button_w = cta_w + button_padding_x * 2
        button_h = cta_h + button_padding_y * 2

        button_x = (width - button_w) // 2
        button_y = height - 150  # Near bottom

        # Draw button (accent color)
        button_color = self._hex_to_rgb(self.tokens.colors.accent.hex)

        overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rounded_rectangle(
            [button_x, button_y, button_x + button_w, button_y + button_h],
            radius=button_h // 2,  # Pill shape
            fill=(*button_color, 255)
        )

        canvas = canvas.convert('RGBA')
        canvas = Image.alpha_composite(canvas, overlay)
        canvas = canvas.convert('RGB')
        draw = ImageDraw.Draw(canvas)

        # Draw CTA text (white on colored button)
        cta_text_x = button_x + button_padding_x
        cta_text_y = button_y + button_padding_y
        draw.text((cta_text_x, cta_text_y), plan.cta_text, font=cta_font, fill=(255, 255, 255))

        return canvas

    def _wrap_text_smart(self, text: str, font: ImageFont.FreeTypeFont, max_width: float) -> str:
        """Smart text wrapping - prefers 2 lines max"""
        words = text.split()

        # Try to split into roughly equal lines
        if len(words) <= 4:
            # Short text - keep on 1-2 lines
            mid = len(words) // 2
            line1 = ' '.join(words[:mid])
            line2 = ' '.join(words[mid:])
            if line2:
                return f"{line1}\n{line2}"
            return line1
        else:
            # Longer text - wrap smartly
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                # Rough estimation
                if len(test_line) * font.size < max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(' '.join(current_line))

            # Limit to 3 lines
            return '\n'.join(lines[:3])

    def _get_font(self, family: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Get font (with fallback)"""
        try:
            weight = 'Bold' if bold else 'Regular'
            return ImageFont.truetype(f"/System/Library/Fonts/Supplemental/{family}-{weight}.ttf", size)
        except:
            try:
                return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size)
            except:
                logger.warning(f"Font {family} not found, using default")
                return ImageFont.load_default()

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _darken_color(self, hex_color: str, factor: float) -> str:
        """Darken a color by factor (0.0-1.0)"""
        rgb = self._hex_to_rgb(hex_color)
        darkened = tuple(int(c * (1 - factor)) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*darkened)

    def _add_logo(self, canvas: Image.Image, logo_url: str, position: str) -> Image.Image:
        """
        Add logo to design at specified position

        Args:
            canvas: Canvas image
            logo_url: URL or path to logo
            position: 'TL' (top-left), 'TR' (top-right), 'BL' (bottom-left), 'BR' (bottom-right)

        Returns:
            Canvas with logo added
        """
        try:
            # Download/load logo
            if logo_url.startswith('http'):
                import requests
                response = requests.get(logo_url, timeout=10)
                logo_image = Image.open(io.BytesIO(response.content))
            else:
                logo_image = Image.open(logo_url)

            # Convert to RGBA if needed
            if logo_image.mode != 'RGBA':
                logo_image = logo_image.convert('RGBA')

            # Resize logo (max 200px width, maintain aspect ratio)
            max_size = 200
            logo_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Calculate position
            width, height = canvas.size
            logo_w, logo_h = logo_image.size
            margin = 40

            positions = {
                'TL': (margin, margin),
                'TR': (width - logo_w - margin, margin),
                'BL': (margin, height - logo_h - margin),
                'BR': (width - logo_w - margin, height - logo_h - margin)
            }

            pos = positions.get(position, positions['TL'])

            # Paste logo (with alpha channel for transparency)
            canvas = canvas.convert('RGBA')
            canvas.paste(logo_image, pos, logo_image)
            canvas = canvas.convert('RGB')

            return canvas

        except Exception as e:
            logger.error(f"Failed to add logo: {e}")
            return canvas
