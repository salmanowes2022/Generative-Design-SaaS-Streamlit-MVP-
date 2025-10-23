#!/usr/bin/env python3
"""
Create brand_guidelines table in database
Run this once to set up the table for brand book uploads
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app.infra.db import get_db
from app.infra.logging import get_logger

logger = get_logger(__name__)

def create_brand_guidelines_table():
    """Create the brand_guidelines table"""

    print("\n" + "="*80)
    print("CREATING BRAND_GUIDELINES TABLE")
    print("="*80 + "\n")

    db = get_db()

    # SQL to create table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS brand_guidelines (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        guidelines JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(org_id)
    );
    """

    # SQL to create index
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_brand_guidelines_org_id
    ON brand_guidelines(org_id);
    """

    try:
        print("📝 Creating brand_guidelines table...")
        db.execute(create_table_sql)
        print("✅ Table created successfully!")

        print("\n📝 Creating index...")
        db.execute(create_index_sql)
        print("✅ Index created successfully!")

        print("\n" + "="*80)
        print("SUCCESS! brand_guidelines table is ready")
        print("="*80)
        print("\nYou can now:")
        print("1. Upload your brand book in the UI")
        print("2. Brand data will be saved correctly")
        print("3. Designs will use your actual brand colors/CTAs/voice")
        print("\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nIf the error says 'relation already exists', that's OK - table already exists!")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = create_brand_guidelines_table()
    sys.exit(0 if success else 1)
