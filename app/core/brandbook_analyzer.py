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
            # Step 1: Extract pages from PDF
            pages_data = self._extract_pdf_pages(pdf_file)
            total_pages = len(pages_data)
            logger.info(f"Extracted {total_pages} pages from brand book")

            # Step 2: Analyze each page with GPT-4 Vision
            page_analyses = []
            for idx, page_data in enumerate(pages_data[:20]):  # Limit to 20 pages for cost
                logger.info(f"Analyzing page {idx + 1}/{min(total_pages, 20)}")
                analysis = self._analyze_page_with_vision(page_data, idx + 1)
                if analysis:
                    page_analyses.append(analysis)

            # Step 3: Extract text content for detailed analysis
            text_content = self._extract_text_from_pdf(pdf_file)

            # Step 4: Synthesize comprehensive brand guidelines
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
                "confidence_score": self._calculate_guideline_confidence(brand_guidelines)
            }

        except Exception as e:
            logger.error(f"Error analyzing brand book: {str(e)}")
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
            images = convert_from_bytes(pdf_file.read(), dpi=150)

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

        except ImportError:
            logger.error("pdf2image not installed. Install with: pip install pdf2image")
            # Fallback: Try to extract images another way or skip vision analysis
            return []
        except Exception as e:
            logger.error(f"Error extracting PDF pages: {str(e)}")
            return []

    def _extract_text_from_pdf(self, pdf_file: BytesIO) -> str:
        """Extract all text content from PDF for text analysis"""
        try:
            pdf_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text_content = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_content.append(text)

            return "\n\n".join(text_content)

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
   - Icon style

3. LAYOUT & COMPOSITION:
   - Grid system (columns, gutters, margins)
   - Spacing rules (padding, gaps, breathing room)
   - Composition principles (balance, hierarchy, focal points)
   - Page layout examples

4. BRAND MESSAGING:
   - Brand voice description (tone, personality)
   - Writing style guidelines
   - Key messages or taglines
   - Brand values or mission

5. USAGE EXAMPLES:
   - Application examples (business cards, social media, websites)
   - Do's and Don'ts
   - Best practices
   - Common mistakes to avoid

6. PATTERNS & ELEMENTS:
   - Decorative elements or patterns
   - Graphic devices
   - Shape usage
   - Texture or background styles

Return detailed JSON with everything you can extract from this page.
Be SPECIFIC - include measurements, exact color codes, specific font names, precise rules."""

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
        # Combine all page analyses
        pages_summary = "\n\n".join([
            f"Page {a.get('page_number', 'N/A')}:\n{json.dumps(a, indent=2)}"
            for a in page_analyses
        ])

        # Truncate text if too long
        text_summary = text_content[:10000] if len(text_content) > 10000 else text_content

        synthesis_prompt = f"""You are analyzing a brand book for "{brand_name}".

VISION ANALYSIS OF PAGES:
{pages_summary}

TEXT CONTENT FROM PDF:
{text_summary}

Synthesize COMPLETE, ACTIONABLE brand guidelines:

Return comprehensive JSON:
{{
    "brand_name": "{brand_name}",

    "visual_identity": {{
        "logo": {{
            "variations": ["primary", "secondary", "icon", "wordmark"],
            "usage_rules": ["rule1", "rule2"],
            "clear_space": "description",
            "minimum_size": "description",
            "placement_guidelines": ["guideline1", "guideline2"]
        }},
        "colors": {{
            "primary": {{"name": "name", "hex": "#HEX", "usage": "description"}},
            "secondary": {{"name": "name", "hex": "#HEX", "usage": "description"}},
            "accent": [{{"name": "name", "hex": "#HEX", "usage": "description"}}],
            "usage_rules": ["rule1", "rule2"]
        }},
        "typography": {{
            "heading_font": {{"family": "name", "weights": ["weight"], "usage": "description"}},
            "body_font": {{"family": "name", "weights": ["weight"], "usage": "description"}},
            "hierarchy": ["H1 rules", "H2 rules", "Body rules"],
            "usage_rules": ["rule1", "rule2"]
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
        "visual_elements": ["element1", "element2"],
        "graphic_devices": ["device1", "device2"],
        "patterns": "description of brand patterns",
        "textures": "description of textures/backgrounds"
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
            db.execute("""
                INSERT INTO brand_guidelines (org_id, guidelines, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
                ON CONFLICT (org_id)
                DO UPDATE SET guidelines = EXCLUDED.guidelines, updated_at = NOW()
            """, (str(org_id), json.dumps(guidelines)))

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
