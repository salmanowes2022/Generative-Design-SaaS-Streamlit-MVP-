## Architecture v2 - Brand Brain + Canva Integration

This document outlines the complete v2 architecture with Brand Brain intelligence and Canva as the rendering engine.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      BRAND BRAIN v2                          │
│  Central Intelligence: Tokens, Policies, Validation          │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                                             ↓
┌───────────────────┐                   ┌─────────────────────┐
│   PLANNER AGENT   │                   │  VALIDATOR ENGINE   │
│  (GPT-4 + Rules)  │                   │ (OCR + Color + WCAG)│
└───────────────────┘                   └─────────────────────┘
        ↓                                             ↑
┌───────────────────┐                   ┌─────────────────────┐
│ CANVA RENDERER    │────────────────→  │   ASSET STORAGE     │
│ (Templates + API) │                   │  (Supabase + URLs)  │
└───────────────────┘                   └─────────────────────┘
```

---

## Core Components

### 1. Brand Brain (`brand_brain.py`)

**Purpose:** Central repository for brand intelligence

**Key Classes:**
- `BrandTokens`: Design tokens (colors, typography, logo, layout, templates, CTAs)
- `BrandPolicies`: Voice traits, forbidden terms
- `BrandBrain`: Persistence, extraction, audit logging

**Token Structure:**
```json
{
  "color": {
    "primary": "#4F46E5",
    "secondary": "#7C3AED",
    "accent": "#F59E0B",
    "background": "#FFFFFF",
    "text": "#111111",
    "min_contrast": 4.5
  },
  "type": {
    "heading": {"family": "Inter", "weights": [700], "scale": [48, 36, 28]},
    "body": {"family": "Inter", "weights": [400], "size": 16}
  },
  "logo": {
    "variants": [{"name": "full", "path": "...", "on": "light"}],
    "min_px": 128,
    "safe_zone": "1x",
    "allowed_positions": ["TL", "TR", "BR"]
  },
  "layout": {"grid": 12, "spacing": 8, "radius": 16},
  "templates": {
    "ig_1x1": "tmpl_IG_1x1_v1",
    "ig_4x5": "tmpl_IG_4x5_promo_v1"
  },
  "cta_whitelist": ["Get Started", "Try Free", "Learn More"]
}
```

**Database:**
- Stored in `brand_kits.tokens` (JSONB)
- Extracted from PDF brand book or set to sensible defaults
- Retrieved per brand kit for all operations

---

### 2. Prompt Builder v2 (`prompt_builder_v2.py`)

**Purpose:** Generate prompts with negative space awareness

**Key Method:**
```python
build_background_prompt(
    user_request: str,
    tokens: BrandTokens,
    aspect_ratio: str,
    logo_position: str
) -> str
```

**Features:**
- **Camera/lighting cues**: Automatic based on subject (product, interior, portrait, etc.)
- **Composition with negative space**: Ensures space in logo corner (TL/TR/BR/BL)
- **Strong negatives**: "NO TEXT, NO LOGOS, NO WORDS" explicit and repeated
- **Brand colors**: Injects primary/secondary from tokens
- **Length optimization**: Trims to <600 chars, keeps user request primary

**Example Output:**
```
Create: modern office interior. Shot with 24mm wide-angle lens, f/8, deep focus.
Composition: rule of thirds, generous empty space in top-right corner, uncluttered.
Color palette: dominant #4F46E5 with #7C3AED accents. Professional studio lighting.
CRITICAL: NO TEXT, NO LOGOS, NO WORDS, NO UI elements. Clean background only.
```

---

### 3. Logo Engine (`logo_engine.py`)

**Purpose:** Intelligent logo variant selection and placement

**Key Functions:**
```python
select_logo_variant(bg_image: Image, position: str, tokens: BrandTokens) -> Dict
apply_logo(bg_image: Image, logo_image: Image, position: str, tokens: BrandTokens) -> Image
```

**Features:**
- **Luminance sampling**: Samples 100x100px at logo position, picks light/dark variant
- **Safe zone enforcement**: Respects `tokens.logo.safe_zone` (1x, 2x logo height)
- **Scale constraints**: `min_px ≤ logo_width ≤ 25% canvas_width`
- **Anchor positions**: TL, TR, BR, BL with proper margins based on `tokens.layout.spacing`
- **Alpha blending**: Proper RGBA handling for transparent logos

**Position Calculation:**
```python
# Example for TR (top-right)
margin = tokens.layout.spacing * 4  # 32px default
x = canvas_width - logo_width - margin
y = margin
```

---

### 4. OCR Gate (`ocr_validator.py`)

**Purpose:** Block backgrounds with accidental text

**Flow:**
1. Run Tesseract OCR on generated image (fast, local)
2. If confidence >60 and text length >3 chars → REJECT
3. Auto-trigger regeneration with stronger negative prompt
4. Log to audit trail

**Implementation:**
```python
def has_text(image: Image) -> Tuple[bool, str]:
    """Returns (has_text, detected_text)"""
    text = pytesseract.image_to_string(image)
    cleaned = text.strip()
    if len(cleaned) > 3:
        return True, cleaned
    return False, ""
```

---

### 5. Validator (`validator_v2.py`)

**Purpose:** Comprehensive brand compliance scoring

**Metrics:**
- **Color ΔE (CIE2000)**: Extract dominant colors, compare to brand palette
- **WCAG Contrast**: Check contrast at logo position vs logo color
- **Policy Check**: Scan for forbidden terms (if text present)
- **OCR Check**: No text allowed in backgrounds

**Scoring Formula:**
```python
score = 0
score += 30 if color_delta_e < 10 else (30 - color_delta_e)  # 30 pts
score += 30 if contrast_ratio >= min_contrast else 0          # 30 pts
score += 20 if not ocr_detected else 0                        # 20 pts
score += 20 if no_policy_violations else 0                    # 20 pts
score = max(0, min(100, score))
```

**Output:**
```json
{
  "on_brand_score": 85,
  "reasons": [
    "✓ Color palette matches (ΔE: 5.2)",
    "✓ WCAG AAA contrast (7.8:1)",
    "✓ No text detected",
    "✓ No policy violations"
  ],
  "details": {
    "color_delta_e": 5.2,
    "contrast_ratio": 7.8,
    "ocr_clean": true,
    "policy_clean": true
  }
}
```

Stored in `assets.validation` JSONB.

---

### 6. Canva Renderer (`renderer_canva.py`)

**Purpose:** Create designs via Canva API using templates

**Authentication:**
- OAuth2 flow (authorization_code grant)
- Scopes: `design:write`, `design:read`, `asset:read`
- Tokens stored securely per organization

**Key Methods:**
```python
create_design_from_template(template_id: str, brand_team_id: str) -> str
autofill_variables(design_id: str, plan: Dict) -> None
export_design(design_id: str, format: str = "png") -> Dict
```

**Template Contract:**
Canva templates MUST expose these placeholders:
- `HEADLINE` (text, max 7 words)
- `SUBHEAD` (text, max 16 words)
- `CTA_TEXT` (text, must be in whitelist)
- `PRODUCT_IMAGE` (image URL)
- `BG_IMAGE` (image URL, from AI generation)
- `PALETTE_MODE` (enum: primary|secondary|accent|mono)

**Autofill Mapping:**
```python
variables = {
    "HEADLINE": plan["headline"],
    "SUBHEAD": plan["subhead"],
    "CTA_TEXT": plan["cta_text"],
    "BG_IMAGE": plan["bg_image_url"],
    "PALETTE_MODE": plan["palette_mode"]
}
await canva_api.autofill(design_id, variables)
```

**Error Handling:**
- Text overflow → return actionable error: "Headline too long (9 words), max 7"
- Missing image → use fallback placeholder from brand kit
- Export failure → retry with exponential backoff (3 attempts)

**ENV Variables:**
```
CANVA_CLIENT_ID=your_client_id
CANVA_CLIENT_SECRET=your_client_secret
CANVA_REDIRECT_URI=https://yourapp.com/oauth/canva/callback
CANVA_API_BASE=https://api.canva.com/v1
CANVA_BRAND_TEAM_ID=your_brand_team_id
```

---

### 7. Planner Agent (`planner_v2.py`)

**Purpose:** Convert chat to strict JSON plan

**Input:** User chat message + brand tokens + channel

**Output (STRICT JSON):**
```json
{
  "channel": "instagram",
  "aspect": "4:5",
  "template_id": "tmpl_IG_4x5_promo_v1",
  "palette_mode": "primary",
  "headline": "Empower Your Workflow",
  "subhead": "New analytics that feel effortless",
  "cta_text": "Get Started",
  "product_image_url": "https://.../product.png",
  "bg_image_url": null,
  "brand_kit_id": "BRAND-UUID",
  "tags": ["promo", "analytics", "oct-2025"]
}
```

**Constraints Enforced:**
- `headline`: ≤ 7 words
- `subhead`: ≤ 16 words
- `cta_text`: MUST be in `tokens.cta_whitelist`
- `template_id`: MUST be in `tokens.templates[{channel}_{aspect}]`
- `palette_mode`: One of ["primary", "secondary", "accent", "mono"]

**GPT-4 Prompt:**
```
You are a brand planner. Convert the user's request into a strict JSON plan.
Brand CTAs allowed: {cta_whitelist}
Templates available: {templates}
Rules:
- headline MAX 7 words
- subhead MAX 16 words
- CTA must be from whitelist
Return ONLY valid JSON, no explanation.
```

---

## Data Flow

### A. Onboarding (Brand Book Upload)

```
1. User uploads brand book PDF
   ↓
2. brandbook_analyzer.analyze_brand_book_pdf()
   → Extracts visual_identity, messaging, layout, etc.
   ↓
3. brand_brain.extract_tokens_from_guidelines()
   → Maps guidelines → BrandTokens (colors, logo, layout, etc.)
   ↓
4. brand_brain.extract_policies_from_guidelines()
   → Maps guidelines → BrandPolicies (voice, forbidden terms)
   ↓
5. brand_brain.save_brand_brain(brand_kit_id, tokens, policies)
   → Saves to brand_kits.tokens + brand_kits.policies
   ↓
6. SUCCESS: Brand Brain ready for design generation
```

---

### B. Design Generation (Chat → Canva)

```
1. User: "Create Instagram promo for new analytics feature"
   ↓
2. planner_v2.plan_design(user_message, tokens, channel="instagram")
   → Returns strict JSON plan
   ↓
3. prompt_builder_v2.build_background_prompt(plan["headline"], tokens, "4:5", "TR")
   → Generates prompt with negative space
   ↓
4. gen_openai.generate_images() [DALL-E 3]
   → Creates background image (NO TEXT)
   ↓
5. ocr_validator.has_text(image)
   → If text detected: regenerate with stronger prompt
   → Else: proceed
   ↓
6. renderer_canva.create_design_from_template(plan["template_id"])
   → Creates Canva design from template
   ↓
7. renderer_canva.autofill_variables(design_id, plan)
   → Fills HEADLINE, SUBHEAD, CTA, BG_IMAGE, etc.
   ↓
8. renderer_canva.export_design(design_id, "png")
   → Exports final PNG with brand overlay
   ↓
9. validator_v2.validate_design(image, tokens, policies)
   → Scores: color ΔE, contrast, OCR, policy
   → Returns on_brand_score (0-100)
   ↓
10. Save to assets table:
    - base_url (from DALL-E)
    - composed_url (from Canva export)
    - canva_design_id + canva_design_url
    - on_brand_score
    - validation (JSONB with reasons)
   ↓
11. brand_brain.audit_action("design_generated", plan, result)
    → Logs to agent_audit for tracking
   ↓
12. UI shows:
    - Design preview
    - "Open in Canva" deep link
    - Validation panel with score + reasons
    - "Regenerate with fix" if score < 75
```

---

## Database Schema

### brand_kits (extended)
```sql
CREATE TABLE brand_kits (
  id UUID PRIMARY KEY,
  org_id UUID REFERENCES organizations(id),
  name TEXT,
  tokens JSONB,        -- NEW: design tokens
  policies JSONB,      -- NEW: brand policies
  version INTEGER DEFAULT 2,  -- NEW: schema version
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);
```

### assets (extended)
```sql
CREATE TABLE assets (
  id UUID PRIMARY KEY,
  org_id UUID,
  job_id UUID,
  base_url TEXT,              -- AI-generated background
  composed_url TEXT,          -- Final Canva export URL
  canva_design_id TEXT,       -- NEW: Canva design ID
  canva_design_url TEXT,      -- NEW: Deep link to Canva editor
  on_brand_score INTEGER,     -- NEW: 0-100 compliance score
  validation JSONB,           -- Enhanced validation results
  validation_reasons JSONB,   -- NEW: Human-readable reasons
  aspect_ratio TEXT,
  created_at TIMESTAMPTZ
);
```

### agent_audit (new)
```sql
CREATE TABLE agent_audit (
  id UUID PRIMARY KEY,
  org_id UUID REFERENCES organizations(id),
  brand_kit_id UUID REFERENCES brand_kits(id),
  asset_id UUID REFERENCES assets(id),
  action TEXT,         -- plan, render, validate, regenerate
  payload JSONB,       -- Input data
  result JSONB,        -- Output data
  duration_ms INTEGER,
  created_at TIMESTAMPTZ
);
```

---

## UI Flow (Streamlit)

### Generate Page (Non-Hybrid UX)

```
┌─────────────────────────────────────────┐
│  💬 Chat to Plan                        │
│  "Create Instagram promo for analytics" │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  📋 Plan Preview (JSON)                 │
│  Channel: Instagram 4:5                 │
│  Headline: "Empower Your Workflow"      │
│  CTA: "Get Started"                     │
│  [ ✏️ Edit Plan ] [ 🎨 Create in Canva ]│
└─────────────────────────────────────────┘
              ↓ (click Create)
┌─────────────────────────────────────────┐
│  ⏳ Generating...                       │
│  ✓ Background created                   │
│  ✓ OCR check passed                     │
│  ✓ Creating Canva design                │
│  ✓ Exporting final image                │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  ✅ Design Complete                     │
│  [Preview Image]                        │
│  Score: 87/100 ⭐⭐⭐⭐                  │
│                                         │
│  Validation:                            │
│  ✓ Colors match (ΔE: 4.2)              │
│  ✓ WCAG AAA contrast (8.1:1)            │
│  ✓ No text in background                │
│  ✓ No policy violations                 │
│                                         │
│  [ 🔗 Open in Canva ] [ ⬇️ Download ]   │
└─────────────────────────────────────────┘
```

If score < 75:
```
┌─────────────────────────────────────────┐
│  ⚠️ Design Needs Improvement (Score: 68)│
│  Issues:                                │
│  ✗ Colors off-brand (ΔE: 15.3)         │
│  ✓ Good contrast                        │
│  ✓ No text detected                     │
│                                         │
│  [ 🔄 Regenerate with Fix ]             │
└─────────────────────────────────────────┘
```

---

## Error Handling

### 1. OCR Detects Text
```
Action: Auto-regenerate with stronger negative prompt
User sees: "Text detected in background, regenerating..."
Audit: {action: "regenerate_ocr_fail", reason: "text_detected"}
```

### 2. Canva Text Overflow
```
Canva API returns: {"error": "Text overflow in HEADLINE"}
Response: "Headline too long (9 words), please shorten to 7 words or less"
UI: Allow user to edit headline in plan
```

### 3. Low On-Brand Score
```
If score < 75:
  - Show validation panel with specific issues
  - Offer "Regenerate with Fix" button
  - Pass issue to prompt_builder_v2.build_regeneration_prompt()
```

### 4. Missing Product Image
```
If plan["product_image_url"] is None:
  - Use transparent placeholder
  - Template shows background only
```

---

## Testing Strategy

See `tests/test_brand_brain_v2.py` for comprehensive test suite:
- Token extraction from guidelines
- Prompt builder negative space
- Logo variant selection by luminance
- OCR gate blocks text
- Validation scoring (color, contrast, policy)
- Canva renderer (mock API)
- End-to-end flow

---

## Deployment Checklist

- [ ] Run migration `001_brand_brain_v2.sql`
- [ ] Set Canva env vars in `.env`
- [ ] Register Canva OAuth app
- [ ] Create Canva templates with required placeholders
- [ ] Map template IDs in default tokens
- [ ] Install OCR dependencies: `apt-get install tesseract-ocr`
- [ ] Install Python packages: `pip install pytesseract colormath`
- [ ] Test with sample brand book
- [ ] Verify Canva export works
- [ ] Check validation scoring
- [ ] Monitor agent_audit logs

---

## Future Enhancements

1. **Multi-brand support**: Multiple brand kits per org
2. **Template versioning**: Track template changes
3. **A/B testing**: Generate variants, pick winner
4. **Feedback loop**: Learn from approved designs
5. **Vector retrieval**: pgvector for semantic asset search
6. **Batch generation**: Create 10 variants at once
7. **Video templates**: Extend to Canva video

---

End of Architecture v2 Documentation
