"""
Brand Parser
Extracts structured brand tokens from PDF brand books using AI
"""
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import io
import re
import base64

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from PIL import Image
except ImportError:
    Image = None

import openai
from app.core.schemas_v2 import (
    BrandTokensV2, ColorPalette, ColorToken,
    TypographyToken, LogoRules, LogoVariant,
    LayoutSystem, VoiceProfile, ContentPolicies
)
from app.infra.config import settings
from app.infra.logging import get_logger

logger = get_logger(__name__)


class BrandParser:
    """
    Parse PDF brand books to extract design tokens

    Features:
    - PDF text extraction
    - GPT-4 Vision for visual analysis
    - Color palette extraction
    - Typography detection
    - Logo rules extraction
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize parser with OpenAI API"""
        openai.api_key = api_key or settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=openai.api_key)

        if not pdfplumber:
            logger.warning("pdfplumber not installed. PDF parsing will be limited.")

    def parse_brand_book(
        self,
        pdf_path: str,
        brand_name: str
    ) -> Tuple[BrandTokensV2, Dict[str, Any]]:
        """
        Main entry point: Parse complete brand book

        Args:
            pdf_path: Path to PDF brand book
            brand_name: Brand name

        Returns:
            Tuple of (BrandTokensV2, parsing_metadata)
        """
        logger.info(f"Parsing brand book for {brand_name}: {pdf_path}")

        # Step 1: Extract text from PDF
        text_content = self._extract_pdf_text(pdf_path)

        # Step 2: Extract images for visual analysis
        images = self._extract_pdf_images(pdf_path, max_images=5)

        # Step 3: Analyze with GPT-4
        analysis = self._analyze_with_gpt4(text_content, images, brand_name)

        # Step 4: Build structured tokens
        tokens = self._build_brand_tokens(analysis, brand_name)

        # Metadata for debugging/auditing
        metadata = {
            "pages_processed": len(text_content) if isinstance(text_content, list) else 1,
            "images_analyzed": len(images),
            "parsing_method": "gpt4_vision",
            "confidence_score": analysis.get("confidence", 0.8)
        }

        logger.info(f"Brand parsing complete. Confidence: {metadata['confidence_score']}")
        return tokens, metadata

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract all text from PDF"""
        if not pdfplumber:
            logger.error("pdfplumber not installed")
            return ""

        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

            full_text = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(full_text)} characters from PDF")
            return full_text

        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""

    def _extract_pdf_images(self, pdf_path: str, max_images: int = 5) -> List[bytes]:
        """Extract sample images from PDF for visual analysis"""
        if not pdfplumber or not Image:
            logger.warning("Image libraries not available")
            return []

        try:
            images = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages[:max_images]):
                    # Convert page to image
                    img = page.to_image(resolution=150)

                    # Convert to bytes
                    buffer = io.BytesIO()
                    img.original.save(buffer, format='PNG')
                    buffer.seek(0)
                    images.append(buffer.getvalue())

                    if len(images) >= max_images:
                        break

            logger.info(f"Extracted {len(images)} images from PDF")
            return images

        except Exception as e:
            logger.error(f"Error extracting PDF images: {e}")
            return []

    def _analyze_with_gpt4(
        self,
        text_content: str,
        images: List[bytes],
        brand_name: str
    ) -> Dict[str, Any]:
        """
        Use GPT-4 Vision to analyze brand guidelines

        Args:
            text_content: Extracted PDF text
            images: Sample images from PDF
            brand_name: Brand name

        Returns:
            Structured analysis dict
        """
        logger.info("Analyzing brand book with GPT-4 Vision...")

        # Build comprehensive prompt
        system_prompt = """You are an expert brand strategist analyzing brand guidelines.
Extract all design tokens, rules, and policies from the brand book.

Focus on:
1. **Colors**: Primary, secondary, accent colors (hex codes)
2. **Typography**: Font families, weights, sizes
3. **Logo**: Usage rules, minimum sizes, clear space, placement
4. **Layout**: Grid system, spacing, border radius
5. **Voice**: Brand personality traits, tone
6. **Content**: Approved CTAs, forbidden terms, messaging rules

Return a JSON object with this exact structure:
{
  "colors": {
    "primary": {"hex": "#...", "name": "...", "usage": "..."},
    "secondary": {"hex": "#...", "name": "...", "usage": "..."},
    "accent": {"hex": "#...", "name": "...", "usage": "..."},
    "neutral": {"black": "#...", "white": "#...", "gray": ["#...", "..."]},
    "semantic": {"success": "#...", "warning": "#...", "error": "#...", "info": "#..."}
  },
  "typography": {
    "heading": {
      "family": "Font Name",
      "weights": [700, 800],
      "scale": [72, 56, 40],
      "line_height": 1.2,
      "letter_spacing": -0.02
    },
    "body": {
      "family": "Font Name",
      "weights": [400, 600],
      "sizes": [16, 18],
      "line_height": 1.5
    }
  },
  "logo": {
    "min_size_px": 128,
    "clear_space": "1x logo height",
    "allowed_positions": ["TL", "TR", "BR"],
    "forbidden_backgrounds": ["busy patterns"]
  },
  "layout": {
    "grid": 12,
    "spacing_scale": [4, 8, 16, 24, 32],
    "border_radius": {"sm": 8, "md": 16, "lg": 24}
  },
  "voice": {
    "traits": ["professional", "friendly"],
    "tone": "confident but approachable",
    "vocabulary": {
      "prefer": ["empower", "transform"],
      "avoid": ["revolutionary", "cheap"]
    }
  },
  "policies": {
    "cta_whitelist": ["Get Started", "Learn More"],
    "forbidden_terms": ["guaranteed", "cheap"],
    "content_rules": ["Always include value proposition"]
  },
  "confidence": 0.9
}

If information is not explicitly stated, use professional defaults.
Be thorough and extract as much as possible."""

        user_prompt = f"""Analyze this brand book for {brand_name}.

TEXT CONTENT:
{text_content[:8000]}  # Limit to avoid token limits

Extract all design tokens and return structured JSON."""

        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # If images available, add first image for visual analysis
            if images and len(images) > 0:
                # Encode first image to base64
                base64_image = base64.b64encode(images[0]).decode('utf-8')

                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Here's a sample page from the brand book:"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                })

            # Call GPT-4 Vision
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=messages,
                max_tokens=2000,
                temperature=0.3  # Lower temp for more consistent extraction
            )

            # Parse response
            content = response.choices[0].message.content

            # Extract JSON from response (handle markdown code blocks)
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            import json
            analysis = json.loads(content)

            logger.info(f"GPT-4 analysis complete. Confidence: {analysis.get('confidence', 0.0)}")
            return analysis

        except Exception as e:
            logger.error(f"Error in GPT-4 analysis: {e}")
            # Return empty analysis
            return {
                "colors": {},
                "typography": {},
                "logo": {},
                "layout": {},
                "voice": {},
                "policies": {},
                "confidence": 0.0,
                "error": str(e)
            }

    def _build_brand_tokens(
        self,
        analysis: Dict[str, Any],
        brand_name: str
    ) -> BrandTokensV2:
        """
        Build BrandTokensV2 from GPT-4 analysis

        Args:
            analysis: Parsed analysis from GPT-4
            brand_name: Brand name

        Returns:
            BrandTokensV2 object
        """
        logger.info("Building brand tokens from analysis...")

        # Start with defaults
        tokens = BrandTokensV2.get_default_tokens()
        tokens.brand_id = brand_name

        # Extract colors
        if "colors" in analysis and analysis["colors"]:
            colors_data = analysis["colors"]

            try:
                tokens.colors = ColorPalette(
                    primary=ColorToken(**colors_data.get("primary", {"hex": "#4F46E5"})),
                    secondary=ColorToken(**colors_data.get("secondary", {"hex": "#7C3AED"})),
                    accent=ColorToken(**colors_data.get("accent", {"hex": "#F59E0B"})),
                    neutral=colors_data.get("neutral", {"black": "#111111", "white": "#FFFFFF"}),
                    semantic=colors_data.get("semantic")
                )
                logger.info(f"✅ Extracted colors: {tokens.colors.primary.hex}, {tokens.colors.secondary.hex}")
            except Exception as e:
                logger.warning(f"Color extraction failed: {e}")

        # Extract typography
        if "typography" in analysis and analysis["typography"]:
            typo_data = analysis["typography"]

            try:
                tokens.typography = {}

                if "heading" in typo_data:
                    tokens.typography["heading"] = TypographyToken(**typo_data["heading"])
                    logger.info(f"✅ Heading font: {tokens.typography['heading'].family}")

                if "body" in typo_data:
                    tokens.typography["body"] = TypographyToken(**typo_data["body"])
                    logger.info(f"✅ Body font: {tokens.typography['body'].family}")

            except Exception as e:
                logger.warning(f"Typography extraction failed: {e}")

        # Extract logo rules
        if "logo" in analysis and analysis["logo"]:
            logo_data = analysis["logo"]

            try:
                tokens.logo = LogoRules(
                    variants=[],  # Logo images will be uploaded separately
                    min_size_px=logo_data.get("min_size_px", 128),
                    clear_space=logo_data.get("clear_space", "1x logo height"),
                    allowed_positions=logo_data.get("allowed_positions", ["TL", "TR", "BR"]),
                    forbidden_backgrounds=logo_data.get("forbidden_backgrounds", [])
                )
                logger.info(f"✅ Logo rules: min {tokens.logo.min_size_px}px")
            except Exception as e:
                logger.warning(f"Logo rules extraction failed: {e}")

        # Extract layout
        if "layout" in analysis and analysis["layout"]:
            layout_data = analysis["layout"]

            try:
                tokens.layout = LayoutSystem(
                    grid=layout_data.get("grid", 12),
                    spacing_scale=layout_data.get("spacing_scale", [4, 8, 16, 24, 32, 48, 64]),
                    border_radius=layout_data.get("border_radius", {"sm": 8, "md": 16, "lg": 24}),
                    shadows=layout_data.get("shadows")
                )
                logger.info(f"✅ Layout: {tokens.layout.grid}-column grid")
            except Exception as e:
                logger.warning(f"Layout extraction failed: {e}")

        # Extract voice
        if "voice" in analysis and analysis["voice"]:
            voice_data = analysis["voice"]

            try:
                tokens.voice = VoiceProfile(
                    traits=voice_data.get("traits", ["professional"]),
                    tone=voice_data.get("tone", "professional"),
                    vocabulary=voice_data.get("vocabulary", {"prefer": [], "avoid": []})
                )
                logger.info(f"✅ Voice: {', '.join(tokens.voice.traits[:3])}")
            except Exception as e:
                logger.warning(f"Voice extraction failed: {e}")

        # Extract policies
        if "policies" in analysis and analysis["policies"]:
            policies_data = analysis["policies"]

            try:
                tokens.policies = ContentPolicies(
                    cta_whitelist=policies_data.get("cta_whitelist", ["Get Started", "Learn More"]),
                    forbidden_terms=policies_data.get("forbidden_terms", []),
                    content_rules=policies_data.get("content_rules", [])
                )
                logger.info(f"✅ CTAs: {len(tokens.policies.cta_whitelist)} approved")
            except Exception as e:
                logger.warning(f"Policies extraction failed: {e}")

        return tokens

    def extract_colors_from_image(self, image_bytes: bytes) -> List[str]:
        """
        Extract dominant colors from an image
        Useful for extracting brand colors from logo or sample designs

        Args:
            image_bytes: Image data

        Returns:
            List of hex colors
        """
        if not Image:
            logger.warning("PIL not available for color extraction")
            return []

        try:
            from collections import Counter

            # Open image
            img = Image.open(io.BytesIO(image_bytes))

            # Resize for performance
            img = img.resize((150, 150))

            # Convert to RGB
            img = img.convert('RGB')

            # Get all pixels
            pixels = list(img.getdata())

            # Count frequencies
            most_common = Counter(pixels).most_common(10)

            # Convert to hex
            hex_colors = []
            for rgb, count in most_common:
                # Skip near-white and near-black
                if sum(rgb) > 700 or sum(rgb) < 50:
                    continue

                hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb)
                hex_colors.append(hex_color)

            logger.info(f"Extracted {len(hex_colors)} colors from image")
            return hex_colors[:5]  # Top 5

        except Exception as e:
            logger.error(f"Color extraction error: {e}")
            return []

    def fallback_manual_input(self) -> BrandTokensV2:
        """
        Fallback: Return default tokens for manual input
        Used when PDF parsing fails
        """
        logger.warning("Using fallback: manual token input required")
        return BrandTokensV2.get_default_tokens()


# Convenience function
def parse_brand_book(pdf_path: str, brand_name: str) -> BrandTokensV2:
    """
    Quick function to parse brand book

    Args:
        pdf_path: Path to PDF brand book
        brand_name: Brand name

    Returns:
        BrandTokensV2
    """
    parser = BrandParser()
    tokens, metadata = parser.parse_brand_book(pdf_path, brand_name)
    return tokens
