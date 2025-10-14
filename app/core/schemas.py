"""
Core Pydantic schemas for data validation and type safety
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any
from uuid import UUID
from pydantic import BaseModel, Field


# Enums
class AssetType(str, Enum):
    LOGO = "logo"
    FONT = "font"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    FAILED = "failed"
    DONE = "done"


class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class AspectRatio(str, Enum):
    SQUARE = "1:1"
    PORTRAIT = "4:5"
    STORY = "9:16"


# Brand Kit Models
class BrandColors(BaseModel):
    primary: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    accent: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    background: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    text: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class BrandStyle(BaseModel):
    descriptors: List[str] = Field(default_factory=list)
    voice: Optional[str] = None
    mood: Optional[str] = None


class BrandKitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    colors: BrandColors
    style: BrandStyle


class BrandKit(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    colors: BrandColors
    style: BrandStyle
    created_at: datetime

    class Config:
        from_attributes = True


# Brand Asset Models
class BrandAssetCreate(BaseModel):
    brand_kit_id: UUID
    type: AssetType
    url: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class BrandAsset(BaseModel):
    id: UUID
    brand_kit_id: UUID
    type: AssetType
    url: str
    meta: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# Job Models
class JobParams(BaseModel):
    aspect_ratio: AspectRatio = AspectRatio.SQUARE
    num_images: int = Field(default=4, ge=1, le=4)
    quality: str = Field(default="standard")
    style: str = Field(default="vivid")


class JobCreate(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000)
    engine: str = Field(default="dall-e-3")
    params: JobParams = Field(default_factory=JobParams)


class Job(BaseModel):
    id: UUID
    org_id: UUID
    status: JobStatus
    prompt: str
    engine: str
    params: Dict[str, Any]
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Asset Models
class ValidationResult(BaseModel):
    logo_verified: bool = False
    logo_match_score: Optional[float] = None
    color_accuracy: Optional[float] = None
    color_delta_e: Optional[float] = None
    font_applied: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AssetCreate(BaseModel):
    job_id: Optional[UUID] = None
    base_url: str
    aspect_ratio: AspectRatio


class Asset(BaseModel):
    id: UUID
    org_id: UUID
    job_id: Optional[UUID]
    base_url: str
    composed_url: Optional[str]
    aspect_ratio: Optional[str]
    validation: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# Organization Models
class Organization(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# User Models
class User(BaseModel):
    id: UUID
    org_id: UUID
    email: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


# Plan Models
class Plan(BaseModel):
    id: UUID
    name: str
    price_cents: int
    monthly_credits: int
    created_at: datetime

    class Config:
        from_attributes = True


# Subscription Models
class Subscription(BaseModel):
    org_id: UUID
    plan_id: UUID
    stripe_subscription_id: Optional[str]
    current_period_end: Optional[datetime]
    status: SubscriptionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Usage Models
class Usage(BaseModel):
    org_id: UUID
    month: datetime
    credits_used: int

    class Config:
        from_attributes = True


# Composition Models
class CompositionPreset(str, Enum):
    TOP_LEFT_LOGO_BOTTOM_CTA = "top_left_logo_bottom_cta"
    CENTER_LOGO_NO_TEXT = "center_logo_no_text"
    BOTTOM_RIGHT_LOGO_TOP_TEXT = "bottom_right_logo_top_text"


class CompositionRequest(BaseModel):
    asset_id: UUID
    brand_kit_id: UUID
    preset: CompositionPreset = CompositionPreset.TOP_LEFT_LOGO_BOTTOM_CTA
    text: Optional[str] = Field(None, max_length=200)
    logo_asset_id: Optional[UUID] = None
    font_asset_id: Optional[UUID] = None