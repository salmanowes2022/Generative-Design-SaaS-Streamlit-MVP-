"""
Run database migration for Canva integration
"""
import psycopg
from app.infra.config import settings

def run_migration():
    """Run the Canva tokens table migration"""

    migration_sql = """
    -- Create table for storing Canva OAuth tokens
    CREATE TABLE IF NOT EXISTS canva_tokens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id VARCHAR(255) UNIQUE NOT NULL,
        access_token TEXT NOT NULL,
        refresh_token TEXT,
        expires_at TIMESTAMP NOT NULL,
        scope TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    -- Create index on user_id for faster lookups
    CREATE INDEX IF NOT EXISTS idx_canva_tokens_user_id ON canva_tokens(user_id);

    -- Create index on expires_at for cleanup queries
    CREATE INDEX IF NOT EXISTS idx_canva_tokens_expires_at ON canva_tokens(expires_at);

    -- Add comment
    COMMENT ON TABLE canva_tokens IS 'Stores Canva OAuth2 tokens for users';
    """

    try:
        print("Connecting to database...")
        conn = psycopg.connect(settings.DATABASE_URL)
        cursor = conn.cursor()

        print("Running migration...")
        cursor.execute(migration_sql)
        conn.commit()

        print("✅ Migration completed successfully!")
        print("Created table: canva_tokens")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    run_migration()
