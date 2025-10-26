"""
Brand Book Analyzer - Comprehensive Brand Guidelines Extraction
Analyzes PDF brand books to extract complete brand guidelines
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from openai import OpenAI
import base64
import json
from pathlib import Path
from io import BytesIO
from PIL import Image
import PyPDF2

from app.infra.config import settings
from app.infra.db import get_db
from app.infra.logging import get_logger

logger = get_logger(__name__)


class BrandBookAnalyzer:
    """
    Comprehensive Brand Book Analysis using GPT-4 Vision and GPT-4

    Extracts complete brand guidelines from PDF brand books:
    1. Visual Identity: Logo, colors, typography, imagery
    2. Brand Messaging: Voice, tone, values, mission
    3. Usage Guidelines: Logo rules, color usage, typography rules
    4. Design Patterns: Layout preferences, spacing, composition
    5. Application Examples: Real-world usage examples
    """

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.vision_model = "gpt-4o"
        self.text_model = "gpt-4o"

    def analyze_brand_book_pdf(
        self,
        org_id: UUID,
        pdf_file: BytesIO,
        brand_name: str
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of a brand book PDF

        Args:
            org_id: Organization UUID
            pdf_file: PDF file as BytesIO
            brand_name: Name of the brand

        Returns:
            Complete brand guidelines extraction
        """
        logger.info(f"Analyzing brand book for {brand_name}")

        try:
            # Step 1: Extract text content first (always works)
            text_content = self._extract_text_from_pdf(pdf_file)

            # Get total page count from PyPDF2
            pdf_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            logger.info(f"PDF has {total_pages} pages")

            # Step 2: Try to extract pages as images for vision analysis
            pages_data = []
            page_analyses = []

            try:
                pages_data = self._extract_pdf_pages(pdf_file)
                logger.info(f"Extracted {len(pages_data)} pages as images")

                # Step 3: Analyze each page with GPT-4 Vision
                if pages_data:
                    for idx, page_data in enumerate(pages_data[:20]):  # Limit to 20 pages for cost
                        logger.info(f"Analyzing page {idx + 1}/{min(len(pages_data), 20)}")
                        analysis = self._analyze_page_with_vision(page_data, idx + 1)
                        if analysis:
                            page_analyses.append(analysis)
                else:
                    logger.warning("No pages extracted as images - will use text-only analysis")

            except Exception as vision_error:
                logger.warning(f"Vision analysis failed, falling back to text-only: {str(vision_error)}")
                # Continue with text-only analysis

            # Step 4: Synthesize comprehensive brand guidelines
            # This will work even with empty page_analyses if we have text_content
            brand_guidelines = self._synthesize_brand_guidelines(
                page_analyses=page_analyses,
                text_content=text_content,
                brand_name=brand_name
            )

            # Step 5: Store in database
            self._store_brand_guidelines(org_id, brand_guidelines)

            return {
                "status": "success",
                "brand_name": brand_name,
                "pages_analyzed": len(page_analyses),
                "total_pages": total_pages,
                "guidelines": brand_guidelines,
                "confidence_score": self._calculate_guideline_confidence(brand_guidelines),
                "analysis_method": "vision+text" if page_analyses else "text-only"
            }

        except Exception as e:
            logger.error(f"Error analyzing brand book: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _extract_pdf_pages(self, pdf_file: BytesIO) -> List[Dict[str, Any]]:
        """
        Extract pages from PDF as images for vision analysis

        Returns list of page data (images converted to base64)
        """
        try:
            from pdf2image import convert_from_bytes

            # Convert PDF pages to images
            pdf_file.seek(0)
            pdf_bytes = pdf_file.read()

            if not pdf_bytes:
                logger.error("PDF file is empty - no data to read")
                raise ValueError("PDF file is empty")

            logger.info(f"Converting PDF ({len(pdf_bytes)} bytes) to images...")
            images = convert_from_bytes(pdf_bytes, dpi=150)

            if not images:
                logger.error("No images extracted from PDF")
                raise ValueError("No pages could be extracted from PDF")

            logger.info(f"Successfully converted {len(images)} PDF pages to images")
            pages_data = []
            for idx, img in enumerate(images):
                # Convert PIL image to base64
                buffered = BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                img_base64 = base64.b64encode(buffered.getvalue()).decode()

                pages_data.append({
                    "page_number": idx + 1,
                    "image_base64": img_base64
                })

            return pages_data

        except ImportError as ie:
            error_msg = "pdf2image library not installed. Please install it: pip install pdf2image"
            logger.error(error_msg)
            logger.error("Note: pdf2image also requires poppler. On Mac: brew install poppler")
            # Return empty list to allow text-only analysis to continue
            return []
        except Exception as e:
            logger.error(f"Error extracting PDF pages: {str(e)}")
            # Return empty list to allow text-only analysis to continue
            return []

    def _extract_text_from_pdf(self, pdf_file: BytesIO) -> str:
        """Extract all text content from PDF for text analysis"""
        try:
            pdf_file.seek(0)
            pdf_bytes = pdf_file.read()

            if not pdf_bytes:
                logger.error("PDF file is empty - no text to extract")
                return ""

            pdf_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            total_pages = len(pdf_reader.pages)
            logger.info(f"Extracting text from {total_pages} PDF pages...")

            text_content = []
            for idx, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    text_content.append(text)
                    logger.debug(f"Page {idx + 1}: Extracted {len(text)} characters")

            extracted_text = "\n\n".join(text_content)
            logger.info(f"Total text extracted: {len(extracted_text)} characters from {len(text_content)} pages")

            if not extracted_text:
                logger.warning("No text content could be extracted from PDF (might be image-only PDF)")

            return extracted_text

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""

    def _analyze_page_with_vision(self, page_data: Dict[str, Any], page_num: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single brand book page with GPT-4 Vision

        Extracts:
        - Visual elements (logos, colors, typography examples)
        - Layout and design patterns
        - Guidelines and rules
        - Usage examples
        """
        image_base64 = page_data.get("image_base64")
        if not image_base64:
            return None

        prompt = """Analyze this brand book page in EXTREME detail.

Extract ALL brand guidelines visible on this page:

1. VISUAL IDENTITY:
   - Logo variations (primary, secondary, icon, wordmark)
   - Logo usage rules (clear space, minimum size, placement)
   - Color palette (primary, secondary, accent colors with HEX codes if visible)
   - Color usage rules (backgrounds, text, accents)
   - Typography (font families, weights, sizes, hierarchy)
   - Typography rules (heading/body usage, letter spacing, line height)

2. IMAGERY & PHOTOGRAPHY:
   - Photography style (lifestyle, product, abstract, etc.)
   - Image treatment (filters, cropping, composition)
   - Illustration style (if applicable)
   - Icon style (outline/filled, rounded/sharp, stroke weight)

3. VISUAL ASSETS (CRITICAL - Describe ALL visual elements visible):
   - Brand characters or mascots (describe appearance, personality, usage)
   - Icons and icon sets (describe style, when to use each)
   - Illustrations (describe style, subject matter, color treatment)
   - Patterns and textures (geometric, organic, abstract - describe in detail)
   - Decorative elements (shapes, dividers, ornaments)
   - Photography examples (describe style, composition, subject)
   - Graphic elements (badges, stamps, frames, borders)
   - Background treatments (gradients, overlays, textures)

4. LAYOUT & COMPOSITION:
   - Grid system (columns, gutters, margins)
   - Spacing rules (padding, gaps, breathing room)
   - Composition principles (balance, hierarchy, focal points)
   - Page layout examples

5. BRAND MESSAGING:
   - Brand voice description (tone, personality)
   - Writing style guidelines
   - Key messages or taglines
   - Brand values or mission

6. USAGE EXAMPLES:
   - Application examples (business cards, social media, websites)
   - Do's and Don'ts
   - Best practices
   - Common mistakes to avoid

7. ASSET INVENTORY (NEW - List EVERYTHING visual you see):
   - Character/mascot names and descriptions
   - Icon categories and their meanings
   - Pattern/texture names and where they're used
   - Photography subjects and themes
   - Illustration themes and styles

IMPORTANT: If you see brand characters, mascots, custom icons, or unique graphic elements:
- Describe them in DETAIL (colors, shapes, personality, emotions)
- Note where and how they should be used
- Describe their relationship to the brand identity

Return detailed JSON with everything you can extract from this page.
Be SPECIFIC - include measurements, exact color codes, specific font names, precise rules, and DETAILED descriptions of ALL visual assets."""

        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.2
            )

            content = response.choices[0].message.content

            # Try to parse as JSON
            try:
                analysis = json.loads(content)
            except:
                # If not JSON, structure the text response
                analysis = {
                    "page_number": page_num,
                    "raw_analysis": content,
                    "extracted": True
                }

            analysis["page_number"] = page_num
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing page {page_num} with vision: {str(e)}")
            return None

    def _synthesize_brand_guidelines(
        self,
        page_analyses: List[Dict[str, Any]],
        text_content: str,
        brand_name: str
    ) -> Dict[str, Any]:
        """
        Synthesize comprehensive brand guidelines from all page analyses and text
        """
        # Check if we have any data to work with
        if not page_analyses and not text_content:
            logger.error("No data available for synthesis - both vision and text extraction failed")
            return self._get_default_guidelines(brand_name)

        # Combine all page analyses
        if page_analyses:
            pages_summary = "\n\n".join([
                f"Page {a.get('page_number', 'N/A')}:\n{json.dumps(a, indent=2)}"
                for a in page_analyses
            ])
            logger.info(f"Using vision analysis from {len(page_analyses)} pages")
        else:
            pages_summary = "No visual analysis available - using text content only"
            logger.warning("No vision analysis available, falling back to text-only")

        # Truncate text if too long
        text_summary = text_content[:15000] if len(text_content) > 15000 else text_content
        logger.info(f"Using {len(text_summary)} characters of text content")

        if not text_summary and not page_analyses:
            logger.error("No usable content found in PDF")
            return self._get_default_guidelines(brand_name)

        synthesis_prompt = f"""You are an expert brand strategist analyzing a comprehensive brand book for "{brand_name}".

VISION ANALYSIS OF PAGES:
{pages_summary}

TEXT CONTENT FROM PDF:
{text_summary}

CRITICAL REQUIREMENTS:
1. Extract EVERY element mentioned - colors (ALL shades), fonts (ALL weights/styles), spacing values, patterns
2. Capture the VISUAL STYLE deeply - modern/classic, minimal/ornate, bold/subtle, playful/serious
3. Extract EXACT values whenever possible - hex colors, font names, spacing in px/rem, border radius
4. Identify DESIGN PATTERNS - button styles, card layouts, gradient directions, shadow depths
5. Understand BRAND PERSONALITY - is it tech-forward? Luxury? Playful? Professional? Bold? Elegant?
6. Note IMAGERY PREFERENCES - photography vs illustrations, color vs B&W, abstract vs literal
7. Extract SPACING/LAYOUT RULES - grid systems, margins, padding, gaps between elements
8. Identify ANIMATION/MOTION preferences if mentioned - smooth/snappy, subtle/dramatic
9. Capture DO/DON'T examples with specific details
10. If visual analysis unavailable, extract maximum detail from text content

Synthesize COMPLETE, ACTIONABLE, PIXEL-PERFECT brand guidelines for design generation:

Return comprehensive JSON:
{{
    "brand_name": "{brand_name}",

    "visual_identity": {{
        "logo": {{
            "variations": ["primary", "secondary", "icon", "wordmark"],
            "usage_rules": ["rule1", "rule2"],
            "clear_space": "exact value if provided",
            "minimum_size": "exact pixel/rem value",
            "placement_guidelines": ["specific position rules"],
            "color_versions": ["full color", "black", "white", "single color"]
        }},
        "colors": {{
            "primary": {{"name": "name", "hex": "#EXACT", "rgb": "rgb(r,g,b)", "usage": "when and where"}},
            "secondary": {{"name": "name", "hex": "#EXACT", "rgb": "rgb(r,g,b)", "usage": "when and where"}},
            "accent": [{{"name": "name", "hex": "#EXACT", "rgb": "rgb(r,g,b)", "usage": "specific use case"}}],
            "neutral": [{{"name": "gray-900/800/etc", "hex": "#EXACT", "usage": "text/backgrounds"}}],
            "semantic": {{
                "success": "#HEX if mentioned",
                "error": "#HEX if mentioned",
                "warning": "#HEX if mentioned",
                "info": "#HEX if mentioned"
            }},
            "gradients": [{{"type": "linear/radial", "colors": ["#HEX1", "#HEX2"], "direction": "degree or position", "usage": "where used"}}],
            "usage_rules": ["specific color pairing rules", "contrast requirements", "background rules"]
        }},
        "typography": {{
            "heading_font": {{"family": "EXACT font name", "weights": [300, 400, 700, 900], "sizes": {{"h1": "px", "h2": "px"}}, "line_height": "value", "letter_spacing": "value"}},
            "body_font": {{"family": "EXACT font name", "weights": [400, 600], "sizes": {{"body": "px", "small": "px"}}, "line_height": "value"}},
            "hierarchy": ["H1: size, weight, usage", "H2: size, weight, usage", "Body: size, weight, usage"],
            "scale": "modular scale if mentioned (1.25, 1.5, etc)",
            "usage_rules": ["when to use each font", "pairing rules"]
        }},
        "spacing": {{
            "base_unit": "4px, 8px, etc - the fundamental spacing unit",
            "scale": ["4px", "8px", "16px", "24px", "32px", "48px", "64px"],
            "margins": "specific margin values",
            "padding": "specific padding values",
            "gaps": "gap between elements"
        }},
        "borders_shadows": {{
            "border_radius": ["sharp (0px)", "subtle (4px)", "rounded (8px)", "pill (999px)"],
            "border_width": "1px, 2px, etc",
            "shadows": [{{"name": "sm/md/lg", "value": "CSS shadow value", "usage": "when to use"}}]
        }}
    }},

    "imagery_guidelines": {{
        "photography_style": "detailed description",
        "composition_rules": ["rule1", "rule2"],
        "image_treatment": ["filter", "cropping", "effects"],
        "subject_matter": "what to photograph",
        "dos": ["do1", "do2"],
        "donts": ["dont1", "dont2"]
    }},

    "layout_system": {{
        "grid": "description of grid system",
        "spacing": {{"margins": "value", "padding": "value", "gaps": "value"}},
        "composition_principles": ["principle1", "principle2"],
        "whitespace_usage": "description"
    }},

    "brand_messaging": {{
        "voice": "description of brand voice",
        "tone": "description of tone",
        "personality": ["trait1", "trait2"],
        "values": ["value1", "value2"],
        "mission": "mission statement",
        "writing_style": ["guideline1", "guideline2"]
    }},

    "design_patterns": {{
        "visual_elements": ["specific decorative elements used"],
        "graphic_devices": ["shapes, lines, dividers used"],
        "patterns": "geometric patterns, textures, background treatments",
        "textures": "smooth/rough, gradients/solid, minimal/detailed",
        "button_styles": [{{"type": "primary/secondary", "background": "#HEX", "text": "#HEX", "border_radius": "px", "padding": "px", "shadow": "value"}}],
        "card_styles": [{{"background": "#HEX or gradient", "border_radius": "px", "shadow": "value", "padding": "px"}}],
        "iconography": "style description - outline/filled, rounded/sharp, stroke weight"
    }},

    "brand_assets": {{
        "characters": [{{
            "name": "character name",
            "description": "detailed physical description - colors, shapes, style",
            "personality": "friendly, playful, professional, etc",
            "usage_context": "when and where to use this character",
            "emotions_poses": ["happy", "excited", "thinking", "etc"],
            "on_page": "page number where found"
        }}],
        "icons": [{{
            "category": "icon category name",
            "style": "outline/filled/duotone, stroke weight, corner radius",
            "examples": ["icon1", "icon2", "icon3"],
            "usage": "when to use these icons",
            "on_page": "page number"
        }}],
        "illustrations": [{{
            "theme": "illustration theme or subject",
            "style": "flat/3D/hand-drawn/geometric",
            "color_treatment": "full color/monochrome/duotone",
            "description": "detailed description of illustration style",
            "usage": "where illustrations are used",
            "on_page": "page number"
        }}],
        "patterns_textures": [{{
            "name": "pattern name",
            "type": "geometric/organic/abstract",
            "description": "detailed description of pattern",
            "colors_used": ["#HEX1", "#HEX2"],
            "usage": "backgrounds, accents, etc",
            "on_page": "page number"
        }}],
        "photography_examples": [{{
            "subject": "what is photographed",
            "style": "lifestyle/product/abstract/etc",
            "composition": "composition rules - rule of thirds, centered, etc",
            "color_grade": "warm/cool/vibrant/muted",
            "description": "detailed description",
            "on_page": "page number"
        }}],
        "graphic_elements": [{{
            "type": "badge/stamp/frame/border/divider",
            "style": "description of visual style",
            "usage": "when and how to use",
            "on_page": "page number"
        }}]
    }},

    "visual_style": {{
        "overall_aesthetic": "modern/classic, minimal/maximal, bold/subtle, playful/serious, tech/organic",
        "mood": "professional, energetic, calm, luxurious, approachable, innovative",
        "design_approach": "flat/skeuomorphic, brutalist/refined, geometric/organic",
        "preferred_layouts": "centered/asymmetric, grid-based/freeform, spacious/compact",
        "animation_style": "smooth/snappy, subtle/dramatic, fast/slow (if mentioned)",
        "graphic_style": "photography-heavy, illustration-based, minimal graphics, data-viz focused"
    }},

    "usage_guidelines": {{
        "dos": ["best practice 1", "best practice 2"],
        "donts": ["mistake to avoid 1", "mistake to avoid 2"],
        "applications": ["business cards", "social media", "website"],
        "examples": "description of good examples"
    }},

    "design_principles": {{
        "key_principles": ["principle1", "principle2"],
        "visual_hierarchy": "how to create hierarchy",
        "balance": "balance guidelines",
        "consistency": "consistency rules"
    }}
}}

Be SPECIFIC and ACTIONABLE. Include all extracted details."""

        try:
            response = self.client.chat.completions.create(
                model=self.text_model,
                messages=[{"role": "user", "content": synthesis_prompt}],
                response_format={"type": "json_object"},
                temperature=0.2
            )

            guidelines = json.loads(response.choices[0].message.content)
            return guidelines

        except Exception as e:
            logger.error(f"Error synthesizing guidelines: {str(e)}")
            return self._get_default_guidelines(brand_name)

    def _store_brand_guidelines(self, org_id: UUID, guidelines: Dict[str, Any]):
        """Store brand guidelines in database for retrieval"""
        try:
            db = get_db()

            # Store as JSON in a brand_guidelines table
            # First check if guidelines exist for this org
            existing = db.fetch_one("""
                SELECT id FROM brand_guidelines WHERE org_id = %s LIMIT 1
            """, (str(org_id),))

            if existing:
                # Update existing record
                db.execute("""
                    UPDATE brand_guidelines
                    SET guidelines = %s, updated_at = NOW()
                    WHERE org_id = %s
                """, (json.dumps(guidelines), str(org_id)))
            else:
                # Insert new record with required fields
                db.execute("""
                    INSERT INTO brand_guidelines (org_id, title, guidelines, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW(), NOW())
                """, (str(org_id), 'Brand Guidelines', json.dumps(guidelines)))

            logger.info(f"Stored brand guidelines for org {org_id}")

        except Exception as e:
            logger.error(f"Error storing brand guidelines: {str(e)}")
            # Non-critical error - guidelines are still returned

    def get_brand_guidelines(self, org_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve stored brand guidelines"""
        try:
            db = get_db()
            result = db.fetch_one(
                "SELECT guidelines FROM brand_guidelines WHERE org_id = %s",
                (str(org_id),)
            )

            if result and result.get("guidelines"):
                guidelines_data = result["guidelines"]
                if isinstance(guidelines_data, str):
                    return json.loads(guidelines_data)
                return guidelines_data

            return None

        except Exception as e:
            logger.error(f"Error retrieving brand guidelines: {str(e)}")
            return None

    def create_generation_prompt_from_guidelines(
        self,
        guidelines: Dict[str, Any],
        user_request: str
    ) -> str:
        """
        Create a DALL-E prompt that follows brand guidelines

        Incorporates:
        - Color palette
        - Photography style
        - Composition rules
        - Visual style
        - Design principles
        """
        visual_identity = guidelines.get("visual_identity", {})
        imagery = guidelines.get("imagery_guidelines", {})
        design_patterns = guidelines.get("design_patterns", {})
        messaging = guidelines.get("brand_messaging", {})

        # Extract colors
        colors = visual_identity.get("colors", {})
        color_palette = []
        if colors.get("primary"):
            color_palette.append(colors["primary"].get("hex", ""))
        if colors.get("secondary"):
            color_palette.append(colors["secondary"].get("hex", ""))
        if colors.get("accent"):
            for accent in colors["accent"][:2]:
                color_palette.append(accent.get("hex", ""))

        color_text = f"Color palette: {', '.join([c for c in color_palette if c])}. " if color_palette else ""

        # Extract photography style
        photo_style = imagery.get("photography_style", "")
        composition = ", ".join(imagery.get("composition_rules", [])[:3])
        composition_text = f"Composition: {composition}. " if composition else ""

        # Extract visual elements
        visual_elements = ", ".join(design_patterns.get("visual_elements", [])[:3])
        elements_text = f"Visual elements: {visual_elements}. " if visual_elements else ""

        # Extract brand personality
        personality = ", ".join(messaging.get("personality", [])[:3])
        personality_text = f"Brand personality: {personality}. " if personality else ""

        # Build prompt
        prompt = (
            f"Subject: {user_request}. "
            f"{photo_style}. "
            f"{color_text}"
            f"{composition_text}"
            f"{elements_text}"
            f"{personality_text}"
            f"Professional photography quality, studio lighting, high resolution. "
            f"CRITICAL: No text, no logos, no watermarks. Clean image ready for brand overlay."
        )

        return prompt

    def _calculate_guideline_confidence(self, guidelines: Dict[str, Any]) -> float:
        """Calculate confidence score based on completeness of guidelines"""
        sections_present = 0
        total_sections = 7

        if guidelines.get("visual_identity"):
            sections_present += 1
        if guidelines.get("imagery_guidelines"):
            sections_present += 1
        if guidelines.get("layout_system"):
            sections_present += 1
        if guidelines.get("brand_messaging"):
            sections_present += 1
        if guidelines.get("design_patterns"):
            sections_present += 1
        if guidelines.get("usage_guidelines"):
            sections_present += 1
        if guidelines.get("design_principles"):
            sections_present += 1

        return sections_present / total_sections

    def _get_default_guidelines(self, brand_name: str) -> Dict[str, Any]:
        """Return minimal default guidelines"""
        return {
            "brand_name": brand_name,
            "visual_identity": {},
            "imagery_guidelines": {},
            "layout_system": {},
            "brand_messaging": {},
            "design_patterns": {},
            "usage_guidelines": {},
            "design_principles": {}
        }


# Singleton instance
brandbook_analyzer = BrandBookAnalyzer()
