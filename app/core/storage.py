"""
Supabase Storage Manager
Handles file uploads and downloads for brand assets and generated images

TEMPORARY: Using mock implementation due to Supabase version issues
"""
from typing import Optional, BinaryIO
import os
from pathlib import Path
from app.infra.config import settings
from app.infra.logging import get_logger

logger = get_logger(__name__)


class StorageManager:
    """Mock storage manager - bypasses Supabase for MVP testing"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.buckets = {
            "logos": "brand-logos",
            "fonts": "brand-fonts",
            "assets": "generated-assets"
        }
        self._initialized = True
        logger.warning("Using MOCK storage manager - files won't be uploaded to Supabase")
    
    def upload_file(
        self,
        bucket_type: str,
        file_path: str,
        file_data: BinaryIO,
        content_type: Optional[str] = None
    ) -> str:
        """
        Mock upload - returns a placeholder URL
        
        For production: This should upload to Supabase storage
        For MVP: Returns a mock URL to bypass storage issues
        """
        logger.warning(f"MOCK: Skipping upload to {bucket_type}/{file_path}")
        
        # Return a placeholder URL
        # In production, this would be the actual Supabase storage URL
        mock_url = f"https://placeholder.com/{bucket_type}/{file_path}"
        
        return mock_url
    
    def download_file(self, bucket_type: str, file_path: str) -> bytes:
        """
        Mock download - returns empty bytes
        """
        logger.warning(f"MOCK: Skipping download from {bucket_type}/{file_path}")
        return b""
    
    def delete_file(self, bucket_type: str, file_path: str) -> bool:
        """
        Mock delete - returns True
        """
        logger.warning(f"MOCK: Skipping delete from {bucket_type}/{file_path}")
        return True
    
    def get_public_url(self, bucket_type: str, file_path: str) -> str:
        """
        Mock get URL - returns placeholder
        """
        return f"https://placeholder.com/{bucket_type}/{file_path}"
    
    def list_files(self, bucket_type: str, folder_path: str = "") -> list:
        """
        Mock list files - returns empty list
        """
        logger.warning(f"MOCK: Skipping list files from {bucket_type}/{folder_path}")
        return []


# Global storage manager instance (singleton)
storage = StorageManager()


# Instructions for enabling real Supabase storage:
"""
TO ENABLE REAL SUPABASE STORAGE:

1. Fix Supabase version compatibility:
   pip uninstall supabase -y
   pip install supabase==2.9.0

2. Replace this file with the original implementation that uses:
   from supabase import create_client, Client
   
3. Uncomment the storage.upload_file() code in:
   - app/core/gen_openai.py (line ~150)
   - app/core/router.py (logo/font uploads)

4. Test with:
   storage.upload_file("logos", "test.png", BytesIO(b"test"), "image/png")
"""