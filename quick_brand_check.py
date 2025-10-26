#!/usr/bin/env python3
"""Quick Brand Status Check - Simple diagnostic"""

import sys
sys.path.insert(0, '.')

from app.infra.db import db

print("\n" + "="*70)
print("🔍 QUICK BRAND STATUS CHECK")
print("="*70 + "\n")

try:
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            # Check brand kits
            cur.execute("SELECT id, name, org_id, tokens, policies FROM brand_kits LIMIT 5")
            kits = cur.fetchall()

            print(f"📦 BRAND KITS: {len(kits)} found\n")

            if not kits:
                print("❌ NO BRAND KITS FOUND!")
                print("\nNext Steps:")
                print("1. Go to 'Onboard Brand Kit' page")
                print("2. Create a brand kit")
                print("3. Upload brand book PDF")
                print("\n")
                sys.exit(0)

            for kit in kits:
                kit_id = kit['id']
                kit_name = kit['name']
                tokens_data = kit['tokens']
                policies_data = kit['policies']

                print(f"Brand Kit: {kit_name} (ID: {kit_id})")
                print("-" * 70)

                # Check tokens from brand_kits table
                if tokens_data:
                    import json
                    tokens = json.loads(tokens_data) if isinstance(tokens_data, str) else tokens_data

                    # Check both old format (color) and new format (colors)
                    colors = None
                    if 'color' in tokens:
                        colors = tokens['color']
                        format_name = "OLD format"
                    elif 'colors' in tokens:
                        colors = tokens['colors']
                        format_name = "NEW format"

                    if colors:
                        # Extract hex values from either format
                        if isinstance(colors.get('primary'), dict):
                            primary = colors['primary'].get('hex', 'NO HEX')
                        else:
                            primary = colors.get('primary', 'NOT SET')

                        if isinstance(colors.get('secondary'), dict):
                            secondary = colors['secondary'].get('hex', 'NO HEX')
                        else:
                            secondary = colors.get('secondary', 'NOT SET')

                        if isinstance(colors.get('accent'), dict):
                            accent = colors['accent'].get('hex', 'NO HEX')
                        else:
                            accent = colors.get('accent', 'NOT SET')

                        print(f"✅ BRAND TOKENS SAVED ({format_name})")
                        print(f"   Primary:   {primary}")
                        print(f"   Secondary: {secondary}")
                        print(f"   Accent:    {accent}")

                        # Check if using defaults
                        default_colors = ['#4F46E5', '#7C3AED', '#F59E0B', '#2563EB']
                        if primary in default_colors or secondary in default_colors or accent in default_colors:
                            print(f"\n   ⚠️  WARNING: Using DEFAULT COLORS!")
                            print(f"   Brand book was never analyzed or colors weren't extracted")
                            print(f"   You need to upload a brand book PDF and analyze it!")
                    else:
                        print(f"⚠️  BRAND TOKENS EXIST but no colors found")
                        print(f"   Token keys: {list(tokens.keys())}")
                else:
                    print(f"❌ NO BRAND TOKENS SAVED")
                    print(f"   This is why you see default colors!")

                # Check brand book analysis from brand_guidelines table
                print(f"\n📘 BRAND BOOK ANALYSIS:")
                cur.execute("""
                    SELECT guidelines
                    FROM brand_guidelines
                    WHERE brand_kit_id = %s
                    LIMIT 1
                """, (kit_id,))
                guideline_row = cur.fetchone()

                if guideline_row and guideline_row['guidelines']:
                    guidelines_data = guideline_row['guidelines']
                    if isinstance(guidelines_data, str):
                        import json
                        guidelines_data = json.loads(guidelines_data)

                    # Check if there's detailed guidelines with visual_identity
                    if isinstance(guidelines_data, dict) and 'visual_identity' in guidelines_data:
                        visual = guidelines_data['visual_identity']
                        if 'colors' in visual:
                            colors_data = visual['colors']
                            print(f"   ✅ Colors extracted from brand book")
                            if 'primary' in colors_data:
                                primary_data = colors_data['primary']
                                if isinstance(primary_data, dict):
                                    print(f"      Primary from book: {primary_data.get('hex', 'NO HEX')}")
                                else:
                                    print(f"      Primary from book: {primary_data}")
                        else:
                            print(f"   ⚠️  No colors in visual_identity")

                        if 'brand_assets' in guidelines_data:
                            assets = guidelines_data['brand_assets']
                            char_count = len(assets.get('characters', []))
                            icon_count = len(assets.get('icons', []))
                            if char_count or icon_count:
                                print(f"\n   📦 Brand Assets Extracted:")
                                if char_count: print(f"      Characters: {char_count}")
                                if icon_count: print(f"      Icons: {icon_count}")
                    else:
                        print(f"   ⚠️  Brand book analyzed but no visual_identity found")
                        if isinstance(guidelines_data, dict):
                            print(f"   Guideline keys: {list(guidelines_data.keys())}")
                else:
                    print(f"   📖 Not analyzed yet")

                # Check brand assets (uploaded files)
                cur.execute("""
                    SELECT COUNT(*) as count, type
                    FROM brand_assets
                    WHERE brand_kit_id = %s
                    GROUP BY type
                """, (kit_id,))
                assets = cur.fetchall()

                if assets:
                    print(f"\n🎨 UPLOADED ASSETS:")
                    for asset in assets:
                        print(f"   {asset['type']}: {asset['count']}")
                else:
                    print(f"\n🎨 No assets uploaded yet")

                print("\n")

            # Summary
            print("="*70)
            print("📋 SUMMARY")
            print("="*70)

            # Check if any kit has brain configured
            cur.execute("SELECT COUNT(*) as count FROM brand_kits WHERE tokens IS NOT NULL")
            brain_count = cur.fetchone()['count']

            if brain_count == 0:
                print("\n❌ NO BRAND BRAIN CONFIGURED FOR ANY KIT")
                print("\nThis is why you're seeing default colors!")
                print("\nYou need to:")
                print("1. Go to 'Onboard Brand Kit' page")
                print("2. Upload a brand book PDF")
                print("3. Click '🧠 Analyze Brand Materials'")
                print("4. Wait 2-5 minutes for analysis")
                print("5. Check this script again to verify\n")
            else:
                print(f"\n✅ {brain_count} brand kit(s) configured")
                print("\nIf you're still seeing default colors, restart Streamlit:\n")
                print("   pkill -f streamlit")
                print("   streamlit run app/Home.py\n")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print()
