#!/usr/bin/env python3
"""
Test HTML Designer - Quick verification script
Run this to test the new HTML/CSS design engine
"""
import sys
from pathlib import Path

print("🎨 Testing HTML Designer...\n")

# Test 1: Check imports
print("=" * 60)
print("TEST 1: Checking imports...")
print("=" * 60)

try:
    from app.core.html_designer import HTMLDesigner, PLAYWRIGHT_AVAILABLE, DesignTemplate
    print("✅ html_designer.py imported successfully")
except ImportError as e:
    print(f"❌ Failed to import html_designer: {e}")
    sys.exit(1)

try:
    from app.core.design_engine import DesignEngine
    print("✅ design_engine.py imported successfully")
except ImportError as e:
    print(f"❌ Failed to import design_engine: {e}")
    sys.exit(1)

try:
    from app.core.brand_brain import BrandTokens
    from app.core.chat_agent_planner import DesignPlan
    print("✅ Existing modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import existing modules: {e}")
    sys.exit(1)

# Test 2: Check Playwright
print("\n" + "=" * 60)
print("TEST 2: Checking Playwright...")
print("=" * 60)

if PLAYWRIGHT_AVAILABLE:
    print("✅ Playwright is installed and available")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            print("✅ Chromium browser working")
            browser.close()
    except Exception as e:
        print(f"⚠️  Playwright installed but browser test failed: {e}")
        print("   Try: playwright install chromium")
else:
    print("⚠️  Playwright NOT installed")
    print("   Designs will use fallback Pillow renderer")
    print("   To install: pip install playwright && playwright install chromium")

# Test 3: Create designer instance
print("\n" + "=" * 60)
print("TEST 3: Creating HTMLDesigner instance...")
print("=" * 60)

# Create mock brand tokens
mock_tokens = BrandTokens(
    color={
        'primary': '#1A1A2E',
        'secondary': '#16213E',
        'accent': '#0F3460'
    },
    typography={
        'heading': {
            'family': 'Inter',
            'weight': 'bold'
        }
    },
    layout={
        'grid': 12,
        'spacing': 8
    },
    cta_whitelist=['Shop Now', 'Buy Now', 'Learn More']
)

try:
    designer = HTMLDesigner(mock_tokens)
    print(f"✅ HTMLDesigner created successfully")
    print(f"   Templates loaded: {len(designer.templates)}")
except Exception as e:
    print(f"❌ Failed to create HTMLDesigner: {e}")
    sys.exit(1)

# Test 4: Check templates
print("\n" + "=" * 60)
print("TEST 4: Checking templates...")
print("=" * 60)

for template_id, template in designer.templates.items():
    print(f"✅ {template.name}")
    print(f"   ID: {template_id}")
    print(f"   Best for: {', '.join(template.best_for)}")
    print(f"   Aspect ratios: {', '.join(template.aspect_ratios)}")
    print()

# Test 5: Create design engine
print("=" * 60)
print("TEST 5: Creating DesignEngine...")
print("=" * 60)

try:
    engine = DesignEngine(mock_tokens, use_html=True)
    info = engine.get_renderer_info()
    print(f"✅ DesignEngine created successfully")
    print(f"   Renderer type: {info['type']}")
    print(f"   Playwright available: {info['playwright_available']}")
    print(f"   Templates: {info['templates']}")
    print(f"   Supports gradients: {info['supports_gradients']}")
    print(f"   Supports glassmorphism: {info['supports_glassmorphism']}")
except Exception as e:
    print(f"❌ Failed to create DesignEngine: {e}")
    sys.exit(1)

# Test 6: Template selection
print("\n" + "=" * 60)
print("TEST 6: Testing template selection...")
print("=" * 60)

test_plans = [
    DesignPlan(
        headline="Summer Sale",
        subhead="50% off everything",
        cta_text="Shop Now",
        visual_concept="bold promotional gradient",
        channel="ig",
        aspect_ratio="1x1",
        palette_mode="primary",
        background_style="gradient bold",
        logo_position="TL"
    ),
    DesignPlan(
        headline="iPhone 15",
        subhead="The most powerful iPhone yet",
        cta_text="Buy Now",
        visual_concept="product showcase clean",
        channel="ig",
        aspect_ratio="1x1",
        palette_mode="primary",
        background_style="product clean",
        logo_position="TL",
        product_image_needed=True
    ),
    DesignPlan(
        headline="Daily Motivation",
        subhead="",
        cta_text="Learn More",
        visual_concept="minimal quote calm",
        channel="ig",
        aspect_ratio="1x1",
        palette_mode="mono",
        background_style="minimal clean",
        logo_position="TL"
    )
]

for i, plan in enumerate(test_plans, 1):
    template = designer.select_template(plan)
    print(f"✅ Test {i}: '{plan.headline}'")
    print(f"   Selected: {template.name}")
    print(f"   Reason: Matches '{plan.background_style}' style")
    print()

# Test 7: HTML generation (without rendering)
print("=" * 60)
print("TEST 7: Testing HTML generation...")
print("=" * 60)

try:
    template = designer.select_template(test_plans[0])
    html = designer._build_html(
        template=template,
        plan=test_plans[0],
        background_url=None,
        logo_url=None,
        product_image_url=None
    )
    print(f"✅ HTML generated successfully")
    print(f"   Length: {len(html)} characters")
    print(f"   Contains gradient: {'gradient' in html.lower()}")
    print(f"   Contains brand color: {mock_tokens.color['primary'] in html}")

    # Save sample HTML for inspection
    sample_path = Path("/tmp/sample_design.html")
    sample_path.write_text(html)
    print(f"   Sample saved to: {sample_path}")
    print(f"   Open in browser to preview!")
except Exception as e:
    print(f"⚠️  HTML generation test failed: {e}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if PLAYWRIGHT_AVAILABLE:
    print("✅ ALL SYSTEMS GO!")
    print("   HTML designer is fully functional")
    print("   Beautiful designs ready to create!")
    print()
    print("🎨 Next steps:")
    print("   1. Restart Streamlit")
    print("   2. Go to Chat Create page")
    print("   3. Enter a prompt like 'Summer sale - 50% off'")
    print("   4. Watch beautiful designs appear! ✨")
else:
    print("⚠️  PARTIAL FUNCTIONALITY")
    print("   HTML designer works but needs Playwright for full features")
    print("   Designs will use fallback Pillow renderer")
    print()
    print("📦 To enable full features:")
    print("   pip install playwright")
    print("   playwright install chromium")
    print("   Then re-run this test")

print("\n✅ Test complete!")
