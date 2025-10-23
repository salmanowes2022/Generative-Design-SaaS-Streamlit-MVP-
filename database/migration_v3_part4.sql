-- ============================================================================
-- Migration V3 - PART 4: Create Views and Functions
-- Run this AFTER part 3
-- ============================================================================

-- Create view: Top performing templates
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

-- Create view: Brand quality metrics
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

-- Create function: Update template performance
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

-- Create trigger
DROP TRIGGER IF EXISTS trigger_update_layout_performance ON design_scores;
CREATE TRIGGER trigger_update_layout_performance
AFTER INSERT ON design_scores
FOR EACH ROW
EXECUTE FUNCTION update_layout_template_performance();

SELECT 'Part 4 completed - Views and functions created!' AS status;
