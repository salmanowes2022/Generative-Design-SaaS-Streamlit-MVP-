"""
Brand Analyzer - Deep Visual Analysis of Brand Examples
Uses GPT-4 Vision to deeply understand design patterns from past examples
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from openai import OpenAI
import base64
import requests
from io import BytesIO
from PIL import Image

from app.infra.config import settings
from app.infra.db import get_db
from app.infra.logging import get_logger

logger = get_logger(__name__)


class BrandAnalyzer:
    """
    Deep brand analysis using GPT-4 Vision to understand design patterns

    This module:
    1. Analyzes existing brand assets using vision AI
    2. Identifies patterns in composition, color usage, typography
    3. Extracts design DNA from examples
    4. Creates detailed brand guidelines from examples
    """

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.vision_model = "gpt-4o"  # Latest vision model

    def analyze_brand_examples(
        self,
        org_id: UUID,
        example_urls: List[str],
        design_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deeply analyze a set of brand examples to extract design DNA

        Args:
            org_id: Organization UUID
            example_urls: List of image URLs to analyze
            design_type: Optional filter for design type

        Returns:
            Comprehensive brand analysis with patterns, guidelines, and insights
        """
        if not example_urls:
            return self._get_default_analysis()

        logger.info(f"Analyzing {len(example_urls)} brand examples for org {org_id}")

        # Analyze each image individually
        individual_analyses = []
        for idx, url in enumerate(example_urls[:5]):  # Limit to 5 examples
            try:
                analysis = self._analyze_single_image(url, idx + 1)
                individual_analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing image {url}: {str(e)}")
                continue

        if not individual_analyses:
            return self._get_default_analysis()

        # Synthesize patterns across all examples
        synthesis = self._synthesize_patterns(individual_analyses)

        # Generate actionable guidelines
        guidelines = self._generate_guidelines(synthesis)

        return {
            "individual_analyses": individual_analyses,
            "synthesis": synthesis,
            "guidelines": guidelines,
            "total_analyzed": len(individual_analyses),
            "confidence_score": self._calculate_confidence(len(individual_analyses))
        }

    def _analyze_single_image(self, image_url: str, index: int) -> Dict[str, Any]:
        """
        Analyze a single brand example image using GPT-4 Vision

        Returns detailed analysis of:
        - Layout and composition
        - Color palette and usage
        - Typography and text placement
        - Visual hierarchy
        - Brand elements positioning
        - Overall style and mood
        """
        prompt = """Analyze this brand/marketing design in EXTREME detail. You are a professional designer conducting a deep analysis.

ANALYZE THESE ASPECTS:

1. COMPOSITION & LAYOUT:
   - Overall layout structure (grid, free-form, centered, asymmetric)
   - Rule of thirds usage
   - Visual flow and eye path
   - Whitespace usage and breathing room
   - Element positioning and alignment

2. COLOR ANALYSIS:
   - Dominant colors (estimate hex codes if possible)
   - Color proportions (% of each color)
   - Color relationships (complementary, analogous, triadic)
   - Contrast ratios
   - Color mood and psychology

3. TYPOGRAPHY:
   - Font styles (serif, sans-serif, display, script)
   - Type hierarchy (heading, subheading, body sizes)
   - Text alignment and positioning
   - Letter spacing and line height
   - Text-to-image ratio

4. BRAND ELEMENTS:
   - Logo size and placement
   - Logo treatment (with effects, plain, etc)
   - Brand mark usage
   - Consistency with brand guidelines

5. VISUAL STYLE:
   - Photography style (lifestyle, product, abstract, illustration)
   - Image treatment (filters, overlays, gradients)
   - Depth and dimension (flat, layered, 3D)
   - Texture and patterns
   - Overall aesthetic (modern, vintage, minimalist, maximal, etc)

6. CONTENT BALANCE:
   - Image-to-text ratio
   - Focal point clarity
   - CTA prominence (if any)
   - Information density

7. TECHNICAL QUALITY:
   - Image quality and resolution
   - Professional polish level
   - Consistency with best practices

Return a detailed JSON analysis with specific, actionable observations."""

        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url, "detail": "high"}}
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )

            content = response.choices[0].message.content

            # Try to parse as JSON, fallback to structured text
            import json
            try:
                analysis = json.loads(content)
            except:
                # Structure the text response
                analysis = {
                    "raw_analysis": content,
                    "index": index,
                    "url": image_url
                }

            analysis["index"] = index
            analysis["url"] = image_url

            logger.info(f"Successfully analyzed example {index}")
            return analysis

        except Exception as e:
            logger.error(f"Vision API error for example {index}: {str(e)}")
            return {
                "index": index,
                "url": image_url,
                "error": str(e),
                "analysis": "Could not analyze this image"
            }

    def _synthesize_patterns(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize patterns across multiple analyzed examples
        Uses GPT-4 to identify consistent patterns and brand DNA
        """
        # Create summary of all analyses
        analyses_summary = "\n\n".join([
            f"Example {a.get('index', i+1)}:\n{str(a)}"
            for i, a in enumerate(analyses)
        ])

        synthesis_prompt = f"""You are analyzing {len(analyses)} brand design examples to extract the brand's "design DNA" - the consistent patterns that make their designs recognizable.

INDIVIDUAL ANALYSES:
{analyses_summary}

SYNTHESIZE THESE PATTERNS:

1. CONSISTENT LAYOUT PATTERNS:
   - What layout structures appear repeatedly?
   - Common positioning of elements
   - Typical composition rules followed

2. COLOR PATTERNS:
   - Recurring color combinations
   - Primary vs secondary color usage
   - Color mood consistency
   - Background vs foreground color patterns

3. TYPOGRAPHY PATTERNS:
   - Font style preferences
   - Text sizing patterns
   - Text placement preferences
   - Typographic hierarchy style

4. BRAND ELEMENT PATTERNS:
   - Logo placement consistency
   - Logo sizing preferences
   - Brand mark treatment

5. VISUAL STYLE CONSISTENCY:
   - Photography/image style
   - Overall aesthetic direction
   - Recurring visual effects or treatments

6. DESIGN PRINCIPLES:
   - What design rules does this brand follow?
   - What makes their designs cohesive?
   - Their unique "signature" elements

Return detailed JSON with:
{{
    "layout_dna": {{"description": "...", "rules": ["rule1", "rule2"]}},
    "color_dna": {{"palette": ["color1", "color2"], "usage_pattern": "..."}},
    "typography_dna": {{"style": "...", "rules": ["rule1", "rule2"]}},
    "visual_style_dna": {{"description": "...", "keywords": ["keyword1", "keyword2"]}},
    "brand_signature": "What makes this brand's designs unique and recognizable",
    "consistency_score": 0.0-1.0,
    "key_patterns": ["pattern1", "pattern2", "pattern3"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": synthesis_prompt}],
                response_format={"type": "json_object"},
                temperature=0.2
            )

            import json
            synthesis = json.loads(response.choices[0].message.content)
            return synthesis

        except Exception as e:
            logger.error(f"Synthesis error: {str(e)}")
            return {
                "brand_signature": "Could not synthesize patterns",
                "error": str(e)
            }

    def _generate_guidelines(self, synthesis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate actionable design guidelines from synthesis
        """
        guidelines_prompt = f"""Based on this brand pattern synthesis:

{str(synthesis)}

Create ACTIONABLE DESIGN GUIDELINES for generating new designs that match this brand.

Format as JSON:
{{
    "image_generation_prompt_template": "Detailed prompt template for DALL-E with placeholders",
    "layout_rules": ["rule1", "rule2", "rule3"],
    "color_rules": ["rule1", "rule2"],
    "composition_rules": ["rule1", "rule2"],
    "must_include": ["element1", "element2"],
    "must_avoid": ["thing1", "thing2"],
    "style_keywords": ["keyword1", "keyword2"],
    "background_style": "Description of typical backgrounds",
    "subject_treatment": "How subjects/products are typically shown"
}}

Make these guidelines SPECIFIC and ACTIONABLE for an AI to follow."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": guidelines_prompt}],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            import json
            guidelines = json.loads(response.choices[0].message.content)
            return guidelines

        except Exception as e:
            logger.error(f"Guidelines generation error: {str(e)}")
            return self._get_default_guidelines()

    def get_brand_analysis_for_generation(
        self,
        org_id: UUID,
        user_request: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive brand analysis to inform image generation

        Combines:
        - Stored brand analysis
        - Recent design examples
        - User request context

        Returns optimized prompt and guidelines for generation
        """
        db = get_db()

        # Get recent approved designs with their URLs
        recent_designs = db.fetch_all("""
            SELECT a.base_url, a.composed_url, dh.design_type, dh.layout_type
            FROM design_history dh
            JOIN assets a ON dh.asset_id = a.id
            LEFT JOIN design_feedback df ON dh.id = df.design_id
            WHERE dh.org_id = %s
            AND (df.feedback_type = 'approved' OR df.feedback_type IS NULL)
            ORDER BY dh.created_at DESC
            LIMIT 5
        """, (str(org_id),))

        # Get image URLs (prefer composed, fall back to base)
        example_urls = [
            d.get('composed_url') or d.get('base_url')
            for d in recent_designs
            if (d.get('composed_url') or d.get('base_url'))
        ]

        if example_urls:
            # Perform deep analysis
            analysis = self.analyze_brand_examples(org_id, example_urls)

            # Generate optimized prompt
            optimized_prompt = self._create_brand_aware_prompt(
                user_request,
                analysis
            )

            return {
                "optimized_prompt": optimized_prompt,
                "analysis": analysis,
                "has_examples": True,
                "example_count": len(example_urls)
            }
        else:
            # No examples yet - use basic guidelines
            return {
                "optimized_prompt": user_request,
                "analysis": self._get_default_analysis(),
                "has_examples": False,
                "example_count": 0
            }

    def _create_brand_aware_prompt(
        self,
        user_request: str,
        analysis: Dict[str, Any]
    ) -> str:
        """
        Create a DALL-E prompt that incorporates brand DNA from analysis
        """
        synthesis = analysis.get("synthesis", {})
        guidelines = analysis.get("guidelines", {})

        # Extract key styling elements
        visual_style = synthesis.get("visual_style_dna", {})
        color_dna = synthesis.get("color_dna", {})
        style_keywords = visual_style.get("keywords", [])
        brand_signature = synthesis.get("brand_signature", "")

        # Get generation template
        template = guidelines.get("image_generation_prompt_template", "")
        background_style = guidelines.get("background_style", "")
        subject_treatment = guidelines.get("subject_treatment", "")
        must_avoid = guidelines.get("must_avoid", [])

        # Build enhanced prompt
        prompt_parts = []

        # Start with user request
        prompt_parts.append(f"Subject: {user_request}.")

        # Add brand styling
        if style_keywords:
            prompt_parts.append(f"Style: {', '.join(style_keywords[:5])}.")

        # Add background guidance
        if background_style:
            prompt_parts.append(f"Background: {background_style}.")

        # Add subject treatment
        if subject_treatment:
            prompt_parts.append(f"Treatment: {subject_treatment}.")

        # Add color guidance
        if color_dna.get("palette"):
            colors = color_dna.get("palette", [])[:3]
            prompt_parts.append(f"Color palette inspired by: {', '.join(colors)}.")

        # Add brand signature elements
        if brand_signature:
            prompt_parts.append(f"Brand aesthetic: {brand_signature}.")

        # Add prohibitions
        if must_avoid:
            avoid_text = ", ".join(must_avoid[:5])
            prompt_parts.append(f"Avoid: {avoid_text}.")

        # Critical instructions
        prompt_parts.append("CRITICAL: No text, no logos, no watermarks. Clean image ready for brand overlay.")
        prompt_parts.append("Professional photography quality, studio lighting, high resolution.")

        enhanced_prompt = " ".join(prompt_parts)

        logger.info(f"Created brand-aware prompt: {enhanced_prompt[:150]}...")
        return enhanced_prompt

    def _calculate_confidence(self, example_count: int) -> float:
        """Calculate confidence score based on number of examples"""
        if example_count == 0:
            return 0.0
        elif example_count == 1:
            return 0.3
        elif example_count == 2:
            return 0.5
        elif example_count == 3:
            return 0.7
        elif example_count >= 4:
            return 0.9
        return 0.5

    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis when no examples available"""
        return {
            "individual_analyses": [],
            "synthesis": {
                "brand_signature": "No examples analyzed yet",
                "consistency_score": 0.0,
                "key_patterns": []
            },
            "guidelines": self._get_default_guidelines(),
            "total_analyzed": 0,
            "confidence_score": 0.0
        }

    def _get_default_guidelines(self) -> Dict[str, Any]:
        """Return default guidelines"""
        return {
            "image_generation_prompt_template": "{subject}, professional, clean, modern",
            "layout_rules": ["centered composition", "clear focal point"],
            "color_rules": ["use brand colors", "maintain good contrast"],
            "composition_rules": ["follow rule of thirds", "balanced layout"],
            "must_include": ["professional quality"],
            "must_avoid": ["cluttered composition", "low quality"],
            "style_keywords": ["professional", "modern", "clean"],
            "background_style": "clean, minimal, professional",
            "subject_treatment": "clear, well-lit, professional"
        }


# Singleton instance
brand_analyzer = BrandAnalyzer()
