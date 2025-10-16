"""
Brand Intelligence System
Learns and applies brand visual logic, layouts, and patterns like a human designer
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from openai import OpenAI
import json
from datetime import datetime

from app.infra.config import settings
from app.infra.db import get_db
from app.infra.logging import get_logger

logger = get_logger(__name__)


class BrandIntelligence:
    """
    Acts like a designer: learns brand patterns and applies them consistently
    """

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def save_brand_intelligence(
        self,
        org_id: UUID,
        brand_name: str,
        guidelines: Dict[str, Any],
        examples_analysis: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save comprehensive brand intelligence to database

        Args:
            org_id: Organization UUID
            brand_name: Brand name
            guidelines: Extracted brand guidelines from PDF
            examples_analysis: Analysis from design examples
        """
        try:
            db = get_db()

            # Combine all intelligence
            brand_intelligence = {
                "brand_name": brand_name,
                "visual_identity": guidelines.get("visual_identity", {}),
                "imagery_guidelines": guidelines.get("imagery_guidelines", {}),
                "layout_system": guidelines.get("layout_system", {}),
                "brand_messaging": guidelines.get("brand_messaging", {}),
                "design_patterns": guidelines.get("design_patterns", {}),
                "usage_guidelines": guidelines.get("usage_guidelines", {}),
                "design_principles": guidelines.get("design_principles", {}),
                "learned_from_examples": examples_analysis or {},
                "last_updated": datetime.now().isoformat()
            }

            # Upsert to brand_guidelines table
            db.execute("""
                INSERT INTO brand_guidelines (org_id, guidelines, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
                ON CONFLICT (org_id)
                DO UPDATE SET
                    guidelines = EXCLUDED.guidelines,
                    updated_at = NOW()
            """, (str(org_id), json.dumps(brand_intelligence)))

            logger.info(f"Saved brand intelligence for org {org_id}")

        except Exception as e:
            logger.error(f"Error saving brand intelligence: {str(e)}")
            raise

    def get_brand_intelligence(self, org_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Retrieve brand intelligence for an organization

        Returns:
            Brand intelligence dict or None
        """
        try:
            db = get_db()
            result = db.fetch_one(
                "SELECT guidelines, updated_at FROM brand_guidelines WHERE org_id = %s",
                (str(org_id),)
            )

            if result and result.get("guidelines"):
                guidelines = result["guidelines"]
                if isinstance(guidelines, str):
                    guidelines = json.loads(guidelines)

                logger.info(f"Retrieved brand intelligence for org {org_id}")
                return guidelines

            return None

        except Exception as e:
            logger.error(f"Error retrieving brand intelligence: {str(e)}")
            return None

    def build_designer_prompt(
        self,
        user_request: str,
        brand_intelligence: Dict[str, Any],
        aspect_ratio: str = "square"
    ) -> str:
        """
        Build a prompt like a designer would think - using brand's visual logic

        Args:
            user_request: What the user wants
            brand_intelligence: Learned brand patterns
            aspect_ratio: Image dimensions

        Returns:
            Comprehensive prompt that follows brand patterns
        """
        logger.info("Building designer-style prompt from brand intelligence")

        # Extract key brand elements
        visual_id = brand_intelligence.get("visual_identity", {})
        imagery = brand_intelligence.get("imagery_guidelines", {})
        layout = brand_intelligence.get("layout_system", {})
        messaging = brand_intelligence.get("brand_messaging", {})
        patterns = brand_intelligence.get("design_patterns", {})
        examples = brand_intelligence.get("learned_from_examples", {})

        # Build prompt sections
        prompt_parts = []

        # 1. USER REQUEST IS PRIMARY - This is what they want!
        # Make it CRYSTAL CLEAR to DALL-E what to generate
        prompt_parts.append(f"Create: {user_request}")

        # 2. Photography/Imagery style
        photo_style = imagery.get("photography_style", "")
        if photo_style:
            prompt_parts.append(f"Photography style: {photo_style}")

        subject_matter = imagery.get("subject_matter", "")
        if subject_matter:
            prompt_parts.append(f"Subject matter: {subject_matter}")

        # 3. Color palette
        colors = visual_id.get("colors", {})
        color_list = []
        if colors.get("primary"):
            color_list.append(colors["primary"].get("hex", ""))
        if colors.get("secondary"):
            color_list.append(colors["secondary"].get("hex", ""))
        if colors.get("accent") and isinstance(colors["accent"], list):
            for accent in colors["accent"][:2]:
                if isinstance(accent, dict):
                    color_list.append(accent.get("hex", ""))

        if color_list:
            prompt_parts.append(f"Color palette: {', '.join([c for c in color_list if c])}")

        # 4. Composition rules
        comp_rules = imagery.get("composition_rules", [])
        if comp_rules:
            prompt_parts.append(f"Composition: {', '.join(comp_rules[:3])}")

        # 5. Layout principles
        grid = layout.get("grid", "")
        spacing = layout.get("spacing", {})
        if grid:
            prompt_parts.append(f"Layout: {grid}")
        if spacing:
            spacing_desc = ", ".join([f"{k}: {v}" for k, v in spacing.items() if v])
            if spacing_desc:
                prompt_parts.append(f"Spacing: {spacing_desc}")

        # 6. Brand personality
        personality = messaging.get("personality", [])
        if personality:
            prompt_parts.append(f"Brand personality: {', '.join(personality[:3])}")

        voice = messaging.get("voice", "")
        if voice:
            prompt_parts.append(f"Brand voice: {voice}")

        # 7. Visual elements and patterns
        visual_elements = patterns.get("visual_elements", [])
        if visual_elements:
            prompt_parts.append(f"Visual elements: {', '.join(visual_elements[:3])}")

        graphic_devices = patterns.get("graphic_devices", [])
        if graphic_devices:
            prompt_parts.append(f"Graphic devices: {', '.join(graphic_devices[:2])}")

        # 8. Learned patterns from examples
        if examples:
            synthesis = examples.get("synthesis", {})
            if synthesis:
                visual_dna = synthesis.get("visual_style_dna", {})
                if visual_dna:
                    keywords = visual_dna.get("keywords", [])
                    if keywords:
                        prompt_parts.append(f"Visual style: {', '.join(keywords[:4])}")

                color_dna = synthesis.get("color_dna", {})
                if color_dna:
                    palette = color_dna.get("palette", [])
                    if palette:
                        prompt_parts.append(f"Example colors: {', '.join(palette[:3])}")

        # 9. Usage guidelines (dos)
        usage = brand_intelligence.get("usage_guidelines", {})
        dos = usage.get("dos", [])
        if dos:
            prompt_parts.append(f"Best practices: {', '.join(dos[:2])}")

        # 10. Quality and technical requirements
        prompt_parts.extend([
            "Professional photography, high resolution, sharp focus"
        ])

        # 11. CRITICAL: No text or logos in generated image
        # DALL-E needs this EXPLICIT
        prompt_parts.append("IMPORTANT: Generate ONLY the background image with NO TEXT, NO LOGOS, NO WORDS, NO LETTERS visible anywhere in the image. Clean background only.")

        # Join all parts - USER REQUEST FIRST, then brand context
        final_prompt = ". ".join([p for p in prompt_parts if p]) + "."

        # Ensure user request is prominent
        if len(final_prompt) > 500:
            # Trim middle parts if too long, keep user request and critical parts
            logger.warning("Prompt too long, prioritizing user request")
            final_prompt = (
                f"Create: {user_request}. "
                f"{color_list[0] if color_list else ''} color palette. "
                f"{', '.join(personality[:2]) if personality else ''} style. "
                f"Professional photography, high resolution. "
                f"IMPORTANT: NO TEXT, NO LOGOS, NO WORDS visible in image. Clean background only."
            )

        logger.info(f"Generated designer prompt: {len(final_prompt)} chars")
        logger.debug(f"Prompt: {final_prompt}")

        return final_prompt

    def merge_brand_data(
        self,
        pdf_guidelines: Optional[Dict[str, Any]] = None,
        examples_analysis: Optional[Dict[str, Any]] = None,
        brand_name: str = "Brand"
    ) -> Dict[str, Any]:
        """
        Intelligently merge data from PDF and examples

        Args:
            pdf_guidelines: Guidelines from brand book PDF
            examples_analysis: Analysis from design examples
            brand_name: Brand name

        Returns:
            Merged brand intelligence
        """
        merged = {
            "brand_name": brand_name,
            "visual_identity": {},
            "imagery_guidelines": {},
            "layout_system": {},
            "brand_messaging": {},
            "design_patterns": {},
            "usage_guidelines": {},
            "design_principles": {},
            "learned_from_examples": {}
        }

        # Merge PDF guidelines
        if pdf_guidelines:
            for key in merged.keys():
                if key in pdf_guidelines and pdf_guidelines[key]:
                    merged[key] = pdf_guidelines[key]

        # Enhance with examples analysis
        if examples_analysis:
            synthesis = examples_analysis.get("synthesis", {})
            guidelines_from_ex = examples_analysis.get("guidelines", {})

            # Add learned patterns
            merged["learned_from_examples"] = {
                "synthesis": synthesis,
                "guidelines": guidelines_from_ex,
                "confidence_score": examples_analysis.get("confidence_score", 0)
            }

            # Enhance visual identity with learned colors
            if synthesis.get("color_dna"):
                color_palette = synthesis["color_dna"].get("palette", [])
                if color_palette and not merged["visual_identity"].get("colors"):
                    # Create colors from learned palette
                    merged["visual_identity"]["colors"] = {
                        "primary": {"hex": color_palette[0], "name": "Primary", "usage": "Learned from examples"},
                        "secondary": {"hex": color_palette[1] if len(color_palette) > 1 else "", "name": "Secondary"},
                        "accent": [{"hex": c, "name": f"Accent {i+1}"} for i, c in enumerate(color_palette[2:5])]
                    }

            # Enhance imagery guidelines
            if synthesis.get("visual_style_dna"):
                keywords = synthesis["visual_style_dna"].get("keywords", [])
                if keywords:
                    if not merged["imagery_guidelines"].get("photography_style"):
                        merged["imagery_guidelines"]["photography_style"] = ", ".join(keywords)

        return merged


# Singleton instance
brand_intelligence = BrandIntelligence()
