"""
Planner Agent v2
Converts chat messages to strict JSON design plans with constraints
Acts as Brand Brain's planning layer before rendering
"""
from typing import Dict, Any, Optional, List
import json
import openai
from uuid import UUID
from app.core.brand_brain import BrandTokens, BrandPolicies, brand_brain
from app.infra.config import settings
from app.infra.logging import get_logger

logger = get_logger(__name__)


class PlannerV2:
    """
    Brand-aware planner that converts user intent to strict JSON plans
    Enforces brand constraints: headline length, CTA whitelist, policies
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize planner

        Args:
            api_key: OpenAI API key (or uses environment variable)
        """
        # Use provided API key, or fall back to settings
        openai.api_key = api_key or settings.OPENAI_API_KEY
        self.model = "gpt-4-turbo-preview"  # Use latest GPT-4 with JSON mode

    def chat_to_plan(
        self,
        user_message: str,
        tokens: BrandTokens,
        policies: Optional[BrandPolicies] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert user message to strict JSON design plan

        Args:
            user_message: User's natural language request
            tokens: Brand design tokens
            policies: Brand policies (optional)
            context: Additional context (channel, previous messages, etc.)

        Returns:
            {
                "success": bool,
                "plan": {
                    "headline": str,           # ≤7 words
                    "subhead": str,            # ≤16 words
                    "cta_text": str,           # Must be in whitelist
                    "visual_concept": str,     # What to generate
                    "channel": str,            # ig, fb, linkedin, etc.
                    "aspect_ratio": str,       # 1x1, 4x5, 9x16
                    "palette_mode": str,       # primary, secondary, accent, mono
                    "background_style": str,   # Detailed prompt for AI
                    "logo_position": str       # top-right, bottom-left, etc.
                },
                "reasoning": str,
                "warnings": List[str]
            }
        """
        try:
            logger.info(f"Planning design from message: '{user_message[:100]}'")

            # Build system prompt with brand context
            system_prompt = self._build_system_prompt(tokens, policies)

            # Build user prompt with context
            user_prompt = self._build_user_prompt(user_message, tokens, context)

            # Call GPT-4 with JSON mode
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1500
            )

            # Parse response
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            # Validate plan
            plan = result.get("plan", {})
            warnings = self._validate_plan(plan, tokens, policies)

            logger.info(f"Plan created: {json.dumps(plan, indent=2)}")

            return {
                "success": True,
                "plan": plan,
                "reasoning": result.get("reasoning", ""),
                "warnings": warnings
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            return {
                "success": False,
                "error": "Failed to parse AI response",
                "plan": {},
                "reasoning": "",
                "warnings": ["AI returned invalid JSON"]
            }

        except Exception as e:
            logger.error(f"Planning error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "plan": {},
                "reasoning": "",
                "warnings": [f"Planning failed: {str(e)}"]
            }

    def _build_system_prompt(self, tokens: BrandTokens, policies: Optional[BrandPolicies]) -> str:
        """Build system prompt with brand context"""

        # Extract brand constraints
        cta_whitelist = tokens.cta_whitelist or ["Get Started", "Learn More", "Try Free", "Shop Now"]
        allowed_positions = tokens.logo.get("allowed_positions", ["top-right", "bottom-right"])

        voice_traits = []
        forbidden_terms = []
        if policies:
            voice_traits = policies.voice or []
            forbidden_terms = policies.forbid or []

        system_prompt = f"""You are a Brand Brain planner. Convert user messages into strict JSON design plans.

BRAND CONSTRAINTS:
- Headline: Maximum 7 words, punchy and clear
- Subhead: Maximum 16 words, supportive detail
- CTA Text: MUST be from whitelist: {json.dumps(cta_whitelist)}
- Logo Position: Choose from: {json.dumps(allowed_positions)}
- Palette Modes: primary, secondary, accent, or mono

BRAND VOICE:
{json.dumps(voice_traits) if voice_traits else "Professional, clear, engaging"}

FORBIDDEN TERMS:
{json.dumps(forbidden_terms) if forbidden_terms else "None specified"}

CHANNELS & ASPECT RATIOS:
- Instagram: 1x1 (feed), 4x5 (portrait), 9x16 (story)
- Facebook: 1x1 (post), 16x9 (link)
- LinkedIn: 1x1 (post), 4x5 (vertical)

OUTPUT FORMAT (strict JSON):
{{
    "plan": {{
        "headline": "Max 7 words headline",
        "subhead": "Max 16 words supporting text that adds context",
        "cta_text": "Learn More",
        "visual_concept": "Detailed description of the visual",
        "channel": "ig",
        "aspect_ratio": "1x1",
        "palette_mode": "primary",
        "background_style": "Professional product photography, clean studio background, soft lighting, minimalist composition",
        "logo_position": "top-right"
    }},
    "reasoning": "Brief explanation of design choices"
}}

CRITICAL:
- Headline ≤7 words
- Subhead ≤16 words
- CTA from whitelist only
- Return ONLY valid JSON
- No markdown, no code blocks, pure JSON"""

        return system_prompt

    def _build_user_prompt(
        self,
        user_message: str,
        tokens: BrandTokens,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build user prompt with context"""

        channel = context.get("channel", "ig") if context else "ig"
        aspect_ratio = context.get("aspect_ratio", "1x1") if context else "1x1"

        user_prompt = f"""USER REQUEST: {user_message}

TARGET CHANNEL: {channel}
ASPECT RATIO: {aspect_ratio}

Create a design plan following brand constraints. Remember:
- Headline ≤7 words
- Subhead ≤16 words
- CTA from whitelist
- Background should be AI-generatable (no text/logos in background)
- Logo will be added separately in {tokens.logo.get("allowed_positions", ["top-right"])[0]}

Return strict JSON only."""

        return user_prompt

    def _validate_plan(
        self,
        plan: Dict[str, Any],
        tokens: BrandTokens,
        policies: Optional[BrandPolicies]
    ) -> List[str]:
        """
        Validate plan against brand constraints

        Args:
            plan: Design plan
            tokens: Brand tokens
            policies: Brand policies

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Validate headline length
        headline = plan.get("headline", "")
        headline_words = len(headline.split())
        if headline_words > 7:
            warnings.append(f"Headline too long: {headline_words} words (max 7)")

        # Validate subhead length
        subhead = plan.get("subhead", "")
        subhead_words = len(subhead.split())
        if subhead_words > 16:
            warnings.append(f"Subhead too long: {subhead_words} words (max 16)")

        # Validate CTA whitelist
        cta_text = plan.get("cta_text", "")
        cta_whitelist = tokens.cta_whitelist or []
        if cta_whitelist and cta_text not in cta_whitelist:
            warnings.append(f"CTA '{cta_text}' not in whitelist. Allowed: {cta_whitelist}")

        # Validate logo position
        logo_position = plan.get("logo_position", "")
        allowed_positions = tokens.logo.get("allowed_positions", [])
        if allowed_positions and logo_position not in allowed_positions:
            warnings.append(f"Logo position '{logo_position}' not allowed. Use: {allowed_positions}")

        # Validate palette mode
        palette_mode = plan.get("palette_mode", "")
        valid_modes = ["primary", "secondary", "accent", "mono"]
        if palette_mode not in valid_modes:
            warnings.append(f"Invalid palette mode '{palette_mode}'. Use: {valid_modes}")

        # Check forbidden terms in policies
        if policies and policies.forbid:
            text_to_check = f"{headline} {subhead} {cta_text}".lower()
            for term in policies.forbid:
                if term.lower() in text_to_check:
                    warnings.append(f"Contains forbidden term: '{term}'")

        # Validate required fields
        required_fields = ["headline", "visual_concept", "channel", "aspect_ratio", "background_style"]
        for field in required_fields:
            if not plan.get(field):
                warnings.append(f"Missing required field: {field}")

        return warnings

    def refine_plan(
        self,
        plan: Dict[str, Any],
        user_feedback: str,
        tokens: BrandTokens,
        policies: Optional[BrandPolicies] = None
    ) -> Dict[str, Any]:
        """
        Refine existing plan based on user feedback

        Args:
            plan: Current design plan
            user_feedback: User's refinement request
            tokens: Brand tokens
            policies: Brand policies

        Returns:
            Updated plan with same format as chat_to_plan
        """
        try:
            logger.info(f"Refining plan based on feedback: '{user_feedback[:100]}'")

            system_prompt = self._build_system_prompt(tokens, policies)

            user_prompt = f"""CURRENT PLAN:
{json.dumps(plan, indent=2)}

USER FEEDBACK: {user_feedback}

Refine the plan based on feedback while maintaining brand constraints.
Return updated plan in the same JSON format."""

            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1500
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            refined_plan = result.get("plan", plan)
            warnings = self._validate_plan(refined_plan, tokens, policies)

            logger.info("Plan refined successfully")

            return {
                "success": True,
                "plan": refined_plan,
                "reasoning": result.get("reasoning", ""),
                "warnings": warnings
            }

        except Exception as e:
            logger.error(f"Plan refinement error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "plan": plan,  # Return original plan on error
                "reasoning": "",
                "warnings": [f"Refinement failed: {str(e)}"]
            }

    def batch_plan(
        self,
        user_message: str,
        channels: List[str],
        tokens: BrandTokens,
        policies: Optional[BrandPolicies] = None
    ) -> Dict[str, Any]:
        """
        Create plans for multiple channels at once

        Args:
            user_message: User request
            channels: List of channels (e.g., ["ig", "fb", "linkedin"])
            tokens: Brand tokens
            policies: Brand policies

        Returns:
            {
                "success": bool,
                "plans": {
                    "ig": {...},
                    "fb": {...},
                    "linkedin": {...}
                }
            }
        """
        try:
            logger.info(f"Creating batch plans for channels: {channels}")

            plans = {}

            for channel in channels:
                # Determine default aspect ratio for channel
                aspect_ratio = self._get_default_aspect_ratio(channel)

                # Create plan for this channel
                result = self.chat_to_plan(
                    user_message,
                    tokens,
                    policies,
                    context={"channel": channel, "aspect_ratio": aspect_ratio}
                )

                if result["success"]:
                    plans[channel] = result["plan"]
                else:
                    logger.warning(f"Failed to create plan for {channel}: {result.get('error')}")
                    plans[channel] = None

            return {
                "success": True,
                "plans": plans
            }

        except Exception as e:
            logger.error(f"Batch planning error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "plans": {}
            }

    def _get_default_aspect_ratio(self, channel: str) -> str:
        """Get default aspect ratio for channel"""
        defaults = {
            "ig": "1x1",
            "fb": "1x1",
            "linkedin": "1x1",
            "twitter": "16x9",
            "pinterest": "2x3"
        }
        return defaults.get(channel, "1x1")


# Global planner instance
planner_v2 = PlannerV2()
