"""
Layout Engine
Smart, slot-based composition system for template-free design generation
"""
from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass
import json
from pathlib import Path

from app.core.schemas_v2 import (
    LayoutTemplate, LayoutSlot, SlotArea, SlotType,
    LayoutRules, DesignPlanV2
)
from app.core.chat_agent_planner import DesignPlan  # Legacy compatibility
from app.infra.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ContentDensity:
    """Analysis of content density in a design"""
    text_heavy: bool  # Lots of text
    image_heavy: bool  # Focus on visuals
    balanced: bool  # Mix of both
    score: float  # 0-1, where 1 = very text heavy


class LayoutEngine:
    """
    Smart layout engine that selects and adapts templates

    Features:
    - Template-free layout generation
    - Rule-based slot composition
    - Content-aware template selection
    - Dynamic grid adaptation
    - Visual weight distribution
    """

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize layout engine

        Args:
            templates_dir: Directory containing layout template JSON files
        """
        self.templates: Dict[str, LayoutTemplate] = {}
        self.templates_dir = templates_dir

        # Load built-in templates
        self._load_builtin_templates()

        # Load custom templates if directory provided
        if templates_dir:
            self._load_custom_templates(templates_dir)

        logger.info(f"Layout engine initialized with {len(self.templates)} templates")

    def _load_builtin_templates(self):
        """Load built-in layout templates"""
        # Hero + Badge + CTA template
        self.templates["hero_badge_cta_v1"] = LayoutTemplate.get_hero_badge_cta_template()

        # Create additional built-in templates
        self.templates["minimal_text_v1"] = self._create_minimal_text_template()
        self.templates["product_showcase_v1"] = self._create_product_showcase_template()
        self.templates["story_immersive_v1"] = self._create_story_immersive_template()
        self.templates["text_heavy_v1"] = self._create_text_heavy_template()

        logger.info(f"Loaded {len(self.templates)} built-in templates")

    def _load_custom_templates(self, templates_dir: str):
        """Load custom templates from directory"""
        templates_path = Path(templates_dir)

        if not templates_path.exists():
            logger.warning(f"Templates directory not found: {templates_dir}")
            return

        for json_file in templates_path.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    template = LayoutTemplate.from_dict(data)
                    self.templates[template.id] = template
                    logger.info(f"Loaded custom template: {template.id}")
            except Exception as e:
                logger.error(f"Failed to load template {json_file}: {e}")

    def select_optimal_layout(
        self,
        plan: DesignPlan,
        aspect_ratio: Optional[str] = None
    ) -> LayoutTemplate:
        """
        Select the best layout template for a design plan

        Args:
            plan: Design plan from chat agent
            aspect_ratio: Override aspect ratio (optional)

        Returns:
            Optimal LayoutTemplate
        """
        aspect = aspect_ratio or plan.aspect_ratio
        channel = plan.channel

        logger.info(f"Selecting layout for {channel} {aspect}")

        # Calculate content density
        density = self._calculate_content_density(plan)

        # Filter templates by aspect ratio and channel
        candidates = [
            t for t in self.templates.values()
            if aspect in t.aspect_ratios and channel in t.channels
        ]

        if not candidates:
            # Fallback: any template matching aspect ratio
            candidates = [
                t for t in self.templates.values()
                if aspect in t.aspect_ratios
            ]

        if not candidates:
            # Last resort: use default
            logger.warning(f"No templates found for {aspect}, using default")
            return self.templates["hero_badge_cta_v1"]

        # Score each candidate
        scored_templates = []
        for template in candidates:
            score = self._score_template_fit(template, plan, density)
            scored_templates.append((score, template))

        # Sort by score (descending)
        scored_templates.sort(key=lambda x: x[0], reverse=True)

        selected = scored_templates[0][1]
        logger.info(f"✅ Selected template: {selected.id} (score: {scored_templates[0][0]:.2f})")

        return selected

    def _calculate_content_density(self, plan: DesignPlan) -> ContentDensity:
        """
        Calculate content density from design plan

        Args:
            plan: Design plan

        Returns:
            ContentDensity analysis
        """
        # Count words
        total_words = (
            len(plan.headline.split()) +
            len(plan.subhead.split()) +
            len(plan.cta_text.split())
        )

        # Analyze visual needs
        has_product = plan.product_image_needed
        has_complex_visual = any(
            keyword in plan.visual_concept.lower()
            for keyword in ["people", "product", "scene", "environment", "lifestyle"]
        )

        # Calculate score
        # More words = higher score (more text-heavy)
        text_score = min(1.0, total_words / 30.0)

        # Image score is inverse
        image_score = 1.0 if (has_product or has_complex_visual) else 0.3

        # Determine type
        text_heavy = text_score > 0.7
        image_heavy = image_score > 0.7 and text_score < 0.5
        balanced = not text_heavy and not image_heavy

        logger.info(f"Content density: text={text_score:.2f}, image={image_score:.2f}")

        return ContentDensity(
            text_heavy=text_heavy,
            image_heavy=image_heavy,
            balanced=balanced,
            score=text_score
        )

    def _score_template_fit(
        self,
        template: LayoutTemplate,
        plan: DesignPlan,
        density: ContentDensity
    ) -> float:
        """
        Score how well a template fits the design plan

        Args:
            template: Layout template
            plan: Design plan
            density: Content density analysis

        Returns:
            Fit score (0-1)
        """
        score = 0.5  # Base score

        # Match content density
        template_id_lower = template.id.lower()

        if density.text_heavy and "text_heavy" in template_id_lower:
            score += 0.3
        elif density.image_heavy and ("product" in template_id_lower or "immersive" in template_id_lower):
            score += 0.3
        elif density.balanced and "hero" in template_id_lower:
            score += 0.2

        # Match product needs
        if plan.product_image_needed:
            has_product_slot = any(s.id == "product" for s in template.slots)
            if has_product_slot:
                score += 0.2

        # Match channel
        if plan.channel in template.channels:
            score += 0.1

        # Match aspect ratio
        if plan.aspect_ratio in template.aspect_ratios:
            score += 0.1

        return min(1.0, score)

    def adapt_template_to_plan(
        self,
        template: LayoutTemplate,
        plan: DesignPlan
    ) -> LayoutTemplate:
        """
        Adapt template slots based on design plan specifics

        Args:
            template: Base template
            plan: Design plan

        Returns:
            Adapted template
        """
        import copy
        adapted = copy.deepcopy(template)

        # Adjust logo position
        for slot in adapted.slots:
            if slot.id == "logo":
                # Update logo position based on plan
                logo_pos = self._get_logo_grid_position(plan.logo_position)
                if isinstance(slot.area, SlotArea):
                    slot.area.x = logo_pos[0]
                    slot.area.y = logo_pos[1]

        # Adjust CTA text
        for slot in adapted.slots:
            if slot.id == "cta" and slot.text:
                slot.text["content"] = plan.cta_text

        logger.info(f"Adapted template {template.id} for plan")
        return adapted

    def _get_logo_grid_position(self, position_code: str) -> tuple[int, int]:
        """Convert logo position code to grid coordinates"""
        positions = {
            'TL': (0, 0),      # Top-left
            'TR': (10, 0),     # Top-right
            'BR': (10, 10),    # Bottom-right
            'BL': (0, 10),     # Bottom-left
        }
        return positions.get(position_code, (10, 0))

    def export_template(self, template_id: str, output_path: str) -> None:
        """
        Export template to JSON file

        Args:
            template_id: Template ID
            output_path: Output file path
        """
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")

        template = self.templates[template_id]

        with open(output_path, 'w') as f:
            f.write(template.to_json())

        logger.info(f"Exported template {template_id} to {output_path}")

    def list_templates(
        self,
        aspect_ratio: Optional[str] = None,
        channel: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List available templates with filters

        Args:
            aspect_ratio: Filter by aspect ratio
            channel: Filter by channel

        Returns:
            List of template info dicts
        """
        templates = list(self.templates.values())

        # Filter
        if aspect_ratio:
            templates = [t for t in templates if aspect_ratio in t.aspect_ratios]
        if channel:
            templates = [t for t in templates if channel in t.channels]

        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "aspect_ratios": t.aspect_ratios,
                "channels": t.channels,
                "slot_count": len(t.slots)
            }
            for t in templates
        ]

    # ========================================================================
    # BUILT-IN TEMPLATE CREATORS
    # ========================================================================

    def _create_minimal_text_template(self) -> LayoutTemplate:
        """Minimal template: Large headline + CTA only"""
        return LayoutTemplate(
            id="minimal_text_v1",
            name="Minimal Text",
            description="Clean layout with large headline and CTA, minimal distractions",
            aspect_ratios=["1x1", "4x5"],
            channels=["ig", "fb", "linkedin"],
            slots=[
                LayoutSlot(
                    id="background",
                    type=SlotType.IMAGE,
                    layer=0,
                    area="full",
                    fit="cover"
                ),
                LayoutSlot(
                    id="headline",
                    type=SlotType.TEXT,
                    layer=2,
                    area=SlotArea(x=1, y=4, w=10, h=4),
                    font_size="clamp(80px, 10vw, 180px)",
                    font_weight=900,
                    color="#FFFFFF",
                    align="center",
                    effects=["drop-shadow"]
                ),
                LayoutSlot(
                    id="cta",
                    type=SlotType.BUTTON,
                    layer=3,
                    area=SlotArea(x=3, y=10, w=6, h=1),
                    background="primary",
                    color="#FFFFFF",
                    border_radius=16,
                    font_size="48px",
                    font_weight=700
                ),
                LayoutSlot(
                    id="logo",
                    type=SlotType.IMAGE,
                    layer=4,
                    area=SlotArea(x=10, y=0, w=2, h=2),
                    fit="contain"
                )
            ],
            rules=LayoutRules(
                text_contrast_min=4.5,
                logo_clearance="1x",
                cta_prominence="must be largest button"
            )
        )

    def _create_product_showcase_template(self) -> LayoutTemplate:
        """Product showcase: Product image + text + CTA"""
        return LayoutTemplate(
            id="product_showcase_v1",
            name="Product Showcase",
            description="Large product image with supporting text and CTA",
            aspect_ratios=["1x1", "4x5"],
            channels=["ig", "fb"],
            slots=[
                LayoutSlot(
                    id="background",
                    type=SlotType.IMAGE,
                    layer=0,
                    area="full",
                    fit="cover"
                ),
                LayoutSlot(
                    id="product",
                    type=SlotType.IMAGE,
                    layer=1,
                    area=SlotArea(x=2, y=1, w=8, h=6),
                    fit="contain"
                ),
                LayoutSlot(
                    id="headline",
                    type=SlotType.TEXT,
                    layer=2,
                    area=SlotArea(x=1, y=7, w=10, h=2),
                    font_size="72px",
                    font_weight=800,
                    color="#000000",
                    align="center"
                ),
                LayoutSlot(
                    id="subhead",
                    type=SlotType.TEXT,
                    layer=2,
                    area=SlotArea(x=1, y=9, w=10, h=1),
                    font_size="36px",
                    color="#000000",
                    align="center"
                ),
                LayoutSlot(
                    id="cta",
                    type=SlotType.BUTTON,
                    layer=3,
                    area=SlotArea(x=2, y=10, w=8, h=1),
                    background="accent",
                    color="#FFFFFF",
                    border_radius=16,
                    font_size="48px",
                    font_weight=700
                ),
                LayoutSlot(
                    id="logo",
                    type=SlotType.IMAGE,
                    layer=4,
                    area=SlotArea(x=0, y=0, w=2, h=2),
                    fit="contain"
                )
            ],
            rules=LayoutRules(
                text_contrast_min=4.5,
                logo_clearance="1x"
            )
        )

    def _create_story_immersive_template(self) -> LayoutTemplate:
        """Instagram Story: Immersive full-bleed design"""
        return LayoutTemplate(
            id="story_immersive_v1",
            name="Story Immersive",
            description="Full-bleed Instagram story with bottom text overlay",
            aspect_ratios=["9x16"],
            channels=["ig"],
            slots=[
                LayoutSlot(
                    id="background",
                    type=SlotType.IMAGE,
                    layer=0,
                    area="full",
                    fit="cover"
                ),
                LayoutSlot(
                    id="gradient",
                    type=SlotType.GRADIENT,
                    layer=1,
                    area="full",
                    gradient="linear-gradient(180deg, rgba(0,0,0,0) 50%, rgba(0,0,0,0.6) 100%)"
                ),
                LayoutSlot(
                    id="headline",
                    type=SlotType.TEXT,
                    layer=2,
                    area=SlotArea(x=1, y=14, w=10, h=2),
                    font_size="64px",
                    font_weight=800,
                    color="#FFFFFF",
                    align="center"
                ),
                LayoutSlot(
                    id="subhead",
                    type=SlotType.TEXT,
                    layer=2,
                    area=SlotArea(x=1, y=16, w=10, h=1),
                    font_size="32px",
                    color="#FFFFFF",
                    align="center"
                ),
                LayoutSlot(
                    id="cta",
                    type=SlotType.BUTTON,
                    layer=3,
                    area=SlotArea(x=2, y=18, w=8, h=1),
                    background="accent",
                    color="#FFFFFF",
                    border_radius=24,
                    font_size="40px",
                    font_weight=700
                ),
                LayoutSlot(
                    id="logo",
                    type=SlotType.IMAGE,
                    layer=4,
                    area=SlotArea(x=5, y=1, w=2, h=2),
                    fit="contain"
                )
            ],
            rules=LayoutRules(
                text_contrast_min=4.5,
                safe_zones=["bottom 25%"]
            )
        )

    def _create_text_heavy_template(self) -> LayoutTemplate:
        """Text-heavy: Multiple text blocks with hierarchy"""
        return LayoutTemplate(
            id="text_heavy_v1",
            name="Text Heavy",
            description="Multiple text blocks for information-dense content",
            aspect_ratios=["1x1", "16x9"],
            channels=["linkedin", "fb"],
            slots=[
                LayoutSlot(
                    id="background",
                    type=SlotType.IMAGE,
                    layer=0,
                    area="full",
                    fit="cover",
                    filters=["brightness(0.4)", "blur(2px)"]
                ),
                LayoutSlot(
                    id="headline",
                    type=SlotType.TEXT,
                    layer=2,
                    area=SlotArea(x=1, y=3, w=10, h=2),
                    font_size="72px",
                    font_weight=800,
                    color="#FFFFFF",
                    align="center"
                ),
                LayoutSlot(
                    id="subhead",
                    type=SlotType.TEXT,
                    layer=2,
                    area=SlotArea(x=1, y=6, w=10, h=2),
                    font_size="36px",
                    color="#FFFFFF",
                    align="center"
                ),
                LayoutSlot(
                    id="body",
                    type=SlotType.TEXT,
                    layer=2,
                    area=SlotArea(x=2, y=8, w=8, h=2),
                    font_size="24px",
                    color="#FFFFFF",
                    align="center"
                ),
                LayoutSlot(
                    id="cta",
                    type=SlotType.BUTTON,
                    layer=3,
                    area=SlotArea(x=3, y=10, w=6, h=1),
                    background="primary",
                    color="#FFFFFF",
                    border_radius=12,
                    font_size="36px",
                    font_weight=700
                ),
                LayoutSlot(
                    id="logo",
                    type=SlotType.IMAGE,
                    layer=4,
                    area=SlotArea(x=0, y=0, w=2, h=2),
                    fit="contain"
                )
            ],
            rules=LayoutRules(
                text_contrast_min=4.5,
                logo_clearance="1x"
            )
        )


# Singleton instance
layout_engine = LayoutEngine()


# Convenience functions
def get_layout_for_plan(plan: DesignPlan) -> LayoutTemplate:
    """Quick function to get optimal layout for a plan"""
    return layout_engine.select_optimal_layout(plan)


def list_available_layouts(aspect_ratio: str = None, channel: str = None) -> List[Dict[str, Any]]:
    """List all available layouts"""
    return layout_engine.list_templates(aspect_ratio, channel)
