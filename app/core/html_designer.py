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

    def __init__(self, tokens: Union[BrandTokens, BrandTokensV2], brand_guidelines: Optional[Dict[str, Any]] = None):
        """
        Initialize HTML designer

        Args:
            tokens: Brand design tokens (supports both old and new formats)
            brand_guidelines: Comprehensive brand guidelines from brandbook analyzer (optional)
        """
        self.tokens = tokens
        self.brand_guidelines = brand_guidelines or {}
        self.templates = self._load_templates()

        # Get colors in compatible way
        colors = self._get_colors_dict()
        logger.info(f"🎨 HTMLDesigner initialized with {len(self.templates)} templates")
        logger.info(f"🎨 Brand colors: Primary={colors.get('primary')}, Accent={colors.get('accent')}")

        if brand_guidelines:
            logger.info(f"✅ Using comprehensive brand guidelines with visual style: {brand_guidelines.get('visual_style', {}).get('overall_aesthetic', 'Not specified')}")

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

    def render_design_with_pbk(
        self,
        plan: DesignPlan,
        logo_url: Optional[str] = None
    ) -> Image.Image:
        """
        Generate design using Promptable Brand Kit (PBK) with LLM.

        This is the "full intelligence" mode where the LLM acts as a
        professional brand designer with complete brand knowledge.

        Args:
            plan: Design plan with headline, subheader, CTA
            logo_url: Optional URL to brand logo

        Returns:
            PIL Image of the generated design
        """
        from app.core.pbk_builder import PromptableBrandKit
        from openai import OpenAI
        from app.infra.config import settings
        import re

        logger.info("🎨 Generating design with PBK (Full Intelligence Mode)")

        # Check if we have brand guidelines
        if not self.brand_guidelines:
            logger.warning("⚠️  No brand guidelines available, falling back to template mode")
            return self.render_design(plan, None, logo_url, None)

        # Build PBK
        pbk_builder = PromptableBrandKit(self.brand_guidelines)

        # Create user request from plan
        user_request = f"""Create a design with:
- Headline: "{plan.headline}"
- Subheader: "{plan.subhead}"
- CTA Button: "{plan.cta_text}"

Target mood: {plan.palette_mode}"""

        # Get complete prompt
        prompt = pbk_builder.to_system_prompt(user_request, logo_url)

        logger.info(f"📤 Sending PBK prompt to GPT-4 ({len(prompt)} chars)")

        try:
            # Call OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert brand designer. Create pixel-perfect HTML/CSS designs that follow brand guidelines exactly."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000
            )

            html_response = response.choices[0].message.content
            logger.info(f"✅ Received HTML response from GPT-4 ({len(html_response)} chars)")

            # Extract HTML from response (might be wrapped in markdown)
            html = self._extract_html_from_response(html_response)

            # Validate HTML
            if not html or '<html' not in html.lower():
                logger.error("❌ Invalid HTML received from LLM")
                logger.warning("Falling back to template mode")
                return self.render_design(plan, None, logo_url, None)

            # CRITICAL: Validate no white boxes on text
            validation_issues = self._validate_no_white_boxes(html)
            if validation_issues:
                logger.error(f"❌ Design validation FAILED: {validation_issues}")
                logger.error("Design has white boxes on text - REJECTING and retrying with stricter prompt")

                # Retry with ULTRA-STRICT prompt
                retry_prompt = self._add_ultra_strict_rules(prompt, validation_issues)

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert brand designer. Create pixel-perfect HTML/CSS designs that follow brand guidelines exactly."
                        },
                        {
                            "role": "user",
                            "content": retry_prompt
                        }
                    ],
                    temperature=0.5,  # Lower temperature for more conservative output
                    max_tokens=4000
                )

                html_response = response.choices[0].message.content
                html = self._extract_html_from_response(html_response)

                # Validate again
                validation_issues = self._validate_no_white_boxes(html)
                if validation_issues:
                    logger.warning(f"⚠️  Still has issues after retry: {validation_issues}")
                    logger.warning("🔧 Forcing CSS cleanup - stripping backgrounds from text elements")
                else:
                    logger.info("✅ Retry successful - validation passed!")
            else:
                logger.info("✅ Design validation PASSED - no white boxes detected")

            # FINAL ENFORCEMENT: Always strip backgrounds from text as safety measure
            # This ensures NO white boxes regardless of LLM output
            logger.info("🔧 Final enforcement: Stripping any remaining backgrounds from text")

            # Save HTML before stripping for debugging
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='_before_strip.html', delete=False) as f:
                f.write(html)
                logger.info(f"HTML before stripping saved to: {f.name}")

            html = self._force_remove_text_backgrounds(html)

            # FORCE replace non-brand colors
            html = self._force_brand_colors(html)

            # Save HTML after stripping for debugging
            with tempfile.NamedTemporaryFile(mode='w', suffix='_after_strip.html', delete=False) as f:
                f.write(html)
                logger.info(f"HTML after stripping saved to: {f.name}")

            # Render to image
            if PLAYWRIGHT_AVAILABLE:
                logger.info("🎭 Rendering HTML with Playwright...")
                image = self._render_with_playwright(html, plan.aspect_ratio)
                logger.info("✅ Design rendered successfully with PBK!")
                return image
            else:
                logger.error("❌ Playwright not available, cannot render HTML")
                return self._create_placeholder(plan.aspect_ratio)

        except Exception as e:
            logger.error(f"❌ Error in PBK generation: {str(e)}")
            logger.warning("Falling back to template mode")
            import traceback
            logger.error(traceback.format_exc())
            return self.render_design(plan, None, logo_url, None)

    def _extract_html_from_response(self, response: str) -> str:
        """
        Extract HTML from LLM response.

        LLM might return HTML wrapped in markdown code blocks like:
        ```html
        <html>...</html>
        ```

        Args:
            response: Raw LLM response

        Returns:
            Clean HTML string
        """
        import re

        # Remove markdown code blocks
        # Pattern: ```html ... ``` or ``` ... ```
        html_block_pattern = r'```(?:html)?\s*(<!DOCTYPE.*?</html>)\s*```'
        match = re.search(html_block_pattern, response, re.DOTALL | re.IGNORECASE)

        if match:
            html = match.group(1)
            logger.info("✅ Extracted HTML from markdown code block")
            return html

        # If no code blocks, check if response is direct HTML
        if '<!DOCTYPE' in response or '<html' in response:
            logger.info("✅ Response is direct HTML")
            return response

        # Last resort: look for any <html> tags
        html_pattern = r'(<html.*?</html>)'
        match = re.search(html_pattern, response, re.DOTALL | re.IGNORECASE)

        if match:
            html = match.group(1)
            # Add DOCTYPE if missing
            if '<!DOCTYPE' not in html:
                html = '<!DOCTYPE html>\n' + html
            logger.info("✅ Extracted HTML tags from response")
            return html

        logger.warning("⚠️  Could not extract valid HTML from response")
        return response  # Return as-is and let validation catch it

    def _validate_no_white_boxes(self, html: str) -> Optional[str]:
        """
        Validate that the HTML does not have white background boxes on headline/subheader text.

        Returns:
            None if valid, error message string if invalid
        """
        import re

        # Extract all CSS (inline styles and <style> blocks)
        css_content = ""

        # Get <style> blocks
        style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE)
        css_content += "\n".join(style_blocks)

        # Check for problematic patterns in CSS
        issues = []

        # Check for background/background-color on headline/title/h1 classes
        headline_patterns = [
            r'\.headline[^{]*\{[^}]*background(?:-color)?:\s*(?!transparent|none|inherit|unset)',
            r'\.title[^{]*\{[^}]*background(?:-color)?:\s*(?!transparent|none|inherit|unset)',
            r'\.hero-title[^{]*\{[^}]*background(?:-color)?:\s*(?!transparent|none|inherit|unset)',
            r'h1[^{]*\{[^}]*background(?:-color)?:\s*(?!transparent|none|inherit|unset)',
        ]

        for pattern in headline_patterns:
            if re.search(pattern, css_content, re.IGNORECASE):
                issues.append("Headline has background/background-color property")
                break

        # Check for background on subheader/subtitle classes
        subheader_patterns = [
            r'\.subheader[^{]*\{[^}]*background(?:-color)?:\s*(?!transparent|none|inherit|unset)',
            r'\.subtitle[^{]*\{[^}]*background(?:-color)?:\s*(?!transparent|none|inherit|unset)',
            r'\.hero-subtitle[^{]*\{[^}]*background(?:-color)?:\s*(?!transparent|none|inherit|unset)',
            r'h2[^{]*\{[^}]*background(?:-color)?:\s*(?!transparent|none|inherit|unset)',
        ]

        for pattern in subheader_patterns:
            if re.search(pattern, css_content, re.IGNORECASE):
                issues.append("Subheader has background/background-color property")
                break

        # Check for white/light backgrounds specifically (rgba(255,255,255), #fff, #ffffff, white, etc)
        white_bg_patterns = [
            r'background(?:-color)?:\s*(?:#fff(?:fff)?|white|rgba?\(255,\s*255,\s*255)',
        ]

        for pattern in white_bg_patterns:
            matches = re.findall(pattern, css_content, re.IGNORECASE)
            if matches:
                issues.append(f"Found {len(matches)} white/light background(s)")
                break

        if issues:
            return "; ".join(issues)

        return None

    def _add_ultra_strict_rules(self, original_prompt: str, validation_issues: str) -> str:
        """
        Add ultra-strict rules to prompt after validation failure.

        Args:
            original_prompt: The original prompt
            validation_issues: What validation issues were found

        Returns:
            Enhanced prompt with ultra-strict rules
        """
        ultra_strict_addition = f"""

🚨🚨🚨 CRITICAL VALIDATION FAILURE - YOUR PREVIOUS DESIGN WAS REJECTED 🚨🚨🚨

The design you just created FAILED validation with these issues:
{validation_issues}

THIS IS YOUR SECOND CHANCE. If you fail again, the design will be discarded.

🔴 ABSOLUTELY MANDATORY RULES - FOLLOW EXACTLY:

1. **NO BACKGROUND PROPERTIES ON TEXT ELEMENTS**
   - DO NOT use `background`, `background-color`, `background-image` on .headline, .title, h1, .subheader, .subtitle, h2
   - Text must be styled ONLY with `color` property
   - Use `text-shadow` for readability if needed, NOT backgrounds

2. **FORBIDDEN CSS - DO NOT USE:**
   ```css
   /* ❌ WRONG - DO NOT DO THIS */
   .headline {{
       background: white;          /* FORBIDDEN */
       background-color: #ffffff;  /* FORBIDDEN */
       background: rgba(255,255,255,0.9); /* FORBIDDEN */
   }}
   ```

3. **REQUIRED CSS - USE THIS INSTEAD:**
   ```css
   /* ✅ CORRECT - DO THIS */
   .headline {{
       color: #FFFFFF;  /* Only color property */
       text-shadow: 2px 2px 8px rgba(0,0,0,0.3);  /* For readability */
       /* NO background property at all */
   }}
   ```

4. **VALIDATION CHECKLIST - CHECK BEFORE SUBMITTING:**
   ☐ Search your CSS for "background" on headline/title/h1/subheader/subtitle/h2
   ☐ If you find ANY background property on these elements, DELETE IT
   ☐ Use ONLY `color` property for text styling
   ☐ Double-check: NO white boxes, NO containers around text

If you add background/background-color to headlines or subheaders, YOU WILL FAIL VALIDATION AGAIN.

This is a professional brand design system - white boxes on text look amateur and unprofessional.

"""

        return original_prompt + ultra_strict_addition

    def _force_remove_text_backgrounds(self, html: str) -> str:
        """
        FORCIBLY remove all background properties from headline and subheader elements.
        This is the nuclear option - we don't trust the LLM, we just strip it out.

        Args:
            html: HTML string with CSS

        Returns:
            HTML with background properties removed from text elements
        """
        import re

        logger.info("🔧 Force-removing backgrounds from text elements...")

        # Extract <style> blocks
        def clean_css_block(match):
            css_content = match.group(1)
            original_css = css_content

            # Target selectors that are headlines/subheaders
            text_selectors = [
                r'\.headline',
                r'\.title',
                r'\.hero-title',
                r'\.subheader',
                r'\.subtitle',
                r'\.hero-subtitle',
                r'h1',
                r'h2',
            ]

            for selector in text_selectors:
                # Find CSS rules for this selector
                # Pattern: .selector { ... }
                selector_pattern = rf'({selector}[^{{]*)\{{([^}}]*)\}}'

                def remove_backgrounds(css_match):
                    selector_part = css_match.group(1)
                    rules = css_match.group(2)

                    # Remove background and background-color properties
                    rules = re.sub(
                        r'background(?:-color|-image)?:\s*[^;]+;?',
                        '',
                        rules,
                        flags=re.IGNORECASE
                    )

                    # Remove padding if it's creating boxes (optional - be aggressive)
                    rules = re.sub(
                        r'padding:\s*[^;]+;?',
                        '',
                        rules,
                        flags=re.IGNORECASE
                    )

                    # Remove border-radius if creating rounded boxes
                    rules = re.sub(
                        r'border-radius:\s*[^;]+;?',
                        '',
                        rules,
                        flags=re.IGNORECASE
                    )

                    # Ensure text has white color for visibility on dark gradients
                    if 'color:' not in rules.lower():
                        rules += '\n  color: #FFFFFF;'

                    # Add text-shadow for readability
                    if 'text-shadow:' not in rules.lower():
                        rules += '\n  text-shadow: 2px 2px 8px rgba(0,0,0,0.4);'

                    return f'{selector_part}{{{rules}}}'

                css_content = re.sub(
                    selector_pattern,
                    remove_backgrounds,
                    css_content,
                    flags=re.DOTALL
                )

            if css_content != original_css:
                logger.info(f"  ✅ Cleaned CSS for text elements")

            return f'<style>{css_content}</style>'

        # Process all <style> blocks
        html = re.sub(
            r'<style[^>]*>(.*?)</style>',
            clean_css_block,
            html,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Also remove inline styles on headline/subheader elements
        # Pattern: <div class="headline" style="background: white;">
        text_class_patterns = [
            r'headline',
            r'title',
            r'hero-title',
            r'subheader',
            r'subtitle',
            r'hero-subtitle',
        ]

        for class_name in text_class_patterns:
            # Find elements with this class and remove background from inline style
            pattern = rf'(<[^>]*class="[^"]*{class_name}[^"]*"[^>]*style=")([^"]*)(">)'

            def clean_inline_style(match):
                before = match.group(1)
                style = match.group(2)
                after = match.group(3)

                # Remove background properties
                style = re.sub(r'background(?:-color|-image)?:\s*[^;]+;?', '', style, flags=re.IGNORECASE)
                style = re.sub(r'padding:\s*[^;]+;?', '', style, flags=re.IGNORECASE)
                style = re.sub(r'border-radius:\s*[^;]+;?', '', style, flags=re.IGNORECASE)

                return f'{before}{style}{after}'

            html = re.sub(pattern, clean_inline_style, html, flags=re.IGNORECASE)

        logger.info("✅ Background stripping complete")
        return html

    def _force_brand_colors(self, html: str) -> str:
        """
        Force replace any non-brand colors, fix logo placement, and enforce brand fonts.
        """
        import re

        logger.info("🎨 Forcing brand compliance...")

        # 1. Fix colors
        wrong_colors = {
            '#A29BFE': '#000000',
            '#a29bfe': '#000000',
            'A29BFE': '#000000',
            '#6C5CE7': '#1DB954',
            '#74B9FF': '#B8E986',
            '#0984E3': '#1DB954',
        }

        for wrong, correct in wrong_colors.items():
            html = html.replace(wrong, correct)
            html = html.replace(wrong.lower(), correct)
            html = html.replace(wrong.upper(), correct)

        # 2. Fix logo placement: left → right, INSIDE the frame
        html = re.sub(
            r'\.logo\s*\{([^}]*?)left:\s*\d+px;',
            r'.logo {\1right: 60px;',
            html,
            flags=re.DOTALL
        )

        # Make logo visible with white circle, positioned safely inside
        html = re.sub(
            r'(\.logo\s*\{[^}]*?)width:\s*\d+px;',
            r'\1width: 80px; background: white; border-radius: 50%; padding: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); z-index: 100; top: 40px;',
            html,
            flags=re.DOTALL
        )

        # CRITICAL: Fix dimensions - must be exactly 1200x630px, NO viewport heights
        html = re.sub(r'height:\s*100vh;?', 'height: 630px;', html, flags=re.IGNORECASE)
        html = re.sub(r'min-height:\s*100vh;?', '', html, flags=re.IGNORECASE)

        # Force body and html to exact dimensions
        html = re.sub(
            r'(body[^{]*\{[^}]*?)',
            r'\1width: 1200px; height: 630px; overflow: hidden; ',
            html,
            flags=re.DOTALL,
            count=1
        )

        # Force container to fill exactly
        html = re.sub(
            r'(\.container[^{]*\{[^}]*?)',
            r'\1width: 1200px !important; height: 630px !important; margin: 0; padding: 64px; box-sizing: border-box; ',
            html,
            flags=re.DOTALL,
            count=1
        )

        # 3. Fix fonts: replace generic fonts with Circular
        generic_fonts = ['Montserrat', 'Roboto', 'Open Sans', 'Lato', 'Helvetica']
        for font in generic_fonts:
            html = html.replace(f"'{font}'", "'Circular', 'Helvetica Neue', Arial")
            html = html.replace(f'"{font}"', "'Circular', 'Helvetica Neue', Arial")

        # 4. Fix button: light green → Spotify green
        html = re.sub(
            r'(\.cta-button[^}]*background:\s*)#B8E986',
            r'\1#1DB954',
            html,
            flags=re.IGNORECASE
        )

        logger.info("✅ Brand compliance enforced")
        return html

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

        # Generate brand-specific CSS utilities
        brand_utilities = self._generate_brand_css_utilities()

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

        /* Brand CSS Utilities */
        {brand_utilities}

        /* Template Styles */
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

    def _generate_brand_css_utilities(self) -> str:
        """
        Generate Tailwind-inspired utility CSS classes based on brand guidelines

        Returns CSS variables and utility classes for brand-specific styling
        """
        colors = self._get_colors_dict()
        typography = self._get_typography_dict()

        # Extract additional brand styling from guidelines
        visual_identity = self.brand_guidelines.get('visual_identity', {})
        spacing = visual_identity.get('spacing', {})
        borders_shadows = visual_identity.get('borders_shadows', {})
        visual_style = self.brand_guidelines.get('visual_style', {})

        # Get spacing scale
        spacing_scale = spacing.get('scale', ['4px', '8px', '16px', '24px', '32px', '48px', '64px'])
        base_unit = spacing.get('base_unit', '8px')

        # Get border radius
        border_radius = borders_shadows.get('border_radius', [])
        default_radius = '8px'
        if border_radius:
            for r in border_radius:
                if 'rounded' in r.lower() or 'subtle' in r.lower():
                    # Extract px value
                    import re
                    match = re.search(r'(\d+px)', r)
                    if match:
                        default_radius = match.group(1)
                        break

        # Get shadows
        shadows = borders_shadows.get('shadows', [])
        box_shadow_sm = '0 1px 2px 0 rgb(0 0 0 / 0.05)'
        box_shadow_md = '0 4px 6px -1px rgb(0 0 0 / 0.1)'
        box_shadow_lg = '0 10px 15px -3px rgb(0 0 0 / 0.1)'

        if shadows:
            for shadow in shadows:
                if isinstance(shadow, dict):
                    name = shadow.get('name', '').lower()
                    value = shadow.get('value', '')
                    if 'sm' in name and value:
                        box_shadow_sm = value
                    elif 'md' in name and value:
                        box_shadow_md = value
                    elif 'lg' in name and value:
                        box_shadow_lg = value

        # Generate CSS
        css_utilities = f"""
/* Brand CSS Variables */
:root {{
    /* Colors */
    --brand-primary: {colors.get('primary', '#4F46E5')};
    --brand-secondary: {colors.get('secondary', '#7C3AED')};
    --brand-accent: {colors.get('accent', '#F59E0B')};
    --brand-text: {colors.get('text', '#1F2937')};
    --brand-background: {colors.get('background', '#FFFFFF')};

    /* Spacing */
    --brand-spacing-base: {base_unit};
    --brand-spacing-xs: {spacing_scale[0] if len(spacing_scale) > 0 else '4px'};
    --brand-spacing-sm: {spacing_scale[1] if len(spacing_scale) > 1 else '8px'};
    --brand-spacing-md: {spacing_scale[2] if len(spacing_scale) > 2 else '16px'};
    --brand-spacing-lg: {spacing_scale[3] if len(spacing_scale) > 3 else '24px'};
    --brand-spacing-xl: {spacing_scale[4] if len(spacing_scale) > 4 else '32px'};
    --brand-spacing-2xl: {spacing_scale[5] if len(spacing_scale) > 5 else '48px'};

    /* Typography */
    --brand-font-heading: {typography.get('heading', {}).get('family', 'Inter, system-ui, sans-serif')};
    --brand-font-body: {typography.get('body', {}).get('family', 'Inter, system-ui, sans-serif')};

    /* Borders & Shadows */
    --brand-radius: {default_radius};
    --brand-shadow-sm: {box_shadow_sm};
    --brand-shadow-md: {box_shadow_md};
    --brand-shadow-lg: {box_shadow_lg};
}}

/* Utility Classes */
.brand-gradient {{
    background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-accent) 100%);
}}

.brand-gradient-secondary {{
    background: linear-gradient(135deg, var(--brand-secondary) 0%, var(--brand-primary) 100%);
}}

.brand-gradient-subtle {{
    background: linear-gradient(180deg, var(--brand-primary) 0%, var(--brand-secondary) 100%);
}}

.brand-btn-primary {{
    background: var(--brand-primary);
    color: white;
    padding: var(--brand-spacing-md) var(--brand-spacing-xl);
    border-radius: var(--brand-radius);
    font-weight: 600;
    box-shadow: var(--brand-shadow-md);
    transition: all 0.3s ease;
}}

.brand-btn-primary:hover {{
    box-shadow: var(--brand-shadow-lg);
    transform: translateY(-2px);
}}

.brand-card {{
    background: white;
    padding: var(--brand-spacing-xl);
    border-radius: var(--brand-radius);
    box-shadow: var(--brand-shadow-lg);
}}

.brand-text-primary {{
    color: var(--brand-primary);
}}

.brand-text-gradient {{
    background: linear-gradient(135deg, var(--brand-primary), var(--brand-accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
"""
        return css_utilities

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
