-- ============================================================================
-- Migration V3 for Supabase SQL Editor
-- Copy and paste this entire file into Supabase SQL Editor and run
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- STEP 1: Enhance existing tables first
-- ============================================================================

-- Add columns to layout_templates
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='layout_templates' AND column_name='template_schema') THEN
        ALTER TABLE layout_templates ADD COLUMN template_schema JSONB;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='layout_templates' AND column_name='aspect_ratios') THEN
        ALTER TABLE layout_templates ADD COLUMN aspect_ratios TEXT[];
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='layout_templates' AND column_name='channels') THEN
        ALTER TABLE layout_templates ADD COLUMN channels TEXT[];
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='layout_templates' AND column_name='is_builtin') THEN
        ALTER TABLE layout_templates ADD COLUMN is_builtin BOOLEAN DEFAULT FALSE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='layout_templates' AND column_name='usage_count') THEN
        ALTER TABLE layout_templates ADD COLUMN usage_count INTEGER DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='layout_templates' AND column_name='performance_score') THEN
        ALTER TABLE layout_templates ADD COLUMN performance_score DECIMAL(3,2);
    END IF;
END $$;

-- Add columns to brand_kits
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
                   WHERE table_name='brand_kits' AND column_name='parent_version') THEN
        ALTER TABLE brand_kits ADD COLUMN parent_version UUID REFERENCES brand_kits(id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='brand_kits' AND column_name='ab_test_variant') THEN
        ALTER TABLE brand_kits ADD COLUMN ab_test_variant VARCHAR(50);
    END IF;
END $$;

-- Add columns to assets (IMPORTANT: Do this first!)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='assets' AND column_name='brand_kit_id') THEN
        ALTER TABLE assets ADD COLUMN brand_kit_id UUID REFERENCES brand_kits(id);
        RAISE NOTICE 'Added brand_kit_id to assets';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='assets' AND column_name='layout_template_id') THEN
        ALTER TABLE assets ADD COLUMN layout_template_id UUID REFERENCES layout_templates(id);
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
-- STEP 2: Create indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_layout_templates_aspect ON layout_templates USING GIN(aspect_ratios);
CREATE INDEX IF NOT EXISTS idx_layout_templates_channels ON layout_templates USING GIN(channels);
CREATE INDEX IF NOT EXISTS idx_layout_templates_usage ON layout_templates(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_assets_layout_template ON assets(layout_template_id);
CREATE INDEX IF NOT EXISTS idx_assets_quality_score ON assets(quality_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_assets_brand_kit ON assets(brand_kit_id);

-- ============================================================================
-- STEP 3: Create new tables
-- ============================================================================

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

CREATE TABLE IF NOT EXISTS brand_learning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_kit_id UUID REFERENCES brand_kits(id) ON DELETE CASCADE,
    design_pattern VARCHAR(255),
    user_feedback VARCHAR(50),
    context JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_brand_learning_brand_kit ON brand_learning(brand_kit_id);

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

-- ============================================================================
-- STEP 4: Insert built-in templates
-- ============================================================================

DELETE FROM layout_templates WHERE is_builtin = TRUE;

INSERT INTO layout_templates (name, category, description, template_schema, aspect_ratios, channels, is_builtin, usage_count)
VALUES
(
    'Hero with Badge and CTA',
    'promotional',
    'Large headline with promotional badge and strong CTA',
    '{"id": "hero_badge_cta_v1", "slots": [{"id": "background", "type": "image", "layer": 0}, {"id": "headline", "type": "text", "layer": 2}]}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb'],
    TRUE,
    0
),
(
    'Minimal Text',
    'minimal',
    'Clean layout with large headline and CTA',
    '{"id": "minimal_text_v1", "slots": []}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb', 'linkedin'],
    TRUE,
    0
),
(
    'Product Showcase',
    'product',
    'Large product image with text',
    '{"id": "product_showcase_v1", "slots": []}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb'],
    TRUE,
    0
),
(
    'Story Immersive',
    'story',
    'Full-bleed Instagram story',
    '{"id": "story_immersive_v1", "slots": []}'::jsonb,
    ARRAY['9x16'],
    ARRAY['ig'],
    TRUE,
    0
),
(
    'Text Heavy',
    'informational',
    'Information-dense layout',
    '{"id": "text_heavy_v1", "slots": []}'::jsonb,
    ARRAY['1x1', '16x9'],
    ARRAY['linkedin', 'fb'],
    TRUE,
    0
);

-- ============================================================================
-- STEP 5: Create views (NOW brand_kit_id exists!)
-- ============================================================================

DROP VIEW IF EXISTS top_layout_templates CASCADE;

CREATE VIEW top_layout_templates AS
SELECT
    lt.id,
    lt.name,
    lt.usage_count,
    lt.performance_score,
    COUNT(DISTINCT a.id) AS design_count,
    AVG(ds.overall_score) AS avg_quality_score
FROM layout_templates lt
LEFT JOIN assets a ON a.layout_template_id = lt.id
LEFT JOIN design_scores ds ON ds.asset_id = a.id
GROUP BY lt.id, lt.name, lt.usage_count, lt.performance_score
ORDER BY lt.usage_count DESC;

DROP VIEW IF EXISTS brand_quality_metrics CASCADE;

CREATE VIEW brand_quality_metrics AS
SELECT
    bk.id AS brand_kit_id,
    bk.name AS brand_name,
    bk.org_id,
    COUNT(DISTINCT a.id) AS total_designs,
    AVG(ds.overall_score) AS avg_quality_score,
    COUNT(DISTINCT de.id) AS export_count
FROM brand_kits bk
LEFT JOIN assets a ON a.brand_kit_id = bk.id
LEFT JOIN design_scores ds ON ds.asset_id = a.id
LEFT JOIN design_exports de ON de.asset_id = a.id
GROUP BY bk.id, bk.name, bk.org_id;

-- ============================================================================
-- STEP 6: Create functions and triggers
-- ============================================================================

CREATE OR REPLACE FUNCTION update_layout_template_performance()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE layout_templates
    SET performance_score = (
        SELECT AVG(ds.overall_score) / 100.0
        FROM design_scores ds
        JOIN assets a ON a.id = ds.asset_id
        WHERE a.layout_template_id = (
            SELECT layout_template_id FROM assets WHERE id = NEW.asset_id
        )
    )
    WHERE id = (SELECT layout_template_id FROM assets WHERE id = NEW.asset_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_layout_performance ON design_scores;
CREATE TRIGGER trigger_update_layout_performance
AFTER INSERT ON design_scores
FOR EACH ROW
EXECUTE FUNCTION update_layout_template_performance();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'Migration completed successfully!' AS status;

SELECT COUNT(*) AS builtin_templates FROM layout_templates WHERE is_builtin = TRUE;

SELECT table_name,
       (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) AS columns
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_name IN ('layout_templates', 'design_scores', 'brand_learning', 'design_exports')
ORDER BY table_name;
