"""
Prompt Builder v2
Generates prompts with camera/lighting cues, composition hints, and negative space for logo placement
"""
from typing import Dict, Any, Optional
from uuid import UUID

from app.core.brand_brain import BrandTokens, BrandPolicies
from app.infra.logging import get_logger

logger = get_logger(__name__)


class PromptBuilderV2:
    """
    Advanced prompt builder that ensures negative space for logo overlays
    """

    def build_background_prompt(
        self,
        user_request: str,
        tokens: BrandTokens,
        aspect_ratio: str = "1:1",
        logo_position: str = "TR"
    ) -> str:
        """
        Build prompt for AI background generation with negative space

        Args:
            user_request: What user wants to create
            tokens: Brand design tokens
            aspect_ratio: Image aspect ratio (1:1, 4:5, 9:16, 191:100)
            logo_position: Where logo will be placed (TL, TR, BR, BL)

        Returns:
            Optimized prompt for DALL-E 3
        """
        logger.info(f"Building prompt v2: request='{user_request}', aspect={aspect_ratio}, logo_pos={logo_position}")

        # 1. Core subject - USER REQUEST IS PRIMARY
        prompt_parts = [f"Create: {user_request}"]

        # 2. Camera and lighting cues for professional look
        camera_cues = self._get_camera_cues(user_request)
        if camera_cues:
            prompt_parts.append(camera_cues)

        # 3. Composition with negative space for logo
        composition = self._get_composition_with_negative_space(logo_position, aspect_ratio)
        prompt_parts.append(composition)

        # 4. Color palette from brand tokens
        color_guidance = self._get_color_guidance(tokens)
        if color_guidance:
            prompt_parts.append(color_guidance)

        # 5. Lighting and quality
        prompt_parts.append("Professional studio lighting, sharp focus, high resolution")

        # 6. CRITICAL negative prompts - explicit and strong
        negative_prompts = [
            "NO TEXT of any kind",
            "NO LOGOS or watermarks",
            "NO UI elements",
            "NO words or letters anywhere",
            "NO overlaid graphics"
        ]
        prompt_parts.append(f"CRITICAL REQUIREMENTS: {', '.join(negative_prompts)}")

        # 7. Final requirement
        prompt_parts.append("Clean professional background image only, ready for brand overlay")

        # Join with periods
        final_prompt = ". ".join(prompt_parts) + "."

        # Ensure not too long (DALL-E 3 max ~1000 chars, but shorter is better)
        if len(final_prompt) > 600:
            # Trim to essentials
            final_prompt = (
                f"Create: {user_request}. "
                f"{composition}. "
                f"{color_guidance if color_guidance else 'Brand colors'}. "
                f"Professional photography, high resolution. "
                f"CRITICAL: NO TEXT, NO LOGOS, NO WORDS anywhere in image. Clean background only."
            )

        logger.info(f"Generated prompt ({len(final_prompt)} chars)")
        logger.debug(f"Prompt: {final_prompt}")

        return final_prompt

    def _get_camera_cues(self, subject: str) -> str:
        """
        Get camera/lens cues based on subject matter

        Args:
            subject: Subject description

        Returns:
            Camera cues string or empty
        """
        subject_lower = subject.lower()

        # Product/object photography
        if any(word in subject_lower for word in ['product', 'device', 'phone', 'laptop', 'gadget']):
            return "Shot with 85mm lens, f/2.8 aperture, shallow depth of field"

        # Architecture/interior
        if any(word in subject_lower for word in ['interior', 'room', 'office', 'building', 'architecture']):
            return "Wide-angle 24mm lens, f/8 aperture, deep focus"

        # People/lifestyle
        if any(word in subject_lower for word in ['person', 'people', 'team', 'portrait', 'lifestyle']):
            return "50mm portrait lens, f/1.8 aperture, natural lighting"

        # Landscape/outdoor
        if any(word in subject_lower for word in ['landscape', 'outdoor', 'nature', 'mountain', 'beach']):
            return "Wide-angle 16-35mm lens, f/11 aperture, golden hour lighting"

        # Food
        if any(word in subject_lower for word in ['food', 'meal', 'dish', 'plate', 'culinary']):
            return "Macro 100mm lens, f/2.8 aperture, natural window light"

        # Default: professional photography
        return "Professional camera, optimal aperture, balanced exposure"

    def _get_composition_with_negative_space(
        self,
        logo_position: str,
        aspect_ratio: str
    ) -> str:
        """
        Get composition rules that ensure negative space for logo

        Args:
            logo_position: TL, TR, BR, BL
            aspect_ratio: Aspect ratio string

        Returns:
            Composition guidance
        """
        # Map position to negative space requirement
        position_map = {
            "TL": "generous empty space in top-left corner",
            "TR": "generous empty space in top-right corner",
            "BR": "generous empty space in bottom-right corner",
            "BL": "generous empty space in bottom-left corner"
        }

        negative_space = position_map.get(logo_position, "generous empty space in corners")

        # Base composition rules
        rules = [
            "rule of thirds composition",
            negative_space,
            "uncluttered background"
        ]

        # Adjust for aspect ratio
        if aspect_ratio in ["9:16", "4:5"]:  # Vertical
            rules.append("vertical orientation")
        elif aspect_ratio == "191:100":  # Wide banner
            rules.append("wide horizontal format")

        return f"Composition: {', '.join(rules)}"

    def _get_color_guidance(self, tokens: BrandTokens) -> str:
        """
        Get color guidance from brand tokens

        Args:
            tokens: Brand design tokens

        Returns:
            Color guidance string
        """
        colors = tokens.color

        # Primary color dominance
        primary = colors.get('primary', '')
        secondary = colors.get('secondary', '')

        if primary:
            if secondary:
                return f"Color palette: dominant {primary} with {secondary} accents"
            else:
                return f"Color palette: {primary} dominant colors"

        return ""

    def build_regeneration_prompt(
        self,
        original_prompt: str,
        issue: str,
        tokens: BrandTokens
    ) -> str:
        """
        Build prompt for regeneration when validation fails

        Args:
            original_prompt: Original prompt that failed
            issue: What went wrong (e.g., "text detected", "wrong colors")
            tokens: Brand tokens

        Returns:
            Modified prompt addressing the issue
        """
        logger.info(f"Building regeneration prompt for issue: {issue}")

        # Extract core request from original
        if "Create:" in original_prompt:
            core_request = original_prompt.split("Create:")[1].split(".")[0].strip()
        else:
            core_request = original_prompt.split(".")[0].strip()

        # Build new prompt with stronger constraints
        if "text" in issue.lower() or "ocr" in issue.lower():
            # Text was detected - be VERY explicit
            return (
                f"Create: {core_request}. "
                f"Composition: clean, uncluttered, generous negative space. "
                f"ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO TYPOGRAPHY of any kind visible. "
                f"NO overlaid graphics, NO watermarks, NO logos. "
                f"Pure photographic background only. Professional quality."
            )

        elif "color" in issue.lower():
            # Color mismatch - emphasize brand colors
            primary = tokens.color.get('primary', '')
            return (
                f"Create: {core_request}. "
                f"IMPORTANT: Use {primary} as the dominant color throughout. "
                f"Color palette must match brand guidelines. "
                f"NO TEXT, NO LOGOS. Clean professional background."
            )

        else:
            # Generic regeneration
            return (
                f"Create: {core_request}. "
                f"Professional photography, clean composition. "
                f"NO TEXT, NO LOGOS, NO WORDS anywhere. "
                f"High quality background image only."
            )


# Singleton instance
prompt_builder_v2 = PromptBuilderV2()
