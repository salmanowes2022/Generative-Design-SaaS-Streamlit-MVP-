#!/usr/bin/env python3
"""
Run Migration V3 - Python Script
Automatically runs the database migration using your .env configuration
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

try:
    import psycopg
except ImportError:
    print("❌ psycopg not installed. Installing...")
    os.system("pip install psycopg[binary]")
    import psycopg

# Load environment variables
load_dotenv()

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text):
    """Print section header"""
    print(f"\n{BOLD}{BLUE}{text}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"{BLUE}ℹ️  {text}{RESET}")


def main():
    """Run migration"""
    print_header("🚀 Architecture V3 Migration")

    # Get database URL
    db_url = os.getenv('DATABASE_URL')

    if not db_url:
        print_error("DATABASE_URL not found in .env file")
        print_info("Please ensure DATABASE_URL is set in your .env file")
        sys.exit(1)

    print_success("Loaded database configuration from .env")
    print(f"   Host: aws-1-us-east-2.pooler.supabase.com")
    print(f"   Database: postgres")
    print(f"   Provider: Supabase")

    # Backup reminder
    print_header("⚠️  Backup Reminder")
    print("   It's recommended to backup your database before migration.")
    print("   You can create a backup in Supabase Dashboard > Database > Backups")
    print()

    response = input("   Continue with migration? (y/n): ").lower().strip()

    if response != 'y':
        print_error("Migration cancelled")
        sys.exit(0)

    # Read migration file
    migration_file = Path(__file__).parent / "database" / "migration_v3_final.sql"

    if not migration_file.exists():
        print_error(f"Migration file not found: {migration_file}")
        sys.exit(1)

    print_info("Reading migration file...")

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    # Connect and run migration
    print_header("🔄 Running Migration")

    try:
        # Connect to database
        print_info("Connecting to database...")
        conn = psycopg.connect(db_url)
        cursor = conn.cursor()

        print_success("Connected successfully")

        # Execute migration
        print_info("Executing migration SQL...")
        cursor.execute(migration_sql)
        conn.commit()

        print_success("Migration executed successfully!")

        # Verify tables
        print_header("📊 Verifying Tables")

        cursor.execute("""
            SELECT
                table_name,
                (SELECT COUNT(*)
                 FROM information_schema.columns
                 WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_name IN ('layout_templates', 'design_scores', 'brand_learning', 'design_exports')
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()

        if tables:
            print_success(f"Found {len(tables)} new tables:")
            for table_name, col_count in tables:
                print(f"   • {table_name} ({col_count} columns)")
        else:
            print_warning("No tables found. Migration may have failed.")

        # Check built-in templates
        print_header("📋 Built-in Templates")

        cursor.execute("""
            SELECT name, array_length(aspect_ratios, 1) as aspects,
                   array_length(channels, 1) as channels
            FROM layout_templates
            WHERE is_builtin = true;
        """)

        templates = cursor.fetchall()

        if templates:
            print_success(f"Found {len(templates)} built-in templates:")
            for name, aspects, channels in templates:
                print(f"   • {name} ({aspects} aspects, {channels} channels)")
        else:
            print_warning("No built-in templates found")

        # Close connection
        cursor.close()
        conn.close()

        # Success message
        print_header("🎉 Migration Complete!")
        print("\nNext steps:")
        print("   1. Run tests: python test_v3_complete.py")
        print("   2. Start app: streamlit run app/streamlit_app.py")
        print("   3. See QUICK_START_V3.md for integration guide")
        print()

    except psycopg.Error as e:
        print_error("Database error occurred!")
        print(f"\n{RED}Error details:{RESET}")
        print(f"   {str(e)}")
        print("\nTroubleshooting:")
        print("   1. Check your database connection")
        print("   2. Verify DATABASE_URL in .env")
        print("   3. Check Supabase project is running")
        print("   4. Try running migration manually via Supabase SQL Editor")
        print("\nNeed help? See IMPLEMENTATION_GUIDE.md")
        sys.exit(1)

    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
