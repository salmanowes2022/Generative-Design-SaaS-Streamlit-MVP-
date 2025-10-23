#!/usr/bin/env python3
"""
Verify V3 Migration Completed Successfully
"""
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

db_url = os.getenv('DATABASE_URL')

print("🔍 Verifying V3 Migration...\n")

try:
    conn = psycopg.connect(db_url)
    cursor = conn.cursor()

    # Check 1: Verify built-in templates inserted
    cursor.execute("""
        SELECT COUNT(*) FROM layout_templates WHERE is_builtin = TRUE;
    """)
    template_count = cursor.fetchone()[0]

    if template_count == 5:
        print(f"✅ Built-in templates: {template_count}/5 inserted")
    else:
        print(f"⚠️  Built-in templates: {template_count}/5 (expected 5)")

    # Check 2: Verify new columns in brand_kits
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'brand_kits' AND column_name IN ('tokens_v2', 'parsing_metadata');
    """)
    brand_kit_cols = [row[0] for row in cursor.fetchall()]

    if 'tokens_v2' in brand_kit_cols:
        print("✅ brand_kits.tokens_v2 column exists")
    else:
        print("⚠️  brand_kits.tokens_v2 column missing")

    if 'parsing_metadata' in brand_kit_cols:
        print("✅ brand_kits.parsing_metadata column exists")
    else:
        print("⚠️  brand_kits.parsing_metadata column missing")

    # Check 3: Verify new columns in assets
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'assets' AND column_name IN ('brand_kit_id', 'layout_template_id', 'quality_score');
    """)
    asset_cols = [row[0] for row in cursor.fetchall()]

    if 'brand_kit_id' in asset_cols:
        print("✅ assets.brand_kit_id column exists")
    else:
        print("⚠️  assets.brand_kit_id column missing")

    if 'layout_template_id' in asset_cols:
        print("✅ assets.layout_template_id column exists")
    else:
        print("⚠️  assets.layout_template_id column missing")

    if 'quality_score' in asset_cols:
        print("✅ assets.quality_score column exists")
    else:
        print("⚠️  assets.quality_score column missing")

    # Check 4: Verify new tables created
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name IN ('design_scores', 'brand_learning', 'design_exports');
    """)
    new_tables = [row[0] for row in cursor.fetchall()]

    if 'design_scores' in new_tables:
        print("✅ design_scores table created")
    else:
        print("⚠️  design_scores table missing")

    if 'brand_learning' in new_tables:
        print("✅ brand_learning table created")
    else:
        print("⚠️  brand_learning table missing")

    if 'design_exports' in new_tables:
        print("✅ design_exports table created")
    else:
        print("⚠️  design_exports table missing")

    # Check 5: Verify views created
    cursor.execute("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public' AND table_name IN ('top_layout_templates', 'brand_quality_metrics');
    """)
    views = [row[0] for row in cursor.fetchall()]

    if 'top_layout_templates' in views:
        print("✅ top_layout_templates view created")
    else:
        print("⚠️  top_layout_templates view missing")

    if 'brand_quality_metrics' in views:
        print("✅ brand_quality_metrics view created")
    else:
        print("⚠️  brand_quality_metrics view missing")

    # Check 6: Verify trigger exists
    cursor.execute("""
        SELECT trigger_name
        FROM information_schema.triggers
        WHERE trigger_name = 'trigger_update_layout_performance';
    """)
    trigger = cursor.fetchone()

    if trigger:
        print("✅ trigger_update_layout_performance created")
    else:
        print("⚠️  trigger_update_layout_performance missing")

    print("\n" + "="*60)

    # Check template details
    cursor.execute("""
        SELECT name, category, aspect_ratio
        FROM layout_templates
        WHERE is_builtin = TRUE
        ORDER BY name;
    """)
    templates = cursor.fetchall()

    if templates:
        print("\n📋 Built-in Templates:")
        for name, category, aspect_ratio in templates:
            print(f"   • {name} ({category}, {aspect_ratio})")

    cursor.close()
    conn.close()

    print("\n✅ Migration verification complete!")

except Exception as e:
    print(f"❌ Error: {e}")
