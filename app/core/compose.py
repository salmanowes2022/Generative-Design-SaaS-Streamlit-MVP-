"""
Composition Engine
Deterministic image composition with Pillow for brand overlay
"""
from typing import Optional, Tuple
from uuid import UUID
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont, ImageColor
from app.core.schemas import CompositionPreset, BrandKit, Asset
from app.core.storage import storage
from app.core.brandkit import brand_kit_manager
from app.infra.db import db
from app.infra.logging import get_logger

logger = get_logger(__name__)


class CompositionEngine:
    """Handles deterministic brand overlay on generated images"""
    
    def __init__(self):
        self.default_font_size = 72
        self.logo_max_width_pct = 0.25  # Logo max 25% of image width
        self.padding = 48  # Standard padding in pixels
    
    def download_image(self, url: str) -> Image.Image:
        """
        Download an image from URL

        Args:
            url: Image URL

        Returns:
            PIL Image
        """
        try:
            # Check for mock/placeholder URLs
            if "placeholder.com" in url:
                logger.warning(f"Mock storage detected - creating placeholder image for {url}")
                # Create a simple placeholder image
                img = Image.new('RGB', (1024, 1024), color=(200, 200, 200))
                return img

            response = requests.get(url)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))

        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            raise
    
    def resize_logo(
        self,
        logo: Image.Image,
        max_width: int,
        max_height: Optional[int] = None
    ) -> Image.Image:
        """
        Resize logo maintaining aspect ratio
        
        Args:
            logo: Logo image
            max_width: Maximum width
            max_height: Maximum height (optional)
        
        Returns:
            Resized logo
        """
        # Calculate new size maintaining aspect ratio
        aspect_ratio = logo.width / logo.height
        
        new_width = min(logo.width, max_width)
        new_height = int(new_width / aspect_ratio)
        
        if max_height and new_height > max_height:
            new_height = max_height
            new_width = int(new_height * aspect_ratio)
        
        return logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def compose_top_left_logo_bottom_cta(
        self,
        base_img: Image.Image,
        logo: Optional[Image.Image] = None,
        text: Optional[str] = None,
        font_path: Optional[str] = None,
        text_color: str = "#FFFFFF"
    ) -> Image.Image:
        """
        Preset: Logo top-left, CTA text bottom
        
        Args:
            base_img: Base generated image
            logo: Brand logo (optional)
            text: CTA text (optional)
            font_path: Path to font file (optional)
            text_color: Text color hex
        
        Returns:
            Composed image
        """
        # Convert to RGBA for transparency support
        img = base_img.convert("RGBA")
        
        # Add logo if provided
        if logo:
            logo = logo.convert("RGBA")
            logo_max_width = int(img.width * self.logo_max_width_pct)
            logo = self.resize_logo(logo, logo_max_width)
            
            # Position: top-left with padding
            img.alpha_composite(logo, dest=(self.padding, self.padding))
            logger.info("Added logo at top-left")
        
        # Add text if provided
        if text:
            draw = ImageDraw.Draw(img)
            
            # Load font
            try:
                if font_path:
                    font = ImageFont.truetype(font_path, size=self.default_font_size)
                else:
                    # Use default font
                    font = ImageFont.load_default()
            except Exception as e:
                logger.warning(f"Error loading font: {e}, using default")
                font = ImageFont.load_default()
            
            # Calculate text position (bottom-left with padding)
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            text_x = self.padding
            text_y = img.height - text_height - self.padding - 20
            
            # Draw text with shadow for better visibility
            shadow_offset = 2
            draw.text(
                (text_x + shadow_offset, text_y + shadow_offset),
                text,
                fill="#000000",
                font=font
            )
            draw.text((text_x, text_y), text, fill=text_color, font=font)
            
            logger.info(f"Added text at bottom: {text}")
        
        return img
    
    def compose_center_logo_no_text(
        self,
        base_img: Image.Image,
        logo: Optional[Image.Image] = None
    ) -> Image.Image:
        """
        Preset: Centered logo, no text
        
        Args:
            base_img: Base generated image
            logo: Brand logo
        
        Returns:
            Composed image
        """
        img = base_img.convert("RGBA")
        
        if logo:
            logo = logo.convert("RGBA")
            logo_max_width = int(img.width * 0.4)  # Larger for center placement
            logo = self.resize_logo(logo, logo_max_width)
            
            # Center position
            x = (img.width - logo.width) // 2
            y = (img.height - logo.height) // 2
            
            img.alpha_composite(logo, dest=(x, y))
            logger.info("Added centered logo")
        
        return img
    
    def compose_bottom_right_logo_top_text(
        self,
        base_img: Image.Image,
        logo: Optional[Image.Image] = None,
        text: Optional[str] = None,
        font_path: Optional[str] = None,
        text_color: str = "#FFFFFF"
    ) -> Image.Image:
        """
        Preset: Logo bottom-right, text top
        
        Args:
            base_img: Base generated image
            logo: Brand logo (optional)
            text: Header text (optional)
            font_path: Path to font file (optional)
            text_color: Text color hex
        
        Returns:
            Composed image
        """
        img = base_img.convert("RGBA")
        
        # Add text at top if provided
        if text:
            draw = ImageDraw.Draw(img)
            
            try:
                if font_path:
                    font = ImageFont.truetype(font_path, size=self.default_font_size)
                else:
                    font = ImageFont.load_default()
            except Exception as e:
                logger.warning(f"Error loading font: {e}, using default")
                font = ImageFont.load_default()
            
            # Top-center text
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            
            text_x = (img.width - text_width) // 2
            text_y = self.padding
            
            # Shadow
            draw.text(
                (text_x + 2, text_y + 2),
                text,
                fill="#000000",
                font=font
            )
            draw.text((text_x, text_y), text, fill=text_color, font=font)
            
            logger.info("Added text at top")
        
        # Add logo at bottom-right
        if logo:
            logo = logo.convert("RGBA")
            logo_max_width = int(img.width * self.logo_max_width_pct)
            logo = self.resize_logo(logo, logo_max_width)
            
            x = img.width - logo.width - self.padding
            y = img.height - logo.height - self.padding
            
            img.alpha_composite(logo, dest=(x, y))
            logger.info("Added logo at bottom-right")
        
        return img
    
    def compose_with_preset(
        self,
        asset_id: UUID,
        brand_kit_id: UUID,
        preset: CompositionPreset,
        text: Optional[str] = None,
        logo_url: Optional[str] = None,
        font_url: Optional[str] = None
    ) -> str:
        """
        Compose an asset with brand elements using a preset
        
        Args:
            asset_id: Asset ID
            brand_kit_id: Brand kit ID
            preset: Composition preset
            text: Optional text to overlay
            logo_url: Optional logo URL (if not provided, fetch from brand kit)
            font_url: Optional font URL (if not provided, use default)
        
        Returns:
            URL of composed image
        """
        try:
            # Get asset
            asset_data = db.fetch_one(
                "SELECT * FROM assets WHERE id = %s",
                (str(asset_id),)
            )
            if not asset_data:
                raise ValueError(f"Asset {asset_id} not found")
            
            # Get brand kit
            brand_kit = brand_kit_manager.get_brand_kit(brand_kit_id)
            if not brand_kit:
                raise ValueError(f"Brand kit {brand_kit_id} not found")
            
            # Download base image
            base_img = self.download_image(asset_data["base_url"])
            
            # Download logo if URL provided or fetch from brand kit
            logo = None
            if logo_url:
                logo = self.download_image(logo_url)
            else:
                # Get first logo from brand kit
                from app.core.schemas import AssetType
                logos = brand_kit_manager.get_brand_assets(brand_kit_id, AssetType.LOGO)
                if logos:
                    logo = self.download_image(logos[0].url)
            
            # Get text color from brand kit
            text_color = brand_kit.colors.primary or "#FFFFFF"
            
            # Apply preset
            if preset == CompositionPreset.TOP_LEFT_LOGO_BOTTOM_CTA:
                composed = self.compose_top_left_logo_bottom_cta(
                    base_img, logo, text, font_url, text_color
                )
            elif preset == CompositionPreset.CENTER_LOGO_NO_TEXT:
                composed = self.compose_center_logo_no_text(base_img, logo)
            elif preset == CompositionPreset.BOTTOM_RIGHT_LOGO_TOP_TEXT:
                composed = self.compose_bottom_right_logo_top_text(
                    base_img, logo, text, font_url, text_color
                )
            else:
                raise ValueError(f"Unknown preset: {preset}")
            
            # Convert back to RGB for JPEG
            if composed.mode == "RGBA":
                rgb_img = Image.new("RGB", composed.size, (255, 255, 255))
                rgb_img.paste(composed, mask=composed.split()[3])
                composed = rgb_img
            
            # Save to BytesIO
            output = BytesIO()
            composed.save(output, format="JPEG", quality=95)
            output.seek(0)
            
            # Upload to storage
            org_id = asset_data["org_id"]
            file_path = f"{org_id}/{asset_id}/composed.jpg"
            
            composed_url = storage.upload_file(
                bucket_type="assets",
                file_path=file_path,
                file_data=output,
                content_type="image/jpeg"
            )
            
            # Update asset with composed URL
            db.update(
                "assets",
                {"composed_url": composed_url},
                "id = %s",
                (str(asset_id),)
            )
            
            logger.info(f"Composed asset {asset_id} with preset {preset.value}")
            
            return composed_url
            
        except Exception as e:
            logger.error(f"Error composing image: {str(e)}")
            raise


# Global composition engine instance
composition_engine = CompositionEngine()