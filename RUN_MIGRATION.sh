#!/bin/bash
# ============================================================================
# Run Migration V3 - Automated Script
# ============================================================================

echo "🚀 Starting Architecture V3 Migration..."
echo ""

# Extract database connection from .env
DB_URL="postgresql://postgres.baruuogtoppzsqmpkvgt:jx3rvMl7Fi8oN2yT@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

echo "📊 Database: Supabase PostgreSQL"
echo "🔗 Host: aws-1-us-east-2.pooler.supabase.com"
echo ""

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo "❌ ERROR: psql is not installed"
    echo ""
    echo "Install PostgreSQL client:"
    echo "  macOS:   brew install postgresql"
    echo "  Ubuntu:  sudo apt-get install postgresql-client"
    echo "  Windows: Download from https://www.postgresql.org/download/"
    exit 1
fi

echo "✅ psql found"
echo ""

# Backup reminder
echo "⚠️  BACKUP REMINDER"
echo "   It's recommended to backup your database before migration."
echo "   You can create a backup in Supabase Dashboard > Database > Backups"
echo ""
read -p "   Continue with migration? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled"
    exit 1
fi

echo ""
echo "🔄 Running migration..."
echo ""

# Run the fixed migration
psql "$DB_URL" -f database/migration_v3_fix.sql

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration completed successfully!"
    echo ""
    echo "📊 Verifying tables..."

    # Verify tables
    psql "$DB_URL" -c "
    SELECT
        table_name,
        (SELECT COUNT(*) FROM information_schema.columns
         WHERE table_name = t.table_name) as column_count
    FROM information_schema.tables t
    WHERE table_schema = 'public'
    AND table_name IN ('layout_templates', 'design_scores', 'brand_learning', 'design_exports')
    ORDER BY table_name;
    "

    echo ""
    echo "📋 Built-in templates:"
    psql "$DB_URL" -c "SELECT name, array_length(aspect_ratios, 1) as aspects, array_length(channels, 1) as channels FROM layout_templates WHERE is_builtin = true;"

    echo ""
    echo "🎉 All done! Next steps:"
    echo "   1. Run tests: python test_v3_complete.py"
    echo "   2. Start app: streamlit run app/streamlit_app.py"
    echo "   3. See QUICK_START_V3.md for integration guide"

else
    echo ""
    echo "❌ Migration failed!"
    echo ""
    echo "Troubleshooting:"
    echo "   1. Check your database connection"
    echo "   2. Verify DATABASE_URL in .env"
    echo "   3. Check Supabase project is running"
    echo "   4. Review error messages above"
    echo ""
    echo "Need help? See IMPLEMENTATION_GUIDE.md"
fi
