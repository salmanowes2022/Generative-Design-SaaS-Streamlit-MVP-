-- Create brand_guidelines table for storing comprehensive brand book analysis
-- Run this in your Supabase SQL Editor
-- FIXED VERSION - No RLS policies to avoid auth.uid() errors

CREATE TABLE IF NOT EXISTS brand_guidelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Complete brand guidelines as JSON
    guidelines JSONB NOT NULL,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure one guideline per org (can be updated)
    UNIQUE(org_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_brand_guidelines_org_id ON brand_guidelines(org_id);

-- Comments
COMMENT ON TABLE brand_guidelines IS 'Comprehensive brand guidelines extracted from brand books';
COMMENT ON COLUMN brand_guidelines.guidelines IS 'Complete brand guidelines including visual identity, messaging, imagery, layout, and design patterns';
