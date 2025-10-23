-- ============================================================================
-- Migration V3 FIX - Handles Existing Tables
-- Run this instead if you got errors with the original migration
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. DROP AND RECREATE LAYOUT_TEMPLATES (if exists with wrong schema)
-- ============================================================================

-- Drop existing table if it has wrong schema
DROP TABLE IF EXISTS layout_templates CASCADE;

-- Create fresh layout_templates table
CREATE TABLE layout_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_schema JSONB NOT NULL,
    aspect_ratios TEXT[] NOT NULL,
    channels TEXT[] NOT NULL,
    usage_count INTEGER DEFAULT 0,
    performance_score DECIMAL(3,2),
    is_builtin BOOLEAN DEFAULT FALSE,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comments
COMMENT ON TABLE layout_templates IS 'Layout templates for design composition';
COMMENT ON COLUMN layout_templates.template_schema IS 'Complete layout specification (slots, rules, etc.)';
COMMENT ON COLUMN layout_templates.aspect_ratios IS 'Supported aspect ratios (1x1, 4x5, 9x16, 16x9)';
COMMENT ON COLUMN layout_templates.channels IS 'Supported channels (ig, fb, linkedin, twitter)';

-- Indexes
CREATE INDEX idx_layout_templates_aspect ON layout_templates USING GIN(aspect_ratios);
CREATE INDEX idx_layout_templates_channels ON layout_templates USING GIN(channels);
CREATE INDEX idx_layout_templates_usage ON layout_templates(usage_count DESC);
CREATE INDEX idx_layout_templates_performance ON layout_templates(performance_score DESC NULLS LAST);

-- ============================================================================
-- 2. DESIGN_SCORES TABLE
-- ============================================================================

-- Drop and recreate if exists
DROP TABLE IF EXISTS design_scores CASCADE;

CREATE TABLE design_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID,
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

COMMENT ON TABLE design_scores IS 'Quality scores for generated designs';

CREATE INDEX idx_design_scores_asset ON design_scores(asset_id);
CREATE INDEX idx_design_scores_overall ON design_scores(overall_score DESC);
CREATE INDEX idx_design_scores_created ON design_scores(created_at DESC);

-- ============================================================================
-- 3. BRAND_LEARNING TABLE
-- ============================================================================

DROP TABLE IF EXISTS brand_learning CASCADE;

CREATE TABLE brand_learning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_kit_id UUID,
    design_pattern VARCHAR(255),
    user_feedback VARCHAR(50),
    context JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE brand_learning IS 'Machine learning data for brand preference optimization';

CREATE INDEX idx_brand_learning_brand_kit ON brand_learning(brand_kit_id);
CREATE INDEX idx_brand_learning_pattern ON brand_learning(design_pattern);
CREATE INDEX idx_brand_learning_feedback ON brand_learning(user_feedback);

-- ============================================================================
-- 4. DESIGN_EXPORTS TABLE
-- ============================================================================

DROP TABLE IF EXISTS design_exports CASCADE;

CREATE TABLE design_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID,
    platform VARCHAR(50) NOT NULL,
    export_url TEXT,
    editor_url TEXT,
    external_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE design_exports IS 'Track exports to external platforms (Canva, Figma)';

CREATE INDEX idx_design_exports_asset ON design_exports(asset_id);
CREATE INDEX idx_design_exports_platform ON design_exports(platform);
CREATE INDEX idx_design_exports_status ON design_exports(status);

-- ============================================================================
-- 5. ENHANCE BRAND_KITS TABLE (Safe - Only add if not exists)
-- ============================================================================

-- Add columns only if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='brand_kits' AND column_name='tokens_v2') THEN
        ALTER TABLE brand_kits ADD COLUMN tokens_v2 JSONB;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='brand_kits' AND column_name='parsing_metadata') THEN
        ALTER TABLE brand_kits ADD COLUMN parsing_metadata JSONB;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='brand_kits' AND column_name='version') THEN
        ALTER TABLE brand_kits ADD COLUMN version INTEGER DEFAULT 2;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='brand_kits' AND column_name='parent_version') THEN
        ALTER TABLE brand_kits ADD COLUMN parent_version UUID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='brand_kits' AND column_name='ab_test_variant') THEN
        ALTER TABLE brand_kits ADD COLUMN ab_test_variant VARCHAR(50);
    END IF;
END $$;

-- ============================================================================
-- 6. ENHANCE ASSETS TABLE (Safe - Only add if not exists)
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='assets' AND column_name='layout_template_id') THEN
        ALTER TABLE assets ADD COLUMN layout_template_id UUID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='assets' AND column_name='design_plan') THEN
        ALTER TABLE assets ADD COLUMN design_plan JSONB;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='assets' AND column_name='quality_score') THEN
        ALTER TABLE assets ADD COLUMN quality_score INTEGER;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='assets' AND column_name='generation_metadata') THEN
        ALTER TABLE assets ADD COLUMN generation_metadata JSONB;
    END IF;
END $$;

-- ============================================================================
-- 7. INSERT BUILT-IN TEMPLATES
-- ============================================================================

-- Clear existing built-in templates
DELETE FROM layout_templates WHERE is_builtin = TRUE;

-- Insert built-in templates
INSERT INTO layout_templates (name, description, template_schema, aspect_ratios, channels, is_builtin)
VALUES
(
    'Hero with Badge and CTA',
    'Large headline with promotional badge and strong CTA',
    '{"id": "hero_badge_cta_v1", "slots": [{"id": "background", "type": "image", "layer": 0}, {"id": "headline", "type": "text", "layer": 2}, {"id": "cta", "type": "button", "layer": 3}], "rules": {"text_contrast_min": 4.5}}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb'],
    TRUE
),
(
    'Minimal Text',
    'Clean layout with large headline and CTA, minimal distractions',
    '{"id": "minimal_text_v1", "slots": [{"id": "background", "type": "image", "layer": 0}, {"id": "headline", "type": "text", "layer": 2}], "rules": {}}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb', 'linkedin'],
    TRUE
),
(
    'Product Showcase',
    'Large product image with supporting text and CTA',
    '{"id": "product_showcase_v1", "slots": [{"id": "product", "type": "image", "layer": 1}, {"id": "headline", "type": "text", "layer": 2}], "rules": {}}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb'],
    TRUE
),
(
    'Story Immersive',
    'Full-bleed Instagram story with bottom text overlay',
    '{"id": "story_immersive_v1", "slots": [{"id": "background", "type": "image", "layer": 0}, {"id": "gradient", "type": "gradient", "layer": 1}], "rules": {}}'::jsonb,
    ARRAY['9x16'],
    ARRAY['ig'],
    TRUE
),
(
    'Text Heavy',
    'Multiple text blocks for information-dense content',
    '{"id": "text_heavy_v1", "slots": [{"id": "background", "type": "image", "layer": 0}, {"id": "headline", "type": "text", "layer": 2}, {"id": "body", "type": "text", "layer": 2}], "rules": {}}'::jsonb,
    ARRAY['1x1', '16x9'],
    ARRAY['linkedin', 'fb'],
    TRUE
);

-- ============================================================================
-- 8. CREATE VIEWS
-- ============================================================================

-- Drop existing views first
DROP VIEW IF EXISTS top_layout_templates CASCADE;
DROP VIEW IF EXISTS brand_quality_metrics CASCADE;

-- View: Top performing layouts
CREATE VIEW top_layout_templates AS
SELECT
    lt.id,
    lt.name,
    lt.usage_count,
    lt.performance_score,
    AVG(ds.overall_score) AS avg_quality_score,
    COUNT(DISTINCT a.id) AS design_count
FROM layout_templates lt
LEFT JOIN assets a ON a.layout_template_id = lt.id
LEFT JOIN design_scores ds ON ds.asset_id = a.id
GROUP BY lt.id, lt.name, lt.usage_count, lt.performance_score
ORDER BY lt.performance_score DESC NULLS LAST, lt.usage_count DESC;

-- View: Brand quality metrics
CREATE VIEW brand_quality_metrics AS
SELECT
    bk.id AS brand_kit_id,
    bk.name AS brand_name,
    COUNT(DISTINCT a.id) AS total_designs,
    AVG(ds.overall_score) AS avg_quality_score,
    AVG(ds.readability_score) AS avg_readability,
    AVG(ds.brand_consistency_score) AS avg_brand_consistency,
    AVG(ds.accessibility_score) AS avg_accessibility,
    COUNT(DISTINCT de.id) AS export_count
FROM brand_kits bk
LEFT JOIN assets a ON a.brand_kit_id = bk.id
LEFT JOIN design_scores ds ON ds.asset_id = a.id
LEFT JOIN design_exports de ON de.asset_id = a.id
GROUP BY bk.id, bk.name
ORDER BY avg_quality_score DESC NULLS LAST;

-- ============================================================================
-- 9. FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function: Update layout template performance
CREATE OR REPLACE FUNCTION update_layout_template_performance()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE layout_templates
    SET
        performance_score = (
            SELECT AVG(ds.overall_score) / 100.0
            FROM design_scores ds
            JOIN assets a ON a.id = ds.asset_id
            WHERE a.layout_template_id = (
                SELECT layout_template_id FROM assets WHERE id = NEW.asset_id
            )
        ),
        updated_at = NOW()
    WHERE id = (
        SELECT layout_template_id FROM assets WHERE id = NEW.asset_id
    )
    AND (SELECT layout_template_id FROM assets WHERE id = NEW.asset_id) IS NOT NULL;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger
DROP TRIGGER IF EXISTS trigger_update_layout_performance ON design_scores;

-- Create trigger
CREATE TRIGGER trigger_update_layout_performance
AFTER INSERT ON design_scores
FOR EACH ROW
EXECUTE FUNCTION update_layout_template_performance();

-- Function: Increment template usage
CREATE OR REPLACE FUNCTION increment_template_usage()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.layout_template_id IS NOT NULL THEN
        UPDATE layout_templates
        SET usage_count = usage_count + 1,
            updated_at = NOW()
        WHERE id = NEW.layout_template_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger
DROP TRIGGER IF EXISTS trigger_increment_template_usage ON assets;

-- Create trigger
CREATE TRIGGER trigger_increment_template_usage
AFTER INSERT ON assets
FOR EACH ROW
EXECUTE FUNCTION increment_template_usage();

-- ============================================================================
-- 10. VERIFY MIGRATION
-- ============================================================================

-- Check tables exist
SELECT 'layout_templates' AS table_name, COUNT(*) AS row_count FROM layout_templates
UNION ALL
SELECT 'design_scores', COUNT(*) FROM design_scores
UNION ALL
SELECT 'brand_learning', COUNT(*) FROM brand_learning
UNION ALL
SELECT 'design_exports', COUNT(*) FROM design_exports;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration V3 FIX completed successfully';
    RAISE NOTICE 'Created tables: layout_templates, design_scores, brand_learning, design_exports';
    RAISE NOTICE 'Enhanced tables: brand_kits, assets';
    RAISE NOTICE 'Created views: top_layout_templates, brand_quality_metrics';
    RAISE NOTICE 'Inserted 5 built-in layout templates';
END $$;
