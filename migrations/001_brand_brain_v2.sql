-- Migration: Brand Brain v2 Schema
-- Adds design tokens, policies, and enhanced validation

-- 1. Add Brand Brain columns to brand_kits
ALTER TABLE brand_kits
ADD COLUMN IF NOT EXISTS tokens JSONB DEFAULT NULL,
ADD COLUMN IF NOT EXISTS policies JSONB DEFAULT NULL,
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;

COMMENT ON COLUMN brand_kits.tokens IS 'Design tokens: colors, typography, logo rules, layout grid, spacing, templates';
COMMENT ON COLUMN brand_kits.policies IS 'Brand policies: voice traits, forbidden terms, legal constraints';
COMMENT ON COLUMN brand_kits.version IS 'Brand kit schema version for migrations';

-- 2. Enhance assets table for Canva integration
ALTER TABLE assets
ADD COLUMN IF NOT EXISTS canva_design_id TEXT,
ADD COLUMN IF NOT EXISTS canva_design_url TEXT,
ADD COLUMN IF NOT EXISTS on_brand_score INTEGER,
ADD COLUMN IF NOT EXISTS validation_reasons JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN assets.canva_design_id IS 'Canva design ID for deep linking';
COMMENT ON COLUMN assets.canva_design_url IS 'Direct URL to edit design in Canva';
COMMENT ON COLUMN assets.on_brand_score IS 'Brand compliance score 0-100';
COMMENT ON COLUMN assets.validation_reasons IS 'Detailed validation results and reasons';

-- 3. Create agent_audit table for tracking Brand Brain decisions
CREATE TABLE IF NOT EXISTS agent_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    brand_kit_id UUID REFERENCES brand_kits(id) ON DELETE SET NULL,
    asset_id UUID REFERENCES assets(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result JSONB DEFAULT '{}'::jsonb,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_audit_org_id ON agent_audit(org_id);
CREATE INDEX idx_agent_audit_brand_kit_id ON agent_audit(brand_kit_id);
CREATE INDEX idx_agent_audit_action ON agent_audit(action);
CREATE INDEX idx_agent_audit_created_at ON agent_audit(created_at DESC);

COMMENT ON TABLE agent_audit IS 'Audit log for Brand Brain agent decisions and actions';
COMMENT ON COLUMN agent_audit.action IS 'Action type: plan, render, validate, regenerate, etc.';
COMMENT ON COLUMN agent_audit.payload IS 'Input data for the action';
COMMENT ON COLUMN agent_audit.result IS 'Output/result of the action';
COMMENT ON COLUMN agent_audit.duration_ms IS 'Execution time in milliseconds';

-- 4. Add validation metadata to existing validation column
COMMENT ON COLUMN assets.validation IS 'Comprehensive validation results: color delta E, contrast, OCR, policy checks';

-- 5. Enable RLS on agent_audit
ALTER TABLE agent_audit ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Organizations can view own audit logs"
    ON agent_audit FOR SELECT
    USING (auth.uid() IN (
        SELECT user_id FROM users WHERE org_id = agent_audit.org_id
    ));

CREATE POLICY "System can insert audit logs"
    ON agent_audit FOR INSERT
    WITH CHECK (true);

-- 6. Create indexes for brand_kits tokens/policies for JSONB queries
CREATE INDEX IF NOT EXISTS idx_brand_kits_tokens ON brand_kits USING GIN (tokens);
CREATE INDEX IF NOT EXISTS idx_brand_kits_policies ON brand_kits USING GIN (policies);

-- 7. Add check constraint for on_brand_score
ALTER TABLE assets
ADD CONSTRAINT check_on_brand_score CHECK (on_brand_score IS NULL OR (on_brand_score >= 0 AND on_brand_score <= 100));
