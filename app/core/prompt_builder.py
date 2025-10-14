"""
Prompt Builder
Constructs optimized prompts for image generation from brand kits
"""
from typing import Optional
from app.core.schemas import BrandKit, AspectRatio
from app.infra.logging import get_logger

logger = get_logger(__name__)


class PromptBuilder:
    """Builds AI prompts from brand kit data"""
    
    def build_prompt(
        self,
        user_prompt: str,
        brand_kit: BrandKit,
        aspect_ratio: Optional[AspectRatio] = None
    ) -> str:
        """
        Build a complete prompt for image generation
        
        Args:
            user_prompt: User's input prompt
            brand_kit: Brand kit with style and color info
            aspect_ratio: Desired aspect ratio (optional)
        
        Returns:
            Complete optimized prompt
        """
        # Extract style descriptors
        style_descriptors = brand_kit.style.descriptors or []
        style_text = ", ".join(style_descriptors) if style_descriptors else "clean, minimalist, professional"
        
        # Extract color palette
        colors = []
        if brand_kit.colors.primary:
            colors.append(brand_kit.colors.primary)
        if brand_kit.colors.secondary:
            colors.append(brand_kit.colors.secondary)
        if brand_kit.colors.accent:
            colors.append(brand_kit.colors.accent)
        
        palette_hint = ""
        if colors:
            palette_hint = f"Use a color palette influenced by {', '.join(colors)}. "
        
        # Build aspect ratio context
        aspect_context = ""
        if aspect_ratio:
            if aspect_ratio == AspectRatio.SQUARE:
                aspect_context = "Square composition, centered subject. "
            elif aspect_ratio == AspectRatio.PORTRAIT:
                aspect_context = "Vertical portrait composition, tall format. "
            elif aspect_ratio == AspectRatio.STORY:
                aspect_context = "Vertical story format, mobile-optimized layout. "
        
        # Negative prompts (things to avoid)
        negatives = (
            "Avoid: cluttered composition, cartoonish style, heavy grunge textures, "
            "chaotic backgrounds, oversaturated colors, multiple focal points."
        )
        
        # Construct final prompt
        final_prompt = (
            f"Photorealistic marketing image, {style_text}. "
            f"{aspect_context}"
            f"Subject: {user_prompt}. "
            f"{palette_hint}"
            f"Studio-quality lighting, crisp focus, professional photography. "
            f"{negatives} "
            f"CRITICAL: Do not include any logos, brand text, watermarks, or typography. "
            f"The image should be clean and ready for brand overlay."
        )
        
        logger.info(f"Built prompt: {final_prompt[:100]}...")
        
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