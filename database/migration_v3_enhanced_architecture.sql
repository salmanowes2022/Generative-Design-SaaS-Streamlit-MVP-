-- ============================================================================
-- Migration V3: Enhanced Architecture
-- Adds support for advanced brand parsing, layout templates, quality scoring
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. ENHANCE BRAND_KITS TABLE
-- ============================================================================

-- Add V2 schema columns
ALTER TABLE brand_kits
ADD COLUMN IF NOT EXISTS tokens_v2 JSONB,
ADD COLUMN IF NOT EXISTS parsing_metadata JSONB,
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 2,
ADD COLUMN IF NOT EXISTS parent_version UUID REFERENCES brand_kits(id),
ADD COLUMN IF NOT EXISTS ab_test_variant VARCHAR(50);

-- Add comments
COMMENT ON COLUMN brand_kits.tokens_v2 IS 'Enhanced brand tokens with V2 schema (colors, typography, layout, voice, policies)';
COMMENT ON COLUMN brand_kits.parsing_metadata IS 'Metadata from PDF parsing (pages processed, confidence score, etc.)';
COMMENT ON COLUMN brand_kits.version IS 'Brand kit schema version (2 = V2 enhanced)';
COMMENT ON COLUMN brand_kits.parent_version IS 'Reference to parent version for version control';
COMMENT ON COLUMN brand_kits.ab_test_variant IS 'A/B test variant identifier';

-- Create index on version
CREATE INDEX IF NOT EXISTS idx_brand_kits_version ON brand_kits(version);

-- ============================================================================
-- 2. LAYOUT TEMPLATES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS layout_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_schema JSONB NOT NULL,
    aspect_ratios TEXT[] NOT NULL,
    channels TEXT[] NOT NULL,
    usage_count INTEGER DEFAULT 0,
    performance_score DECIMAL(3,2),
    is_builtin BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES organizations(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comments
COMMENT ON TABLE layout_templates IS 'Layout templates for design composition';
COMMENT ON COLUMN layout_templates.template_schema IS 'Complete layout specification (slots, rules, etc.)';
COMMENT ON COLUMN layout_templates.aspect_ratios IS 'Supported aspect ratios (1x1, 4x5, 9x16, 16x9)';
COMMENT ON COLUMN layout_templates.channels IS 'Supported channels (ig, fb, linkedin, twitter)';
COMMENT ON COLUMN layout_templates.usage_count IS 'Number of times template has been used';
COMMENT ON COLUMN layout_templates.performance_score IS 'Average quality score of designs using this template';
COMMENT ON COLUMN layout_templates.is_builtin IS 'Whether template is built-in or custom';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_layout_templates_aspect ON layout_templates USING GIN(aspect_ratios);
CREATE INDEX IF NOT EXISTS idx_layout_templates_channels ON layout_templates USING GIN(channels);
CREATE INDEX IF NOT EXISTS idx_layout_templates_usage ON layout_templates(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_layout_templates_performance ON layout_templates(performance_score DESC NULLS LAST);

-- ============================================================================
-- 3. DESIGN SCORES TABLE
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

-- Comments
COMMENT ON TABLE design_scores IS 'Quality scores for generated designs';
COMMENT ON COLUMN design_scores.overall_score IS 'Overall quality score (0-100)';
COMMENT ON COLUMN design_scores.issues IS 'JSON array of issues found in each category';
COMMENT ON COLUMN design_scores.suggestions IS 'JSON array of improvement suggestions';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_design_scores_asset ON design_scores(asset_id);
CREATE INDEX IF NOT EXISTS idx_design_scores_overall ON design_scores(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_design_scores_created ON design_scores(created_at DESC);

-- ============================================================================
-- 4. BRAND LEARNING TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS brand_learning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_kit_id UUID REFERENCES brand_kits(id) ON DELETE CASCADE,
    design_pattern VARCHAR(255),
    user_feedback VARCHAR(50),
    context JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comments
COMMENT ON TABLE brand_learning IS 'Machine learning data for brand preference optimization';
COMMENT ON COLUMN brand_learning.design_pattern IS 'Design pattern used (e.g., high_contrast, minimal, text_heavy)';
COMMENT ON COLUMN brand_learning.user_feedback IS 'User feedback (liked, disliked, exported, shared)';
COMMENT ON COLUMN brand_learning.context IS 'Design context (channel, campaign, etc.)';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_brand_learning_brand_kit ON brand_learning(brand_kit_id);
CREATE INDEX IF NOT EXISTS idx_brand_learning_pattern ON brand_learning(design_pattern);
CREATE INDEX IF NOT EXISTS idx_brand_learning_feedback ON brand_learning(user_feedback);
CREATE INDEX IF NOT EXISTS idx_brand_learning_created ON brand_learning(created_at DESC);

-- ============================================================================
-- 5. DESIGN EXPORTS TABLE
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

-- Comments
COMMENT ON TABLE design_exports IS 'Track exports to external platforms (Canva, Figma)';
COMMENT ON COLUMN design_exports.platform IS 'Export platform (canva, figma)';
COMMENT ON COLUMN design_exports.export_url IS 'URL to exported design';
COMMENT ON COLUMN design_exports.editor_url IS 'URL to edit exported design';
COMMENT ON COLUMN design_exports.external_id IS 'Platform-specific design ID';
COMMENT ON COLUMN design_exports.status IS 'Export status (pending, success, failed)';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_design_exports_asset ON design_exports(asset_id);
CREATE INDEX IF NOT EXISTS idx_design_exports_platform ON design_exports(platform);
CREATE INDEX IF NOT EXISTS idx_design_exports_status ON design_exports(status);

-- ============================================================================
-- 6. ENHANCE ASSETS TABLE
-- ============================================================================

ALTER TABLE assets
ADD COLUMN IF NOT EXISTS layout_template_id UUID REFERENCES layout_templates(id),
ADD COLUMN IF NOT EXISTS design_plan JSONB,
ADD COLUMN IF NOT EXISTS quality_score INTEGER,
ADD COLUMN IF NOT EXISTS generation_metadata JSONB;

-- Comments
COMMENT ON COLUMN assets.layout_template_id IS 'Layout template used to create this asset';
COMMENT ON COLUMN assets.design_plan IS 'Original design plan (headline, subhead, cta, etc.)';
COMMENT ON COLUMN assets.quality_score IS 'Cached overall quality score';
COMMENT ON COLUMN assets.generation_metadata IS 'Metadata about generation (DALL-E params, render time, etc.)';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_assets_layout_template ON assets(layout_template_id);
CREATE INDEX IF NOT EXISTS idx_assets_quality_score ON assets(quality_score DESC NULLS LAST);

-- ============================================================================
-- 7. VIEWS FOR ANALYTICS
-- ============================================================================

-- View: Top performing layouts
CREATE OR REPLACE VIEW top_layout_templates AS
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

COMMENT ON VIEW top_layout_templates IS 'Top performing layout templates by quality and usage';

-- View: Brand quality metrics
CREATE OR REPLACE VIEW brand_quality_metrics AS
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

COMMENT ON VIEW brand_quality_metrics IS 'Quality metrics aggregated by brand kit';

-- ============================================================================
-- 8. FUNCTIONS
-- ============================================================================

-- Function: Update layout template performance
CREATE OR REPLACE FUNCTION update_layout_template_performance()
RETURNS TRIGGER AS $$
BEGIN
    -- Update performance score when new design score is added
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
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Update template performance on new score
DROP TRIGGER IF EXISTS trigger_update_layout_performance ON design_scores;
CREATE TRIGGER trigger_update_layout_performance
AFTER INSERT ON design_scores
FOR EACH ROW
EXECUTE FUNCTION update_layout_template_performance();

-- Function: Increment template usage
CREATE OR REPLACE FUNCTION increment_template_usage()
RETURNS TRIGGER AS $$
BEGIN
    -- Increment usage count when asset is created with template
    IF NEW.layout_template_id IS NOT NULL THEN
        UPDATE layout_templates
        SET usage_count = usage_count + 1,
            updated_at = NOW()
        WHERE id = NEW.layout_template_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Increment usage on asset creation
DROP TRIGGER IF EXISTS trigger_increment_template_usage ON assets;
CREATE TRIGGER trigger_increment_template_usage
AFTER INSERT ON assets
FOR EACH ROW
EXECUTE FUNCTION increment_template_usage();

-- ============================================================================
-- 9. SEED BUILT-IN LAYOUT TEMPLATES
-- ============================================================================

-- Insert built-in templates (simplified JSON - full schema would be larger)
INSERT INTO layout_templates (name, description, template_schema, aspect_ratios, channels, is_builtin)
VALUES
(
    'Hero with Badge and CTA',
    'Large headline with promotional badge and strong CTA',
    '{"id": "hero_badge_cta_v1", "slots": [], "rules": {}}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb'],
    TRUE
),
(
    'Minimal Text',
    'Clean layout with large headline and CTA, minimal distractions',
    '{"id": "minimal_text_v1", "slots": [], "rules": {}}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb', 'linkedin'],
    TRUE
),
(
    'Product Showcase',
    'Large product image with supporting text and CTA',
    '{"id": "product_showcase_v1", "slots": [], "rules": {}}'::jsonb,
    ARRAY['1x1', '4x5'],
    ARRAY['ig', 'fb'],
    TRUE
),
(
    'Story Immersive',
    'Full-bleed Instagram story with bottom text overlay',
    '{"id": "story_immersive_v1", "slots": [], "rules": {}}'::jsonb,
    ARRAY['9x16'],
    ARRAY['ig'],
    TRUE
),
(
    'Text Heavy',
    'Multiple text blocks for information-dense content',
    '{"id": "text_heavy_v1", "slots": [], "rules": {}}'::jsonb,
    ARRAY['1x1', '16x9'],
    ARRAY['linkedin', 'fb'],
    TRUE
)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 10. GRANT PERMISSIONS
-- ============================================================================

-- Grant permissions to app user (adjust user name as needed)
-- GRANT ALL ON layout_templates TO your_app_user;
-- GRANT ALL ON design_scores TO your_app_user;
-- GRANT ALL ON brand_learning TO your_app_user;
-- GRANT ALL ON design_exports TO your_app_user;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify tables
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

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration V3 completed successfully';
    RAISE NOTICE 'Created tables: layout_templates, design_scores, brand_learning, design_exports';
    RAISE NOTICE 'Enhanced tables: brand_kits, assets';
    RAISE NOTICE 'Created views: top_layout_templates, brand_quality_metrics';
END $$;
