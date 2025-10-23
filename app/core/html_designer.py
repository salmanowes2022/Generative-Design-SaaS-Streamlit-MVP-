"""
HTML/CSS Design Engine - Beautiful, Brand-Consistent Designs
Generates modern, pixel-perfect designs using HTML/CSS templates
Inspired by Lovable's beautiful design system
"""
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import base64
from io import BytesIO
from PIL import Image
import requests

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. HTML rendering will be limited.")
    print("   Install with: pip install playwright && playwright install chromium")

from app.core.brand_brain import BrandTokens
from app.core.schemas_v2 import BrandTokensV2
from app.core.chat_agent_planner import DesignPlan
from app.infra.logging import get_logger
from typing import Union

logger = get_logger(__name__)


@dataclass
class DesignTemplate:
    """HTML/CSS design template"""
    name: str
    html_template: str
    css_template: str
    slots: List[str] = field(default_factory=list)  # headline, subhead, cta, image, logo
    best_for: List[str] = field(default_factory=list)  # promotional, minimal, product
    aspect_ratios: List[str] = field(default_factory=list)  # 1x1, 4x5, 9x16


class HTMLDesigner:
    """
    Modern HTML/CSS-based design engine

    Features:
    - Beautiful, modern design templates
    - CSS Grid and Flexbox layouts
    - Responsive typography
    - Brand-consistent styling
    - Glassmorphism, gradients, shadows
    - Renders to PNG using Playwright
    """

    def __init__(self, tokens: Union[BrandTokens, BrandTokensV2]):
        """
        Initialize HTML designer

        Args:
            tokens: Brand design tokens (supports both old and new formats)
        """
        self.tokens = tokens
        self.templates = self._load_templates()

        # Get colors in compatible way
        colors = self._get_colors_dict()
        logger.info(f"🎨 HTMLDesigner initialized with {len(self.templates)} templates")
        logger.info(f"🎨 Brand colors: Primary={colors.get('primary')}, Accent={colors.get('accent')}")

    def _load_templates(self) -> Dict[str, DesignTemplate]:
        """Load built-in design templates"""
        templates = {}

        # Template 1: Hero with Gradient
        templates['hero_gradient'] = DesignTemplate(
            name="Hero with Gradient",
            html_template=self._get_hero_gradient_html(),
            css_template=self._get_hero_gradient_css(),
            slots=['headline', 'subhead', 'cta', 'logo'],
            best_for=['promotional', 'announcement', 'launch'],
            aspect_ratios=['1x1', '4x5', '9x16']
        )

        # Template 2: Minimal Card
        templates['minimal_card'] = DesignTemplate(
            name="Minimal Card",
            html_template=self._get_minimal_card_html(),
            css_template=self._get_minimal_card_css(),
            slots=['headline', 'subhead', 'cta', 'logo'],
            best_for=['minimal', 'text-heavy', 'informational'],
            aspect_ratios=['1x1', '4x5']
        )

        # Template 3: Product Showcase
        templates['product_showcase'] = DesignTemplate(
            name="Product Showcase",
            html_template=self._get_product_showcase_html(),
            css_template=self._get_product_showcase_css(),
            slots=['headline', 'subhead', 'cta', 'image', 'logo'],
            best_for=['product', 'e-commerce', 'showcase'],
            aspect_ratios=['1x1', '4x5']
        )

        # Template 4: Story Immersive
        templates['story_immersive'] = DesignTemplate(
            name="Story Immersive",
            html_template=self._get_story_immersive_html(),
            css_template=self._get_story_immersive_css(),
            slots=['headline', 'cta', 'image', 'logo'],
            best_for=['story', 'vertical', 'social'],
            aspect_ratios=['9x16']
        )

        # Template 5: Glassmorphism Modern
        templates['glassmorphism'] = DesignTemplate(
            name="Glassmorphism Modern",
            html_template=self._get_glassmorphism_html(),
            css_template=self._get_glassmorphism_css(),
            slots=['headline', 'subhead', 'cta', 'image', 'logo'],
            best_for=['modern', 'tech', 'premium'],
            aspect_ratios=['1x1', '4x5', '16x9']
        )

        return templates

    def select_template(self, plan: DesignPlan) -> DesignTemplate:
        """
        Select best template for design plan

        Args:
            plan: Design plan

        Returns:
            Selected template
        """
        # Simple scoring system
        scores = {}

        for template_id, template in self.templates.items():
            score = 0

            # Check aspect ratio match
            if plan.aspect_ratio in template.aspect_ratios:
                score += 10

            # Check style match
            style_keywords = plan.background_style.lower().split()
            for keyword in style_keywords:
                if keyword in template.best_for:
                    score += 5

            # Check visual concept match
            concept_keywords = plan.visual_concept.lower().split()
            for keyword in concept_keywords:
                if keyword in template.best_for:
                    score += 3

            scores[template_id] = score

        # Get template with highest score
        best_template_id = max(scores, key=scores.get)
        selected = self.templates[best_template_id]

        logger.info(f"✅ Selected template: {selected.name} (score: {scores[best_template_id]})")

        return selected

    def render_design(
        self,
        plan: DesignPlan,
        background_url: Optional[str] = None,
        logo_url: Optional[str] = None,
        product_image_url: Optional[str] = None
    ) -> Image.Image:
        """
        Render design to image using HTML/CSS

        Args:
            plan: Design plan
            background_url: Background image URL (optional)
            logo_url: Logo image URL (optional)
            product_image_url: Product image URL (optional)

        Returns:
            PIL Image object
        """
        logger.info(f"🎨 Rendering HTML design: {plan.headline}")

        # Select template
        template = self.select_template(plan)

        # Build HTML
        html = self._build_html(template, plan, background_url, logo_url, product_image_url)

        # Render to image
        if PLAYWRIGHT_AVAILABLE:
            image = self._render_with_playwright(html, plan.aspect_ratio)
        else:
            # Fallback: Save HTML file and return placeholder
            logger.warning("⚠️  Playwright not available, saving HTML file instead")
            html_path = Path(f"/tmp/design_{plan.headline[:20]}.html")
            html_path.write_text(html)
            logger.info(f"📄 HTML saved to: {html_path}")
            image = self._create_placeholder(plan.aspect_ratio)

        return image

    def _build_html(
        self,
        template: DesignTemplate,
        plan: DesignPlan,
        background_url: Optional[str],
        logo_url: Optional[str],
        product_image_url: Optional[str]
    ) -> str:
        """Build complete HTML document"""

        # Get canvas size
        width, height = self._get_canvas_size(plan.aspect_ratio)

        # Get brand colors
        colors = self._get_brand_colors(plan.palette_mode)

        # Get typography using compatible helper
        typography = self._get_typography_dict()
        font_family = typography.get('heading', {}).get('family', 'Inter, system-ui, sans-serif')

        # Build CSS with brand tokens
        css = template.css_template.format(
            width=width,
            height=height,
            primary_color=colors['primary'],
            secondary_color=colors['secondary'],
            accent_color=colors['accent'],
            text_color=colors['text'],
            font_family=font_family,
            background_url=background_url or '',
            product_image_url=product_image_url or ''
        )

        # Prepare HTML snippets
        logo_html = f'<img src="{logo_url}" class="logo" alt="Logo">' if logo_url else ''
        product_image_html = f'<img src="{product_image_url}" class="product-image" alt="Product">' if product_image_url else ''

        # Build HTML with content - use double braces for placeholders
        html = template.html_template.replace('{{logo_html}}', logo_html)
        html = html.replace('{{product_image_html}}', product_image_html)
        html = html.replace('{{headline}}', plan.headline)
        html = html.replace('{{subhead}}', plan.subhead)
        html = html.replace('{{cta_text}}', plan.cta_text)

        # Wrap in complete HTML document
        full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Design Preview</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: {font_family};
            overflow: hidden;
        }}

        {css}
    </style>
</head>
<body>
    {html}
</body>
</html>
"""

        return full_html

    def _render_with_playwright(self, html: str, aspect_ratio: str) -> Image.Image:
        """Render HTML to image using Playwright"""
        width, height = self._get_canvas_size(aspect_ratio)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': width, 'height': height})
            page.set_content(html)

            # Wait for any animations/fonts to load
            page.wait_for_timeout(1000)

            # Take screenshot
            screenshot_bytes = page.screenshot(type='png')
            browser.close()

        # Convert to PIL Image
        image = Image.open(BytesIO(screenshot_bytes))
        logger.info(f"✅ Rendered {width}x{height} design")

        return image

    def _get_canvas_size(self, aspect_ratio: str) -> Tuple[int, int]:
        """Get canvas dimensions for aspect ratio"""
        ratios = {
            "1x1": (1080, 1080),
            "4x5": (1080, 1350),
            "9x16": (1080, 1920),
            "16x9": (1920, 1080)
        }
        return ratios.get(aspect_ratio, (1080, 1080))

    def _get_colors_dict(self) -> Dict[str, str]:
        """
        Get colors dict compatible with both BrandTokens and BrandTokensV2

        Returns:
            Dict with 'primary', 'secondary', 'accent', 'text', 'background' keys
        """
        if hasattr(self.tokens, 'colors'):
            # BrandTokensV2 format - ColorPalette object
            neutral = self.tokens.colors.neutral if self.tokens.colors.neutral else {}
            return {
                'primary': self.tokens.colors.primary.hex,
                'secondary': self.tokens.colors.secondary.hex,
                'accent': self.tokens.colors.accent.hex,
                'text': neutral.get('text', neutral.get('black', '#1F2937')),
                'background': neutral.get('background', neutral.get('white', '#FFFFFF'))
            }
        else:
            # Old BrandTokens format - .color dict
            return {
                'primary': self.tokens.color.get('primary', '#4F46E5'),
                'secondary': self.tokens.color.get('secondary', '#7C3AED'),
                'accent': self.tokens.color.get('accent', '#F59E0B'),
                'text': self.tokens.color.get('text', '#1F2937'),
                'background': self.tokens.color.get('background', '#FFFFFF')
            }

    def _get_typography_dict(self) -> Dict[str, Any]:
        """
        Get typography dict compatible with both BrandTokens and BrandTokensV2

        Returns:
            Dict with typography settings
        """
        # BrandTokens uses 'type' field for typography
        if hasattr(self.tokens, 'type') and isinstance(self.tokens.type, dict):
            # Old BrandTokens format - 'type' contains typography
            return self.tokens.type
        elif hasattr(self.tokens, 'typography'):
            if isinstance(self.tokens.typography, dict):
                # BrandTokensV2 format as dict
                return self.tokens.typography
            else:
                # BrandTokensV2 format - may be a Typography object
                # For now, return sensible defaults
                return {
                    'heading': {'family': 'Inter, system-ui, sans-serif'},
                    'body': {'family': 'Inter, system-ui, sans-serif'}
                }
        else:
            # No typography data
            return {
                'heading': {'family': 'Inter, system-ui, sans-serif'},
                'body': {'family': 'Inter, system-ui, sans-serif'}
            }

    def _get_brand_colors(self, palette_mode: str) -> Dict[str, str]:
        """Get color palette based on mode - uses compatible helper"""
        # Get colors using compatible method
        colors = self._get_colors_dict()

        if palette_mode == 'primary':
            return {
                'primary': colors['primary'],
                'secondary': colors['secondary'],
                'accent': colors['accent'],
                'text': '#FFFFFF'
            }
        elif palette_mode == 'secondary':
            return {
                'primary': colors['secondary'],
                'secondary': colors['primary'],
                'accent': colors['accent'],
                'text': '#FFFFFF'
            }
        elif palette_mode == 'accent':
            return {
                'primary': colors['accent'],
                'secondary': colors['primary'],
                'accent': colors['secondary'],
                'text': '#FFFFFF'
            }
        else:  # mono or vibrant
            return {
                'primary': colors['primary'],
                'secondary': '#FFFFFF',
                'accent': colors['accent'],
                'text': '#FFFFFF'
            }

    def _create_placeholder(self, aspect_ratio: str) -> Image.Image:
        """Create placeholder image when Playwright not available"""
        width, height = self._get_canvas_size(aspect_ratio)
        return Image.new('RGB', (width, height), color='#F0F0F0')

    # ========================================================================
    # TEMPLATE HTML/CSS DEFINITIONS
    # ========================================================================

    def _get_hero_gradient_html(self) -> str:
        return """
<div class="design-container">
    <div class="gradient-bg"></div>
    <div class="content">
        {{logo_html}}
        <h1 class="headline">{{headline}}</h1>
        <p class="subhead">{{subhead}}</p>
        <button class="cta-button">{{cta_text}}</button>
    </div>
</div>
"""

    def _get_hero_gradient_css(self) -> str:
        return """
.design-container {{
    width: {width}px;
    height: {height}px;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 100%);
}}

.gradient-bg {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 0;
}}

.content {{
    position: relative;
    z-index: 1;
    text-align: center;
    padding: 80px;
    max-width: 85%;
}}

.logo {{
    width: 100px;
    height: auto;
    margin-bottom: 50px;
    filter: brightness(0) invert(1);
}}

.headline {{
    font-size: 84px;
    font-weight: 900;
    color: white;
    line-height: 0.95;
    margin-bottom: 30px;
    text-transform: uppercase;
    letter-spacing: -3px;
    text-shadow: 0 4px 20px rgba(0,0,0,0.3);
}}

.subhead {{
    font-size: 32px;
    font-weight: 400;
    color: white;
    opacity: 0.95;
    line-height: 1.3;
    margin-bottom: 50px;
}}

.cta-button {{
    background: white;
    color: {primary_color};
    font-size: 26px;
    font-weight: 700;
    padding: 24px 70px;
    border: none;
    border-radius: 60px;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 2px;
    box-shadow: 0 15px 50px rgba(0,0,0,0.4);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}}

.cta-button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}}
"""

    def _get_minimal_card_html(self) -> str:
        return """
<div class="design-container">
    <div class="card">
        {{logo_html}}
        <h1 class="headline">{{headline}}</h1>
        <p class="subhead">{{subhead}}</p>
        <div class="cta-button">{{cta_text}}</div>
    </div>
</div>
"""

    def _get_minimal_card_css(self) -> str:
        return """
.design-container {{
    width: {width}px;
    height: {height}px;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 60px;
}}

.card {{
    background: white;
    padding: 100px 80px;
    border-radius: 32px;
    box-shadow: 0 30px 80px rgba(0,0,0,0.12);
    text-align: center;
    max-width: 85%;
}}

.logo {{
    width: 90px;
    height: auto;
    margin-bottom: 50px;
}}

.headline {{
    font-size: 64px;
    font-weight: 800;
    color: {primary_color};
    line-height: 1.1;
    margin-bottom: 25px;
    letter-spacing: -1px;
}}

.subhead {{
    font-size: 26px;
    font-weight: 400;
    color: #555;
    line-height: 1.4;
    margin-bottom: 50px;
}}

.cta-button {{
    background: {primary_color};
    color: white;
    font-size: 22px;
    font-weight: 700;
    padding: 22px 55px;
    border-radius: 14px;
    display: inline-block;
    text-transform: uppercase;
    letter-spacing: 1px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}

.cta-button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.2);
}}
"""

    def _get_product_showcase_html(self) -> str:
        return """
<div class="design-container">
    <div class="product-section">
        {{product_image_html}}
    </div>
    <div class="text-section">
        {{logo_html}}
        <h1 class="headline">{{headline}}</h1>
        <p class="subhead">{{subhead}}</p>
        <button class="cta-button">{{cta_text}}</button>
    </div>
</div>
"""

    def _get_product_showcase_css(self) -> str:
        return """
.design-container {{
    width: {width}px;
    height: {height}px;
    display: flex;
    flex-direction: column;
    background: linear-gradient(180deg, {secondary_color} 0%, white 100%);
}}

.product-section {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 60px;
}}

.product-image {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    filter: drop-shadow(0 20px 40px rgba(0,0,0,0.2));
}}

.text-section {{
    padding: 60px;
    text-align: center;
    background: white;
}}

.logo {{
    width: 100px;
    height: auto;
    margin-bottom: 24px;
}}

.headline {{
    font-size: 48px;
    font-weight: 800;
    color: {primary_color};
    margin-bottom: 16px;
    line-height: 1.1;
}}

.subhead {{
    font-size: 20px;
    color: {secondary_color};
    margin-bottom: 32px;
    line-height: 1.5;
}}

.cta-button {{
    background: {primary_color};
    color: white;
    font-size: 18px;
    font-weight: 600;
    padding: 16px 48px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
}}
"""

    def _get_story_immersive_html(self) -> str:
        return """
<div class="design-container">
    <div class="background-image"></div>
    <div class="overlay"></div>
    <div class="content">
        {{logo_html}}
        <h1 class="headline">{{headline}}</h1>
        <button class="cta-button">{{cta_text}}</button>
    </div>
</div>
"""

    def _get_story_immersive_css(self) -> str:
        return """
.design-container {{
    width: {width}px;
    height: {height}px;
    position: relative;
    overflow: hidden;
}}

.background-image {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: url('{background_url}');
    background-size: cover;
    background-position: center;
    z-index: 0;
}}

.overlay {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.7) 100%);
    z-index: 1;
}}

.content {{
    position: absolute;
    bottom: 80px;
    left: 40px;
    right: 40px;
    z-index: 2;
}}

.logo {{
    width: 80px;
    height: auto;
    margin-bottom: 24px;
    filter: brightness(0) invert(1);
}}

.headline {{
    font-size: 56px;
    font-weight: 900;
    color: white;
    line-height: 1.1;
    margin-bottom: 32px;
    text-shadow: 0 4px 20px rgba(0,0,0,0.5);
}}

.cta-button {{
    background: {accent_color};
    color: white;
    font-size: 20px;
    font-weight: 700;
    padding: 18px 48px;
    border: none;
    border-radius: 50px;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 1px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}}
"""

    def _get_glassmorphism_html(self) -> str:
        return """
<div class="design-container">
    <div class="background-image"></div>
    <div class="glass-card">
        {{logo_html}}
        <h1 class="headline">{{headline}}</h1>
        <p class="subhead">{{subhead}}</p>
        <button class="cta-button">{{cta_text}}</button>
    </div>
</div>
"""

    def _get_glassmorphism_css(self) -> str:
        return """
.design-container {{
    width: {width}px;
    height: {height}px;
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 50%, {primary_color} 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 60px;
}}

.background-image {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 30% 50%, rgba(255,255,255,0.1) 0%, transparent 50%),
                radial-gradient(circle at 70% 50%, rgba(255,255,255,0.1) 0%, transparent 50%);
    z-index: 0;
}}

.glass-card {{
    position: relative;
    z-index: 1;
    background: rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(30px);
    -webkit-backdrop-filter: blur(30px);
    border-radius: 40px;
    padding: 90px 70px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 25px 70px rgba(0, 0, 0, 0.4);
    text-align: center;
    max-width: 85%;
}}

.logo {{
    width: 110px;
    height: auto;
    margin-bottom: 45px;
    filter: brightness(0) invert(1) drop-shadow(0 4px 12px rgba(0,0,0,0.3));
}}

.headline {{
    font-size: 72px;
    font-weight: 900;
    color: white;
    line-height: 1.05;
    margin-bottom: 28px;
    text-shadow: 0 6px 24px rgba(0,0,0,0.3);
    letter-spacing: -2px;
}}

.subhead {{
    font-size: 28px;
    font-weight: 400;
    color: white;
    opacity: 0.96;
    line-height: 1.35;
    margin-bottom: 48px;
}}

.cta-button {{
    background: white;
    color: {primary_color};
    font-size: 24px;
    font-weight: 700;
    padding: 23px 65px;
    border: none;
    border-radius: 60px;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    box-shadow: 0 12px 45px rgba(0,0,0,0.25);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}}

.cta-button:hover {{
    transform: translateY(-3px);
    box-shadow: 0 18px 55px rgba(0,0,0,0.35);
}}
"""
