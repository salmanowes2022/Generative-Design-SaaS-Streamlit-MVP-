-- ============================================================================
-- Migration V3 FINAL - Tailored to Your Existing Schema
-- Based on your actual database structure
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. UPDATE LAYOUT_TEMPLATES (Already exists, just ensure correct schema)
-- ============================================================================

-- Check if template_schema column exists, if not, add it
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='layout_templates' AND column_name='template_schema') THEN
        ALTER TABLE layout_templates ADD COLUMN template_schema JSONB;
        RAISE NOTICE 'Added template_schema column to layout_templates';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='layout_templates' AND column_name='aspect_ratios') THEN
        ALTER TABLE layout_templates ADD COLUMN aspect_ratios TEXT[];
        RAISE NOTICE 'Added aspect_ratios column to layout_templates';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='layout_templates' AND column_name='channels') THEN
        ALTER TABLE layout_templates ADD COLUMN channels TEXT[];
        RAISE NOTICE 'Added channels column to layout_templates';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='layout_templates' AND column_name='is_builtin') THEN
        ALTER TABLE layout_templates ADD COLUMN is_builtin BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added is_builtin column to layout_templates';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='layout_templates' AND column_name='usage_count') THEN
        ALTER TABLE layout_templates ADD COLUMN usage_count INTEGER DEFAULT 0;
        RAISE NOTICE 'Added usage_count column to layout_templates';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='layout_templates' AND column_name='performance_score') THEN
        ALTER TABLE layout_templates ADD COLUMN performance_score DECIMAL(3,2);
        RAISE NOTICE 'Added performance_score column to layout_templates';
    END IF;
END $$;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_layout_templates_aspect ON layout_templates USING GIN(aspect_ratios);
CREATE INDEX IF NOT EXISTS idx_layout_templates_channels ON layout_templates USING GIN(channels);
CREATE INDEX IF NOT EXISTS idx_layout_templates_usage ON layout_templates(usage_count DESC);

-- ============================================================================
-- 2. CREATE DESIGN_SCORES TABLE (if not exists)
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
CREATE INDEX IF NOT EXISTS idx_design_scores_created ON design_scores(created_at DESC);

-- ============================================================================
-- 3. CREATE BRAND_LEARNING TABLE (if not exists)
-- ============================================================================

CREATE TABLE IF NOT EXISTS brand_learning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_kit_id UUID REFERENCES brand_kits(id) ON DELETE CASCADE,
    design_pattern VARCHAR(255),
    user_feedback VARCHAR(50),
    context JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_brand_learning_brand_kit ON brand_learning(brand_kit_id);
CREATE INDEX IF NOT EXISTS idx_brand_learning_pattern ON brand_learning(design_pattern);
CREATE INDEX IF NOT EXISTS idx_brand_learning_feedback ON brand_learning(user_feedback);

-- ============================================================================
-- 4. CREATE DESIGN_EXPORTS TABLE (if not exists)
-- ============================================================================

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
CREATE INDEX IF NOT EXISTS idx_design_exports_platform ON design_exports(platform);
CREATE INDEX IF NOT EXISTS idx_design_exports_status ON design_exports(status);

-- ============================================================================
-- 5. ENHANCE BRAND_KITS TABLE (add V3 columns)
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='brand_kits' AND column_name='tokens_v2') THEN
        ALTER TABLE brand_kits ADD COLUMN tokens_v2 JSONB;
        RAISE NOTICE 'Added tokens_v2 to brand_kits';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='brand_kits' AND column_name='parsing_metadata') THEN
        ALTER TABLE brand_kits ADD COLUMN parsing_metadata JSONB;
        RAISE NOTICE 'Added parsing_metadata to brand_kits';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='brand_kits' AND column_name='parent_version') THEN
        ALTER TABLE brand_kits ADD COLUMN parent_version UUID REFERENCES brand_kits(id);
        RAISE NOTICE 'Added parent_version to brand_kits';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='brand_kits' AND column_name='ab_test_variant') THEN
        ALTER TABLE brand_kits ADD COLUMN ab_test_variant VARCHAR(50);
        RAISE NOTICE 'Added ab_test_variant to brand_kits';
    END IF;
END $$;

-- ============================================================================
-- 6. ENHANCE ASSETS TABLE (add V3 columns)
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='assets' AND column_name='layout_template_id') THEN
        ALTER TABLE assets ADD COLUMN layout_template_id UUID REFERENCES layout_templates(id);
        RAISE NOTICE 'Added layout_template_id to assets';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='assets' AND column_name='design_plan') THEN
        ALTER TABLE assets ADD COLUMN design_plan JSONB;
        RAISE NOTICE 'Added design_plan to assets';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='assets' AND column_name='quality_score') THEN
        ALTER TABLE assets ADD COLUMN quality_score INTEGER;
        RAISE NOTICE 'Added quality_score to assets';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='assets' AND column_name='generation_metadata') THEN
        ALTER TABLE assets ADD COLUMN generation_metadata JSONB;
        RAISE NOTICE 'Added generation_metadata to assets';
    END IF;

    -- Add brand_kit_id for easier brand-based queries
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='assets' AND column_name='brand_kit_id') THEN
        ALTER TABLE assets ADD COLUMN brand_kit_id UUID REFERENCES brand_kits(id);
        RAISE NOTICE 'Added brand_kit_id to assets (will need to be populated from jobs/context)';
    END IF;
END $$;

-- Create indexes on new columns
CREATE INDEX IF NOT EXISTS idx_assets_layout_template ON assets(layout_template_id);
CREATE INDEX IF NOT EXISTS idx_assets_quality_score ON assets(quality_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_assets_brand_kit ON assets(brand_kit_id);

-- ============================================================================
-- 7. INSERT BUILT-IN TEMPLATES (only if they don't exist)
-- ============================================================================

-- Delete old test data if any
DELETE FROM layout_templates WHERE is_builtin = TRUE;

-- Insert built-in templates
INSERT INTO layout_templates (name, description, template_schema, aspect_ratios, channels, is_builtin, usage_count)
VALUES
(
    'Hero with Badge and CTA',
    'Large headline with promotional badge and strong CTA',
    '{"id": "hero_badge_cta_v1", "slots": [{"id": "background", "type": "image", "layer": 0}, {"id": "headline", "type": "text", "layer": 2}, {"id": "subhead", "type": "text", "layer": 2}, {"id": "cta", "type": "button", "layer": 3}, {"id": "logo", "type": "image", "layer": 4}], "rules": {"text_contrast_min": 4.5}}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb'],
    TRUE,
    0
),
(
    'Minimal Text',
    'Clean layout with large headline and CTA, minimal distractions',
    '{"id": "minimal_text_v1", "slots": [{"id": "background", "type": "image"}, {"id": "headline", "type": "text"}, {"id": "cta", "type": "button"}], "rules": {}}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb', 'linkedin'],
    TRUE,
    0
),
(
    'Product Showcase',
    'Large product image with supporting text and CTA',
    '{"id": "product_showcase_v1", "slots": [{"id": "product", "type": "image"}, {"id": "headline", "type": "text"}], "rules": {}}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb'],
    TRUE,
    0
),
(
    'Story Immersive',
    'Full-bleed Instagram story with bottom text overlay',
    '{"id": "story_immersive_v1", "slots": [{"id": "background", "type": "image"}, {"id": "gradient", "type": "gradient"}], "rules": {}}'::jsonb,
    ARRAY['9x16'],
    ARRAY['ig'],
    TRUE,
    0
),
(
    'Text Heavy',
    'Multiple text blocks for information-dense content',
    '{"id": "text_heavy_v1", "slots": [{"id": "headline", "type": "text"}, {"id": "body", "type": "text"}], "rules": {}}'::jsonb,
    ARRAY['1x1', '16x9'],
    ARRAY['linkedin', 'fb'],
    TRUE,
    0
)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 8. CREATE VIEWS (Using your actual schema)
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
ORDER BY lt.performance_score DESC NULLS LAST, lt.usage_count DESC;

DROP VIEW IF EXISTS brand_quality_metrics CASCADE;

CREATE VIEW brand_quality_metrics AS
SELECT
    bk.id AS brand_kit_id,
    bk.name AS brand_name,
    bk.org_id,
    COUNT(DISTINCT a.id) AS total_designs,
    AVG(ds.overall_score) AS avg_quality_score,
    AVG(ds.readability_score) AS avg_readability,
    AVG(ds.brand_consistency_score) AS avg_brand_consistency,
    AVG(ds.accessibility_score) AS avg_accessibility,
    COUNT(DISTINCT de.id) AS export_count
FROM brand_kits bk
LEFT JOIN assets a ON a.brand_kit_id = bk.id OR a.org_id = bk.org_id
LEFT JOIN design_scores ds ON ds.asset_id = a.id
LEFT JOIN design_exports de ON de.asset_id = a.id
GROUP BY bk.id, bk.name, bk.org_id
ORDER BY avg_quality_score DESC NULLS LAST;

-- ============================================================================
-- 9. FUNCTIONS & TRIGGERS
-- ============================================================================

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

DROP TRIGGER IF EXISTS trigger_update_layout_performance ON design_scores;
CREATE TRIGGER trigger_update_layout_performance
AFTER INSERT ON design_scores
FOR EACH ROW
EXECUTE FUNCTION update_layout_template_performance();

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

DROP TRIGGER IF EXISTS trigger_increment_template_usage ON assets;
CREATE TRIGGER trigger_increment_template_usage
AFTER INSERT ON assets
FOR EACH ROW
EXECUTE FUNCTION increment_template_usage();

-- ============================================================================
-- 10. VERIFICATION
-- ============================================================================

SELECT
    'layout_templates' AS table_name,
    COUNT(*) AS row_count,
    COUNT(*) FILTER (WHERE is_builtin = TRUE) AS builtin_count
FROM layout_templates
UNION ALL
SELECT 'design_scores', COUNT(*), NULL FROM design_scores
UNION ALL
SELECT 'brand_learning', COUNT(*), NULL FROM brand_learning
UNION ALL
SELECT 'design_exports', COUNT(*), NULL FROM design_exports;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✅ ================================================';
    RAISE NOTICE '✅ Migration V3 FINAL completed successfully!';
    RAISE NOTICE '✅ ================================================';
    RAISE NOTICE '';
    RAISE NOTICE '📦 Tables updated:';
    RAISE NOTICE '   • layout_templates (enhanced with new columns)';
    RAISE NOTICE '   • design_scores (created)';
    RAISE NOTICE '   • brand_learning (created)';
    RAISE NOTICE '   • design_exports (created)';
    RAISE NOTICE '   • brand_kits (added V3 columns)';
    RAISE NOTICE '   • assets (added V3 columns)';
    RAISE NOTICE '';
    RAISE NOTICE '✨ Built-in templates: 5 inserted';
    RAISE NOTICE '📊 Views created: top_layout_templates, brand_quality_metrics';
    RAISE NOTICE '🔧 Triggers created: Auto-update performance & usage';
    RAISE NOTICE '';
    RAISE NOTICE '🎉 Next steps:';
    RAISE NOTICE '   1. Run: python test_v3_complete.py';
    RAISE NOTICE '   2. Start: streamlit run app/streamlit_app.py';
    RAISE NOTICE '   3. See: QUICK_START_V3.md for integration';
    RAISE NOTICE '';
END $$;
