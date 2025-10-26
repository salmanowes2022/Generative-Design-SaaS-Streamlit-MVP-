#!/usr/bin/env python3
"""
Brand Status Checker
====================
Run this script to check what brand data exists in your database.
This will show you exactly why you're seeing default colors.

Usage:
    python check_brand_status.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.brandkit import brand_kit_manager
from app.core.brand_brain import brand_brain
from app.infra.db import db
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_brand_status():
    """Check what brand data exists in the database."""

    print("\n" + "="*70)
    print("🔍 BRAND STATUS CHECK")
    print("="*70 + "\n")

    # Check brand kits
    print("📦 BRAND KITS:")
    print("-" * 70)

    try:
        # Get all brand kits by querying the database directly
        with db.get_session() as session:
            # Query using table name directly to avoid model import issues
            result = session.execute("SELECT id, name, org_id, created_at FROM brand_kit")
            brand_kits = result.fetchall()

            if not brand_kits:
                print("❌ NO BRAND KITS FOUND")
                print("   → You need to create a brand kit first!")
                print("   → Go to 'Onboard Brand Kit' page in the app")
                print()
                return

            for i, kit in enumerate(brand_kits, 1):
                kit_id, kit_name, org_id, created_at = kit
                print(f"\n{i}. Brand Kit: {kit_name}")
                print(f"   ID: {kit_id}")
                print(f"   Org ID: {org_id}")
                print(f"   Created: {created_at}")

                # Check brand brain for this kit
                print(f"\n   🧠 BRAND BRAIN STATUS:")
                tokens = brand_brain.get_brand_tokens(kit_id)
                policies = brand_brain.get_brand_policies(kit_id)

                if tokens:
                    print(f"   ✅ Brand Tokens FOUND")
                    if hasattr(tokens, 'color'):
                        colors = tokens.color
                        print(f"      Primary:   {colors.get('primary', 'NOT SET')}")
                        print(f"      Secondary: {colors.get('secondary', 'NOT SET')}")
                        print(f"      Accent:    {colors.get('accent', 'NOT SET')}")
                    else:
                        print(f"      ⚠️  Token format: {type(tokens)}")
                else:
                    print(f"   ❌ Brand Tokens NOT FOUND")
                    print(f"      → This is why you see default colors!")

                if policies:
                    print(f"   ✅ Brand Policies FOUND")
                    if hasattr(policies, 'voice'):
                        print(f"      Voice: {policies.voice.get('tone', 'NOT SET')[:50]}...")
                else:
                    print(f"   ❌ Brand Policies NOT FOUND")

                # Check brand assets
                print(f"\n   🎨 BRAND ASSETS:")
                try:
                    assets = brand_kit_manager.get_brand_assets(kit_id)
                    if assets:
                        logo_count = len([a for a in assets if a.asset_type == 'logo'])
                        image_count = len([a for a in assets if a.asset_type == 'image'])
                        print(f"   ✅ Assets found: {logo_count} logos, {image_count} images")
                    else:
                        print(f"   ⚠️  No assets uploaded yet")
                except Exception as e:
                    print(f"   ⚠️  Could not check assets: {e}")

                # Check if guidelines exist
                print(f"\n   📘 BRAND GUIDELINES:")
                try:
                    with db.get_session() as session:
                        intel_result = session.execute(
                            "SELECT guidelines FROM brand_intelligence WHERE brand_kit_id = :kit_id",
                            {"kit_id": kit_id}
                        )
                        intel_row = intel_result.fetchone()

                        if intel_row and intel_row[0]:
                            import json
                            guidelines = json.loads(intel_row[0]) if isinstance(intel_row[0], str) else intel_row[0]
                            if 'visual_identity' in guidelines:
                                visual = guidelines['visual_identity']
                                if 'colors' in visual:
                                    print(f"   ✅ Brand book colors extracted")
                                    colors = visual['colors']
                                    if 'primary' in colors:
                                        primary_color = colors['primary']
                                        if isinstance(primary_color, dict):
                                            print(f"      Primary: {primary_color.get('hex', 'NO HEX')}")
                                        else:
                                            print(f"      Primary: {primary_color}")
                                else:
                                    print(f"   ⚠️  No colors in visual_identity")
                            else:
                                print(f"   ⚠️  No visual_identity in guidelines")

                            # Check for brand assets in guidelines
                            if 'brand_assets' in guidelines:
                                assets = guidelines['brand_assets']
                                char_count = len(assets.get('characters', []))
                                icon_count = len(assets.get('icons', []))
                                illust_count = len(assets.get('illustrations', []))
                                pattern_count = len(assets.get('patterns_textures', []))

                                total = char_count + icon_count + illust_count + pattern_count
                                if total > 0:
                                    print(f"   ✅ Brand assets in guidelines:")
                                    if char_count: print(f"      Characters: {char_count}")
                                    if icon_count: print(f"      Icons: {icon_count}")
                                    if illust_count: print(f"      Illustrations: {illust_count}")
                                    if pattern_count: print(f"      Patterns: {pattern_count}")
                                else:
                                    print(f"   ⚠️  No brand assets extracted from brand book")
                        else:
                            print(f"   ❌ No brand book analysis found")
                            print(f"      → Upload a brand book PDF and click 'Analyze'")

                except Exception as e:
                    print(f"   ⚠️  Could not check guidelines: {e}")

                print()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Summary and next steps
    print("\n" + "="*70)
    print("📋 SUMMARY & NEXT STEPS")
    print("="*70)
    print()

    if not brand_kits:
        print("❌ NO BRAND KITS FOUND")
        print()
        print("Next Steps:")
        print("1. Go to 'Onboard Brand Kit' page")
        print("2. Create a new brand kit")
        print("3. Upload your brand book PDF")
        print("4. Click 'Analyze Brand Materials'")
        print()
    else:
        has_tokens = any(brand_brain.get_brand_tokens(kit[0]) for kit in brand_kits)
        has_guidelines = False

        try:
            with db.get_session() as session:
                result = session.execute(
                    "SELECT COUNT(*) FROM brand_intelligence WHERE brand_kit_id = :kit_id",
                    {"kit_id": brand_kits[0][0]}
                )
                has_guidelines = result.scalar() > 0
        except:
            pass

        if not has_tokens:
            print("❌ BRAND BRAIN NOT CONFIGURED")
            print("   This is why you see default colors (#4F46E5, #7C3AED, #F59E0B)")
            print()
            print("Next Steps:")
            print("1. Go to 'Onboard Brand Kit' page")
            print("2. Upload your brand book PDF")
            print("3. Click '🧠 Analyze Brand Materials'")
            print("4. Wait 2-5 minutes for analysis")
            print("5. Return to Chat page")
            print()
            print("Alternative (no PDF):")
            print("1. Go to 'Onboard Brand Kit' page")
            print("2. Use the manual 'Create New Brand Kit' form")
            print("3. Pick your brand colors manually")
            print()
        else:
            print("✅ BRAND BRAIN CONFIGURED")
            print("   Your designs should use your brand colors")
            print()
            if not has_guidelines:
                print("⚠️  No brand book analyzed yet")
                print("   → Upload PDF for richer brand guidelines")
                print()

if __name__ == "__main__":
    check_brand_status()
