"""
Enhanced Data Schemas V2
JSON schemas for brand tokens, layout templates, and design plans
"""
from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass, field, asdict
from enum import Enum
import json


# ============================================================================
# BRAND TOKEN SCHEMAS
# ============================================================================

@dataclass
class ColorToken:
    """Single color token"""
    hex: str
    name: Optional[str] = None
    usage: Optional[str] = None  # "headlines, CTAs", etc.

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ColorPalette:
    """Complete brand color palette"""
    primary: ColorToken
    secondary: ColorToken
    accent: ColorToken
    neutral: Dict[str, str]  # {"black": "#111", "white": "#FFF", ...}
    semantic: Optional[Dict[str, str]] = None  # {"success": "#10B981", ...}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary": self.primary.to_dict(),
            "secondary": self.secondary.to_dict(),
            "accent": self.accent.to_dict(),
            "neutral": self.neutral,
            "semantic": self.semantic or {}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColorPalette':
        return cls(
            primary=ColorToken(**data.get("primary", {"hex": "#4F46E5"})),
            secondary=ColorToken(**data.get("secondary", {"hex": "#7C3AED"})),
            accent=ColorToken(**data.get("accent", {"hex": "#F59E0B"})),
            neutral=data.get("neutral", {"black": "#111111", "white": "#FFFFFF"}),
            semantic=data.get("semantic")
        )


@dataclass
class TypographyToken:
    """Typography configuration"""
    family: str
    weights: List[int]
    sizes: Optional[List[int]] = None
    line_height: Optional[float] = None
    letter_spacing: Optional[float] = None
    scale: Optional[List[int]] = None  # For headings

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class LogoVariant:
    """Single logo variant"""
    name: str  # "full_color", "white", "icon"
    url: str
    background: Optional[str] = None  # "light", "dark"
    format: str = "png"
    dimensions: Optional[Dict[str, int]] = None  # {"w": 400, "h": 100}

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class LogoRules:
    """Logo usage rules"""
    variants: List[LogoVariant]
    min_size_px: int = 128
    clear_space: str = "1x logo height"
    allowed_positions: List[str] = field(default_factory=lambda: ["TL", "TR", "BR"])
    forbidden_backgrounds: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variants": [v.to_dict() for v in self.variants],
            "min_size_px": self.min_size_px,
            "clear_space": self.clear_space,
            "allowed_positions": self.allowed_positions,
            "forbidden_backgrounds": self.forbidden_backgrounds
        }


@dataclass
class LayoutSystem:
    """Layout and spacing system"""
    grid: int = 12
    spacing_scale: List[int] = field(default_factory=lambda: [4, 8, 16, 24, 32, 48, 64])
    border_radius: Dict[str, int] = field(default_factory=lambda: {"sm": 8, "md": 16, "lg": 24})
    shadows: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VoiceProfile:
    """Brand voice and messaging"""
    traits: List[str]  # ["professional", "friendly", "innovative"]
    tone: str  # "confident but approachable"
    vocabulary: Dict[str, List[str]]  # {"prefer": [...], "avoid": [...]}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContentPolicies:
    """Content policies and restrictions"""
    cta_whitelist: List[str]
    forbidden_terms: List[str]
    content_rules: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BrandTokensV2:
    """
    Enhanced brand tokens schema V2
    Complete design system specification
    """
    version: str = "2.0"
    brand_id: Optional[str] = None
    colors: Optional[ColorPalette] = None
    typography: Optional[Dict[str, TypographyToken]] = None
    logo: Optional[LogoRules] = None
    layout: Optional[LayoutSystem] = None
    voice: Optional[VoiceProfile] = None
    policies: Optional[ContentPolicies] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"version": self.version}

        if self.brand_id:
            result["brand_id"] = self.brand_id
        if self.colors:
            result["colors"] = self.colors.to_dict()
        if self.typography:
            result["typography"] = {k: v.to_dict() for k, v in self.typography.items()}
        if self.logo:
            result["logo"] = self.logo.to_dict()
        if self.layout:
            result["layout"] = self.layout.to_dict()
        if self.voice:
            result["voice"] = self.voice.to_dict()
        if self.policies:
            result["policies"] = self.policies.to_dict()

        return result

    def to_json(self) -> str:
        """Export as JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrandTokensV2':
        """Create from dictionary"""
        return cls(
            version=data.get("version", "2.0"),
            brand_id=data.get("brand_id"),
            colors=ColorPalette.from_dict(data["colors"]) if "colors" in data else None,
            typography={
                k: TypographyToken(**v) for k, v in data.get("typography", {}).items()
            } if "typography" in data else None,
            logo=LogoRules(
                variants=[LogoVariant(**v) for v in data["logo"].get("variants", [])],
                **{k: v for k, v in data["logo"].items() if k != "variants"}
            ) if "logo" in data else None,
            layout=LayoutSystem(**data["layout"]) if "layout" in data else None,
            voice=VoiceProfile(**data["voice"]) if "voice" in data else None,
            policies=ContentPolicies(**data["policies"]) if "policies" in data else None
        )

    @classmethod
    def get_default_tokens(cls) -> 'BrandTokensV2':
        """Default tokens for new brands"""
        return cls(
            version="2.0",
            colors=ColorPalette(
                primary=ColorToken(hex="#4F46E5", name="Indigo", usage="headlines, CTAs"),
                secondary=ColorToken(hex="#7C3AED", name="Purple", usage="accents, badges"),
                accent=ColorToken(hex="#F59E0B", name="Amber", usage="urgency, highlights"),
                neutral={
                    "black": "#111111",
                    "white": "#FFFFFF",
                    "gray": ["#F3F4F6", "#D1D5DB", "#6B7280"]
                },
                semantic={
                    "success": "#10B981",
                    "warning": "#F59E0B",
                    "error": "#EF4444",
                    "info": "#3B82F6"
                }
            ),
            typography={
                "heading": TypographyToken(
                    family="Inter",
                    weights=[700, 800, 900],
                    scale=[72, 56, 40, 32],
                    line_height=1.2,
                    letter_spacing=-0.02
                ),
                "body": TypographyToken(
                    family="Inter",
                    weights=[400, 500, 600],
                    sizes=[16, 18, 20],
                    line_height=1.5
                )
            },
            logo=LogoRules(
                variants=[],
                min_size_px=128,
                clear_space="1x logo height",
                allowed_positions=["TL", "TR", "BR"]
            ),
            layout=LayoutSystem(
                grid=12,
                spacing_scale=[4, 8, 16, 24, 32, 48, 64],
                border_radius={"sm": 8, "md": 16, "lg": 24}
            ),
            voice=VoiceProfile(
                traits=["professional", "friendly", "innovative"],
                tone="confident but approachable",
                vocabulary={
                    "prefer": ["empower", "transform", "streamline"],
                    "avoid": ["revolutionary", "game-changing", "disrupt"]
                }
            ),
            policies=ContentPolicies(
                cta_whitelist=["Get Started", "Learn More", "Try Free", "Join Now"],
                forbidden_terms=["guaranteed", "miraculous", "cheap"],
                content_rules=[
                    "Always include a clear value proposition",
                    "Use data/numbers when possible",
                    "Avoid superlatives without proof"
                ]
            )
        )


# ============================================================================
# LAYOUT TEMPLATE SCHEMAS
# ============================================================================

class SlotType(str, Enum):
    """Types of layout slots"""
    IMAGE = "image"
    TEXT = "text"
    SHAPE = "shape"
    BUTTON = "button"
    GRADIENT = "gradient"


@dataclass
class SlotArea:
    """Grid area definition"""
    x: int  # Starting column (0-indexed)
    y: int  # Starting row
    w: int  # Width in columns
    h: int  # Height in rows

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class LayoutSlot:
    """Single slot in a layout template"""
    id: str  # "headline", "cta", "logo", etc.
    type: SlotType
    layer: int  # Z-index (0 = background)
    area: Any  # SlotArea or "full"

    # Slot-specific properties
    fit: Optional[str] = None  # "cover", "contain" for images
    filters: Optional[List[str]] = None  # CSS filters
    gradient: Optional[str] = None  # For gradient slots
    font_size: Optional[str] = None  # CSS size or clamp()
    font_weight: Optional[int] = None
    color: Optional[str] = None
    align: Optional[str] = None  # "left", "center", "right"
    effects: Optional[List[str]] = None  # ["drop-shadow", "text-outline"]
    shape: Optional[str] = None  # "circle", "rectangle"
    background: Optional[str] = None  # Color or "primary", "accent"
    text: Optional[Dict[str, Any]] = None  # For shapes with text
    border_radius: Optional[int] = None
    opacity: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "type": self.type.value,
            "layer": self.layer,
            "area": self.area.to_dict() if isinstance(self.area, SlotArea) else self.area
        }

        # Add optional properties
        for key in ["fit", "filters", "gradient", "font_size", "font_weight", "color",
                    "align", "effects", "shape", "background", "text", "border_radius", "opacity"]:
            value = getattr(self, key, None)
            if value is not None:
                result[key] = value

        return result


@dataclass
class LayoutRules:
    """Layout validation rules"""
    text_contrast_min: float = 4.5
    logo_clearance: str = "1x"
    cta_prominence: str = "must be largest button"
    safe_zones: List[str] = field(default_factory=lambda: ["top 10%", "bottom 10%"])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LayoutTemplate:
    """
    Complete layout template specification
    Defines how content slots are arranged
    """
    id: str
    name: str
    description: str
    aspect_ratios: List[str]  # ["1x1", "4x5"]
    channels: List[str]  # ["ig", "fb", "linkedin"]
    slots: List[LayoutSlot]
    rules: LayoutRules

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "aspect_ratios": self.aspect_ratios,
            "channels": self.channels,
            "slots": [slot.to_dict() for slot in self.slots],
            "rules": self.rules.to_dict()
        }

    def to_json(self) -> str:
        """Export as JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayoutTemplate':
        """Create from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            aspect_ratios=data["aspect_ratios"],
            channels=data["channels"],
            slots=[
                LayoutSlot(
                    id=s["id"],
                    type=SlotType(s["type"]),
                    layer=s["layer"],
                    area=SlotArea(**s["area"]) if isinstance(s["area"], dict) else s["area"],
                    **{k: v for k, v in s.items() if k not in ["id", "type", "layer", "area"]}
                )
                for s in data["slots"]
            ],
            rules=LayoutRules(**data.get("rules", {}))
        )

    @classmethod
    def get_hero_badge_cta_template(cls) -> 'LayoutTemplate':
        """Default template: Hero with badge and CTA"""
        return cls(
            id="hero_badge_cta_v1",
            name="Hero with Badge and CTA",
            description="Large headline with promotional badge and strong CTA",
            aspect_ratios=["1x1", "4x5"],
            channels=["ig", "fb"],
            slots=[
                LayoutSlot(
                    id="background",
                    type=SlotType.IMAGE,
                    layer=0,
                    area="full",
                    fit="cover",
                    filters=["brightness(0.9)"]
                ),
                LayoutSlot(
                    id="headline",
                    type=SlotType.TEXT,
                    layer=2,
                    area=SlotArea(x=1, y=5, w=10, h=2),
                    font_size="clamp(60px, 8vw, 140px)",
                    font_weight=800,
                    color="#FFFFFF",
                    align="center",
                    effects=["drop-shadow"]
                ),
                LayoutSlot(
                    id="subhead",
                    type=SlotType.TEXT,
                    layer=2,
                    area=SlotArea(x=1, y=8, w=10, h=1),
                    font_size="clamp(24px, 3vw, 60px)",
                    color="#FFFFFF",
                    align="center"
                ),
                LayoutSlot(
                    id="badge",
                    type=SlotType.SHAPE,
                    layer=3,
                    area=SlotArea(x=8, y=2, w=3, h=2),
                    shape="circle",
                    background="accent",
                    text={"content": "30% OFF", "size": 32, "weight": 700}
                ),
                LayoutSlot(
                    id="cta",
                    type=SlotType.BUTTON,
                    layer=3,
                    area=SlotArea(x=2, y=10, w=8, h=1),
                    background="primary",
                    color="#FFFFFF",
                    border_radius=16,
                    font_size="48px",
                    font_weight=700
                ),
                LayoutSlot(
                    id="logo",
                    type=SlotType.IMAGE,
                    layer=4,
                    area=SlotArea(x=10, y=0, w=2, h=2),
                    fit="contain",
                    opacity=0.95
                )
            ],
            rules=LayoutRules(
                text_contrast_min=4.5,
                logo_clearance="1x",
                cta_prominence="must be largest button",
                safe_zones=["top 10%", "bottom 10%"]
            )
        )


# ============================================================================
# DESIGN PLAN SCHEMAS (Enhanced from existing)
# ============================================================================

@dataclass
class DesignPlanV2:
    """Enhanced design plan with more metadata"""
    # Content
    headline: str
    subhead: str
    cta_text: str
    visual_concept: str

    # Platform
    channel: Literal["ig", "fb", "linkedin", "twitter"]
    aspect_ratio: Literal["1x1", "4x5", "9x16", "16x9"]

    # Style
    palette_mode: Literal["primary", "secondary", "accent", "mono"]
    background_style: str  # DALL-E prompt
    logo_position: Literal["TL", "TR", "BR", "BL"]

    # Optional
    product_image_needed: bool = False
    reasoning: Optional[str] = None

    # New in V2
    layout_template_id: Optional[str] = None
    mood: Optional[str] = None  # "urgent", "elegant", "fun"
    target_audience: Optional[str] = None  # "B2B", "B2C"
    campaign_context: Optional[str] = None  # "Black Friday", "Product Launch"

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DesignPlanV2':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


# ============================================================================
# QUALITY SCORE SCHEMAS
# ============================================================================

@dataclass
class ScoreCategory:
    """Single quality score category"""
    score: int  # 0-100
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QualityScore:
    """Complete quality score for a design"""
    overall_score: int  # 0-100
    readability: ScoreCategory
    brand_consistency: ScoreCategory
    composition: ScoreCategory
    impact: ScoreCategory
    accessibility: ScoreCategory
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "breakdown": {
                "readability": self.readability.to_dict(),
                "brand_consistency": self.brand_consistency.to_dict(),
                "composition": self.composition.to_dict(),
                "impact": self.impact.to_dict(),
                "accessibility": self.accessibility.to_dict()
            },
            "suggestions": self.suggestions
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def load_brand_tokens_from_json(json_path: str) -> BrandTokensV2:
    """Load brand tokens from JSON file"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return BrandTokensV2.from_dict(data)


def load_layout_template_from_json(json_path: str) -> LayoutTemplate:
    """Load layout template from JSON file"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return LayoutTemplate.from_dict(data)


def save_to_json(obj: Any, json_path: str) -> None:
    """Save dataclass to JSON file"""
    with open(json_path, 'w') as f:
        if hasattr(obj, 'to_dict'):
            json.dump(obj.to_dict(), f, indent=2)
        else:
            json.dump(asdict(obj), f, indent=2)
