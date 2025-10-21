"""
Configuration management using pydantic-settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Database Configuration
    DATABASE_URL: str
    
    # Stripe Configuration
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_ID: str
    
    # Application Configuration
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "dev-secret-key-change-in-production"
    LOG_LEVEL: str = "INFO"
    
    # Image Generation Defaults
    DEFAULT_IMAGE_MODEL: str = "dall-e-3"
    DEFAULT_IMAGE_SIZE: str = "1024x1024"
    MAX_IMAGES_PER_GENERATION: int = 4
    
    # Credit System
    CREDITS_PER_GENERATION: int = 10
    CREDITS_PER_COMPOSITION: int = 5
    DEFAULT_MONTHLY_CREDITS: int = 300

    # Canva Configuration
    CANVA_CLIENT_ID: Optional[str] = None
    CANVA_CLIENT_SECRET: Optional[str] = None
    CANVA_REDIRECT_URI: Optional[str] = "http://localhost:8501/canva/callback"
    # IMPORTANT: Must use /rest/v1 not /v1 for brand templates endpoint
    CANVA_API_BASE: str = "https://api.canva.com/rest/v1"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"

    @property
    def canva_configured(self) -> bool:
        """Check if Canva credentials are configured"""
        return bool(self.CANVA_CLIENT_ID and self.CANVA_CLIENT_SECRET)


# Global settings instance
settings = Settings()