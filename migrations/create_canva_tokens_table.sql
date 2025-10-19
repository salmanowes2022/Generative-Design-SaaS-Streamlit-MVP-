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
