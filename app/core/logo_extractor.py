"""
Logo Extractor
Intelligently extracts logo from brand book PDF and applies it to designs
"""
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from io import BytesIO
from PIL import Image
import base64
from openai import OpenAI

from app.infra.config import settings
from app.infra.logging import get_logger
from app.core.storage import storage

logger = get_logger(__name__)


class LogoExtractor:
    """
    Extracts logo from brand book and applies it following brand rules
    """

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def extract_logo_from_pdf_pages(
        self,
        pdf_pages: list,  # List of page images as base64
        brand_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Use GPT-4 Vision to identify and extract logo from brand book pages

        Args:
            pdf_pages: List of PDF pages as base64 images
            brand_name: Brand name to help identify logo

        Returns:
            Dict with logo info and placement rules, or None
        """
        logger.info(f"Searching for {brand_name} logo in {len(pdf_pages)} pages")

        # Check first 5 pages (logo usually on first pages)
        for idx, page_data in enumerate(pdf_pages[:5]):
            image_base64 = page_data.get("image_base64")
            if not image_base64:
                continue

            logger.info(f"Analyzing page {idx + 1} for logo...")

            prompt = f"""Analyze this brand book page for the {brand_name} logo.

TASK 1: Identify if there's a logo on this page.
TASK 2: If found, describe:
- Logo position (top-left, top-right, center, etc.)
- Logo size relative to page
- Logo style (wordmark, icon, combination)
- Clear space requirements mentioned
- Minimum size requirements mentioned
- Placement rules mentioned
- Background requirements (dark/light)

TASK 3: Most important - describe the logo in EXTREME detail so I can identify it:
- Exact shapes, colors, text
- Visual characteristics
- Distinctive features

Return JSON:
{{
    "logo_found": true/false,
    "logo_description": "detailed description",
    "position": "where on page",
    "style": "wordmark/icon/combination",
    "clear_space": "requirements if mentioned",
    "minimum_size": "requirements if mentioned",
    "placement_rules": ["rule1", "rule2"],
    "preferred_position": "corner/top/bottom based on examples",
    "background_requirements": "light/dark/any"
}}
"""

            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
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
                    max_tokens=1000,
                    temperature=0.2
                )

                content = response.choices[0].message.content

                # Try to parse JSON
                import json
                try:
                    logo_info = json.loads(content)
                except:
                    # Extract from text
                    logo_info = {
                        "logo_found": "logo" in content.lower(),
                        "raw_analysis": content
                    }

                if logo_info.get("logo_found"):
                    logger.info(f"Logo found on page {idx + 1}!")
                    logo_info["page_number"] = idx + 1
                    logo_info["page_image_base64"] = image_base64
                    return logo_info

            except Exception as e:
                logger.error(f"Error analyzing page {idx + 1}: {str(e)}")
                continue

        logger.warning("No logo found in first 5 pages")
        return None

    def extract_logo_image(
        self,
        page_image_base64: str,
        logo_info: Dict[str, Any]
    ) -> Optional[Image.Image]:
        """
        Extract the actual logo image from the page

        Args:
            page_image_base64: Base64 image of page containing logo
            logo_info: Info about logo location

        Returns:
            PIL Image of logo, or None
        """
        try:
            # Decode base64 to PIL Image
            import base64
            img_data = base64.b64decode(page_image_base64)
            page_image = Image.open(BytesIO(img_data))

            # Use GPT-4 Vision to get exact coordinates
            # For MVP, we'll use the whole page and ask GPT to describe location
            # In production, you'd use computer vision to crop exact logo

            logger.info("Logo image extracted from page")
            return page_image

        except Exception as e:
            logger.error(f"Error extracting logo image: {str(e)}")
            return None

    def apply_logo_to_design(
        self,
        base_image_url: str,
        logo_image: Image.Image,
        logo_rules: Dict[str, Any],
        org_id: UUID,
        asset_id: UUID
    ) -> str:
        """
        Apply logo to generated design following brand rules

        Args:
            base_image_url: URL of generated image
            logo_image: Logo as PIL Image
            logo_rules: Brand rules for logo placement
            org_id: Organization ID
            asset_id: Asset ID

        Returns:
            URL of final image with logo
        """
        logger.info("Applying logo to design following brand rules")

        try:
            from PIL import Image
            import requests

            # Download base image
            response = requests.get(base_image_url)
            base_img = Image.open(BytesIO(response.content))

            # Get placement rules
            preferred_position = logo_rules.get("preferred_position", "top-right")
            clear_space = logo_rules.get("clear_space", "20px")

            # Calculate logo size (10% of image width by default)
            logo_width = int(base_img.width * 0.10)
            logo_height = int(logo_image.height * (logo_width / logo_image.width))

            # Resize logo
            logo_resized = logo_image.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

            # Ensure logo has alpha channel
            if logo_resized.mode != 'RGBA':
                logo_resized = logo_resized.convert('RGBA')

            # Convert base to RGBA
            if base_img.mode != 'RGBA':
                base_img = base_img.convert('RGBA')

            # Calculate position based on rules
            margin = 30  # Default margin
            if preferred_position == "top-right":
                x = base_img.width - logo_width - margin
                y = margin
            elif preferred_position == "top-left":
                x = margin
                y = margin
            elif preferred_position == "bottom-right":
                x = base_img.width - logo_width - margin
                y = base_img.height - logo_height - margin
            elif preferred_position == "bottom-left":
                x = margin
                y = base_img.height - logo_height - margin
            else:  # center
                x = (base_img.width - logo_width) // 2
                y = (base_img.height - logo_height) // 2

            # Paste logo
            base_img.paste(logo_resized, (x, y), logo_resized)

            # Save to storage
            output = BytesIO()
            base_img.save(output, format='PNG')
            output.seek(0)

            file_path = f"{org_id}/{asset_id}/with_logo.png"
            final_url = storage.upload_file(
                bucket_type="assets",
                file_path=file_path,
                file_data=output,
                content_type="image/png"
            )

            logger.info(f"Logo applied successfully: {final_url}")
            return final_url

        except Exception as e:
            logger.error(f"Error applying logo: {str(e)}")
            raise

    def get_logo_placement_rules(self, brand_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract logo placement rules from brand intelligence

        Args:
            brand_intelligence: Saved brand intelligence

        Returns:
            Logo placement rules
        """
        visual_id = brand_intelligence.get("visual_identity", {})
        logo_info = visual_id.get("logo", {})

        return {
            "position": logo_info.get("placement_guidelines", ["top-right"])[0] if logo_info.get("placement_guidelines") else "top-right",
            "clear_space": logo_info.get("clear_space", "Standard clear space"),
            "minimum_size": logo_info.get("minimum_size", "10% of image width"),
            "usage_rules": logo_info.get("usage_rules", [])
        }


# Singleton instance
logo_extractor = LogoExtractor()
