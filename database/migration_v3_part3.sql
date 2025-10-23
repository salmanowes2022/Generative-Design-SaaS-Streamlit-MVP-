-- ============================================================================
-- Migration V3 - PART 3: Insert Built-in Templates
-- Run this AFTER part 2
-- ============================================================================

-- Delete old built-in templates if any
DELETE FROM layout_templates WHERE is_builtin = TRUE;

-- Insert 5 built-in templates
INSERT INTO layout_templates (name, category, aspect_ratio, canvas, slots, description, template_schema, aspect_ratios, channels, is_builtin, usage_count)
VALUES
(
    'Hero with Badge and CTA',
    'promotional',
    '1x1',
    '{"width": 1080, "height": 1080}'::jsonb,
    '[{"id": "background", "type": "image", "layer": 0, "bounds": {"x": 0, "y": 0, "width": 1080, "height": 1080}}, {"id": "headline", "type": "text", "layer": 2, "bounds": {"x": 80, "y": 300, "width": 920, "height": 400}}]'::jsonb,
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
    '1x1',
    '{"width": 1080, "height": 1080}'::jsonb,
    '[{"id": "headline", "type": "text", "layer": 1, "bounds": {"x": 80, "y": 400, "width": 920, "height": 300}}, {"id": "cta", "type": "text", "layer": 2, "bounds": {"x": 80, "y": 750, "width": 920, "height": 100}}]'::jsonb,
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
    '1x1',
    '{"width": 1080, "height": 1080}'::jsonb,
    '[{"id": "product", "type": "image", "layer": 1, "bounds": {"x": 140, "y": 200, "width": 800, "height": 600}}, {"id": "headline", "type": "text", "layer": 2, "bounds": {"x": 80, "y": 850, "width": 920, "height": 150}}]'::jsonb,
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
    '9x16',
    '{"width": 1080, "height": 1920}'::jsonb,
    '[{"id": "background", "type": "image", "layer": 0, "bounds": {"x": 0, "y": 0, "width": 1080, "height": 1920}}, {"id": "headline", "type": "text", "layer": 2, "bounds": {"x": 80, "y": 1400, "width": 920, "height": 400}}]'::jsonb,
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
    '1x1',
    '{"width": 1080, "height": 1080}'::jsonb,
    '[{"id": "headline", "type": "text", "layer": 1, "bounds": {"x": 80, "y": 100, "width": 920, "height": 200}}, {"id": "body", "type": "text", "layer": 2, "bounds": {"x": 80, "y": 350, "width": 920, "height": 600}}]'::jsonb,
    'Information-dense layout',
    '{"id": "text_heavy_v1", "slots": []}'::jsonb,
    ARRAY['1x1', '16x9'],
    ARRAY['linkedin', 'fb'],
    TRUE,
    0
);

SELECT 'Part 3 completed - 5 built-in templates inserted!' AS status;
SELECT COUNT(*) AS template_count FROM layout_templates WHERE is_builtin = TRUE;
