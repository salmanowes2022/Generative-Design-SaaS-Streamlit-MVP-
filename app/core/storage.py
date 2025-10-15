"""
Supabase Storage Manager
Handles file uploads and downloads for brand assets and generated images
"""
from typing import Optional, BinaryIO
from supabase import create_client, Client
from app.infra.config import settings
from app.infra.logging import get_logger

logger = get_logger(__name__)


class StorageManager:
    """Supabase storage manager for file uploads and downloads"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Initialize Supabase client with service key for storage operations
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )

        self.buckets = {
            "logos": "brand-logos",
            "fonts": "brand-fonts",
            "assets": "generated-assets"
        }

        self._initialized = True
        logger.info("Supabase storage manager initialized")

    def upload_file(
        self,
        bucket_type: str,
        file_path: str,
        file_data: BinaryIO,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload file to Supabase storage

        Args:
            bucket_type: Type of bucket (logos, fonts, assets)
            file_path: Path within the bucket
            file_data: File data as BinaryIO
            content_type: MIME type (optional)

        Returns:
            Public URL of uploaded file
        """
        try:
            bucket_name = self.buckets.get(bucket_type)
            if not bucket_name:
                raise ValueError(f"Unknown bucket type: {bucket_type}")

            # Read file data
            file_data.seek(0)  # Reset pointer to beginning
            file_bytes = file_data.read()

            # Upload to Supabase
            file_options = {"upsert": "true"}
            if content_type:
                file_options["content-type"] = content_type

            self.supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_bytes,
                file_options=file_options
            )

            # Get public URL
            public_url = self.supabase.storage.from_(bucket_name).get_public_url(file_path)

            logger.info(f"Uploaded file to Supabase storage: {file_path}")
            return public_url

        except Exception as e:
            logger.error(f"Error uploading file to Supabase storage: {str(e)}")
            raise

    def download_file(self, bucket_type: str, file_path: str) -> bytes:
        """
        Download file from Supabase storage
        """
        try:
            bucket_name = self.buckets.get(bucket_type)
            if not bucket_name:
                raise ValueError(f"Unknown bucket type: {bucket_type}")

            # Download from Supabase
            response = self.supabase.storage.from_(bucket_name).download(file_path)
            return response

        except Exception as e:
            logger.error(f"Error downloading file from Supabase storage: {str(e)}")
            return b""

    def delete_file(self, bucket_type: str, file_path: str) -> bool:
        """
        Delete file from Supabase storage
        """
        try:
            bucket_name = self.buckets.get(bucket_type)
            if not bucket_name:
                return False

            # Delete from Supabase
            self.supabase.storage.from_(bucket_name).remove([file_path])
            logger.info(f"Deleted file from Supabase storage: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file from Supabase storage: {str(e)}")
            return False

    def get_public_url(self, bucket_type: str, file_path: str) -> str:
        """
        Get public URL for file in Supabase storage
        """
        bucket_name = self.buckets.get(bucket_type)
        if not bucket_name:
            raise ValueError(f"Unknown bucket type: {bucket_type}")

        return self.supabase.storage.from_(bucket_name).get_public_url(file_path)

    def list_files(self, bucket_type: str, folder_path: str = "") -> list:
        """
        List files in Supabase storage
        """
        try:
            bucket_name = self.buckets.get(bucket_type)
            if not bucket_name:
                return []

            # List files in Supabase
            files = self.supabase.storage.from_(bucket_name).list(folder_path)
            return [f["name"] for f in files]

        except Exception as e:
            logger.error(f"Error listing files from Supabase storage: {str(e)}")
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