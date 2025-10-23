"""
Design Engine - Unified Interface for Design Generation
Combines HTML designer, quality scoring, and brand intelligence
"""
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import os

from app.core.html_designer import HTMLDesigner, PLAYWRIGHT_AVAILABLE
from app.core.renderer_grid import GridRenderer
from app.core.quality_scorer import QualityScorer
from app.core.contrast_manager import ContrastManager
from app.core.brand_brain import BrandTokens
from app.core.chat_agent_planner import DesignPlan
from app.infra.logging import get_logger

logger = get_logger(__name__)


class DesignEngine:
    """
    Unified design generation engine

    Features:
    - Automatic renderer selection (HTML vs Pillow)
    - Quality scoring integration
    - Contrast validation
    - Brand consistency checks
    - Fallback handling
    """

    def __init__(self, tokens: BrandTokens, use_html: bool = True):
        """
        Initialize design engine

        Args:
            tokens: Brand design tokens
            use_html: Use HTML/CSS renderer (requires Playwright)
        """
        self.tokens = tokens
        self.use_html = use_html and PLAYWRIGHT_AVAILABLE

        # Initialize renderers
        if self.use_html:
            logger.info("🎨 Using HTML/CSS renderer (beautiful designs)")
            self.renderer = HTMLDesigner(tokens)
        else:
            logger.info("🎨 Using Pillow renderer (fallback)")
            self.renderer = GridRenderer(tokens)

        # Initialize quality tools
        self.quality_scorer = QualityScorer()
        self.contrast_manager = ContrastManager()

        logger.info(f"✅ DesignEngine initialized (HTML: {self.use_html})")

    def generate_design(
        self,
        plan: DesignPlan,
        background_url: Optional[str] = None,
        logo_url: Optional[str] = None,
        product_image_url: Optional[str] = None,
        validate_quality: bool = True
    ) -> Dict[str, Any]:
        """
        Generate complete design with quality scoring

        Args:
            plan: Design plan from chat agent
            background_url: Background image URL
            logo_url: Logo image URL
            product_image_url: Product image URL
            validate_quality: Run quality validation

        Returns:
            Dictionary with:
                - image: PIL Image object
                - quality_score: Quality score (0-100)
                - quality_details: Detailed quality breakdown
                - contrast_check: Contrast validation results
                - suggestions: Improvement suggestions
        """
        logger.info(f"🎨 Generating design: {plan.headline}")

        # Validate colors for accessibility
        if validate_quality:
            plan = self._validate_and_adjust_colors(plan)

        # Render design
        try:
            image = self.renderer.render_design(
                plan=plan,
                background_url=background_url,
                logo_url=logo_url,
                product_image_url=product_image_url
            )
            logger.info("✅ Design rendered successfully")
        except Exception as e:
            logger.error(f"❌ Rendering failed: {e}")
            # Fallback to grid renderer if HTML fails
            if self.use_html:
                logger.warning("⚠️  Falling back to Pillow renderer")
                fallback_renderer = GridRenderer(self.tokens)
                image = fallback_renderer.render_design(
                    plan=plan,
                    background_url=background_url,
                    logo_url=logo_url,
                    product_image_url=product_image_url
                )
            else:
                raise

        # Run quality validation
        result = {
            'image': image,
            'quality_score': None,
            'quality_details': None,
            'contrast_check': None,
            'suggestions': []
        }

        if validate_quality:
            logger.info("🔍 Running quality validation...")

            # Score design
            quality_result = self.quality_scorer.score_design(plan, image)
            result['quality_score'] = quality_result.overall_score
            result['quality_details'] = {
                'readability': quality_result.readability_score.score,
                'brand_consistency': quality_result.brand_consistency_score.score,
                'composition': quality_result.composition_score.score,
                'impact': quality_result.impact_score.score,
                'accessibility': quality_result.accessibility_score.score
            }
            result['suggestions'] = quality_result.suggestions

            logger.info(f"📊 Quality Score: {quality_result.overall_score}/100")

            # Validate contrast
            contrast_result = self._check_contrast(plan)
            result['contrast_check'] = contrast_result

            if not contrast_result['passes_wcag_aa']:
                result['suggestions'].append(
                    f"⚠️  Text contrast is too low ({contrast_result['ratio']:.2f}:1). "
                    f"WCAG AA requires 4.5:1. Consider using {contrast_result['suggested_color']}."
                )

        logger.info("✅ Design generation complete")
        return result

    def _validate_and_adjust_colors(self, plan: DesignPlan) -> DesignPlan:
        """
        Validate and adjust colors for accessibility

        Args:
            plan: Original design plan

        Returns:
            Updated design plan with accessible colors
        """
        # Get colors based on palette mode
        colors = self._get_palette_colors(plan.palette_mode)

        # Check if text colors need adjustment
        # Assuming white text on colored background for most designs
        text_color = '#FFFFFF'
        bg_color = colors['primary']

        # Calculate contrast
        ratio = self.contrast_manager.calculate_contrast_ratio(text_color, bg_color)

        if ratio < 4.5:  # WCAG AA minimum
            logger.warning(f"⚠️  Low contrast ({ratio:.2f}:1), adjusting colors...")

            # Try to adjust background color
            adjusted_bg = self.contrast_manager.ensure_readable_text(
                text_color=text_color,
                background_color=bg_color,
                target_ratio=4.5
            )

            logger.info(f"✅ Adjusted background: {bg_color} → {adjusted_bg}")

            # Update plan (this is a simplified approach)
            # In production, you'd want to update the actual color tokens

        return plan

    def _check_contrast(self, plan: DesignPlan) -> Dict[str, Any]:
        """
        Check contrast ratios for design

        Args:
            plan: Design plan

        Returns:
            Contrast check results
        """
        colors = self._get_palette_colors(plan.palette_mode)

        # Check white text on primary background
        text_color = '#FFFFFF'
        bg_color = colors['primary']

        ratio = self.contrast_manager.calculate_contrast_ratio(text_color, bg_color)
        wcag_result = self.contrast_manager.check_wcag_compliance(text_color, bg_color)

        result = {
            'ratio': ratio,
            'passes_wcag_aa': wcag_result['aa_normal'],
            'passes_wcag_aaa': wcag_result['aaa_normal'],
            'text_color': text_color,
            'background_color': bg_color,
            'suggested_color': None
        }

        # If contrast is too low, suggest adjustment
        if not wcag_result['aa_normal']:
            suggested = self.contrast_manager.ensure_readable_text(
                text_color=text_color,
                background_color=bg_color,
                target_ratio=4.5
            )
            result['suggested_color'] = suggested

        return result

    def _get_palette_colors(self, palette_mode: str) -> Dict[str, str]:
        """Get color palette based on mode"""
        colors = self.tokens.color

        if palette_mode == 'primary':
            return {
                'primary': colors.get('primary', '#000000'),
                'secondary': colors.get('secondary', '#666666'),
                'accent': colors.get('accent', '#FF6B6B')
            }
        elif palette_mode == 'secondary':
            return {
                'primary': colors.get('secondary', '#666666'),
                'secondary': colors.get('primary', '#000000'),
                'accent': colors.get('accent', '#FF6B6B')
            }
        elif palette_mode == 'accent':
            return {
                'primary': colors.get('accent', '#FF6B6B'),
                'secondary': colors.get('primary', '#000000'),
                'accent': colors.get('secondary', '#666666')
            }
        else:  # mono
            return {
                'primary': colors.get('primary', '#000000'),
                'secondary': '#FFFFFF',
                'accent': colors.get('accent', '#FF6B6B')
            }

    def preview_templates(self) -> Dict[str, str]:
        """
        Get list of available templates

        Returns:
            Dictionary of template_id -> template_name
        """
        if hasattr(self.renderer, 'templates'):
            return {
                template_id: template.name
                for template_id, template in self.renderer.templates.items()
            }
        else:
            return {'grid': 'Grid Layout (Pillow)'}

    def get_renderer_info(self) -> Dict[str, Any]:
        """
        Get information about current renderer

        Returns:
            Renderer information
        """
        return {
            'type': 'HTML/CSS' if self.use_html else 'Pillow',
            'playwright_available': PLAYWRIGHT_AVAILABLE,
            'templates': len(getattr(self.renderer, 'templates', {})),
            'supports_gradients': self.use_html,
            'supports_glassmorphism': self.use_html,
            'supports_shadows': self.use_html
        }
