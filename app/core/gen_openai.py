"""
OpenAI Image Generation
Integration with DALL-E 3 for AI image generation
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
import requests
import json
import time
from io import BytesIO

from openai import OpenAI
from openai import RateLimitError
from app.core.schemas import JobCreate, Job, JobStatus, Asset, AssetCreate, AspectRatio
from app.infra.config import settings
from app.infra.db import db
from app.core.storage import storage
from app.infra.logging import get_logger


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        from uuid import UUID
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)

logger = get_logger(__name__)


class OpenAIImageGenerator:
    """Handles image generation with OpenAI DALL-E"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.DEFAULT_IMAGE_MODEL

    def _retry_with_exponential_backoff(
        self,
        func,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0
    ):
        """
        Retry a function with exponential backoff for rate limit errors

        Args:
            func: Function to retry
            max_retries: Maximum number of retries
            initial_delay: Initial delay in seconds
            backoff_factor: Multiplier for delay on each retry

        Returns:
            Function result if successful

        Raises:
            Exception if all retries fail
        """
        delay = initial_delay
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return func()
            except RateLimitError as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"Rate limit hit, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    delay *= backoff_factor
                else:
                    logger.error(f"Rate limit exceeded after {max_retries} retries")
                    raise ValueError(
                        f"OpenAI rate limit exceeded. Please wait a few minutes and try again. "
                        f"If this persists, you may have exceeded your API quota."
                    ) from e
            except Exception as e:
                # For non-rate-limit errors, fail immediately
                raise

        # Should never reach here, but just in case
        raise last_exception
    
    def moderate_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Check if prompt passes OpenAI moderation
        
        Args:
            prompt: Prompt to check
        
        Returns:
            Moderation result
        """
        try:
            response = self.client.moderations.create(input=prompt)
            result = response.results[0]
            
            return {
                "flagged": result.flagged,
                "categories": result.categories.model_dump() if hasattr(result.categories, 'model_dump') else {},
                "safe": not result.flagged
            }
            
        except Exception as e:
            logger.error(f"Error in moderation: {str(e)}")
            raise
    
    def create_job(
        self,
        org_id: UUID,
        job_data: JobCreate
    ) -> Job:
        """
        Create a generation job in database
        
        Args:
            org_id: Organization ID
            job_data: Job creation data
        
        Returns:
            Created job
        """
        try:
            import json
            
            result = db.insert("jobs", {
                "org_id": str(org_id),
                "status": JobStatus.QUEUED.value,
                "prompt": job_data.prompt,
                "engine": job_data.engine,
                "params": json.dumps(job_data.params.model_dump(), cls=UUIDEncoder)
            })
            
            logger.info(f"Created job: {result['id']}")
            
            # Handle both string and dict for params
            params_data = result["params"]
            if isinstance(params_data, str):
                params_data = json.loads(params_data)
            
            return Job(
                id=result["id"],
                org_id=result["org_id"],
                status=JobStatus(result["status"]),
                prompt=result["prompt"],
                engine=result["engine"],
                params=params_data,
                created_at=result["created_at"],
                updated_at=result["updated_at"]
            )
            
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise
    
    def update_job_status(
        self,
        job_id: UUID,
        status: JobStatus,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update job status
        
        Args:
            job_id: Job ID
            status: New status
            error_message: Error message if failed
        """
        try:
            update_data = {"status": status.value}
            if error_message:
                update_data["error_message"] = error_message
            
            db.update("jobs", update_data, "id = %s", (str(job_id),))
            
            logger.info(f"Updated job {job_id} status to {status.value}")
            
        except Exception as e:
            logger.error(f"Error updating job status: {str(e)}")
            raise
    
    def generate_images(
        self,
        org_id: UUID,
        job_id: UUID,
        prompt: str,
        aspect_ratio: AspectRatio = AspectRatio.SQUARE,
        num_images: int = 1,
        quality: str = "standard",
        style: str = "vivid"
    ) -> List[Asset]:
        """
        Generate images with DALL-E 3
        
        Args:
            org_id: Organization ID
            job_id: Job ID
            prompt: Image generation prompt
            aspect_ratio: Desired aspect ratio
            num_images: Number of images to generate (1-4)
            quality: Image quality (standard, hd)
            style: Image style (vivid, natural)
        
        Returns:
            List of generated assets
        """
        try:
            # Update job status
            self.update_job_status(job_id, JobStatus.RUNNING)
            
            # Map aspect ratio to size
            size_map = {
                AspectRatio.SQUARE: "1024x1024",
                AspectRatio.PORTRAIT: "1024x1792",
                AspectRatio.STORY: "1024x1792"
            }
            size = size_map.get(aspect_ratio, "1024x1024")
            
            generated_assets = []
            
            # DALL-E 3 generates 1 image per call
            for i in range(min(num_images, 4)):
                logger.info(f"Generating image {i+1}/{num_images} with DALL-E 3")

                # Use retry logic for rate limit handling
                def _generate_image():
                    return self.client.images.generate(
                        model=self.model,
                        prompt=prompt,
                        size=size,
                        quality=quality,
                        style=style,
                        n=1
                    )

                response = self._retry_with_exponential_backoff(_generate_image)
                
                # Get image URL
                image_url = response.data[0].url
                
                # Download and upload to Supabase Storage
                image_data = requests.get(image_url).content
                file_path = f"{org_id}/{job_id}/base_{i+1}.png"
                public_url = storage.upload_file(
                    bucket_type="assets",
                    file_path=file_path,
                    file_data=BytesIO(image_data),
                    content_type="image/png"
                )
                logger.info(f"Generated image uploaded to Supabase: {public_url}")
                
                # Create asset record
                import json
                asset_result = db.insert("assets", {
                    "org_id": str(org_id),
                    "job_id": str(job_id),
                    "base_url": public_url,
                    "aspect_ratio": aspect_ratio.value,
                    "validation": json.dumps({}, cls=UUIDEncoder)
                })
                
                # Handle both string and dict for validation
                validation_data = asset_result["validation"]
                if isinstance(validation_data, str):
                    validation_data = json.loads(validation_data)
                
                asset = Asset(
                    id=asset_result["id"],
                    org_id=asset_result["org_id"],
                    job_id=asset_result["job_id"],
                    base_url=asset_result["base_url"],
                    composed_url=asset_result.get("composed_url"),
                    aspect_ratio=asset_result.get("aspect_ratio"),
                    validation=validation_data,
                    created_at=asset_result["created_at"]
                )
                
                generated_assets.append(asset)

                logger.info(f"Generated and stored asset: {asset.id}")

                # Add delay between generations to avoid rate limits (except for last image)
                if i < min(num_images, 4) - 1:
                    logger.info("Waiting 2 seconds before next generation to avoid rate limits...")
                    time.sleep(2)

            # Update job status to done
            self.update_job_status(job_id, JobStatus.DONE)
            
            return generated_assets
            
        except Exception as e:
            logger.error(f"Error generating images: {str(e)}")
            self.update_job_status(job_id, JobStatus.FAILED, str(e))
            raise
    
    def generate_with_moderation(
        self,
        org_id: UUID,
        job_data: JobCreate
    ) -> Dict[str, Any]:
        """
        Generate images with automatic moderation check
        
        Args:
            org_id: Organization ID
            job_data: Job data
        
        Returns:
            Dict with job and assets
        """
        try:
            # Check moderation first
            moderation = self.moderate_prompt(job_data.prompt)
            
            if not moderation["safe"]:
                logger.warning(f"Prompt flagged by moderation: {job_data.prompt}")
                raise ValueError("Prompt violates content policy")
            
            # Create job
            job = self.create_job(org_id, job_data)
            
            # Generate images
            assets = self.generate_images(
                org_id=org_id,
                job_id=job.id,
                prompt=job_data.prompt,
                aspect_ratio=job_data.params.aspect_ratio,
                num_images=job_data.params.num_images,
                quality=job_data.params.quality,
                style=job_data.params.style
            )
            
            return {
                "job": job,
                "assets": assets,
                "moderation": moderation
            }
            
        except Exception as e:
            logger.error(f"Error in generate_with_moderation: {str(e)}")
            raise


# Global generator instance
image_generator = OpenAIImageGenerator()