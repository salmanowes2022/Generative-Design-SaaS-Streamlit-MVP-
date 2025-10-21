"""
BrandBook Parser
Extracts brand tokens and policies from uploaded brand books (PDF, DOCX, etc.)
Converts into BrandKit JSON format compatible with brand_brain.py
"""
from typing import Dict, Any, List, Optional, Tuple
import re
from pathlib import Path
from dataclasses import dataclass
import json

# PDF parsing
try:
    import PyPDF2
    import pdfplumber
except ImportError:
    PyPDF2 = None
    pdfplumber = None

# DOCX parsing
try:
    from docx import Document
except ImportError:
    Document = None

# OpenAI for intelligent extraction
import openai
from app.infra.config import settings
from app.infra.logging import get_logger
from app.core.brand_brain import BrandTokens, BrandPolicies

logger = get_logger(__name__)


@dataclass
class BrandBookSection:
    """Represents a parsed section of the brand book"""
    title: str
    content: str
    page_number: Optional[int] = None


class BrandBookParser:
    """
    Intelligent brand book parser that extracts design tokens and policies
    Uses multi-modal approach: regex patterns + GPT-4 understanding
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize parser with OpenAI API key"""
        openai.api_key = api_key or settings.OPENAI_API_KEY
        self.model = "gpt-4-turbo-preview"

        # Pattern matchers for common brand book elements
        self.color_patterns = [
            r'#([0-9A-Fa-f]{6})',  # Hex colors
            r'rgb\((\d+),\s*(\d+),\s*(\d+)\)',  # RGB
            r'(?i)(primary|secondary|accent|brand).*?color.*?[:=]\s*([#\w]+)',
        ]

        self.font_patterns = [
            r'(?i)font.*?[:=]\s*["\']?([A-Za-z\s]+)["\']?',
            r'(?i)typeface.*?[:=]\s*["\']?([A-Za-z\s]+)["\']?',
            r'(?i)(heading|body|display).*?[:=]\s*["\']?([A-Za-z\s]+)["\']?',
        ]

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse brand book file and extract brand kit

        Args:
            file_path: Path to brand book (PDF, DOCX, TXT)

        Returns:
            Structured brand kit data compatible with BrandBrain
        """
        logger.info(f"Parsing brand book: {file_path}")

        path = Path(file_path)

        # Extract raw text based on file type
        if path.suffix.lower() == '.pdf':
            text, sections = self._parse_pdf(file_path)
        elif path.suffix.lower() in ['.docx', '.doc']:
            text, sections = self._parse_docx(file_path)
        elif path.suffix.lower() == '.txt':
            text, sections = self._parse_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        logger.info(f"Extracted {len(text)} characters, {len(sections)} sections")

        # Extract tokens using hybrid approach
        tokens = self._extract_tokens(text, sections)
        policies = self._extract_policies(text, sections)

        return {
            "tokens": tokens.to_dict(),
            "policies": policies.to_dict()
        }

    def _parse_pdf(self, file_path: str) -> Tuple[str, List[BrandBookSection]]:
        """Extract text from PDF using pdfplumber"""
        if not pdfplumber:
            raise ImportError("pdfplumber not installed. Run: pip install pdfplumber")

        full_text = []
        sections = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    full_text.append(text)

                    # Try to detect section headers (bold, larger text, etc.)
                    lines = text.split('\n')
                    for line in lines:
                        if self._is_section_header(line):
                            sections.append(BrandBookSection(
                                title=line.strip(),
                                content="",
                                page_number=page_num
                            ))

        return '\n'.join(full_text), sections

    def _parse_docx(self, file_path: str) -> Tuple[str, List[BrandBookSection]]:
        """Extract text from DOCX"""
        if not Document:
            raise ImportError("python-docx not installed. Run: pip install python-docx")

        doc = Document(file_path)
        full_text = []
        sections = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                full_text.append(text)

                # Detect headings
                if para.style.name.startswith('Heading'):
                    sections.append(BrandBookSection(
                        title=text,
                        content=""
                    ))

        return '\n'.join(full_text), sections

    def _parse_text(self, file_path: str) -> Tuple[str, List[BrandBookSection]]:
        """Extract text from plain text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Simple section detection (lines that are all caps or have markdown headers)
        sections = []
        lines = text.split('\n')
        for line in lines:
            if self._is_section_header(line):
                sections.append(BrandBookSection(
                    title=line.strip(),
                    content=""
                ))

        return text, sections

    def _is_section_header(self, line: str) -> bool:
        """Heuristic to detect section headers"""
        line = line.strip()
        if not line:
            return False

        # All caps (min 3 words)
        if line.isupper() and len(line.split()) >= 2:
            return True

        # Markdown header
        if line.startswith('#'):
            return True

        # Short line with colon
        if ':' in line and len(line) < 50:
            return True

        return False

    def _extract_tokens(self, text: str, sections: List[BrandBookSection]) -> BrandTokens:
        """
        Extract design tokens using GPT-4 + regex patterns

        Priority:
        1. GPT-4 structured extraction (primary)
        2. Regex pattern matching (fallback/validation)
        """
        logger.info("Extracting design tokens with GPT-4...")

        # Use GPT-4 for intelligent extraction
        prompt = f"""
You are a brand design expert analyzing a brand book. Extract the following design tokens from the text below.

Return a JSON object with this exact structure:
{{
  "colors": {{
    "primary": "#HEXCODE",
    "secondary": "#HEXCODE",
    "accent": "#HEXCODE",
    "text": "#HEXCODE",
    "background": "#HEXCODE"
  }},
  "fonts": {{
    "heading": {{"family": "Font Name", "weights": [700]}},
    "body": {{"family": "Font Name", "weights": [400, 600]}}
  }},
  "logo": {{
    "min_size_px": 128,
    "positions": ["TL", "TR", "BR"],
    "safe_zone": "1x"
  }},
  "layout": {{
    "grid_columns": 12,
    "spacing_px": 8,
    "border_radius_px": 16
  }},
  "cta_whitelist": ["Get Started", "Learn More", "Try Free"]
}}

Brand Book Text:
{text[:8000]}  # Limit to 8k chars for token limits

Extract as much as possible. For missing values, use sensible defaults.
"""

        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a brand design token extractor. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content.strip()

            # Extract JSON from markdown code blocks if present
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()

            extracted_data = json.loads(result_text)
            logger.info("Successfully extracted tokens with GPT-4")

        except Exception as e:
            logger.error(f"GPT-4 extraction failed: {e}, falling back to regex")
            extracted_data = self._regex_extract_tokens(text)

        # Convert to BrandTokens
        return self._convert_to_brand_tokens(extracted_data)

    def _regex_extract_tokens(self, text: str) -> Dict[str, Any]:
        """Fallback regex-based extraction"""
        colors = {}
        fonts = {}

        # Extract hex colors
        hex_colors = re.findall(self.color_patterns[0], text)
        if hex_colors:
            colors['primary'] = f"#{hex_colors[0]}"
            if len(hex_colors) > 1:
                colors['secondary'] = f"#{hex_colors[1]}"

        # Extract font names
        for pattern in self.font_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    fonts['heading'] = {"family": matches[0][1], "weights": [700]}
                else:
                    fonts['heading'] = {"family": matches[0], "weights": [700]}
                break

        return {
            "colors": colors,
            "fonts": fonts,
            "logo": {},
            "layout": {},
            "cta_whitelist": []
        }

    def _convert_to_brand_tokens(self, data: Dict[str, Any]) -> BrandTokens:
        """Convert extracted data to BrandTokens object"""

        # Build tokens dict with defaults
        tokens_dict = {
            "color": {
                "primary": data.get("colors", {}).get("primary", "#4F46E5"),
                "secondary": data.get("colors", {}).get("secondary", "#7C3AED"),
                "accent": data.get("colors", {}).get("accent", "#F59E0B"),
                "text": data.get("colors", {}).get("text", "#111111"),
                "background": data.get("colors", {}).get("background", "#FFFFFF"),
                "min_contrast": 4.5
            },
            "type": {
                "heading": data.get("fonts", {}).get("heading", {
                    "family": "Inter",
                    "weights": [700],
                    "scale": [48, 36, 28]
                }),
                "body": data.get("fonts", {}).get("body", {
                    "family": "Inter",
                    "weights": [400],
                    "size": 16
                })
            },
            "logo": {
                "min_px": data.get("logo", {}).get("min_size_px", 128),
                "variants": [{"name": "full", "on": "light", "path": ""}],
                "safe_zone": data.get("logo", {}).get("safe_zone", "1x"),
                "allowed_positions": data.get("logo", {}).get("positions", ["TL", "TR", "BR"])
            },
            "layout": {
                "grid": data.get("layout", {}).get("grid_columns", 12),
                "spacing": data.get("layout", {}).get("spacing_px", 8),
                "radius": data.get("layout", {}).get("border_radius_px", 16)
            },
            "templates": {},
            "cta_whitelist": data.get("cta_whitelist", [
                "Get Started", "Try Free", "Learn More", "Join Now"
            ])
        }

        return BrandTokens.from_dict(tokens_dict)

    def _extract_policies(self, text: str, sections: List[BrandBookSection]) -> BrandPolicies:
        """Extract brand policies (voice, forbidden terms, guidelines)"""
        logger.info("Extracting brand policies with GPT-4...")

        prompt = f"""
You are analyzing a brand book to extract brand voice and content policies.

Return a JSON object with this structure:
{{
  "voice": ["Friendly", "Professional", "Innovative", "Trustworthy"],
  "forbidden_terms": ["cheap", "discount", "limited time"],
  "content_guidelines": ["Use active voice", "Avoid jargon", "Be concise"]
}}

Brand Book Text:
{text[:8000]}

Extract brand personality traits, forbidden words/phrases, and key content guidelines.
"""

        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a brand policy extractor. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            result_text = response.choices[0].message.content.strip()

            # Extract JSON
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()

            policy_data = json.loads(result_text)
            logger.info("Successfully extracted policies")

        except Exception as e:
            logger.error(f"Policy extraction failed: {e}")
            policy_data = {
                "voice": ["Professional", "Trustworthy"],
                "forbidden_terms": [],
                "content_guidelines": []
            }

        # Convert to BrandPolicies (use 'forbid' to match schema)
        policies_dict = {
            "voice": policy_data.get("voice", [])[:5],  # Top 5 traits
            "forbid": policy_data.get("forbidden_terms", [])
        }

        return BrandPolicies.from_dict(policies_dict)


# Convenience function
def parse_brand_book(file_path: str) -> Dict[str, Any]:
    """
    Quick function to parse a brand book file

    Args:
        file_path: Path to brand book (PDF, DOCX, TXT)

    Returns:
        Dict with 'tokens' and 'policies' keys
    """
    parser = BrandBookParser()
    return parser.parse_file(file_path)
