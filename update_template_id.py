#!/usr/bin/env python3
"""
Update brand template ID in brand brain
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from uuid import UUID
from app.core.brand_brain import brand_brain
from app.core.brandkit import brand_kit_manager

def main():
    # Default org and kit IDs
    org_id = UUID("00000000-0000-0000-0000-000000000001")

    print("🔍 Finding brand kits...")
    brand_kits = brand_kit_manager.get_brand_kits_by_org(org_id)

    if not brand_kits:
        print("❌ No brand kits found")
        return

    kit = brand_kits[0]
    print(f"✅ Found brand kit: {kit.name} (ID: {kit.id})")

    # Get current brain data
    print("\n📊 Loading current brand brain...")
    brain_data = brand_brain.get_brand_brain(kit.id)

    if not brain_data:
        print("❌ No brand brain found")
        return

    # Handle tuple response
    if isinstance(brain_data, tuple):
        print("⚠️  Brain data is tuple, using defaults")
        from app.core.brand_brain import BrandTokens, BrandPolicies
        tokens = BrandTokens.get_default_tokens()
        policies = BrandPolicies.get_default_policies()
    else:
        tokens = brain_data.get("tokens")
        policies = brain_data.get("policies")
        if not policies:
            from app.core.brand_brain import BrandPolicies
            policies = BrandPolicies.get_default_policies()

    print(f"\n📝 Current templates:")
    if tokens.templates:
        for key, value in tokens.templates.items():
            print(f"  {key}: {value}")
    else:
        print("  (none)")

    # Update template ID
    new_template_id = "EAG2XKYinQ8"
    print(f"\n🔧 Updating ig_1x1 template to: {new_template_id}")

    if not tokens.templates:
        tokens.templates = {}

    tokens.templates["ig_1x1"] = new_template_id

    # Save to database
    print("💾 Saving to database...")
    brand_brain.save_brand_brain(
        brand_kit_id=kit.id,
        tokens=tokens,
        policies=policies
    )

    print("✅ Template ID updated successfully!")
    print(f"\n📋 New templates:")
    for key, value in tokens.templates.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
