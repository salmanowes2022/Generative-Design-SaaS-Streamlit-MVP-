"""
Design Agent - The AI Brain

Works with YOUR existing system (UUID-based with organizations)
to understand context, plan designs, and explain decisions.
"""

from typing import Dict, Any, Optional, List
import json
from uuid import UUID
from openai import OpenAI

from app.infra.config import settings
from app.infra.logging import get_logger
from app.core.brand_memory import brand_memory
from app.core.brand_analyzer import brand_analyzer
from app.core.brandbook_analyzer import brandbook_analyzer
from app.core.brandkit import BrandKitManager
from app.core.schemas import BrandKit, JobCreate, JobParams, AspectRatio, CompositionPreset
from app.core.gen_openai import OpenAIImageGenerator
from app.core.compose import CompositionEngine
from app.core.validate import ValidationEngine

logger = get_logger(__name__)


class DesignAgent:
    """
    The AI Design Agent that thinks like a designer

    This agent:
    1. Understands natural language design requests
    2. Retrieves relevant brand context and history
    3. Plans layout, colors, and composition
    4. Generates designs using your existing pipeline
    5. Explains its reasoning and decisions
    """

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.brand_kit_manager = BrandKitManager()
        self.image_generator = OpenAIImageGenerator()
        self.composer = CompositionEngine()
        self.validator = ValidationEngine()

    # ==================== UNDERSTAND REQUEST ====================

    def understand_request(
        self,
        org_id: UUID,
        user_message: str,
        brand_kit_id: Optional[UUID] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        model: str = "gpt-4o-mini",
    ) -> Dict[str, Any]:
        """
        Parse and understand what the user wants.

        Args:
            org_id: Organization UUID
            user_message: End-user request (natural language)
            brand_kit_id: Optional brand kit UUID
            conversation_history: Optional chat turns [{"role": "...", "content": "..."}]
            model: OpenAI chat model to use

        Returns:
            Structured intent dict.
        """
        # Fetch brand kit (optional)
        brand_kit: Optional[BrandKit] = None
        if brand_kit_id:
            try:
                brand_kit = self.brand_kit_manager.get_brand_kit(brand_kit_id)
            except Exception:
                brand_kit = None  # tolerate missing kit gracefully

        # Fetch brand context/patterns/stats from memory
        # Prefer a consolidated method if your brand_memory has it.
        try:
            # If your implementation has get_brand_context, use it:
            brand_context = brand_memory.get_brand_context(org_id)  # type: ignore[attr-defined]
        except Exception:
            # Fallback composition from available calls
            try:
                patterns = brand_memory.get_brand_patterns(org_id)
            except Exception:
                patterns = []
            brand_context = {
                "patterns": patterns,
                "stats": {"total_designs": 0, "recent_designs": 0},
                "similar_designs": [],
            }

        system_prompt = self._build_understanding_prompt(brand_context, brand_kit)

        # Build messages
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            # Trust caller to pass sanitized roles; otherwise clamp to user/assistant
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        # Call model (JSON mode)
        resp = self.client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        raw = resp.choices[0].message.content or "{}"
        try:
            intent = json.loads(raw)
        except Exception:
            # Last-resort safe scaffolding
            intent = {
                "design_type": "social_post",
                "platform": "general",
                "aspect_ratio": "1:1",
                "tone": "professional",
                "key_elements": [],
                "constraints": [],
                "description": user_message.strip(),
            }

        # Enhance with brand insights for downstream planning
        intent["brand_context"] = brand_context
        intent["similar_past_work"] = brand_context.get("similar_designs", [])

        return intent

    # ==================== PLAN DESIGN ====================

    def plan_design(
        self,
        org_id: UUID,
        intent: Dict[str, Any],
        brand_kit_id: UUID,
        model: str = "gpt-4o-mini",
    ) -> Dict[str, Any]:
        """
        Plan the design based on understood intent and brand context
        Enhanced with deep brand analysis from past examples
        """
        # Get brand kit details
        brand_kit = None
        try:
            brand_kit = self.brand_kit_manager.get_brand_kit(brand_kit_id)
        except Exception:
            brand_kit = None

        # STEP 1: Get Brand Book Guidelines (PRIORITY)
        logger.info(f"Checking for brand book guidelines for org {org_id}")
        brand_book_guidelines = None
        try:
            brand_book_guidelines = brandbook_analyzer.get_brand_guidelines(org_id)
            if brand_book_guidelines:
                logger.info("✅ Found brand book guidelines - using as primary source")
            else:
                logger.info("No brand book uploaded - will use examples and brand kit")
        except Exception as e:
            logger.error(f"Error retrieving brand book: {str(e)}")
            brand_book_guidelines = None

        # STEP 2: Deep Brand Analysis from past examples
        logger.info(f"Performing deep brand analysis for org {org_id}")
        brand_analysis = None
        try:
            user_request = intent.get("description", "")
            brand_analysis = brand_analyzer.get_brand_analysis_for_generation(
                org_id=org_id,
                user_request=user_request
            )

            if brand_analysis.get("has_examples"):
                logger.info(f"Found {brand_analysis.get('example_count', 0)} examples for deep analysis")
                confidence = brand_analysis.get("analysis", {}).get("confidence_score", 0)
                logger.info(f"Brand analysis confidence: {confidence:.1%}")
            else:
                logger.info("No past examples found")
        except Exception as e:
            logger.error(f"Brand analysis failed: {str(e)}")
            brand_analysis = None

        # Get learned patterns
        try:
            patterns = brand_memory.get_brand_patterns(org_id)
        except Exception:
            patterns = []

        # Build planning prompt with ALL brand knowledge
        planning_prompt = self._build_planning_prompt(
            intent,
            brand_kit,
            patterns,
            brand_analysis,
            brand_book_guidelines
        )

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": planning_prompt},
                {
                    "role": "user",
                    "content": f"Plan design for: {intent.get('description', 'Design request')}",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        content = response.choices[0].message.content or "{}"
        try:
            plan = json.loads(content)
        except Exception:
            plan = {
                "background_prompt": "abstract, brand-appropriate background, no text or logos",
                "layout_choice": "centered-logo",
                "aspect_ratio": intent.get("aspect_ratio", "1:1"),
                "colors_used": [],
                "text_overlay": None,
                "quality": "standard",
                "reasoning": {
                    "overall": "Fallback plan using brand defaults.",
                    "layout": "Centered for maximum flexibility.",
                    "colors": "Use brand primary/secondary if available.",
                },
            }

        # Add metadata
        plan["intent"] = intent
        plan["brand_kit_id"] = str(brand_kit_id)
        plan["org_id"] = str(org_id)
        plan["brand_analysis"] = brand_analysis  # Pass brand analysis to generation step

        # Normalize aspect ratio
        if plan.get("aspect_ratio") not in {"1:1", "4:5", "9:16"}:
            plan["aspect_ratio"] = "1:1"

        # Normalize quality
        if plan.get("quality") not in {"standard", "hd"}:
            plan["quality"] = "standard"

        return plan

    # ==================== GENERATE DESIGN ====================

    def generate_design(
        self,
        org_id: UUID,
        plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the design plan using your existing pipeline
        """
        brand_kit_id = UUID(plan["brand_kit_id"])

        aspect_ratio_map = {
            "1:1": AspectRatio.SQUARE,
            "4:5": AspectRatio.PORTRAIT,
            "9:16": AspectRatio.STORY,
        }
        aspect_ratio = aspect_ratio_map.get(plan.get("aspect_ratio", "1:1"), AspectRatio.SQUARE)

        # Step 1: Generate background
        job_data = JobCreate(
            prompt=plan["background_prompt"],
            params=JobParams(
                aspect_ratio=aspect_ratio,
                num_images=1,
                quality=plan.get("quality", "standard"),
                style="vivid",
            ),
        )

        background_result = self.image_generator.generate_with_moderation(
            org_id=org_id,
            job_data=job_data,
        )

        job = background_result.get("job")
        assets = background_result.get("assets", [])
        job_id = getattr(job, "id", None)
        asset_id = getattr(assets[0], "id", None) if assets else None

        if not asset_id:
            raise ValueError("No assets generated")

        # Step 2: Compose with brand elements
        preset_map = {
            "top-left-logo": CompositionPreset.TOP_LEFT_LOGO_BOTTOM_CTA,
            "centered-logo": CompositionPreset.CENTER_LOGO_NO_TEXT,
            "bottom-right-logo": CompositionPreset.BOTTOM_RIGHT_LOGO_TOP_TEXT,
            "minimal": CompositionPreset.CENTER_LOGO_NO_TEXT,
        }
        preset = preset_map.get(plan.get("layout_choice", "centered-logo"), CompositionPreset.CENTER_LOGO_NO_TEXT)

        composed_url = self.composer.compose_with_preset(
            asset_id=asset_id,
            brand_kit_id=brand_kit_id,
            preset=preset,
            text=plan.get("text_overlay"),
        )

        # Step 3: Validate
        brand_kit = None
        try:
            brand_kit = self.brand_kit_manager.get_brand_kit(brand_kit_id)
        except Exception:
            brand_kit = None

        brand_colors = {}
        if brand_kit:
            brand_colors = {
                "primary": getattr(brand_kit.colors, "primary", None),
                "secondary": getattr(brand_kit.colors, "secondary", None),
            }

        validation = self.validator.validate_composed_asset(
            asset_id=asset_id,
            brand_colors=brand_colors,
        )

        # Step 4: Store in memory for learning
        try:
            design_id = brand_memory.store_design(
                org_id=org_id,
                asset_id=asset_id,
                design_type=plan.get("intent", {}).get("design_type", "social_post"),
                platform=plan.get("intent", {}).get("platform"),
                aspect_ratio=plan.get("aspect_ratio", "1:1"),
                layout_type=plan.get("layout_choice"),
                colors_used=plan.get("colors_used"),
                text_content=plan.get("text_overlay"),
            )
        except Exception:
            design_id = None

        return {
            "design_id": design_id,
            "asset_id": asset_id,
            "job_id": job_id,
            "final_url": composed_url,
            "validation": validation,
            "reasoning": plan.get("reasoning", {}),
            "plan": plan,
        }

    # ==================== EXPLAIN DECISIONS ====================

    def explain_decision(self, plan: Dict[str, Any], aspect: str) -> str:
        """
        Explain why certain design decisions were made
        """
        reasoning = plan.get("reasoning", {}) or {}
        if aspect == "overall":
            return reasoning.get("overall", "Design planned based on brand guidelines and past successful work.")
        if aspect == "layout":
            return reasoning.get("layout", f"Chose {plan.get('layout_choice')} layout for optimal visual hierarchy.")
        if aspect == "colors":
            return reasoning.get("colors", "Using brand primary and secondary colors for consistency.")
        if aspect == "typography":
            return reasoning.get("typography", "Selected fonts match brand guidelines.")
        return "This decision was made based on brand patterns and best practices."

    # ==================== PROMPT BUILDERS ====================

    def _build_understanding_prompt(
        self,
        brand_context: Dict[str, Any],
        brand_kit: Optional[BrandKit],
    ) -> str:
        """Build system prompt for understanding user intent"""
        patterns_summary = "No learned patterns yet."
        patterns = brand_context.get("patterns") or []
        if patterns:
            parts = []
            for p in patterns[:5]:
                name = p.get("pattern_name", "pattern")
                conf = p.get("confidence_score", 0)
                try:
                    conf_pct = f"{float(conf):.0%}"
                except Exception:
                    conf_pct = "—"
                parts.append(f"- {name}: {conf_pct} confidence")
            patterns_summary = "\n".join(parts)

        brand_info = "No brand kit configured."
        if brand_kit:
            style_desc = ", ".join(getattr(getattr(brand_kit, "style", object), "descriptors", []) or []) or "Not specified"
            secondary = getattr(getattr(brand_kit, "colors", object), "secondary", None) or "Not specified"
            brand_info = f"""
Brand Name: {getattr(brand_kit, "name", "Unknown")}
Primary Color: {getattr(getattr(brand_kit, "colors", object), "primary", "Not specified")}
Secondary Color: {secondary}
Style: {style_desc}
""".strip()

        total_designs = brand_context.get("stats", {}).get("total_designs", 0)
        recent_designs = brand_context.get("stats", {}).get("recent_designs", 0)

        return f"""You are an expert design agent helping to understand design requests.

BRAND CONTEXT:
{brand_info}

LEARNED PATTERNS:
{patterns_summary}

BRAND STATS:
- Total designs: {total_designs}
- Recent designs: {recent_designs}

Your task: Parse the user's message and extract structured intent.

Return JSON with:
{{
    "design_type": "social_post|ad|banner|story",
    "platform": "instagram|facebook|linkedin|twitter|general",
    "aspect_ratio": "1:1|4:5|9:16|16:9",
    "tone": "professional|friendly|bold|minimal|energetic",
    "key_elements": ["element1", "element2"],
    "constraints": ["avoid X", "must include Y"],
    "description": "clear description of what user wants"
}}

Be specific and infer details when not explicitly stated."""
    def _build_planning_prompt(
        self,
        intent: Dict[str, Any],
        brand_kit: Optional[BrandKit],
        patterns: List[Dict[str, Any]],
        brand_analysis: Optional[Dict[str, Any]] = None,
        brand_book_guidelines: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build system prompt for design planning with complete brand knowledge"""
        if patterns:
            patterns_text = "\n".join(
                f"- {p.get('pattern_name','pattern')}: Used {p.get('sample_count',0)} times, "
                f"{(lambda v: f'{float(v):.0%}' if isinstance(v,(int,float)) else '—')(p.get('confidence_score',0))} confidence"
                for p in patterns[:5]
            )
        else:
            patterns_text = "No patterns learned yet - using standard best practices."

        style_desc = (
            ", ".join(getattr(getattr(brand_kit, "style", object), "descriptors", []) or [])
            if brand_kit else "Not specified"
        )
        brand_name = getattr(brand_kit, "name", "Not specified") if brand_kit else "Not specified"
        primary = getattr(getattr(brand_kit, "colors", object), "primary", "Not specified") if brand_kit else "Not specified"
        secondary = getattr(getattr(brand_kit, "colors", object), "secondary", "Not specified") if brand_kit else "Not specified"

        similar_work = ""
        if intent.get("similar_past_work"):
            lines = [
                f"- {d.get('design_type','design')} ({d.get('platform','general')}): {d.get('layout_type','layout')} layout"
                for d in intent["similar_past_work"][:3]
            ]
            similar_work = "SIMILAR PAST WORK:\n" + "\n".join(lines)

        # Add brand book guidelines (HIGHEST PRIORITY)
        brand_book_section = ""
        if brand_book_guidelines:
            visual_id = brand_book_guidelines.get("visual_identity", {})
            imagery = brand_book_guidelines.get("imagery_guidelines", {})
            messaging = brand_book_guidelines.get("brand_messaging", {})

            brand_book_section = f"""
🎯 BRAND BOOK GUIDELINES (HIGHEST PRIORITY - MUST FOLLOW):

Visual Identity:
{json.dumps(visual_id, indent=2)}

Imagery Guidelines:
{json.dumps(imagery, indent=2)}

Brand Messaging:
{json.dumps(messaging, indent=2)}

CRITICAL: These are the official brand guidelines. Follow them EXACTLY!
"""

        # Add deep brand analysis insights if available
        brand_dna_section = ""
        if brand_analysis and brand_analysis.get("has_examples"):
            analysis_data = brand_analysis.get("analysis", {})
            synthesis = analysis_data.get("synthesis", {})
            guidelines = analysis_data.get("guidelines", {})

            brand_signature = synthesis.get("brand_signature", "")
            visual_style = synthesis.get("visual_style_dna", {})
            color_dna = synthesis.get("color_dna", {})

            style_keywords = ", ".join(visual_style.get("keywords", [])[:5])

            brand_dna_section = f"""
DEEP BRAND ANALYSIS (from {brand_analysis.get('example_count', 0)} past examples):
- Brand Signature: {brand_signature}
- Visual Style DNA: {style_keywords}
- Color Patterns: {json.dumps(color_dna.get('palette', [])[:3])}
- Background Style: {guidelines.get('background_style', 'Not analyzed')}
- Must Include: {json.dumps(guidelines.get('must_include', []))}
- Must Avoid: {json.dumps(guidelines.get('must_avoid', []))}

IMPORTANT: Use these insights to complement the brand book guidelines!
"""

        return f"""
You are an expert design strategist planning a design.

INTENT:
{json.dumps(intent, indent=2)}

{brand_book_section}

BRAND KIT:
- Name: {brand_name}
- Primary: {primary}
- Secondary: {secondary}
- Style: {style_desc}

LEARNED PATTERNS:
{patterns_text}

{similar_work}

{brand_dna_section}

Plan the design and return JSON:
{{
    "background_prompt": "Detailed DALL-E prompt (no text, no logos)",
    "layout_choice": "top-left-logo|centered-logo|bottom-right-logo|minimal",
    "aspect_ratio": "1:1|4:5|9:16",
    "colors_used": ["#HEX1", "#HEX2"],
    "text_overlay": "Optional text to add",
    "quality": "standard|hd",
    "reasoning": {{
        "overall": "Why this approach works",
        "layout": "Why this layout",
        "colors": "Why these colors"
    }}
}}

Make decisions based on learned patterns and brand consistency.
""".strip()


# Singleton instance
design_agent = DesignAgent()
