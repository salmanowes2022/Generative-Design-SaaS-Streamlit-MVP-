#!/usr/bin/env python3
"""
Quick script to list brand templates from Canva
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.canva_oauth_bridge import canva_oauth_bridge
from app.core.renderer_canva import CanvaRenderer
import json

def main():
    print("🔍 Fetching brand templates from Canva...\n")

    # Check if authenticated
    if not canva_oauth_bridge.is_authenticated():
        print("❌ Not authenticated with Canva. Please connect first.")
        return

    # Get access token
    access_token = canva_oauth_bridge.get_access_token()
    if not access_token:
        print("❌ Failed to get access token")
        return

    print("✅ Access token retrieved")

    # Initialize renderer
    renderer = CanvaRenderer(access_token=access_token)

    # List templates
    print("📡 Calling Canva API...\n")
    templates = renderer.list_brand_templates(limit=50)

    if not templates:
        print("⚠️  No brand templates found in your Canva account.")
        print("\nTo create a Brand Template:")
        print("1. Go to Canva and create/open a design")
        print("2. Click 'Share' → 'More' → 'Template'")
        print("3. Click 'Publish template'")
        print("4. Make sure it's published to your 'Brand Templates'")
        print("\nNote: Regular designs (like DAG2XMql9IM) are NOT brand templates.")
        return

    print(f"✅ Found {len(templates)} brand template(s):\n")
    print("=" * 80)

    for idx, template in enumerate(templates, 1):
        print(f"\n#{idx}")
        print(f"  Name: {template.get('name', 'Untitled')}")
        print(f"  ID: {template.get('id')}")

        # Dimensions
        width = template.get('width', {}).get('value', 0)
        height = template.get('height', {}).get('value', 0)
        if width and height:
            print(f"  Size: {width}x{height}px")

        # Thumbnail
        thumbnail = template.get('thumbnail', {}).get('url')
        if thumbnail:
            print(f"  Thumbnail: {thumbnail}")

        print("  " + "-" * 76)

    print("\n" + "=" * 80)
    print("\n💡 Copy the template ID and use it in your Brand Brain configuration")
    print("   For example: ig_1x1 → <template_id>")

if __name__ == "__main__":
    main()
