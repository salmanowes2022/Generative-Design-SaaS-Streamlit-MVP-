"""
Prompt Builder
Constructs optimized prompts for image generation from brand kits
Enhanced with deep brand analysis for true brand consistency
"""
from typing import Optional, Dict, Any
from uuid import UUID
from app.core.schemas import BrandKit, AspectRatio
from app.infra.logging import get_logger

logger = get_logger(__name__)


class PromptBuilder:
    """Builds AI prompts from brand kit data with deep brand understanding"""

    def build_prompt(
        self,
        user_prompt: str,
        brand_kit: BrandKit,
        aspect_ratio: Optional[AspectRatio] = None,
        brand_analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build a complete prompt for image generation

        Args:
            user_prompt: User's input prompt
            brand_kit: Brand kit with style and color info
            aspect_ratio: Desired aspect ratio (optional)
            brand_analysis: Deep brand analysis from past examples (optional)

        Returns:
            Complete optimized prompt that matches brand DNA
        """
        # If we have brand analysis, use the AI-generated brand-aware prompt
        if brand_analysis and brand_analysis.get("has_examples") and brand_analysis.get("optimized_prompt"):
            logger.info("Using AI-generated brand-aware prompt from deep analysis")
            return brand_analysis["optimized_prompt"]

        # Fall back to template-based prompt building
        logger.info("No brand analysis available, using template-based prompt")

        # Extract learned patterns from brand analysis if available
        synthesis = brand_analysis.get("analysis", {}).get("synthesis", {}) if brand_analysis else {}
        guidelines = brand_analysis.get("analysis", {}).get("guidelines", {}) if brand_analysis else {}

        # Get style keywords from analysis or brand kit
        style_keywords = []
        if synthesis.get("visual_style_dna"):
            style_keywords = synthesis["visual_style_dna"].get("keywords", [])
        if not style_keywords:
            style_descriptors = brand_kit.style.descriptors or []
            style_keywords = style_descriptors if style_descriptors else ["clean", "minimalist", "professional"]

        style_text = ", ".join(style_keywords[:5])

        # Get color guidance from analysis or brand kit
        color_guidance = ""
        if synthesis.get("color_dna", {}).get("palette"):
            colors = synthesis["color_dna"]["palette"][:3]
            color_guidance = f"Color palette: {', '.join(colors)}. "
        else:
            colors = []
            if brand_kit.colors.primary:
                colors.append(brand_kit.colors.primary)
            if brand_kit.colors.secondary:
                colors.append(brand_kit.colors.secondary)
            if brand_kit.colors.accent:
                colors.append(brand_kit.colors.accent)
            if colors:
                color_guidance = f"Color palette influenced by {', '.join(colors)}. "

        # Get background style from guidelines
        background_style = guidelines.get("background_style", "")
        if background_style:
            background_style = f"Background: {background_style}. "

        # Get composition rules
        composition_rules = guidelines.get("composition_rules", [])
        composition_text = ""
        if composition_rules:
            composition_text = f"Composition: {', '.join(composition_rules[:3])}. "

        # Build aspect ratio context
        aspect_context = ""
        if aspect_ratio:
            if aspect_ratio == AspectRatio.SQUARE:
                aspect_context = "Square 1:1 format, balanced composition. "
            elif aspect_ratio == AspectRatio.PORTRAIT:
                aspect_context = "Vertical 4:5 portrait format. "
            elif aspect_ratio == AspectRatio.STORY:
                aspect_context = "Vertical 9:16 story format, mobile-optimized. "

        # Get must-avoid items from guidelines
        must_avoid = guidelines.get("must_avoid", [])
        if not must_avoid:
            must_avoid = [
                "cluttered composition", "cartoonish style", "heavy textures",
                "chaotic backgrounds", "oversaturated colors", "multiple focal points"
            ]
        negatives = f"Avoid: {', '.join(must_avoid[:5])}. "

        # Brand signature if available
        brand_signature = synthesis.get("brand_signature", "")
        if brand_signature:
            brand_signature = f"Brand aesthetic: {brand_signature}. "

        # Construct final prompt
        final_prompt = (
            f"Subject: {user_prompt}. "
            f"Style: {style_text}. "
            f"{aspect_context}"
            f"{background_style}"
            f"{composition_text}"
            f"{color_guidance}"
            f"{brand_signature}"
            f"Professional photography quality, studio lighting, crisp focus, high resolution. "
            f"{negatives}"
            f"CRITICAL: No text, no logos, no watermarks, no typography in the image. "
            f"Clean background image ready for brand overlay."
        )

        logger.info(f"Built brand-aware prompt: {final_prompt[:120]}...")

        return final_prompt
    
    def build_variation_prompt(
        self,
        base_prompt: str,
        variation_style: str = "subtle"
    ) -> str:
        """
        Build a variation of an existing prompt
        
        Args:
            base_prompt: Original prompt
            variation_style: Type of variation (subtle, moderate, dramatic)
        
        Returns:
            Modified prompt for variation
        """
        variation_modifiers = {
            "subtle": "with slight composition changes",
            "moderate": "with different angle and lighting",
            "dramatic": "with completely different composition and mood"
        }
        
        modifier = variation_modifiers.get(variation_style, variation_modifiers["subtle"])
        
        return f"{base_prompt} Generate a variation {modifier}."
    
    def optimize_for_dalle3(self, prompt: str) -> str:
        """
        Optimize prompt specifically for DALL-E 3
        
        Args:
            prompt: Base prompt
        
        Returns:
            DALL-E 3 optimized prompt
        """
        # DALL-E 3 works best with detailed, natural language
        # It's less sensitive to negative prompts
        
        # Ensure prompt is descriptive enough
        if len(prompt) < 50:
            prompt = f"Create a high-quality, professional image: {prompt}"
        
        return prompt
    
    def add_moderation_safety(self, prompt: str) -> str:
        """
        Add safety guidelines to prompt to pass OpenAI moderation
        
        Args:
            prompt: Base prompt
        
        Returns:
            Prompt with safety guidelines
        """
        safety_suffix = (
            " Ensure the image is appropriate for all audiences, "
            "professional, and suitable for commercial marketing use."
        )
        
        return prompt + safety_suffix


# Global prompt builder instance
prompt_builder = PromptBuilder()