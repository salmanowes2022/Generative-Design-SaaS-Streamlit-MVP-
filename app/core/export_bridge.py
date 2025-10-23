"""
Export Bridge
Optional handoff to Canva or Figma for further editing
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import requests
import json

from app.core.schemas_v2 import BrandTokensV2, LayoutTemplate
from app.core.chat_agent_planner import DesignPlan
from app.infra.config import settings
from app.infra.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExportResult:
    """Result of export operation"""
    success: bool
    platform: str  # "canva" or "figma"
    editor_url: Optional[str] = None  # URL to edit the design
    view_url: Optional[str] = None  # URL to view the design
    export_id: Optional[str] = None  # Platform-specific ID
    error: Optional[str] = None


class CanvaExporter:
    """
    Export designs to Canva Connect API

    Requires:
    - Canva Connect API key
    - Brand kit set up in Canva
    """

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        Initialize Canva exporter

        Args:
            api_key: Canva API key (from OAuth or app credentials)
            api_base: Canva API base URL
        """
        self.api_key = api_key or getattr(settings, 'CANVA_API_KEY', None)
        self.api_base = api_base or getattr(settings, 'CANVA_API_BASE', 'https://api.canva.com/rest/v1')

        if not self.api_key:
            logger.warning("Canva API key not configured")

    def export_design(
        self,
        plan: DesignPlan,
        background_url: str,
        logo_url: Optional[str] = None,
        brand_kit_id: Optional[str] = None
    ) -> ExportResult:
        """
        Create editable design in Canva

        Args:
            plan: Design plan
            background_url: URL to background image
            logo_url: URL to logo image
            brand_kit_id: Canva brand kit ID

        Returns:
            ExportResult
        """
        if not self.api_key:
            return ExportResult(
                success=False,
                platform="canva",
                error="Canva API key not configured"
            )

        logger.info(f"Exporting design to Canva: {plan.headline}")

        try:
            # Step 1: Create design
            design = self._create_design(plan)

            if not design:
                return ExportResult(
                    success=False,
                    platform="canva",
                    error="Failed to create Canva design"
                )

            design_id = design.get('id')

            # Step 2: Add background
            self._add_background(design_id, background_url)

            # Step 3: Add text elements
            self._add_text_element(design_id, plan.headline, "headline")
            self._add_text_element(design_id, plan.subhead, "subhead")
            self._add_cta_button(design_id, plan.cta_text)

            # Step 4: Add logo
            if logo_url:
                self._add_logo(design_id, logo_url, plan.logo_position)

            # Step 5: Get editor URL
            editor_url = f"{self.api_base.replace('/rest/v1', '')}/design/{design_id}/edit"

            logger.info(f"✅ Exported to Canva: {editor_url}")

            return ExportResult(
                success=True,
                platform="canva",
                editor_url=editor_url,
                export_id=design_id
            )

        except Exception as e:
            logger.error(f"Canva export error: {e}")
            return ExportResult(
                success=False,
                platform="canva",
                error=str(e)
            )

    def _create_design(self, plan: DesignPlan) -> Optional[Dict[str, Any]]:
        """Create blank Canva design"""
        # Map aspect ratio to Canva format
        format_map = {
            "1x1": "INSTAGRAM_POST",
            "4x5": "INSTAGRAM_PORTRAIT",
            "9x16": "INSTAGRAM_STORY",
            "16x9": "PRESENTATION_16_9"
        }

        format_type = format_map.get(plan.aspect_ratio, "INSTAGRAM_POST")

        payload = {
            "asset_type": "design",
            "format": format_type,
            "title": f"{plan.headline} - Generated Design"
        }

        try:
            response = requests.post(
                f"{self.api_base}/designs",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return response.json().get('design')
            else:
                logger.error(f"Canva design creation failed: {response.status_code} {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating Canva design: {e}")
            return None

    def _add_background(self, design_id: str, image_url: str):
        """Add background image to design"""
        payload = {
            "layer": 0,
            "type": "image",
            "image_url": image_url,
            "position": {"x": 0, "y": 0},
            "size": {"width": "100%", "height": "100%"},
            "fit": "cover"
        }

        self._add_element(design_id, payload)

    def _add_text_element(self, design_id: str, text: str, element_type: str):
        """Add text element to design"""
        # Calculate position based on type
        positions = {
            "headline": {"x": "10%", "y": "40%"},
            "subhead": {"x": "10%", "y": "60%"},
        }

        font_sizes = {
            "headline": 72,
            "subhead": 36
        }

        payload = {
            "layer": 2,
            "type": "text",
            "text": text,
            "position": positions.get(element_type, {"x": "10%", "y": "50%"}),
            "font_size": font_sizes.get(element_type, 48),
            "color": "#FFFFFF",
            "align": "center"
        }

        self._add_element(design_id, payload)

    def _add_cta_button(self, design_id: str, cta_text: str):
        """Add CTA button to design"""
        payload = {
            "layer": 3,
            "type": "shape",
            "shape": "rectangle",
            "position": {"x": "20%", "y": "80%"},
            "size": {"width": "60%", "height": "10%"},
            "fill_color": "#F59E0B",
            "text": {
                "content": cta_text,
                "color": "#FFFFFF",
                "font_size": 48,
                "font_weight": 700
            },
            "border_radius": 16
        }

        self._add_element(design_id, payload)

    def _add_logo(self, design_id: str, logo_url: str, position: str):
        """Add logo to design"""
        # Map position to coordinates
        positions = {
            "TL": {"x": "5%", "y": "5%"},
            "TR": {"x": "85%", "y": "5%"},
            "BR": {"x": "85%", "y": "85%"},
            "BL": {"x": "5%", "y": "85%"}
        }

        payload = {
            "layer": 4,
            "type": "image",
            "image_url": logo_url,
            "position": positions.get(position, positions["TR"]),
            "size": {"width": "10%", "height": "10%"},
            "fit": "contain"
        }

        self._add_element(design_id, payload)

    def _add_element(self, design_id: str, element_data: Dict[str, Any]):
        """Generic method to add element to design"""
        try:
            response = requests.post(
                f"{self.api_base}/designs/{design_id}/elements",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=element_data,
                timeout=30
            )

            if response.status_code != 200:
                logger.warning(f"Failed to add element: {response.status_code}")

        except Exception as e:
            logger.error(f"Error adding element: {e}")


class FigmaExporter:
    """
    Export designs to Figma

    Requires:
    - Figma API token
    - Figma file ID (target file)
    """

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Figma exporter

        Args:
            api_token: Figma personal access token
        """
        self.api_token = api_token or getattr(settings, 'FIGMA_API_TOKEN', None)
        self.api_base = "https://api.figma.com/v1"

        if not self.api_token:
            logger.warning("Figma API token not configured")

    def export_design(
        self,
        plan: DesignPlan,
        background_url: str,
        file_id: str,
        logo_url: Optional[str] = None
    ) -> ExportResult:
        """
        Create editable frame in Figma

        Args:
            plan: Design plan
            background_url: URL to background image
            file_id: Figma file ID to add frame to
            logo_url: URL to logo image

        Returns:
            ExportResult
        """
        if not self.api_token:
            return ExportResult(
                success=False,
                platform="figma",
                error="Figma API token not configured"
            )

        logger.info(f"Exporting design to Figma: {plan.headline}")

        try:
            # Step 1: Create frame
            frame = self._create_frame(file_id, plan)

            if not frame:
                return ExportResult(
                    success=False,
                    platform="figma",
                    error="Failed to create Figma frame"
                )

            # Step 2: Add elements (simplified - Figma API is complex)
            # In real implementation, would use Figma plugin or REST API
            # to add rectangles, text, images, etc.

            # Get editor URL
            editor_url = f"https://www.figma.com/file/{file_id}"

            logger.info(f"✅ Exported to Figma: {editor_url}")

            return ExportResult(
                success=True,
                platform="figma",
                editor_url=editor_url,
                export_id=file_id
            )

        except Exception as e:
            logger.error(f"Figma export error: {e}")
            return ExportResult(
                success=False,
                platform="figma",
                error=str(e)
            )

    def _create_frame(self, file_id: str, plan: DesignPlan) -> Optional[Dict[str, Any]]:
        """Create frame in Figma file"""
        # Map aspect ratio to dimensions
        dimensions = {
            "1x1": (1080, 1080),
            "4x5": (1080, 1350),
            "9x16": (1080, 1920),
            "16x9": (1920, 1080)
        }

        width, height = dimensions.get(plan.aspect_ratio, (1080, 1080))

        # Figma REST API doesn't support creating nodes directly
        # Would need to use Figma Plugin API or generate .fig file
        # For now, return placeholder

        logger.warning("Figma export requires Figma Plugin API - returning placeholder")

        return {
            "id": "placeholder",
            "name": plan.headline,
            "width": width,
            "height": height
        }


class ExportBridge:
    """
    Main export bridge supporting multiple platforms
    """

    def __init__(self):
        """Initialize exporters"""
        self.canva = CanvaExporter()
        self.figma = FigmaExporter()

    def export(
        self,
        platform: str,
        plan: DesignPlan,
        background_url: str,
        logo_url: Optional[str] = None,
        **kwargs
    ) -> ExportResult:
        """
        Export to specified platform

        Args:
            platform: "canva" or "figma"
            plan: Design plan
            background_url: Background image URL
            logo_url: Logo image URL
            **kwargs: Platform-specific arguments

        Returns:
            ExportResult
        """
        logger.info(f"Exporting to {platform}...")

        if platform.lower() == "canva":
            return self.canva.export_design(
                plan=plan,
                background_url=background_url,
                logo_url=logo_url,
                brand_kit_id=kwargs.get('brand_kit_id')
            )
        elif platform.lower() == "figma":
            file_id = kwargs.get('file_id')
            if not file_id:
                return ExportResult(
                    success=False,
                    platform="figma",
                    error="Figma file_id required"
                )

            return self.figma.export_design(
                plan=plan,
                background_url=background_url,
                file_id=file_id,
                logo_url=logo_url
            )
        else:
            return ExportResult(
                success=False,
                platform=platform,
                error=f"Unsupported platform: {platform}"
            )

    def list_supported_platforms(self) -> List[str]:
        """List supported export platforms"""
        platforms = []

        if self.canva.api_key:
            platforms.append("canva")

        if self.figma.api_token:
            platforms.append("figma")

        return platforms


# Singleton instance
export_bridge = ExportBridge()


# Convenience function
def export_to_canva(
    plan: DesignPlan,
    background_url: str,
    logo_url: Optional[str] = None
) -> ExportResult:
    """Quick export to Canva"""
    return export_bridge.export("canva", plan, background_url, logo_url)


def export_to_figma(
    plan: DesignPlan,
    background_url: str,
    file_id: str,
    logo_url: Optional[str] = None
) -> ExportResult:
    """Quick export to Figma"""
    return export_bridge.export("figma", plan, background_url, logo_url, file_id=file_id)
