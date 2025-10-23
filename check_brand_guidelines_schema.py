#!/usr/bin/env python3
"""
Check brand_guidelines table schema
"""
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

db_url = os.getenv('DATABASE_URL')

print("🔍 Checking brand_guidelines table schema...\n")

try:
    conn = psycopg.connect(db_url)
    cursor = conn.cursor()

    # Check table structure
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'brand_guidelines'
        ORDER BY ordinal_position;
    """)

    cols = cursor.fetchall()

    if cols:
        print("✅ brand_guidelines table columns:")
        for col_name, data_type, is_nullable in cols:
            nullable = "nullable" if is_nullable == "YES" else "NOT NULL"
            print(f"   • {col_name} ({data_type}) - {nullable}")
    else:
        print("❌ brand_guidelines table not found")

    print("\n" + "="*60)

    # Check constraints
    cursor.execute("""
        SELECT constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE table_name = 'brand_guidelines';
    """)

    constraints = cursor.fetchall()

    if constraints:
        print("\n🔒 Constraints:")
        for name, ctype in constraints:
            print(f"   • {name} ({ctype})")
    else:
        print("\n⚠️  No constraints found")

    print("\n" + "="*60)

    # Check unique constraints specifically
    cursor.execute("""
        SELECT
            tc.constraint_name,
            kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_name = 'brand_guidelines'
            AND tc.constraint_type IN ('UNIQUE', 'PRIMARY KEY');
    """)

    unique_cols = cursor.fetchall()

    if unique_cols:
        print("\n🔑 Unique/Primary Key Columns:")
        for constraint, col in unique_cols:
            print(f"   • {col} ({constraint})")
    else:
        print("\n⚠️  No unique constraints found")

    cursor.close()
    conn.close()

    print("\n✅ Schema check complete!")

except Exception as e:
    print(f"❌ Error: {e}")
