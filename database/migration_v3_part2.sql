-- ============================================================================
-- Migration V3 - PART 2: Create New Tables
-- Run this AFTER part 1
-- ============================================================================

-- Create design_scores table
CREATE TABLE IF NOT EXISTS design_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    overall_score INTEGER NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    readability_score INTEGER CHECK (readability_score >= 0 AND readability_score <= 100),
    brand_consistency_score INTEGER CHECK (brand_consistency_score >= 0 AND brand_consistency_score <= 100),
    composition_score INTEGER CHECK (composition_score >= 0 AND composition_score <= 100),
    impact_score INTEGER CHECK (impact_score >= 0 AND impact_score <= 100),
    accessibility_score INTEGER CHECK (accessibility_score >= 0 AND accessibility_score <= 100),
    issues JSONB,
    suggestions JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_design_scores_asset ON design_scores(asset_id);
CREATE INDEX IF NOT EXISTS idx_design_scores_overall ON design_scores(overall_score DESC);

-- Create brand_learning table
CREATE TABLE IF NOT EXISTS brand_learning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_kit_id UUID REFERENCES brand_kits(id) ON DELETE CASCADE,
    design_pattern VARCHAR(255),
    user_feedback VARCHAR(50),
    context JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_brand_learning_brand_kit ON brand_learning(brand_kit_id);

-- Create design_exports table
CREATE TABLE IF NOT EXISTS design_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    export_url TEXT,
    editor_url TEXT,
    external_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_design_exports_asset ON design_exports(asset_id);

SELECT 'Part 2 completed - New tables created!' AS status;
