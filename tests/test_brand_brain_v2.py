"""
Test Suite for Brand Brain v2
Comprehensive tests for all v2 components
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from PIL import Image
import io

# Import components to test
from app.core.brand_brain import BrandTokens, BrandPolicies, BrandBrain
from app.core.prompt_builder_v2 import PromptBuilderV2
from app.core.ocr_validator import OCRValidator
from app.core.validator_v2 import ValidatorV2
from app.core.logo_engine import LogoEngine
from app.core.renderer_canva import CanvaRenderer
from app.core.planner_v2 import PlannerV2


# Fixtures

@pytest.fixture
def sample_tokens():
    """Sample brand tokens"""
    return BrandTokens(
        color={
            "primary": "#4F46E5",
            "secondary": "#7C3AED",
            "accent": "#EC4899",
            "background": "#FFFFFF",
            "text": "#1F2937",
            "min_contrast": 4.5
        },
        type={
            "heading": {"font": "Inter", "weight": 700, "scale": [32, 24, 20]},
            "body": {"font": "Inter", "weight": 400, "scale": [16, 14]}
        },
        logo={
            "variants": ["light", "dark", "full_color"],
            "min_px": 120,
            "safe_zone_px": 40,
            "allowed_positions": ["top-right", "bottom-right"]
        },
        layout={
            "grid_columns": 12,
            "spacing_unit": 8,
            "border_radius": 8
        },
        templates={
            "ig_1x1": "tmpl_IG_1x1_v1",
            "ig_4x5": "tmpl_IG_4x5_promo_v1",
            "fb_1x1": "tmpl_FB_1x1_v1"
        },
        cta_whitelist=["Get Started", "Learn More", "Try Free", "Shop Now"]
    )


@pytest.fixture
def sample_policies():
    """Sample brand policies"""
    return BrandPolicies(
        voice=["professional", "friendly", "clear", "concise"],
        forbid=["cheap", "discount", "hurry", "limited time"]
    )


@pytest.fixture
def sample_guidelines():
    """Sample brand guidelines from PDF analysis"""
    return {
        "visual_identity": {
            "colors": {
                "primary": "#4F46E5",
                "secondary": "#7C3AED",
                "accent": "#EC4899"
            },
            "typography": {
                "heading": "Inter Bold",
                "body": "Inter Regular"
            },
            "logo": {
                "placement": "top-right or bottom-right",
                "minimum_size": "120px width",
                "safe_zone": "40px clearance on all sides"
            }
        },
        "messaging": {
            "voice": ["professional", "friendly", "clear"],
            "forbidden_terms": ["cheap", "discount"]
        }
    }


# Brand Brain Tests

class TestBrandBrain:
    """Test Brand Brain core functionality"""

    def test_default_tokens(self):
        """Test default token generation"""
        tokens = BrandTokens.get_default_tokens()
        assert tokens.color["primary"] is not None
        assert len(tokens.cta_whitelist) > 0
        assert "ig_1x1" in tokens.templates

    def test_extract_tokens_from_guidelines(self, sample_guidelines):
        """Test token extraction from guidelines"""
        brain = BrandBrain()
        tokens = brain.extract_tokens_from_guidelines(sample_guidelines, "TestBrand")

        assert tokens.color["primary"] == "#4F46E5"
        assert tokens.logo["min_px"] == 120
        assert "top-right" in tokens.logo["allowed_positions"]

    def test_extract_policies_from_guidelines(self, sample_guidelines):
        """Test policy extraction from guidelines"""
        brain = BrandBrain()
        policies = brain.extract_policies_from_guidelines(sample_guidelines)

        assert "professional" in policies.voice
        assert "cheap" in policies.forbid

    @patch('app.infra.db.db.execute')
    def test_save_brand_brain(self, mock_db, sample_tokens, sample_policies):
        """Test saving brand brain to database"""
        brain = BrandBrain()
        brand_kit_id = uuid4()

        brain.save_brand_brain(brand_kit_id, sample_tokens, sample_policies)

        mock_db.assert_called_once()
        call_args = mock_db.call_args[0]
        assert "UPDATE brand_kits" in call_args[0]


# Prompt Builder v2 Tests

class TestPromptBuilderV2:
    """Test enhanced prompt builder"""

    def test_build_background_prompt(self, sample_tokens):
        """Test background prompt building"""
        builder = PromptBuilderV2()

        prompt = builder.build_background_prompt(
            user_request="modern office workspace",
            tokens=sample_tokens,
            aspect_ratio="1x1",
            logo_position="top-right"
        )

        assert "modern office workspace" in prompt.lower()
        assert "no text" in prompt.lower()
        assert "no logos" in prompt.lower()

    def test_camera_cues_product(self):
        """Test camera cues for product shots"""
        builder = PromptBuilderV2()

        cues = builder._get_camera_cues("smartphone on desk")

        assert "mm" in cues.lower()
        assert "f/" in cues.lower()

    def test_composition_with_negative_space(self, sample_tokens):
        """Test composition with negative space"""
        builder = PromptBuilderV2()

        composition = builder._get_composition_with_negative_space("top-right", "1x1")

        assert "space" in composition.lower()
        assert "top-right" in composition.lower() or "top right" in composition.lower()

    def test_prompt_length_limit(self, sample_tokens):
        """Test prompt trimming when too long"""
        builder = PromptBuilderV2()

        # Create tokens with verbose color guidance
        verbose_tokens = sample_tokens
        verbose_tokens.color["guidance"] = "Very long guidance " * 100

        prompt = builder.build_background_prompt(
            user_request="test request",
            tokens=verbose_tokens,
            aspect_ratio="1x1",
            logo_position="top-right"
        )

        assert len(prompt) <= 600


# OCR Validator Tests

class TestOCRValidator:
    """Test OCR text detection"""

    def test_validate_clean_background(self):
        """Test validation of clean background (no text)"""
        validator = OCRValidator()

        # Create clean test image
        img = Image.new('RGB', (1024, 1024), color=(100, 150, 200))

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = self._image_to_bytes(img)
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = validator.validate_background("http://test.com/image.png")

            assert result["passed"] is True
            assert result["has_text"] is False

    def test_validate_background_with_text(self):
        """Test validation of background with text"""
        validator = OCRValidator()

        # Would need actual image with text for real test
        # This is a mock test
        with patch.object(validator, 'has_text', return_value=(True, "SALE", 85.0)):
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.content = b"fake_image_data"
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response

                result = validator.validate_background("http://test.com/image.png")

                assert result["passed"] is False
                assert result["has_text"] is True
                assert "SALE" in result["detected_text"]

    def _image_to_bytes(self, img):
        """Helper to convert PIL Image to bytes"""
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()


# Validator v2 Tests

class TestValidatorV2:
    """Test brand compliance validator"""

    def test_calculate_delta_e(self):
        """Test ΔE color difference calculation"""
        validator = ValidatorV2()

        # Same color should have ΔE ≈ 0
        delta_e = validator._calculate_delta_e("#FF0000", "#FF0000")
        assert delta_e < 1.0

        # Very different colors should have high ΔE
        delta_e = validator._calculate_delta_e("#FF0000", "#0000FF")
        assert delta_e > 50

    def test_calculate_contrast_ratio(self):
        """Test WCAG contrast ratio calculation"""
        validator = ValidatorV2()

        # Black on white should have ratio ≈ 21
        ratio = validator._calculate_contrast_ratio("#000000", "#FFFFFF")
        assert ratio > 20

        # Same colors should have ratio ≈ 1
        ratio = validator._calculate_contrast_ratio("#FF0000", "#FF0000")
        assert ratio < 1.5

    def test_validate_policies_forbidden_terms(self, sample_policies):
        """Test policy validation with forbidden terms"""
        validator = ValidatorV2()

        result = validator.validate_policies("Get cheap deals now!", sample_policies)

        assert result["score"] < 100
        assert len(result["violations"]) > 0
        assert any("cheap" in v.lower() for v in result["violations"])

    def test_validate_policies_clean_text(self, sample_policies):
        """Test policy validation with clean text"""
        validator = ValidatorV2()

        result = validator.validate_policies("Learn more about our solution", sample_policies)

        assert result["score"] == 100
        assert len(result["violations"]) == 0

    def test_hex_to_rgb(self):
        """Test hex to RGB conversion"""
        validator = ValidatorV2()

        rgb = validator._hex_to_rgb("#FF0000")
        assert rgb == (255, 0, 0)

        rgb = validator._hex_to_rgb("#00FF00")
        assert rgb == (0, 255, 0)


# Logo Engine Tests

class TestLogoEngine:
    """Test logo placement engine"""

    def test_sample_luminance_dark(self):
        """Test luminance sampling on dark background"""
        engine = LogoEngine()

        # Create dark image
        img = Image.new('RGBA', (1024, 1024), color=(20, 20, 20, 255))

        luminance = engine._sample_luminance(img, (0.5, 0.5), 40)

        assert luminance < 0.3  # Should detect dark

    def test_sample_luminance_light(self):
        """Test luminance sampling on light background"""
        engine = LogoEngine()

        # Create light image
        img = Image.new('RGBA', (1024, 1024), color=(240, 240, 240, 255))

        luminance = engine._sample_luminance(img, (0.5, 0.5), 40)

        assert luminance > 0.7  # Should detect light

    def test_select_variant_dark_background(self):
        """Test variant selection for dark background"""
        engine = LogoEngine()

        logo_variants = {
            "light": "http://logo-light.png",
            "dark": "http://logo-dark.png",
            "full_color": "http://logo-color.png"
        }

        variant = engine._select_variant(0.2, logo_variants)  # Dark background

        assert variant == "light"  # Should select light logo

    def test_select_variant_light_background(self):
        """Test variant selection for light background"""
        engine = LogoEngine()

        logo_variants = {
            "light": "http://logo-light.png",
            "dark": "http://logo-dark.png",
            "full_color": "http://logo-color.png"
        }

        variant = engine._select_variant(0.8, logo_variants)  # Light background

        assert variant == "dark"  # Should select dark logo

    def test_calculate_final_position(self, sample_tokens):
        """Test logo position calculation"""
        engine = LogoEngine()

        # Top-right position
        x, y = engine._calculate_final_position(
            1024, 1024,  # Background size
            120, 60,     # Logo size
            (0.95, 0.05),  # Position ratio
            40           # Safe zone
        )

        # Should be near top-right with safe zone
        assert x > 800
        assert y < 100

    def test_check_safe_zone(self):
        """Test safe zone checking"""
        engine = LogoEngine()

        # Logo within safe zone
        result = engine._check_safe_zone(40, 40, 120, 60, 1024, 1024, 40)
        assert result is True

        # Logo outside safe zone
        result = engine._check_safe_zone(10, 10, 120, 60, 1024, 1024, 40)
        assert result is False


# Canva Renderer Tests

class TestCanvaRenderer:
    """Test Canva API integration"""

    def test_validate_content_headline_length(self, sample_tokens):
        """Test headline length validation"""
        renderer = CanvaRenderer()

        content = {
            "headline": "This is a very long headline with more than seven words total",
            "subhead": "Short subhead",
            "cta_text": "Learn More",
            "bg_image_url": "http://test.com/bg.png",
            "palette_mode": "primary"
        }

        with pytest.raises(ValueError, match="Headline too long"):
            renderer._validate_content(content, sample_tokens)

    def test_validate_content_cta_whitelist(self, sample_tokens):
        """Test CTA whitelist validation"""
        renderer = CanvaRenderer()

        content = {
            "headline": "Test Headline",
            "subhead": "Test subhead",
            "cta_text": "Buy Now!",  # Not in whitelist
            "bg_image_url": "http://test.com/bg.png",
            "palette_mode": "primary"
        }

        with pytest.raises(ValueError, match="not in whitelist"):
            renderer._validate_content(content, sample_tokens)

    def test_validate_content_valid(self, sample_tokens):
        """Test validation of valid content"""
        renderer = CanvaRenderer()

        content = {
            "headline": "Great Product Here",
            "subhead": "Learn more about our amazing solution",
            "cta_text": "Learn More",
            "bg_image_url": "http://test.com/bg.png",
            "palette_mode": "primary"
        }

        # Should not raise
        renderer._validate_content(content, sample_tokens)

    def test_prepare_autofill_data(self, sample_tokens):
        """Test autofill data preparation"""
        renderer = CanvaRenderer()

        content = {
            "headline": "Test Headline",
            "subhead": "Test subhead",
            "cta_text": "Learn More",
            "bg_image_url": "http://test.com/bg.png",
            "palette_mode": "primary",
            "product_image_url": "http://test.com/product.png"
        }

        autofill_data = renderer._prepare_autofill_data(content, sample_tokens)

        assert autofill_data["data"]["HEADLINE"]["text"] == "Test Headline"
        assert autofill_data["data"]["BG_IMAGE"]["image_url"] == "http://test.com/bg.png"
        assert autofill_data["data"]["PRIMARY_COLOR"]["value"] == sample_tokens.color["primary"]


# Planner v2 Tests

class TestPlannerV2:
    """Test planning agent"""

    def test_build_system_prompt(self, sample_tokens, sample_policies):
        """Test system prompt building"""
        planner = PlannerV2()

        prompt = planner._build_system_prompt(sample_tokens, sample_policies)

        assert "7 words" in prompt
        assert "16 words" in prompt
        assert json.dumps(sample_tokens.cta_whitelist) in prompt
        assert "professional" in prompt.lower()

    def test_validate_plan_headline_length(self, sample_tokens):
        """Test plan validation - headline length"""
        planner = PlannerV2()

        plan = {
            "headline": "This is way too long for a headline and will fail",
            "subhead": "Short subhead",
            "cta_text": "Learn More",
            "visual_concept": "Test",
            "channel": "ig",
            "aspect_ratio": "1x1",
            "palette_mode": "primary",
            "background_style": "Test",
            "logo_position": "top-right"
        }

        warnings = planner._validate_plan(plan, sample_tokens, None)

        assert len(warnings) > 0
        assert any("Headline too long" in w for w in warnings)

    def test_validate_plan_cta_whitelist(self, sample_tokens):
        """Test plan validation - CTA whitelist"""
        planner = PlannerV2()

        plan = {
            "headline": "Short Headline",
            "subhead": "Short subhead",
            "cta_text": "Click Here",  # Not in whitelist
            "visual_concept": "Test",
            "channel": "ig",
            "aspect_ratio": "1x1",
            "palette_mode": "primary",
            "background_style": "Test",
            "logo_position": "top-right"
        }

        warnings = planner._validate_plan(plan, sample_tokens, None)

        assert any("not in whitelist" in w for w in warnings)

    def test_validate_plan_valid(self, sample_tokens, sample_policies):
        """Test plan validation - valid plan"""
        planner = PlannerV2()

        plan = {
            "headline": "Great Product",
            "subhead": "Learn about our solution",
            "cta_text": "Learn More",
            "visual_concept": "Modern office workspace",
            "channel": "ig",
            "aspect_ratio": "1x1",
            "palette_mode": "primary",
            "background_style": "Professional photography",
            "logo_position": "top-right"
        }

        warnings = planner._validate_plan(plan, sample_tokens, sample_policies)

        assert len(warnings) == 0

    def test_get_default_aspect_ratio(self):
        """Test default aspect ratio selection"""
        planner = PlannerV2()

        assert planner._get_default_aspect_ratio("ig") == "1x1"
        assert planner._get_default_aspect_ratio("twitter") == "16x9"
        assert planner._get_default_aspect_ratio("unknown") == "1x1"


# Integration Tests

class TestIntegrationWorkflow:
    """Test complete workflow integration"""

    def test_onboarding_to_tokens(self, sample_guidelines):
        """Test: Guidelines → Tokens → Database"""
        brain = BrandBrain()

        # Extract tokens
        tokens = brain.extract_tokens_from_guidelines(sample_guidelines, "TestBrand")
        policies = brain.extract_policies_from_guidelines(sample_guidelines)

        assert tokens.color["primary"] == "#4F46E5"
        assert "professional" in policies.voice

    @patch('openai.chat.completions.create')
    def test_chat_to_plan_workflow(self, mock_openai, sample_tokens, sample_policies):
        """Test: Chat → Plan with validation"""
        planner = PlannerV2()

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "plan": {
                "headline": "New Product",
                "subhead": "Check out our solution",
                "cta_text": "Learn More",
                "visual_concept": "Modern office",
                "channel": "ig",
                "aspect_ratio": "1x1",
                "palette_mode": "primary",
                "background_style": "Professional photo",
                "logo_position": "top-right"
            },
            "reasoning": "Test reasoning"
        })
        mock_openai.return_value = mock_response

        result = planner.chat_to_plan(
            "Create an Instagram post for our new product",
            sample_tokens,
            sample_policies,
            context={"channel": "ig"}
        )

        assert result["success"] is True
        assert result["plan"]["headline"] == "New Product"
        assert len(result["warnings"]) == 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
