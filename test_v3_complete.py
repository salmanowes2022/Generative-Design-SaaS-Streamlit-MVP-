"""
Complete Test Suite for Architecture V3
Run this to verify all new modules are working correctly
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from typing import Dict, Any
import json


def print_section(title: str):
    """Print a test section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"      {details}")


def test_imports():
    """Test 1: Verify all modules can be imported"""
    print_section("TEST 1: Module Imports")

    tests = {
        "Brand Parser": lambda: __import__('app.core.brand_parser', fromlist=['BrandParser']),
        "Layout Engine": lambda: __import__('app.core.layout_engine', fromlist=['LayoutEngine']),
        "Contrast Manager": lambda: __import__('app.core.contrast_manager', fromlist=['ContrastManager']),
        "Quality Scorer": lambda: __import__('app.core.quality_scorer', fromlist=['QualityScorer']),
        "Export Bridge": lambda: __import__('app.core.export_bridge', fromlist=['ExportBridge']),
        "Schemas V2": lambda: __import__('app.core.schemas_v2', fromlist=['BrandTokensV2']),
    }

    results = []
    for name, import_func in tests.items():
        try:
            import_func()
            print_result(name, True)
            results.append(True)
        except Exception as e:
            print_result(name, False, str(e))
            results.append(False)

    return all(results)


def test_schemas():
    """Test 2: Verify schema creation"""
    print_section("TEST 2: Schema Creation")

    try:
        from app.core.schemas_v2 import (
            BrandTokensV2, ColorPalette, ColorToken,
            LayoutTemplate, QualityScore, ScoreCategory
        )

        # Test brand tokens creation
        tokens = BrandTokensV2.get_default_tokens()
        assert tokens.version == "2.0"
        assert tokens.colors is not None
        print_result("BrandTokensV2 creation", True, f"Version: {tokens.version}")

        # Test layout template creation
        template = LayoutTemplate.get_hero_badge_cta_template()
        assert len(template.slots) > 0
        print_result("LayoutTemplate creation", True, f"Slots: {len(template.slots)}")

        # Test quality score creation
        score = QualityScore(
            overall_score=85,
            readability=ScoreCategory(score=90, issues=[]),
            brand_consistency=ScoreCategory(score=95, issues=[]),
            composition=ScoreCategory(score=80, issues=[]),
            impact=ScoreCategory(score=85, issues=[]),
            accessibility=ScoreCategory(score=90, issues=[]),
            suggestions=[]
        )
        assert score.overall_score == 85
        print_result("QualityScore creation", True, f"Score: {score.overall_score}")

        return True

    except Exception as e:
        print_result("Schema creation", False, str(e))
        return False


def test_layout_engine():
    """Test 3: Layout Engine"""
    print_section("TEST 3: Layout Engine")

    try:
        from app.core.layout_engine import layout_engine
        from app.core.chat_agent_planner import DesignPlan

        # Create test plan
        plan = DesignPlan(
            headline="Test Headline",
            subhead="Test subhead text",
            cta_text="Learn More",
            visual_concept="Professional background",
            channel="ig",
            aspect_ratio="1x1",
            palette_mode="primary",
            background_style="Modern office",
            logo_position="TR"
        )

        # Test layout selection
        layout = layout_engine.select_optimal_layout(plan)
        assert layout is not None
        print_result("Layout selection", True, f"Selected: {layout.name}")

        # Test template listing
        templates = layout_engine.list_templates()
        assert len(templates) > 0
        print_result("Template listing", True, f"Found: {len(templates)} templates")

        # Test content density calculation
        density = layout_engine._calculate_content_density(plan)
        print_result("Content density", True, f"Score: {density.score:.2f}")

        return True

    except Exception as e:
        print_result("Layout engine", False, str(e))
        return False


def test_contrast_manager():
    """Test 4: Contrast Manager"""
    print_section("TEST 4: Contrast Manager")

    try:
        from app.core.contrast_manager import contrast_manager

        # Test contrast calculation
        ratio = contrast_manager.calculate_contrast_ratio("#FFFFFF", "#000000")
        assert ratio == 21.0  # Perfect contrast
        print_result("Contrast calculation", True, f"Ratio: {ratio}:1")

        # Test WCAG compliance check
        result = contrast_manager.check_contrast("#FFFFFF", "#4F46E5")
        print_result("WCAG compliance check", True,
                    f"Ratio: {result.ratio}:1, AA: {result.passes_aa}, AAA: {result.passes_aaa}")

        # Test color adjustment
        adjusted = contrast_manager.ensure_readable_text("#999999", "#4F46E5")
        assert adjusted is not None
        print_result("Color adjustment", True, f"Adjusted: {adjusted}")

        # Test overlay opacity calculation
        opacity = contrast_manager.calculate_overlay_opacity(0.8)
        print_result("Overlay opacity", True, f"Opacity: {opacity:.2f}")

        return True

    except Exception as e:
        print_result("Contrast manager", False, str(e))
        return False


def test_quality_scorer():
    """Test 5: Quality Scorer"""
    print_section("TEST 5: Quality Scorer")

    try:
        from app.core.quality_scorer import score_design, QualityScorer
        from app.core.chat_agent_planner import DesignPlan
        from app.core.schemas_v2 import BrandTokensV2

        # Create test plan
        plan = DesignPlan(
            headline="Black Friday Sale",
            subhead="Save up to 50% off",
            cta_text="Shop Now",
            visual_concept="Modern shopping scene with authentic people",
            channel="ig",
            aspect_ratio="1x1",
            palette_mode="primary",
            background_style="Professional retail environment",
            logo_position="TR"
        )

        # Score design
        tokens = BrandTokensV2.get_default_tokens()
        scorer = QualityScorer(tokens)
        score = scorer.score_design(plan)

        assert 0 <= score.overall_score <= 100
        print_result("Overall scoring", True, f"Score: {score.overall_score}/100")

        assert 0 <= score.readability.score <= 100
        print_result("Readability scoring", True, f"Score: {score.readability.score}/100")

        assert 0 <= score.brand_consistency.score <= 100
        print_result("Brand consistency scoring", True, f"Score: {score.brand_consistency.score}/100")

        assert isinstance(score.suggestions, list)
        print_result("Suggestions generation", True, f"Count: {len(score.suggestions)}")

        return True

    except Exception as e:
        print_result("Quality scorer", False, str(e))
        return False


def test_export_bridge():
    """Test 6: Export Bridge"""
    print_section("TEST 6: Export Bridge")

    try:
        from app.core.export_bridge import ExportBridge, CanvaExporter, FigmaExporter

        # Test bridge creation
        bridge = ExportBridge()
        print_result("Bridge creation", True)

        # Test platform listing
        platforms = bridge.list_supported_platforms()
        print_result("Platform listing", True, f"Available: {len(platforms)} platforms")

        # Test exporters exist
        assert bridge.canva is not None
        assert bridge.figma is not None
        print_result("Exporter initialization", True)

        return True

    except Exception as e:
        print_result("Export bridge", False, str(e))
        return False


def test_brand_parser():
    """Test 7: Brand Parser (Basic)"""
    print_section("TEST 7: Brand Parser")

    try:
        from app.core.brand_parser import BrandParser

        # Test parser creation
        parser = BrandParser()
        print_result("Parser creation", True)

        # Test color extraction (mock)
        # Note: Actual PDF parsing requires a PDF file
        print_result("Parser ready", True, "Use with actual PDF for full test")

        # Test fallback
        fallback_tokens = parser.fallback_manual_input()
        assert fallback_tokens is not None
        print_result("Fallback tokens", True, f"Version: {fallback_tokens.version}")

        return True

    except Exception as e:
        print_result("Brand parser", False, str(e))
        return False


def test_json_serialization():
    """Test 8: JSON Serialization"""
    print_section("TEST 8: JSON Serialization")

    try:
        from app.core.schemas_v2 import BrandTokensV2, LayoutTemplate

        # Test brand tokens serialization
        tokens = BrandTokensV2.get_default_tokens()
        tokens_dict = tokens.to_dict()
        tokens_json = tokens.to_json()

        assert isinstance(tokens_dict, dict)
        assert isinstance(tokens_json, str)
        print_result("BrandTokens serialization", True)

        # Test deserialization
        tokens_reloaded = BrandTokensV2.from_dict(tokens_dict)
        assert tokens_reloaded.version == tokens.version
        print_result("BrandTokens deserialization", True)

        # Test layout template serialization
        template = LayoutTemplate.get_hero_badge_cta_template()
        template_dict = template.to_dict()
        template_json = template.to_json()

        assert isinstance(template_dict, dict)
        assert isinstance(template_json, str)
        print_result("LayoutTemplate serialization", True)

        # Test deserialization
        template_reloaded = LayoutTemplate.from_dict(template_dict)
        assert template_reloaded.id == template.id
        print_result("LayoutTemplate deserialization", True)

        return True

    except Exception as e:
        print_result("JSON serialization", False, str(e))
        return False


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*60)
    print("  ARCHITECTURE V3 - COMPLETE TEST SUITE")
    print("="*60)

    results = {
        "Imports": test_imports(),
        "Schemas": test_schemas(),
        "Layout Engine": test_layout_engine(),
        "Contrast Manager": test_contrast_manager(),
        "Quality Scorer": test_quality_scorer(),
        "Export Bridge": test_export_bridge(),
        "Brand Parser": test_brand_parser(),
        "JSON Serialization": test_json_serialization(),
    }

    # Summary
    print_section("TEST SUMMARY")

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{'='*60}")
    print(f"  Total: {total} | Passed: {passed} | Failed: {failed}")
    print(f"  Success Rate: {(passed/total)*100:.1f}%")
    print(f"{'='*60}\n")

    if failed == 0:
        print("🎉 ALL TESTS PASSED! Your V3 architecture is ready to use.")
        print("\nNext steps:")
        print("1. Run database migration: psql -d your_db -f database/migration_v3_enhanced_architecture.sql")
        print("2. Configure .env file with API keys")
        print("3. Start Streamlit: streamlit run app/streamlit_app.py")
        print("4. See QUICK_START_V3.md for integration guide")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip install -r requirements_v3.txt")
        print("- Check Python version: python --version (need 3.10+)")
        print("- Review error messages for specific issues")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
