-- Seed data for development and testing

-- Create a demo organization
INSERT INTO organizations (id, name, created_at)
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'Demo Company', NOW())
ON CONFLICT DO NOTHING;

-- Create demo users
INSERT INTO users (id, org_id, email, role, created_at)
VALUES 
    ('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000001', 'owner@demo.com', 'owner', NOW()),
    ('00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000001', 'admin@demo.com', 'admin', NOW()),
    ('00000000-0000-0000-0000-000000000013', '00000000-0000-0000-0000-000000000001', 'member@demo.com', 'member', NOW())
ON CONFLICT DO NOTHING;

-- Create a demo brand kit
INSERT INTO brand_kits (id, org_id, name, colors, style, created_at)
VALUES 
    (
        '00000000-0000-0000-0000-000000000021',
        '00000000-0000-0000-0000-000000000001',
        'Demo Brand Kit',
        '{
            "primary": "#2563EB",
            "secondary": "#7C3AED",
            "accent": "#F59E0B",
            "background": "#FFFFFF",
            "text": "#1F2937"
        }',
        '{
            "descriptors": ["modern", "professional", "clean", "minimalist"],
            "voice": "confident and approachable",
            "mood": "innovative and trustworthy"
        }',
        NOW()
    )
ON CONFLICT DO NOTHING;

-- Create subscription plans
INSERT INTO plans (id, name, price_cents, monthly_credits)
VALUES 
    ('00000000-0000-0000-0000-000000000031', 'Starter', 2900, 300),
    ('00000000-0000-0000-0000-000000000032', 'Professional', 9900, 1000),
    ('00000000-0000-0000-0000-000000000033', 'Enterprise', 29900, 5000)
ON CONFLICT DO NOTHING;

-- Create demo subscription (active trial)
INSERT INTO subscriptions (org_id, plan_id, current_period_end, status, created_at)
VALUES 
    (
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000031',
        NOW() + INTERVAL '30 days',
        'trialing',
        NOW()
    )
ON CONFLICT DO NOTHING;

-- Initialize usage for current month
INSERT INTO usage (org_id, month, credits_used)
VALUES 
    (
        '00000000-0000-0000-0000-000000000001',
        DATE_TRUNC('month', NOW())::DATE,
        0
    )
ON CONFLICT DO NOTHING;