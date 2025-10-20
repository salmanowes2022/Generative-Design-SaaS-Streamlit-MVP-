"""
Brand Kit Manager
CRUD operations for brand kits and brand assets
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
import json
class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        from uuid import UUID
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)
from app.core.schemas import (
    BrandKit, BrandKitCreate, BrandAsset, BrandAssetCreate,
    BrandColors, BrandStyle, AssetType
)
from app.infra.db import db
from app.infra.logging import get_logger

logger = get_logger(__name__)


class BrandKitManager:
    """Manages brand kit operations"""
    
    def create_brand_kit(
        self,
        org_id: UUID,
        brand_kit_data: BrandKitCreate
    ) -> BrandKit:
        """
        Create a new brand kit
        
        Args:
            org_id: Organization ID
            brand_kit_data: Brand kit creation data
        
        Returns:
            Created brand kit
        """
        try:
            # Convert Pydantic models to JSONB
            colors_json = brand_kit_data.colors.model_dump()
            style_json = brand_kit_data.style.model_dump()
            
            result = db.insert("brand_kits", {
                "org_id": str(org_id),
                "name": brand_kit_data.name,
                "colors": json.dumps(colors_json, cls=UUIDEncoder),
                "style": json.dumps(style_json, cls=UUIDEncoder)
            })
            
            logger.info(f"Created brand kit: {result['id']}")
            
            # Convert back to Pydantic model
            # Handle both string and dict (psycopg may auto-parse JSONB)
            colors_data = result["colors"]
            if isinstance(colors_data, str):
                colors_data = json.loads(colors_data)
            
            style_data = result["style"]
            if isinstance(style_data, str):
                style_data = json.loads(style_data)
            
            return BrandKit(
                id=result["id"],
                org_id=result["org_id"],
                name=result["name"],
                colors=BrandColors(**colors_data),
                style=BrandStyle(**style_data),
                created_at=result["created_at"]
            )
            
        except Exception as e:
            logger.error(f"Error creating brand kit: {str(e)}")
            raise
    
    def get_brand_kit(self, brand_kit_id: UUID) -> Optional[BrandKit]:
        """
        Get a brand kit by ID
        
        Args:
            brand_kit_id: Brand kit ID
        
        Returns:
            Brand kit or None
        """
        try:
            result = db.fetch_one(
                "SELECT * FROM brand_kits WHERE id = %s",
                (str(brand_kit_id),)
            )
            
            if not result:
                return None
            
            # Handle both string and dict (psycopg may auto-parse JSONB)
            colors_data = result["colors"]
            if isinstance(colors_data, str):
                colors_data = json.loads(colors_data)
            
            style_data = result["style"]
            if isinstance(style_data, str):
                style_data = json.loads(style_data)
            
            return BrandKit(
                id=result["id"],
                org_id=result["org_id"],
                name=result["name"],
                colors=BrandColors(**colors_data),
                style=BrandStyle(**style_data),
                created_at=result["created_at"]
            )
            
        except Exception as e:
            logger.error(f"Error getting brand kit: {str(e)}")
            raise
    
    def get_brand_kits_by_org(self, org_id: UUID) -> List[BrandKit]:
        """
        Get all brand kits for an organization
        
        Args:
            org_id: Organization ID
        
        Returns:
            List of brand kits
        """
        try:
            results = db.fetch_all(
                "SELECT * FROM brand_kits WHERE org_id = %s ORDER BY created_at DESC",
                (str(org_id),)
            )

            brand_kits = []
            for r in results:
                # Handle both string and dict for JSONB columns
                colors_data = r.get("colors") if isinstance(r, dict) else None
                if colors_data is None:
                    logger.error(f"Skipping brand kit - no colors data")
                    continue

                if isinstance(colors_data, str):
                    colors_data = json.loads(colors_data)
                elif isinstance(colors_data, tuple):
                    # This shouldn't happen but handle it
                    logger.error(f"colors_data is tuple: {colors_data}")
                    continue

                style_data = r.get("style") if isinstance(r, dict) else None
                if style_data is None:
                    logger.error(f"Skipping brand kit - no style data")
                    continue

                if isinstance(style_data, str):
                    style_data = json.loads(style_data)
                elif isinstance(style_data, tuple):
                    logger.error(f"style_data is tuple: {style_data}")
                    continue

                try:
                    brand_kits.append(BrandKit(
                        id=r["id"],
                        org_id=r["org_id"],
                        name=r["name"],
                        colors=BrandColors(**colors_data),
                        style=BrandStyle(**style_data),
                        created_at=r["created_at"]
                    ))
                except Exception as e:
                    logger.warning(f"Skipping brand kit '{r.get('name', 'unknown')}': {e}")
                    continue
            
            return brand_kits

        except Exception as e:
            logger.error(f"Error getting brand kits: {str(e)}")
            # If we got at least some brand kits, return them instead of failing completely
            if 'brand_kits' in locals() and brand_kits:
                logger.warning(f"Returning {len(brand_kits)} brand kits despite error")
                return brand_kits
            raise
    
    def update_brand_kit(
        self,
        brand_kit_id: UUID,
        update_data: Dict[str, Any]
    ) -> Optional[BrandKit]:
        """
        Update a brand kit
        
        Args:
            brand_kit_id: Brand kit ID
            update_data: Fields to update
        
        Returns:
            Updated brand kit or None
        """
        try:
            # Convert Pydantic models to JSON if present
            if "colors" in update_data and isinstance(update_data["colors"], BrandColors):
                update_data["colors"] = json.dumps(update_data["colors"].model_dump(), cls=UUIDEncoder)
            
            if "style" in update_data and isinstance(update_data["style"], BrandStyle):
                update_data["style"] = json.dumps(update_data["style"].model_dump(), cls=UUIDEncoder)
            
            result = db.update(
                "brand_kits",
                update_data,
                "id = %s",
                (str(brand_kit_id),)
            )
            
            if not result:
                return None
            
            logger.info(f"Updated brand kit: {brand_kit_id}")
            
            # Handle both string and dict (psycopg may auto-parse JSONB)
            colors_data = result["colors"]
            if isinstance(colors_data, str):
                colors_data = json.loads(colors_data)
            
            style_data = result["style"]
            if isinstance(style_data, str):
                style_data = json.loads(style_data)
            
            return BrandKit(
                id=result["id"],
                org_id=result["org_id"],
                name=result["name"],
                colors=BrandColors(**colors_data),
                style=BrandStyle(**style_data),
                created_at=result["created_at"]
            )
            
        except Exception as e:
            logger.error(f"Error updating brand kit: {str(e)}")
            raise
    
    def delete_brand_kit(self, brand_kit_id: UUID) -> bool:
        """
        Delete a brand kit
        
        Args:
            brand_kit_id: Brand kit ID
        
        Returns:
            True if successful
        """
        try:
            db.execute(
                "DELETE FROM brand_kits WHERE id = %s",
                (str(brand_kit_id),)
            )
            
            logger.info(f"Deleted brand kit: {brand_kit_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting brand kit: {str(e)}")
            raise
    
    # Brand Asset Operations
    
    def add_brand_asset(
        self,
        asset_data: BrandAssetCreate
    ) -> BrandAsset:
        """
        Add a brand asset (logo or font)
        
        Args:
            asset_data: Brand asset creation data
        
        Returns:
            Created brand asset
        """
        try:
            result = db.insert("brand_assets", {
                "brand_kit_id": str(asset_data.brand_kit_id),
                "type": asset_data.type.value,
                "url": asset_data.url,
                "meta": json.dumps(asset_data.meta, cls=UUIDEncoder)
            })
            
            logger.info(f"Added brand asset: {result['id']}")
            
            # Handle both string and dict
            meta_data = result["meta"]
            if isinstance(meta_data, str):
                meta_data = json.loads(meta_data)
            
            return BrandAsset(
                id=result["id"],
                brand_kit_id=result["brand_kit_id"],
                type=AssetType(result["type"]),
                url=result["url"],
                meta=meta_data,
                created_at=result["created_at"]
            )
            
        except Exception as e:
            logger.error(f"Error adding brand asset: {str(e)}")
            raise
    
    def get_brand_assets(
        self,
        brand_kit_id: UUID,
        asset_type: Optional[AssetType] = None
    ) -> List[BrandAsset]:
        """
        Get brand assets for a kit
        
        Args:
            brand_kit_id: Brand kit ID
            asset_type: Filter by asset type (optional)
        
        Returns:
            List of brand assets
        """
        try:
            if asset_type:
                query = "SELECT * FROM brand_assets WHERE brand_kit_id = %s AND type = %s"
                params = (str(brand_kit_id), asset_type.value)
            else:
                query = "SELECT * FROM brand_assets WHERE brand_kit_id = %s"
                params = (str(brand_kit_id),)
            
            results = db.fetch_all(query, params)
            
            assets = []
            for r in results:
                # Handle both string and dict
                meta_data = r["meta"]
                if isinstance(meta_data, str):
                    meta_data = json.loads(meta_data)
                
                assets.append(BrandAsset(
                    id=r["id"],
                    brand_kit_id=r["brand_kit_id"],
                    type=AssetType(r["type"]),
                    url=r["url"],
                    meta=meta_data,
                    created_at=r["created_at"]
                ))
            
            return assets
            
        except Exception as e:
            logger.error(f"Error getting brand assets: {str(e)}")
            raise
    
    def delete_brand_asset(self, asset_id: UUID) -> bool:
        """
        Delete a brand asset
        
        Args:
            asset_id: Brand asset ID
        
        Returns:
            True if successful
        """
        try:
            db.execute(
                "DELETE FROM brand_assets WHERE id = %s",
                (str(asset_id),)
            )
            
            logger.info(f"Deleted brand asset: {asset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting brand asset: {str(e)}")
            raise


# Global brand kit manager instance
brand_kit_manager = BrandKitManager()