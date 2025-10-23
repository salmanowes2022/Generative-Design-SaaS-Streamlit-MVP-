"""
Test Brand Data Flow
Verify that brand book data flows correctly from upload → chat → design
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from uuid import UUID
from app.core.brand_brain import brand_brain, BrandTokens, BrandPolicies
from app.core.brandkit import brand_kit_manager
from app.infra.logging import get_logger

logger = get_logger(__name__)

def test_brand_brain_flow():
    """Test complete brand brain flow"""

    print("\n" + "="*80)
    print("TESTING BRAND DATA FLOW")
    print("="*80 + "\n")

    # Step 1: Get existing brand kits
    print("Step 1: Loading existing brand kits...")
    org_id = UUID("00000000-0000-0000-0000-000000000001")
    brand_kits = brand_kit_manager.get_brand_kits_by_org(org_id)

    if not brand_kits:
        print("❌ ERROR: No brand kits found!")
        print("   Please create a brand kit first using the UI:")
        print("   1. Run: cd app && streamlit run streamlit_app.py")
        print("   2. Click '📖 1. Upload Brand Book'")
        print("   3. Upload a brand book PDF")
        return

    print(f"✅ Found {len(brand_kits)} brand kit(s)")

    for kit in brand_kits:
        print(f"   - {kit.name} (ID: {kit.id})")

    # Test with first brand kit
    test_kit = brand_kits[0]
    print(f"\nUsing brand kit: {test_kit.name}")

    # Step 2: Load brand brain
    print("\nStep 2: Loading brand brain from database...")
    tokens, policies = brand_brain.get_brand_brain(test_kit.id)

    if not tokens:
        print("❌ ERROR: No brand brain data found!")
        print("   This means the brand book upload did NOT save to brand_brain")
        print("   Expected: Tokens should contain colors, fonts, CTAs")
        print("   Actual: Got None")
        return

    print("✅ Brand brain loaded successfully")

    # Step 3: Verify token data
    print("\nStep 3: Verifying brand tokens...")
    print(f"\n🎨 COLORS:")
    print(f"   Primary:   {tokens.color.get('primary')}")
    print(f"   Secondary: {tokens.color.get('secondary')}")
    print(f"   Accent:    {tokens.color.get('accent')}")

    print(f"\n📝 CTAs:")
    print(f"   {tokens.cta_whitelist}")

    print(f"\n🔤 FONTS:")
    print(f"   Heading: {tokens.type.get('heading', {}).get('family')}")
    print(f"   Body:    {tokens.type.get('body', {}).get('family')}")

    # Step 4: Verify policy data
    print("\nStep 4: Verifying brand policies...")
    if policies:
        print(f"\n🗣️ VOICE:")
        print(f"   {policies.voice}")

        print(f"\n🚫 FORBIDDEN:")
        print(f"   {policies.forbid}")
    else:
        print("⚠️ WARNING: No policies found")

    # Step 5: Check if using defaults or actual extracted data
    print("\nStep 5: Checking if data is from brand book or defaults...")

    default_tokens = BrandTokens.get_default_tokens()

    if tokens.color.get('primary') == default_tokens.color.get('primary'):
        print("⚠️ WARNING: Using DEFAULT primary color (#4F46E5)")
        print("   This means brand book colors were NOT extracted correctly")
    else:
        print(f"✅ Using CUSTOM primary color: {tokens.color.get('primary')}")

    if tokens.cta_whitelist == default_tokens.cta_whitelist:
        print("⚠️ WARNING: Using DEFAULT CTAs")
        print("   This means brand book CTAs were NOT extracted correctly")
    else:
        print(f"✅ Using CUSTOM CTAs: {tokens.cta_whitelist[:3]}...")

    if policies and policies.voice == ["professional", "clear", "authentic"]:
        print("⚠️ WARNING: Using DEFAULT voice traits")
        print("   This means brand book voice was NOT extracted correctly")
    else:
        print(f"✅ Using CUSTOM voice: {policies.voice[:3]}...")

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    issues_found = []

    if not tokens:
        issues_found.append("Brand brain not saved to database")

    if tokens.color.get('primary') == default_tokens.color.get('primary'):
        issues_found.append("Brand colors not extracted from brand book")

    if tokens.cta_whitelist == default_tokens.cta_whitelist:
        issues_found.append("CTAs not extracted from brand book")

    if policies and policies.voice == ["professional", "clear", "authentic"]:
        issues_found.append("Voice traits not extracted from brand book")

    if issues_found:
        print("\n❌ ISSUES FOUND:")
        for issue in issues_found:
            print(f"   - {issue}")
        print("\nThis explains why designs don't match the brand book!")
    else:
        print("\n✅ ALL CHECKS PASSED!")
        print("Brand data is flowing correctly from brand book → brand_brain")
        print("\nIf designs still don't match brand, the issue is in:")
        print("   - Chat agent not using the data in prompts")
        print("   - Renderer not applying the data to designs")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        test_brand_flow()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
