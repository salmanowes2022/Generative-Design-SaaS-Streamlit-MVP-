-- ============================================================================
-- Migration V3 - PART 1: Enhance Existing Tables
-- Run this first in Supabase SQL Editor
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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
        ALTER TABLE brand_kits ADD COLUMN parent_version UUID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='brand_kits' AND column_name='ab_test_variant') THEN
        ALTER TABLE brand_kits ADD COLUMN ab_test_variant VARCHAR(50);
    END IF;
END $$;

-- Add columns to assets
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='assets' AND column_name='brand_kit_id') THEN
        ALTER TABLE assets ADD COLUMN brand_kit_id UUID;
    END IF;

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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_layout_templates_aspect ON layout_templates USING GIN(aspect_ratios);
CREATE INDEX IF NOT EXISTS idx_layout_templates_channels ON layout_templates USING GIN(channels);
CREATE INDEX IF NOT EXISTS idx_assets_brand_kit ON assets(brand_kit_id);
CREATE INDEX IF NOT EXISTS idx_assets_layout_template ON assets(layout_template_id);

SELECT 'Part 1 completed - Existing tables enhanced!' AS status;
