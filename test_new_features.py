#!/usr/bin/env python3
"""
Test Script for New AI Design Assistant Features

Tests:
1. BrandBookParser - PDF/TXT extraction
2. ChatAgentPlanner - Conversational design planning
3. GridRenderer - Template-free rendering
4. QualityScorer - Design quality evaluation
5. TemplateValidator - Canva template inspection
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from uuid import UUID
from app.core.brandbook_parser import BrandBookParser
from app.core.chat_agent_planner import ChatAgentPlanner, chat_plan_design
from app.core.renderer_grid import GridRenderer
from app.core.quality_scorer import DesignQualityScorer, score_design_quality
from app.core.brand_brain import BrandTokens, BrandPolicies
from app.infra.logging import get_logger

logger = get_logger(__name__)


def test_brandbook_parser():
    """Test 1: BrandBook Parsing"""
    print("\n" + "="*80)
    print("TEST 1: BrandBook Parser")
    print("="*80)

    parser = BrandBookParser()

    # Parse sample brand book
    brandbook_path = "sample_brandbook.txt"

    if not Path(brandbook_path).exists():
        print(f"❌ Sample brand book not found: {brandbook_path}")
        return None

    print(f"📄 Parsing brand book: {brandbook_path}")

    try:
        result = parser.parse_file(brandbook_path)

        print("\n✅ Parsing successful!")
        print("\n🎨 Extracted Tokens:")
        tokens = BrandTokens.from_dict(result["tokens"])
        print(f"  - Primary Color: {tokens.color.get('primary')}")
        print(f"  - Heading Font: {tokens.type.get('heading', {}).get('family')}")
        print(f"  - CTA Whitelist: {len(tokens.cta_whitelist)} items")

        print("\n📋 Extracted Policies:")
        policies = BrandPolicies.from_dict(result["policies"])
        print(f"  - Voice Traits: {', '.join(policies.voice[:3])}")
        print(f"  - Forbidden Terms: {len(policies.forbid)} terms")

        return tokens, policies

    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_chat_agent(tokens, policies):
    """Test 2: Chat Agent Planner"""
    print("\n" + "="*80)
    print("TEST 2: Chat Agent Planner")
    print("="*80)

    print("💬 Initializing chat agent...")
    agent = ChatAgentPlanner(tokens, policies)

    # Test conversation
    test_prompts = [
        "Create a Black Friday Instagram post for our automation platform",
        "Make it more professional and less salesy",
    ]

    for prompt in test_prompts:
        print(f"\n👤 User: {prompt}")
        response = agent.chat(prompt)
        print(f"🤖 Assistant: {response[:200]}...")

        # Try to extract plan
        plan = agent.extract_design_plan(response)
        if plan:
            print("\n✅ Design plan extracted:")
            print(f"  - Headline: {plan.headline}")
            print(f"  - CTA: {plan.cta_text}")
            print(f"  - Channel: {plan.channel} ({plan.aspect_ratio})")
            return plan

    return None


def test_grid_renderer(plan, tokens):
    """Test 3: Grid Renderer (Template-Free)"""
    print("\n" + "="*80)
    print("TEST 3: Grid Renderer")
    print("="*80)

    print("🎨 Initializing grid renderer...")
    renderer = GridRenderer(tokens)

    # For testing, use a placeholder background image
    test_bg_url = "https://via.placeholder.com/1080x1080/4F46E5/FFFFFF?text=Background"

    print(f"📐 Rendering design: {plan.aspect_ratio}")
    print(f"  - Headline: {plan.headline}")

    try:
        design_image = renderer.render_design(
            plan=plan,
            background_url=test_bg_url,
            logo_url=None,
            product_image_url=None
        )

        print(f"\n✅ Design rendered: {design_image.size[0]}x{design_image.size[1]}px")

        # Save locally for inspection
        output_path = "test_design_output.png"
        design_image.save(output_path)
        print(f"💾 Saved to: {output_path}")

        return design_image

    except Exception as e:
        print(f"❌ Rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_quality_scorer(design_image, plan, tokens):
    """Test 4: Quality Scorer"""
    print("\n" + "="*80)
    print("TEST 4: Quality Scorer")
    print("="*80)

    print("📊 Evaluating design quality...")
    scorer = DesignQualityScorer(tokens, quality_threshold=70.0)

    try:
        score = scorer.score_design(design_image, plan)

        print(f"\n{'✅' if score.passed else '⚠️'} Overall Score: {score.overall_score}/100")

        print("\n📈 Dimension Scores:")
        for dim, value in score.dimensions.items():
            print(f"  - {dim.replace('_', ' ').title()}: {value:.1f}")

        if score.issues:
            print("\n⚠️ Issues Found:")
            for issue in score.issues:
                print(f"  - {issue}")

        if score.suggestions:
            print("\n💡 Suggestions:")
            for suggestion in score.suggestions:
                print(f"  - {suggestion}")

        return score

    except Exception as e:
        print(f"❌ Scoring failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_template_validator():
    """Test 5: Template Validator"""
    print("\n" + "="*80)
    print("TEST 5: Template Validator")
    print("="*80)

    print("⚠️ Template validator requires Canva access token")
    print("   Skipping automated test - see manual usage below")

    print("\n📝 Manual usage:")
    print("""
from app.core.template_validator import validate_template
from app.core.canva_oauth_bridge import canva_oauth_bridge

# Get access token
token = canva_oauth_bridge.get_access_token()

# Validate template
result = validate_template("EAG2aiNOtSM", token)

print(f"Valid: {result.is_valid}")
print(f"Fields: {result.placeholder_fields}")
print(f"Issues: {result.issues}")
    """)


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*80)
    print("🚀 AI Design Assistant - Feature Test Suite")
    print("="*80)

    # Test 1: Parse brand book
    result = test_brandbook_parser()
    if not result:
        print("\n❌ Brand book parsing failed - stopping tests")
        return

    tokens, policies = result

    # Test 2: Chat agent
    plan = test_chat_agent(tokens, policies)
    if not plan:
        print("\n⚠️ No design plan generated - skipping rendering tests")
        return

    # Test 3: Grid renderer
    design_image = test_grid_renderer(plan, tokens)
    if not design_image:
        print("\n⚠️ Rendering failed - skipping quality tests")
        return

    # Test 4: Quality scorer
    quality_score = test_quality_scorer(design_image, plan, tokens)

    # Test 5: Template validator (manual)
    test_template_validator()

    # Summary
    print("\n" + "="*80)
    print("✅ TEST SUITE COMPLETE")
    print("="*80)
    print(f"\nResults:")
    print(f"  - Brand Book Parsed: ✅")
    print(f"  - Design Plan Created: ✅")
    print(f"  - Design Rendered: ✅")
    print(f"  - Quality Score: {quality_score.overall_score if quality_score else 'N/A'}/100")
    print(f"\n📁 Output saved to: test_design_output.png")


if __name__ == "__main__":
    run_all_tests()
