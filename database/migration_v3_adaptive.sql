-- ============================================================================
-- Migration V3 ADAPTIVE - Works with Your Existing Schema
-- This version adapts to your current database structure
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. CREATE NEW TABLES (Drop existing if they exist)
-- ============================================================================

-- Layout Templates
DROP TABLE IF EXISTS layout_templates CASCADE;

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

CREATE INDEX idx_layout_templates_aspect ON layout_templates USING GIN(aspect_ratios);
CREATE INDEX idx_layout_templates_channels ON layout_templates USING GIN(channels);

-- Design Scores
DROP TABLE IF EXISTS design_scores CASCADE;

CREATE TABLE design_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID,
    overall_score INTEGER NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    readability_score INTEGER,
    brand_consistency_score INTEGER,
    composition_score INTEGER,
    impact_score INTEGER,
    accessibility_score INTEGER,
    issues JSONB,
    suggestions JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_design_scores_asset ON design_scores(asset_id);
CREATE INDEX idx_design_scores_overall ON design_scores(overall_score DESC);

-- Brand Learning
DROP TABLE IF EXISTS brand_learning CASCADE;

CREATE TABLE brand_learning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_kit_id UUID,
    design_pattern VARCHAR(255),
    user_feedback VARCHAR(50),
    context JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_brand_learning_brand_kit ON brand_learning(brand_kit_id);

-- Design Exports
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

CREATE INDEX idx_design_exports_asset ON design_exports(asset_id);

-- ============================================================================
-- 2. ENHANCE EXISTING TABLES (Safe - Only add if not exists)
-- ============================================================================

-- Add columns to brand_kits (if they don't exist)
DO $$
BEGIN
    -- Check if brand_kits table exists first
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'brand_kits') THEN

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
                       WHERE table_name='brand_kits' AND column_name='version') THEN
            ALTER TABLE brand_kits ADD COLUMN version INTEGER DEFAULT 2;
            RAISE NOTICE 'Added version to brand_kits';
        END IF;

    ELSE
        RAISE NOTICE 'brand_kits table does not exist - skipping';
    END IF;
END $$;

-- Add columns to assets (if they don't exist)
DO $$
BEGIN
    -- Check if assets table exists first
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'assets') THEN

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name='assets' AND column_name='layout_template_id') THEN
            ALTER TABLE assets ADD COLUMN layout_template_id UUID;
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

        -- Add brand_kit_id if it doesn't exist (likely missing based on error)
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name='assets' AND column_name='brand_kit_id') THEN
            ALTER TABLE assets ADD COLUMN brand_kit_id UUID;
            RAISE NOTICE 'Added brand_kit_id to assets';
        END IF;

    ELSE
        RAISE NOTICE 'assets table does not exist - skipping';
    END IF;
END $$;

-- ============================================================================
-- 3. INSERT BUILT-IN TEMPLATES
-- ============================================================================

INSERT INTO layout_templates (name, description, template_schema, aspect_ratios, channels, is_builtin)
VALUES
(
    'Hero with Badge and CTA',
    'Large headline with promotional badge and strong CTA',
    '{"id": "hero_badge_cta_v1", "slots": [{"id": "background", "type": "image", "layer": 0}, {"id": "headline", "type": "text", "layer": 2}, {"id": "cta", "type": "button", "layer": 3}]}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb'],
    TRUE
),
(
    'Minimal Text',
    'Clean layout with large headline and CTA',
    '{"id": "minimal_text_v1", "slots": []}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb', 'linkedin'],
    TRUE
),
(
    'Product Showcase',
    'Large product image with text and CTA',
    '{"id": "product_showcase_v1", "slots": []}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb'],
    TRUE
),
(
    'Story Immersive',
    'Full-bleed Instagram story',
    '{"id": "story_immersive_v1", "slots": []}'::jsonb,
    ARRAY['9x16'],
    ARRAY['ig'],
    TRUE
),
(
    'Text Heavy',
    'Information-dense layout',
    '{"id": "text_heavy_v1", "slots": []}'::jsonb,
    ARRAY['1x1', '16x9'],
    ARRAY['linkedin', 'fb'],
    TRUE
);

-- ============================================================================
-- 4. CREATE VIEWS (Adaptive - handles missing columns)
-- ============================================================================

DROP VIEW IF EXISTS top_layout_templates CASCADE;

CREATE VIEW top_layout_templates AS
SELECT
    lt.id,
    lt.name,
    lt.usage_count,
    lt.performance_score,
    COUNT(DISTINCT CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'assets' AND column_name = 'layout_template_id'
    ) THEN a.id END) AS design_count,
    AVG(ds.overall_score) AS avg_quality_score
FROM layout_templates lt
LEFT JOIN LATERAL (
    SELECT id FROM assets WHERE layout_template_id = lt.id
) a ON true
LEFT JOIN design_scores ds ON ds.asset_id = a.id
GROUP BY lt.id, lt.name, lt.usage_count, lt.performance_score
ORDER BY lt.usage_count DESC;

DROP VIEW IF EXISTS brand_quality_metrics CASCADE;

CREATE VIEW brand_quality_metrics AS
SELECT
    bk.id AS brand_kit_id,
    bk.name AS brand_name,
    COUNT(DISTINCT CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'assets' AND column_name = 'brand_kit_id'
    ) THEN a.id END) AS total_designs,
    AVG(ds.overall_score) AS avg_quality_score,
    COUNT(DISTINCT de.id) AS export_count
FROM brand_kits bk
LEFT JOIN LATERAL (
    SELECT id FROM assets
    WHERE CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'assets' AND column_name = 'brand_kit_id'
    ) THEN brand_kit_id = bk.id ELSE false END
) a ON true
LEFT JOIN design_scores ds ON ds.asset_id = a.id
LEFT JOIN design_exports de ON de.asset_id = a.id
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'brand_kits')
GROUP BY bk.id, bk.name;

-- ============================================================================
-- 5. FUNCTIONS & TRIGGERS (Only if assets table has necessary columns)
-- ============================================================================

CREATE OR REPLACE FUNCTION update_layout_template_performance()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'assets' AND column_name = 'layout_template_id') THEN

        UPDATE layout_templates
        SET performance_score = (
            SELECT AVG(ds.overall_score) / 100.0
            FROM design_scores ds
            JOIN assets a ON a.id = ds.asset_id
            WHERE a.layout_template_id = (
                SELECT layout_template_id FROM assets WHERE id = NEW.asset_id
            )
        ),
        updated_at = NOW()
        WHERE id = (SELECT layout_template_id FROM assets WHERE id = NEW.asset_id)
        AND (SELECT layout_template_id FROM assets WHERE id = NEW.asset_id) IS NOT NULL;

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_layout_performance ON design_scores;
CREATE TRIGGER trigger_update_layout_performance
AFTER INSERT ON design_scores
FOR EACH ROW
EXECUTE FUNCTION update_layout_template_performance();

-- ============================================================================
-- 6. VERIFICATION
-- ============================================================================

SELECT
    'layout_templates' AS table_name,
    COUNT(*) AS row_count
FROM layout_templates
UNION ALL
SELECT 'design_scores', COUNT(*) FROM design_scores
UNION ALL
SELECT 'brand_learning', COUNT(*) FROM brand_learning
UNION ALL
SELECT 'design_exports', COUNT(*) FROM design_exports;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration V3 ADAPTIVE completed successfully!';
    RAISE NOTICE 'Created: layout_templates, design_scores, brand_learning, design_exports';
    RAISE NOTICE 'Enhanced: brand_kits, assets (columns added safely)';
    RAISE NOTICE 'Inserted: 5 built-in layout templates';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Run: python test_v3_complete.py';
    RAISE NOTICE '  2. Start: streamlit run app/streamlit_app.py';
END $$;
