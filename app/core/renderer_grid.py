"""
Template-Free Grid Renderer
Composes layouts programmatically using brand tokens and grid system
No Canva templates required - pure Python rendering with Pillow
"""
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from pathlib import Path
import io
import requests

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
except ImportError:
    raise ImportError("Pillow not installed. Run: pip install Pillow")

from app.core.brand_brain import BrandTokens
from app.core.schemas_v2 import BrandTokensV2
from app.core.chat_agent_planner import DesignPlan
from app.infra.logging import get_logger
from app.core.storage import storage
from typing import Union

logger = get_logger(__name__)


@dataclass
class GridLayout:
    """Grid layout configuration"""
    columns: int = 12
    rows: int = 12
    cell_size: int = 100  # pixels per grid cell
    gutter: int = 8  # spacing between cells
    padding: int = 40  # outer padding

    @property
    def width(self) -> int:
        """Total canvas width"""
        return (self.columns * self.cell_size) + ((self.columns - 1) * self.gutter) + (2 * self.padding)

    @property
    def height(self) -> int:
        """Total canvas height"""
        return (self.rows * self.cell_size) + ((self.rows - 1) * self.gutter) + (2 * self.padding)


@dataclass
class LayoutElement:
    """Single element in layout"""
    type: str  # 'text', 'image', 'logo', 'cta'
    content: Any
    grid_x: int  # Starting column (0-indexed)
    grid_y: int  # Starting row
    grid_w: int  # Width in columns
    grid_h: int  # Height in rows
    style: Dict[str, Any] = None  # Additional styling

    def get_bbox(self, layout: GridLayout) -> Tuple[int, int, int, int]:
        """Get absolute bounding box (x1, y1, x2, y2)"""
        x1 = layout.padding + (self.grid_x * (layout.cell_size + layout.gutter))
        y1 = layout.padding + (self.grid_y * (layout.cell_size + layout.gutter))
        x2 = x1 + (self.grid_w * layout.cell_size) + ((self.grid_w - 1) * layout.gutter)
        y2 = y1 + (self.grid_h * layout.cell_size) + ((self.grid_h - 1) * layout.gutter)
        return (x1, y1, x2, y2)


class GridRenderer:
    """
    Template-free renderer using programmatic grid layouts

    Features:
    - Responsive grid system (12x12 by default)
    - Brand font/color application
    - Logo placement with safe zones
    - Text wrapping and sizing
    - Background image compositing
    - Export to PNG
    """

    def __init__(self, tokens: Union[BrandTokens, BrandTokensV2]):
        """
        Initialize renderer

        Args:
            tokens: Brand design tokens (supports both old and new versions)
        """
        # DEBUG: Log what brand data the renderer receives
        logger.info(f"🔍 DEBUG - Renderer Init")

        # Get colors dict (works for both BrandTokens and BrandTokensV2)
        colors_dict = self._get_colors_dict(tokens)
        cta_list = self._get_cta_whitelist(tokens)
        logger.info(f"🎨 Received Colors: primary={colors_dict.get('primary')}, secondary={colors_dict.get('secondary')}, accent={colors_dict.get('accent')}")
        logger.info(f"📝 Received CTAs: {cta_list}")

        self.tokens = tokens
        layout_dict = self._get_layout_dict(tokens)
        self.layout = GridLayout(
            columns=layout_dict.get('grid', 12),
            gutter=layout_dict.get('spacing', 8)
        )

        # Font cache
        self._font_cache = {}

    def _get_colors_dict(self, tokens: Union[BrandTokens, BrandTokensV2]) -> Dict[str, str]:
        """Get colors dict, compatible with both BrandTokens and BrandTokensV2"""
        # BrandTokensV2 uses 'colors' (ColorPalette object)
        if hasattr(tokens, 'colors'):
            # Convert ColorPalette to dict format
            return {
                'primary': tokens.colors.primary.hex,
                'secondary': tokens.colors.secondary.hex,
                'accent': tokens.colors.accent.hex
            }
        # Old BrandTokens uses 'color' (dict)
        else:
            return tokens.color

    def _get_cta_whitelist(self, tokens: Union[BrandTokens, BrandTokensV2]) -> List[str]:
        """Get CTA whitelist, compatible with both BrandTokens and BrandTokensV2"""
        # BrandTokensV2 has cta_whitelist nested in policies
        if hasattr(tokens, 'policies') and tokens.policies:
            return tokens.policies.cta_whitelist
        # Old BrandTokens has cta_whitelist at top level
        elif hasattr(tokens, 'cta_whitelist'):
            return tokens.cta_whitelist
        # Default empty list
        else:
            return []

    def _get_layout_dict(self, tokens: Union[BrandTokens, BrandTokensV2]) -> Dict[str, Any]:
        """Get layout dict, compatible with both BrandTokens and BrandTokensV2"""
        # BrandTokensV2 uses LayoutSystem object
        if hasattr(tokens, 'layout') and hasattr(tokens.layout, 'grid'):
            return {
                'grid': tokens.layout.grid,
                'spacing': tokens.layout.spacing_scale[1] if tokens.layout.spacing_scale else 8,
                'radius': tokens.layout.border_radius.get('md', 16) if tokens.layout.border_radius else 16
            }
        # Old BrandTokens uses dict
        elif hasattr(tokens, 'layout') and isinstance(tokens.layout, dict):
            return tokens.layout
        # Default
        else:
            return {'grid': 12, 'spacing': 8, 'radius': 16}

    def _get_typography_dict(self, tokens: Union[BrandTokens, BrandTokensV2]) -> Dict[str, Any]:
        """Get typography dict, compatible with both BrandTokens and BrandTokensV2"""
        # BrandTokensV2 uses typography dict with TypographyToken objects
        if hasattr(tokens, 'typography') and tokens.typography:
            # Convert TypographyToken objects to simple dict format
            result = {}
            for key, typography_token in tokens.typography.items():
                result[key] = {
                    'family': typography_token.family,
                    'weight': str(typography_token.weights[0]) if typography_token.weights else 'normal',
                    'size': typography_token.sizes[0] if typography_token.sizes else 16
                }
            return result
        # Old BrandTokens uses 'type' dict
        elif hasattr(tokens, 'type'):
            return tokens.type
        # Default
        else:
            return {
                'heading': {'family': 'Arial', 'weight': 'bold', 'size': 48},
                'body': {'family': 'Arial', 'weight': 'normal', 'size': 16}
            }

    def render_design(
        self,
        plan: DesignPlan,
        background_url: str,
        logo_url: Optional[str] = None,
        product_image_url: Optional[str] = None
    ) -> Image.Image:
        """
        Render complete design from plan

        Args:
            plan: Design plan from ChatAgentPlanner
            background_url: URL to background image
            logo_url: Optional logo image URL
            product_image_url: Optional product image URL

        Returns:
            PIL Image object
        """
        logger.info(f"Rendering design: {plan.headline}")

        # Determine canvas size from aspect ratio
        width, height = self._get_canvas_size(plan.aspect_ratio)

        # Create base canvas
        canvas = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(canvas)

        # 1. Apply background (image or gradient)
        if background_url:
            canvas = self._apply_background(canvas, background_url)
        else:
            # Generate gradient background using brand colors
            logger.info("No background URL provided - generating gradient background")
            canvas = self._generate_gradient_background(canvas, plan.palette_mode)

        # 2. SKIP overlay - we now use white background boxes on text instead
        # This keeps the background image vibrant and visible
        # canvas = self._apply_overlay(canvas, plan.palette_mode)

        # 3. Render layout elements
        elements = self._plan_to_elements(plan, logo_url, product_image_url)
        logger.info(f"Created {len(elements)} layout elements")

        for element in elements:
            logger.info(f"Rendering {element.type}: {str(element.content)[:50]}")
            canvas = self._render_element(canvas, element)

        logger.info("Design rendering complete")
        return canvas

    def _get_canvas_size(self, aspect_ratio: str) -> Tuple[int, int]:
        """Get canvas dimensions for aspect ratio"""
        ratios = {
            "1x1": (1080, 1080),    # Instagram square
            "4x5": (1080, 1350),    # Instagram portrait
            "9x16": (1080, 1920),   # Instagram story
            "16x9": (1920, 1080),   # YouTube thumbnail
        }
        return ratios.get(aspect_ratio, (1080, 1080))

    def _apply_background(self, canvas: Image.Image, bg_url: str) -> Image.Image:
        """Apply and fit background image"""
        try:
            # Download background
            response = requests.get(bg_url, timeout=30)
            response.raise_for_status()
            bg_image = Image.open(io.BytesIO(response.content))

            # Resize to cover canvas (crop to fit)
            bg_image = self._resize_cover(bg_image, canvas.size)

            # Paste onto canvas
            canvas.paste(bg_image, (0, 0))
            logger.info("Background applied")
            return canvas

        except Exception as e:
            logger.error(f"Failed to apply background: {e}")
            return canvas

    def _generate_gradient_background(self, canvas: Image.Image, palette_mode: str) -> Image.Image:
        """
        Generate a beautiful gradient background using brand colors

        Args:
            canvas: Base canvas to apply gradient to
            palette_mode: Color scheme (primary, vibrant, mono, etc.)

        Returns:
            Canvas with gradient background
        """
        colors_dict = self._get_colors_dict(self.tokens)

        # Select colors based on palette mode
        if palette_mode == 'vibrant':
            start_color = colors_dict.get('primary', '#4F46E5')
            end_color = colors_dict.get('accent', '#F59E0B')
        elif palette_mode == 'mono':
            start_color = '#1F2937'  # Dark gray
            end_color = '#4B5563'    # Medium gray
        else:  # primary or secondary
            start_color = colors_dict.get('primary', '#4F46E5')
            end_color = colors_dict.get('secondary', '#7C3AED')

        logger.info(f"Generating gradient: {start_color} → {end_color}")

        # Convert hex to RGB
        start_rgb = self._hex_to_rgb(start_color)
        end_rgb = self._hex_to_rgb(end_color)

        # Create gradient (diagonal, top-left to bottom-right)
        width, height = canvas.size
        for y in range(height):
            for x in range(width):
                # Calculate position ratio (0.0 to 1.0) along diagonal
                ratio = (x / width + y / height) / 2

                # Interpolate RGB values
                r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
                g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
                b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)

                canvas.putpixel((x, y), (r, g, b))

        logger.info("Gradient background generated")
        return canvas

    def _resize_cover(self, image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """Resize image to cover target size (like CSS background-size: cover)"""
        img_ratio = image.width / image.height
        target_ratio = target_size[0] / target_size[1]

        if img_ratio > target_ratio:
            # Image is wider, fit to height
            new_height = target_size[1]
            new_width = int(new_height * img_ratio)
        else:
            # Image is taller, fit to width
            new_width = target_size[0]
            new_height = int(new_width / img_ratio)

        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Crop to center
        left = (new_width - target_size[0]) // 2
        top = (new_height - target_size[1]) // 2
        right = left + target_size[0]
        bottom = top + target_size[1]

        return resized.crop((left, top, right, bottom))

    def _apply_overlay(self, canvas: Image.Image, palette_mode: str) -> Image.Image:
        """Apply semi-transparent overlay for text contrast"""
        overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Get color from palette mode
        colors_dict = self._get_colors_dict(self.tokens)
        color_map = {
            'primary': colors_dict.get('primary', '#4F46E5'),
            'secondary': colors_dict.get('secondary', '#7C3AED'),
            'accent': colors_dict.get('accent', '#F59E0B'),
            'mono': '#000000'
        }

        color = color_map.get(palette_mode, '#000000')
        logger.info(f"🔍 DEBUG - Overlay Color: {color} (palette_mode={palette_mode}, brand primary={colors_dict.get('primary')})")
        color_rgb = self._hex_to_rgb(color)

        # Draw gradient overlay (darker at bottom for text)
        for y in range(canvas.height):
            alpha = int((y / canvas.height) * 120)  # 0-120 opacity
            draw.rectangle(
                [(0, y), (canvas.width, y + 1)],
                fill=(*color_rgb, alpha)
            )

        # Composite overlay
        canvas = canvas.convert('RGBA')
        canvas = Image.alpha_composite(canvas, overlay)
        canvas = canvas.convert('RGB')

        return canvas

    def _plan_to_elements(
        self,
        plan: DesignPlan,
        logo_url: Optional[str],
        product_image_url: Optional[str]
    ) -> List[LayoutElement]:
        """Convert design plan to layout elements"""
        elements = []

        # Logo (if provided)
        if logo_url:
            logo_pos = self._get_logo_position(plan.logo_position)
            elements.append(LayoutElement(
                type='logo',
                content=logo_url,
                grid_x=logo_pos[0],
                grid_y=logo_pos[1],
                grid_w=2,
                grid_h=2
            ))

        # Product image (if needed)
        if product_image_url and plan.product_image_needed:
            elements.append(LayoutElement(
                type='image',
                content=product_image_url,
                grid_x=1,
                grid_y=1,
                grid_w=5,
                grid_h=5
            ))

        # HEADLINE - HUGE, CENTER, IMPOSSIBLE TO MISS
        # Use absolute positioning for social media impact
        elements.append(LayoutElement(
            type='headline',
            content=plan.headline,
            grid_x=1,  # Small margins
            grid_y=5,  # Middle area
            grid_w=10,  # Almost full width
            grid_h=2,
            style={
                'color': '#000000',
                'font_size': 180,  # MASSIVE
                'bg_box': True,
                'align': 'center'
            }
        ))

        # SUBHEAD - LARGE, READABLE
        elements.append(LayoutElement(
            type='subhead',
            content=plan.subhead,
            grid_x=1,
            grid_y=8,  # Below headline
            grid_w=10,
            grid_h=2,
            style={
                'color': '#000000',
                'font_size': 80,  # LARGE
                'bg_box': True,
                'align': 'center'
            }
        ))

        # CTA BUTTON - MASSIVE, BOTTOM CENTER
        elements.append(LayoutElement(
            type='cta',
            content=plan.cta_text,
            grid_x=2,  # Centered
            grid_y=10,  # Near bottom
            grid_w=8,  # Wide button
            grid_h=1,
            style={
                'color': self._get_colors_dict(self.tokens).get('accent', '#F59E0B'),
                'font_size': 90  # HUGE
            }
        ))

        return elements

    def _get_logo_position(self, position_code: str) -> Tuple[int, int]:
        """Get grid coordinates for logo position"""
        positions = {
            'TL': (0, 0),      # Top-left
            'TR': (10, 0),     # Top-right
            'BR': (10, 10),    # Bottom-right
            'BL': (0, 10),     # Bottom-left
        }
        return positions.get(position_code, (0, 0))

    def _render_element(self, canvas: Image.Image, element: LayoutElement) -> Image.Image:
        """Render single element onto canvas"""
        if element.type == 'logo':
            return self._render_logo(canvas, element)
        elif element.type == 'image':
            return self._render_image(canvas, element)
        elif element.type == 'headline':
            font_size = element.style.get('font_size', 72) if element.style else 72
            return self._render_text(canvas, element, bold=True, size=font_size)
        elif element.type == 'subhead':
            font_size = element.style.get('font_size', 36) if element.style else 36
            return self._render_text(canvas, element, bold=False, size=font_size)
        elif element.type == 'cta':
            return self._render_cta(canvas, element)
        else:
            logger.warning(f"Unknown element type: {element.type}")
            return canvas

    def _render_text(
        self,
        canvas: Image.Image,
        element: LayoutElement,
        bold: bool = False,
        size: int = 48
    ) -> Image.Image:
        """Render text element with wrapping and background box for visibility"""
        draw = ImageDraw.Draw(canvas)

        # Get bounding box
        x1, y1, x2, y2 = element.get_bbox(self.layout)

        # Get font
        typography_dict = self._get_typography_dict(self.tokens)
        font_family = typography_dict.get('heading', {}).get('family', 'Arial') if bold else \
                      typography_dict.get('body', {}).get('family', 'Arial')

        font = self._get_font(font_family, size, bold)

        # Get color
        color = element.style.get('color', '#000000') if element.style else '#000000'
        color_rgb = self._hex_to_rgb(color)

        # Word wrap text
        wrapped_text = self._wrap_text(element.content, font, x2 - x1)

        # Get text bounding box for positioning
        text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Center align if requested
        text_x = x1
        text_y = y1
        if element.style and element.style.get('align') == 'center':
            text_x = x1 + ((x2 - x1) - text_width) // 2
            text_y = y1 + ((y2 - y1) - text_height) // 2

        # CRITICAL: Draw semi-transparent white background box for visibility
        if element.style and element.style.get('bg_box', False):
            # Get exact text bounding box at final position
            final_bbox = draw.textbbox((text_x, text_y), wrapped_text, font=font)
            # Add generous padding
            padding = 40
            bg_box = [
                final_bbox[0] - padding,
                final_bbox[1] - padding,
                final_bbox[2] + padding,
                final_bbox[3] + padding
            ]
            # Draw white background with 90% opacity
            overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(bg_box, fill=(255, 255, 255, 230))  # White, 90% opacity

            canvas = canvas.convert('RGBA')
            canvas = Image.alpha_composite(canvas, overlay)
            canvas = canvas.convert('RGB')
            draw = ImageDraw.Draw(canvas)

        # Draw text (BLACK for maximum contrast)
        draw.text((text_x, text_y), wrapped_text, font=font, fill=color_rgb)

        return canvas

    def _render_cta(self, canvas: Image.Image, element: LayoutElement) -> Image.Image:
        """Render CTA button"""
        draw = ImageDraw.Draw(canvas)

        # Get bounding box
        x1, y1, x2, y2 = element.get_bbox(self.layout)

        # Background color
        bg_color = element.style.get('color', '#F59E0B') if element.style else '#F59E0B'
        logger.info(f"🔍 DEBUG - CTA Button Color: {bg_color} (Brand accent: {self._get_colors_dict(self.tokens).get('accent')})")
        bg_rgb = self._hex_to_rgb(bg_color)

        # Draw rounded rectangle
        layout_dict = self._get_layout_dict(self.tokens)
        radius = layout_dict.get('radius', 16)
        draw.rounded_rectangle(
            [(x1, y1), (x2, y2)],
            radius=radius,
            fill=bg_rgb
        )

        # Draw text centered (use font size from style)
        font_size = element.style.get('font_size', 70) if element.style else 70
        font = self._get_font('Arial', font_size, bold=True)

        # Get text size for centering
        bbox = draw.textbbox((0, 0), element.content, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = x1 + ((x2 - x1) - text_width) // 2
        text_y = y1 + ((y2 - y1) - text_height) // 2

        draw.text((text_x, text_y), element.content, font=font, fill=(255, 255, 255))

        return canvas

    def _render_logo(self, canvas: Image.Image, element: LayoutElement) -> Image.Image:
        """Render logo with safe zone"""
        try:
            # Download logo
            response = requests.get(element.content, timeout=30)
            response.raise_for_status()
            logo = Image.open(io.BytesIO(response.content))

            # Convert to RGBA
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')

            # Get bounding box
            x1, y1, x2, y2 = element.get_bbox(self.layout)

            # Resize maintaining aspect ratio
            logo.thumbnail((x2 - x1, y2 - y1), Image.Resampling.LANCZOS)

            # Paste with alpha
            canvas_rgba = canvas.convert('RGBA')
            canvas_rgba.paste(logo, (x1, y1), logo)
            canvas = canvas_rgba.convert('RGB')

            logger.info("Logo rendered")
            return canvas

        except Exception as e:
            logger.error(f"Failed to render logo: {e}")
            return canvas

    def _render_image(self, canvas: Image.Image, element: LayoutElement) -> Image.Image:
        """Render product image"""
        try:
            response = requests.get(element.content, timeout=30)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))

            # Get bounding box
            x1, y1, x2, y2 = element.get_bbox(self.layout)

            # Resize to fit
            img = self._resize_cover(img, (x2 - x1, y2 - y1))

            # Paste
            canvas.paste(img, (x1, y1))
            return canvas

        except Exception as e:
            logger.error(f"Failed to render image: {e}")
            return canvas

    def _get_font(self, family: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Get font with caching"""
        key = f"{family}_{size}_{bold}"

        if key in self._font_cache:
            return self._font_cache[key]

        # Try to load font (fallback to default if not available)
        try:
            # Try common font paths
            font_paths = [
                f"/System/Library/Fonts/{family}.ttc",
                f"/usr/share/fonts/truetype/{family.lower()}.ttf",
                f"C:\\Windows\\Fonts\\{family}.ttf",
            ]

            font = None
            for path in font_paths:
                if Path(path).exists():
                    font = ImageFont.truetype(path, size)
                    break

            if font is None:
                # Fallback to default
                font = ImageFont.load_default()
                logger.warning(f"Font {family} not found, using default")

        except Exception as e:
            logger.error(f"Font loading error: {e}")
            font = ImageFont.load_default()

        self._font_cache[key] = font
        return font

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
        """Wrap text to fit within width"""
        words = text.split()
        lines = []
        current_line = []

        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))

        for word in words:
            current_line.append(word)
            line_text = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), line_text, font=font)
            line_width = bbox[2] - bbox[0]

            if line_width > max_width:
                if len(current_line) == 1:
                    # Single word too long, keep it
                    lines.append(word)
                    current_line = []
                else:
                    # Remove last word and start new line
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return '\n'.join(lines)

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def save_design(
        self,
        image: Image.Image,
        org_id: str,
        filename: str = "design.png"
    ) -> str:
        """
        Save design to storage and return URL

        Args:
            image: PIL Image
            org_id: Organization ID for storage path
            filename: Output filename

        Returns:
            Public URL to saved design
        """
        # Convert to bytes
        buffer = io.BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        # Upload to storage
        storage_path = f"{org_id}/grid-designs/{filename}"
        url = storage.upload_file(
            bucket_type="assets",
            file_path=storage_path,
            file_data=buffer,
            content_type='image/png'
        )

        logger.info(f"Design saved to: {url}")
        return url
