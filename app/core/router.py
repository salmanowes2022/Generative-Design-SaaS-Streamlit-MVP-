"""
Router Module
Orchestrates requests between different components
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from app.core.brandkit import brand_kit_manager
from app.core.prompt_builder import prompt_builder
from app.core.gen_openai import image_generator
from app.core.compose import composition_engine
from app.core.validate import validation_engine
from app.infra.billing import billing_manager
from app.core.schemas import (
    BrandKitCreate, JobCreate, CompositionRequest, Asset, BrandKit
)
from app.infra.logging import get_logger

logger = get_logger(__name__)


class Router:
    """Orchestrates end-to-end workflows"""
    
    def generate_assets_workflow(
        self,
        org_id: UUID,
        brand_kit_id: UUID,
        user_prompt: str,
        job_data: JobCreate
    ) -> Dict[str, Any]:
        """
        Complete workflow: Generate images with brand context
        
        Args:
            org_id: Organization ID
            brand_kit_id: Brand kit to use for prompt building
            user_prompt: User's prompt
            job_data: Job configuration
        
        Returns:
            Dict with job and generated assets
        """
        try:
            # Check credits first
            credits_needed = billing_manager.credits_per_generation * job_data.params.num_images
            
            if not billing_manager.check_credits_available(org_id, credits_needed):
                raise ValueError("Insufficient credits for this operation")
            
            # Get brand kit
            brand_kit = brand_kit_manager.get_brand_kit(brand_kit_id)
            if not brand_kit:
                raise ValueError(f"Brand kit {brand_kit_id} not found")
            
            # Build optimized prompt
            enhanced_prompt = prompt_builder.build_prompt(
                user_prompt=user_prompt,
                brand_kit=brand_kit,
                aspect_ratio=job_data.params.aspect_ratio
            )
            
            # Update job data with enhanced prompt
            job_data.prompt = enhanced_prompt
            
            # Generate images with moderation
            result = image_generator.generate_with_moderation(org_id, job_data)
            
            # Deduct credits on success
            billing_manager.deduct_credits(
                org_id,
                credits_needed,
                f"Generated {len(result['assets'])} images"
            )
            
            logger.info(f"Generated {len(result['assets'])} assets for org {org_id}")
            
            return {
                "job": result["job"],
                "assets": result["assets"],
                "moderation": result["moderation"],
                "credits_used": credits_needed,
                "brand_kit": brand_kit
            }
            
        except Exception as e:
            logger.error(f"Error in generate workflow: {str(e)}")
            raise
    
    def compose_and_validate_workflow(
        self,
        org_id: UUID,
        composition_request: CompositionRequest
    ) -> Dict[str, Any]:
        """
        Complete workflow: Compose image with brand elements and validate
        
        Args:
            org_id: Organization ID
            composition_request: Composition configuration
        
        Returns:
            Dict with composed URL and validation results
        """
        try:
            # Check credits
            if not billing_manager.check_credits_available(org_id, billing_manager.credits_per_composition):
                raise ValueError("Insufficient credits for composition")
            
            # Get brand kit for colors and logos
            brand_kit = brand_kit_manager.get_brand_kit(composition_request.brand_kit_id)
            if not brand_kit:
                raise ValueError(f"Brand kit {composition_request.brand_kit_id} not found")
            
            # Get logo URL if logo_asset_id provided
            logo_url = None
            if composition_request.logo_asset_id:
                from app.core.schemas import AssetType
                logos = brand_kit_manager.get_brand_assets(
                    composition_request.brand_kit_id,
                    AssetType.LOGO
                )
                matching_logo = next((l for l in logos if str(l.id) == str(composition_request.logo_asset_id)), None)
                if matching_logo:
                    logo_url = matching_logo.url
            else:
                # Use first logo from brand kit
                from app.core.schemas import AssetType
                logos = brand_kit_manager.get_brand_assets(
                    composition_request.brand_kit_id,
                    AssetType.LOGO
                )
                if logos:
                    logo_url = logos[0].url
            
            # Get font URL if font_asset_id provided
            font_url = None
            if composition_request.font_asset_id:
                from app.core.schemas import AssetType
                fonts = brand_kit_manager.get_brand_assets(
                    composition_request.brand_kit_id,
                    AssetType.FONT
                )
                matching_font = next((f for f in fonts if str(f.id) == str(composition_request.font_asset_id)), None)
                if matching_font:
                    font_url = matching_font.url
            
            # Compose image
            composed_url = composition_engine.compose_with_preset(
                asset_id=composition_request.asset_id,
                brand_kit_id=composition_request.brand_kit_id,
                preset=composition_request.preset,
                text=composition_request.text,
                logo_url=logo_url,
                font_url=font_url
            )
            
            # Validate composition
            brand_colors = {
                "primary": brand_kit.colors.primary,
                "secondary": brand_kit.colors.secondary,
                "accent": brand_kit.colors.accent
            }
            
            validation_result = validation_engine.validate_composed_asset(
                asset_id=composition_request.asset_id,
                brand_colors=brand_colors,
                logo_url=logo_url
            )
            
            # Deduct credits
            billing_manager.deduct_credits(
                org_id,
                billing_manager.credits_per_composition,
                "Image composition and validation"
            )
            
            logger.info(f"Composed and validated asset {composition_request.asset_id}")
            
            return {
                "composed_url": composed_url,
                "validation": validation_result,
                "credits_used": billing_manager.credits_per_composition
            }
            
        except Exception as e:
            logger.error(f"Error in compose workflow: {str(e)}")
            raise
    
    def get_organization_summary(self, org_id: UUID) -> Dict[str, Any]:
        """
        Get complete organization summary
        
        Args:
            org_id: Organization ID
        
        Returns:
            Summary with usage, assets, and brand kits
        """
        try:
            # Get usage
            usage = billing_manager.get_current_usage(org_id)
            
            # Get brand kits
            brand_kits = brand_kit_manager.get_brand_kits_by_org(org_id)
            
            # Get recent assets
            from app.infra.db import db
            recent_assets = db.fetch_all(
                """
                SELECT * FROM assets
                WHERE org_id = %s
                ORDER BY created_at DESC
                LIMIT 10
                """,
                (str(org_id),)
            )
            
            # Get job stats
            job_stats = db.fetch_one(
                """
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE status = 'done') as completed_jobs,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs
                FROM jobs
                WHERE org_id = %s
                """,
                (str(org_id),)
            )
            
            return {
                "usage": usage,
                "brand_kits_count": len(brand_kits),
                "brand_kits": brand_kits,
                "recent_assets_count": len(recent_assets),
                "recent_assets": recent_assets,
                "job_stats": job_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting org summary: {str(e)}")
            raise
    
    def create_brand_kit_with_assets(
        self,
        org_id: UUID,
        brand_kit_data: BrandKitCreate,
        logo_file: Optional[Any] = None,
        font_file: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Create brand kit and upload assets in one workflow
        
        Args:
            org_id: Organization ID
            brand_kit_data: Brand kit data
            logo_file: Logo file upload (optional)
            font_file: Font file upload (optional)
        
        Returns:
            Created brand kit with asset URLs
        """
        try:
            # Create brand kit
            brand_kit = brand_kit_manager.create_brand_kit(org_id, brand_kit_data)
            
            uploaded_assets = []
            
            # TEMPORARY: Skip file uploads due to Supabase storage issues
            # For MVP testing, brand kits work without uploaded files
            if logo_file:
                logger.warning("MOCK: Logo upload skipped - Supabase storage disabled for MVP")
                # In production, this would upload to Supabase:
                # logo_path = f"{org_id}/{brand_kit.id}/logo.png"
                # logo_url = storage.upload_file(...)
                # Create brand asset record with URL
            
            if font_file:
                logger.warning("MOCK: Font upload skipped - Supabase storage disabled for MVP")
                # In production, this would upload to Supabase:
                # font_path = f"{org_id}/{brand_kit.id}/font.ttf"
                # font_url = storage.upload_file(...)
                # Create brand asset record with URL
            
            logger.info(f"Created brand kit {brand_kit.id} with {len(uploaded_assets)} assets")
            
            return {
                "brand_kit": brand_kit,
                "assets": uploaded_assets
            }
            
        except Exception as e:
            logger.error(f"Error creating brand kit with assets: {str(e)}")
            raise


# Global router instance
router = Router()