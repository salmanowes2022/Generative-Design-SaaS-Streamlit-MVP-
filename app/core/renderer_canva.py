"""
Canva Renderer
Create designs via Canva Connect API using templates with strict placeholder contract
Replaces manual overlay system with native Canva rendering
"""
from typing import Dict, Any, Optional, List
import requests
import time
from uuid import UUID
from app.core.brand_brain import BrandTokens
from app.infra.db import db
from app.infra.config import settings
from app.infra.logging import get_logger

logger = get_logger(__name__)


class CanvaRenderer:
    """
    Native Canva rendering engine
    Creates designs using Canva Connect API (Autofill)
    """

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Canva renderer

        Args:
            access_token: Canva OAuth2 access token (or set via environment)
        """
        self.api_base = settings.CANVA_API_BASE

        self.access_token = access_token
        self.session = requests.Session()
        if self.access_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            })

    # Template placeholder contract
    PLACEHOLDER_HEADLINE = "HEADLINE"
    PLACEHOLDER_SUBHEAD = "SUBHEAD"
    PLACEHOLDER_CTA = "CTA_TEXT"
    PLACEHOLDER_PRODUCT_IMAGE = "PRODUCT_IMAGE"
    PLACEHOLDER_BG_IMAGE = "BG_IMAGE"
    PLACEHOLDER_PALETTE = "PALETTE_MODE"

    def set_access_token(self, access_token: str):
        """Update access token after OAuth2 flow"""
        self.access_token = access_token
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}"
        })

    def create_design(
        self,
        template_id: str,
        content: Dict[str, Any],
        tokens: BrandTokens,
        org_id: UUID,
        asset_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Create design in Canva using template + autofill

        Args:
            template_id: Canva template ID (from tokens.templates)
            content: Design content with keys:
                - headline: str (max 7 words)
                - subhead: str (max 16 words)
                - cta_text: str (must be in whitelist)
                - product_image_url: str (optional)
                - bg_image_url: str (from AI generation)
                - palette_mode: str (primary|secondary|accent|mono)
            tokens: Brand design tokens
            org_id: Organization ID
            asset_id: Asset ID for tracking (optional)

        Returns:
            {
                "success": bool,
                "design_id": str,
                "design_url": str,
                "export_url": str,
                "thumbnail_url": str
            }
        """
        try:
            if not self.access_token:
                raise ValueError("Canva access token not set. Complete OAuth2 flow first.")

            logger.info(f"Creating Canva design with template {template_id}")

            # Validate content
            self._validate_content(content, tokens)

            # Prepare autofill data
            autofill_data = self._prepare_autofill_data(content, tokens)

            # Create design from template
            design = self._create_from_template(template_id, autofill_data)

            design_id = design["id"]
            design_url = design["urls"]["edit_url"]

            logger.info(f"Canva design created: {design_id}")

            # Export design as PNG
            export_url = self._export_design(design_id, format="png")

            # Get thumbnail
            thumbnail_url = design.get("thumbnail", {}).get("url", export_url)

            # Save to database
            if asset_id:
                self._save_canva_metadata(asset_id, design_id, design_url, export_url)

            return {
                "success": True,
                "design_id": design_id,
                "design_url": design_url,
                "export_url": export_url,
                "thumbnail_url": thumbnail_url
            }

        except Exception as e:
            logger.error(f"Canva design creation error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "design_id": None,
                "design_url": None,
                "export_url": None
            }

    def _validate_content(self, content: Dict[str, Any], tokens: BrandTokens):
        """
        Validate content against brand constraints

        Args:
            content: Design content
            tokens: Brand tokens with constraints

        Raises:
            ValueError: If content violates constraints
        """
        # Validate headline length
        headline = content.get("headline", "")
        headline_words = len(headline.split())
        if headline_words > 7:
            raise ValueError(f"Headline too long: {headline_words} words (max 7)")

        # Validate subhead length
        subhead = content.get("subhead", "")
        subhead_words = len(subhead.split())
        if subhead_words > 16:
            raise ValueError(f"Subhead too long: {subhead_words} words (max 16)")

        # Validate CTA against whitelist
        cta_text = content.get("cta_text", "")
        cta_whitelist = tokens.cta_whitelist or []
        if cta_text and cta_whitelist and cta_text not in cta_whitelist:
            raise ValueError(f"CTA '{cta_text}' not in whitelist: {cta_whitelist}")

        # Validate palette mode
        palette_mode = content.get("palette_mode", "primary")
        valid_modes = ["primary", "secondary", "accent", "mono"]
        if palette_mode not in valid_modes:
            raise ValueError(f"Invalid palette mode: {palette_mode} (must be one of {valid_modes})")

        # Validate required fields
        if not content.get("bg_image_url"):
            raise ValueError("Background image URL required")

        logger.info("Content validation passed")

    def _prepare_autofill_data(self, content: Dict[str, Any], tokens: BrandTokens) -> Dict[str, Any]:
        """
        Prepare Canva autofill data following template contract

        Args:
            content: Design content
            tokens: Brand tokens

        Returns:
            Autofill data matching Canva API format
        """
        # Map palette mode to colors
        palette_mode = content.get("palette_mode", "primary")
        color_mapping = {
            "primary": tokens.color.get("primary", "#4F46E5"),
            "secondary": tokens.color.get("secondary", "#7C3AED"),
            "accent": tokens.color.get("accent", "#EC4899"),
            "mono": tokens.color.get("text", "#000000")
        }
        primary_color = color_mapping[palette_mode]

        # Build autofill data
        autofill_data = {
            "data": {
                self.PLACEHOLDER_HEADLINE: {
                    "type": "text",
                    "text": content.get("headline", "")
                },
                self.PLACEHOLDER_SUBHEAD: {
                    "type": "text",
                    "text": content.get("subhead", "")
                },
                self.PLACEHOLDER_CTA: {
                    "type": "text",
                    "text": content.get("cta_text", "Learn More")
                },
                self.PLACEHOLDER_BG_IMAGE: {
                    "type": "image",
                    "image_url": content.get("bg_image_url")
                },
                "PRIMARY_COLOR": {
                    "type": "color",
                    "value": primary_color
                }
            }
        }

        # Add optional product image
        if content.get("product_image_url"):
            autofill_data["data"][self.PLACEHOLDER_PRODUCT_IMAGE] = {
                "type": "image",
                "image_url": content["product_image_url"]
            }

        return autofill_data

    def _create_from_template(self, template_id: str, autofill_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create design from template using Canva API

        Args:
            template_id: Canva template ID
            autofill_data: Autofill data

        Returns:
            Design object from Canva API
        """
        try:
            # Canva Connect API - Autofill endpoint
            url = f"{self.api_base}/autofills"

            payload = {
                "brand_template_id": template_id,
                "title": "AI Generated Design",
                "data": autofill_data["data"]
            }

            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()

            # Extract design info from autofill response with safeguards
            job = result.get("job") or {}
            job_id = job.get("id")
            design_obj = result.get("design") or {}
            edit_url = design_obj.get("url", "")

            if not job_id:
                logger.error(f"Canva autofill response missing job id: {result}")
                raise ValueError("Canva autofill response missing job id")

            design = {
                "id": job_id,
                "urls": {
                    "edit_url": edit_url
                },
                "thumbnail": design_obj
            }

            return design

        except requests.exceptions.RequestException as e:
            logger.error(f"Canva API error: {str(e)}")
            resp = getattr(e, 'response', None)
            if resp is not None and hasattr(resp, 'text'):
                logger.error(f"Response: {resp.text}")
            raise ValueError(f"Failed to create Canva design: {str(e)}")

    def _export_design(self, design_id: str, format: str = "png", quality: str = "high") -> str:
        """
        Export design as image using Canva Connect API

        Args:
            design_id: Canva design ID
            format: Export format (png, jpg, pdf)
            quality: Export quality (low, medium, high)

        Returns:
            Export URL
        """
        try:
            url = f"{self.api_base}/exports"

            payload = {
                "design_id": design_id,
                "format": {
                    "type": format
                }
            }

            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()

            export_job = response.json()
            job_id = export_job["job"]["id"]

            # Poll for completion
            export_url = self._poll_export_job(job_id)

            return export_url

        except requests.exceptions.RequestException as e:
            logger.error(f"Canva export error: {str(e)}")
            resp = getattr(e, 'response', None)
            if resp is not None and hasattr(resp, 'text'):
                logger.error(f"Response: {resp.text}")
            raise ValueError(f"Failed to export Canva design: {str(e)}")

    def _poll_export_job(self, job_id: str, max_attempts: int = 30) -> str:
        """
        Poll export job until complete

        Args:
            job_id: Export job ID
            max_attempts: Maximum polling attempts

        Returns:
            Export URL when ready
        """
        url = f"{self.api_base}/exports/{job_id}"

        for attempt in range(max_attempts):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                job_status = response.json()
                status = job_status["job"]["status"]

                if status == "success":
                    export_url = job_status["job"]["url"]
                    logger.info(f"Export complete: {export_url}")
                    return export_url

                elif status == "failed":
                    error = job_status["job"].get("error", {}).get("message", "Unknown error")
                    raise ValueError(f"Export failed: {error}")

                # Still processing, wait and retry
                logger.debug(f"Export in progress... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)

            except requests.exceptions.RequestException as e:
                logger.warning(f"Export polling error: {str(e)}")
                time.sleep(2)

        raise ValueError("Export timeout: Job did not complete in time")

    def _save_canva_metadata(self, asset_id: UUID, design_id: str, design_url: str, export_url: str):
        """
        Save Canva metadata to assets table

        Args:
            asset_id: Asset ID
            design_id: Canva design ID
            design_url: Canva edit URL
            export_url: Export URL
        """
        try:
            db.execute(
                """
                UPDATE assets
                SET canva_design_id = %s,
                    canva_design_url = %s,
                    url = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (design_id, design_url, export_url, str(asset_id))
            )
            logger.info(f"Saved Canva metadata for asset {asset_id}")

        except Exception as e:
            logger.error(f"Failed to save Canva metadata: {str(e)}")

    def get_template_for_channel(self, tokens: BrandTokens, channel: str, aspect_ratio: str) -> Optional[str]:
        """
        Get template ID for channel and aspect ratio

        Args:
            tokens: Brand tokens with template mappings
            channel: Channel name (e.g., "ig", "fb", "linkedin")
            aspect_ratio: Aspect ratio (e.g., "1x1", "4x5", "9x16")

        Returns:
            Template ID or None
        """
        template_key = f"{channel}_{aspect_ratio}"
        template_id = tokens.templates.get(template_key)

        if not template_id:
            logger.warning(f"No template found for {template_key}")
            # Fallback to default square template
            template_id = tokens.templates.get("ig_1x1")

        return template_id

    def list_user_designs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List user's Canva designs using Connect API

        Args:
            limit: Maximum number of designs to return

        Returns:
            List of design objects
        """
        try:
            if not self.access_token:
                raise ValueError("Canva access token not set")

            url = f"{self.api_base}/designs"
            params = {"limit": limit}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            designs = data.get("items", [])

            return designs

        except Exception as e:
            logger.error(f"Failed to list designs: {str(e)}")
            return []

    def list_brand_templates(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List available brand templates

        Args:
            limit: Maximum number of templates to return

        Returns:
            List of brand template objects
        """
        try:
            if not self.access_token:
                raise ValueError("Canva access token not set")

            url = f"{self.api_base}/brand-templates"
            params = {"limit": limit}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            templates = data.get("items", [])

            logger.info(f"Found {len(templates)} brand templates")
            return templates

        except Exception as e:
            logger.error(f"Failed to list brand templates: {str(e)}")
            return []

    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get Canva user profile

        Returns:
            User profile data or None
        """
        try:
            if not self.access_token:
                raise ValueError("Canva access token not set")

            url = f"{self.api_base}/users/me/profile"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            profile = response.json()
            logger.info(f"Retrieved user profile: {profile.get('display_name')}")

            return profile

        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            return None


# OAuth2 helper functions

def get_canva_oauth_url(client_id: str, redirect_uri: str, state: str) -> str:
    """
    Generate Canva OAuth2 authorization URL

    Args:
        client_id: Canva app client ID
        redirect_uri: OAuth redirect URI
        state: Random state for CSRF protection

    Returns:
        Authorization URL
    """
    scope = "design:content:read design:content:write design:meta:read"
    auth_url = (
        f"https://www.canva.com/api/oauth/authorize"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&state={state}"
    )
    return auth_url


def exchange_code_for_token(code: str, client_id: str, client_secret: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access token

    Args:
        code: Authorization code from callback
        client_id: Canva app client ID
        client_secret: Canva app client secret
        redirect_uri: OAuth redirect URI

    Returns:
        {
            "access_token": str,
            "refresh_token": str,
            "expires_in": int,
            "token_type": str
        }
    """
    try:
        url = "https://api.canva.com/oauth/token"

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri
        }

        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()

        token_data = response.json()
        logger.info("Successfully exchanged code for Canva access token")

        return token_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Token exchange error: {str(e)}")
        raise ValueError(f"Failed to get Canva access token: {str(e)}")


def refresh_access_token(refresh_token: str, client_id: str, client_secret: str) -> Dict[str, Any]:
    """
    Refresh Canva access token

    Args:
        refresh_token: Refresh token
        client_id: Canva app client ID
        client_secret: Canva app client secret

    Returns:
        New token data
    """
    try:
        url = "https://api.canva.com/oauth/token"

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret
        }

        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()

        token_data = response.json()
        logger.info("Successfully refreshed Canva access token")

        return token_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise ValueError(f"Failed to refresh Canva access token: {str(e)}")


# Global renderer instance (token set per-user)
canva_renderer = CanvaRenderer()
