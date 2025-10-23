#!/usr/bin/env python3
"""
Check Current Database Schema
This will help us understand your existing table structure
"""
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

db_url = os.getenv('DATABASE_URL')

print("🔍 Checking current database schema...\n")

try:
    conn = psycopg.connect(db_url)
    cursor = conn.cursor()

    # Check layout_templates table - THIS IS WHAT WE NEED
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'layout_templates'
        ORDER BY ordinal_position;
    """)

    layout_cols = cursor.fetchall()

    if layout_cols:
        print("✅ Layout_templates table columns:")
        for col_name, data_type, is_nullable in layout_cols:
            nullable = "nullable" if is_nullable == "YES" else "NOT NULL"
            print(f"   • {col_name} ({data_type}) - {nullable}")
    else:
        print("❌ Layout_templates table not found")

    print()

    # List all tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)

    tables = cursor.fetchall()
    print("📋 All tables in database:")
    for (table_name,) in tables:
        print(f"   • {table_name}")

    cursor.close()
    conn.close()

    print("\n✅ Schema check complete!")

except Exception as e:
    print(f"❌ Error: {e}")
