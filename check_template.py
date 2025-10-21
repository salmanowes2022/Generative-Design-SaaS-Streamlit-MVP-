#!/usr/bin/env python3
"""
Check what template ID is actually in the database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from uuid import UUID
from app.core.brand_brain import brand_brain
from app.core.brandkit import brand_kit_manager
import json

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

    # Get brain data
    print("\n📊 Loading brand brain...")
    tokens, policies = brand_brain.get_brand_brain(kit.id)

    if not tokens:
        print("❌ No tokens found")
        return

    print(f"\n✅ Tokens loaded successfully!")
    print(f"Type: {type(tokens)}")

    print(f"\n📝 Templates:")
    if tokens.templates:
        for key, value in tokens.templates.items():
            print(f"  {key}: {value}")
    else:
        print("  ❌ No templates in tokens!")

    # Check the raw tokens dict
    print(f"\n📋 Full tokens dict:")
    tokens_dict = tokens.to_dict()
    print(json.dumps(tokens_dict, indent=2))

if __name__ == "__main__":
    main()
