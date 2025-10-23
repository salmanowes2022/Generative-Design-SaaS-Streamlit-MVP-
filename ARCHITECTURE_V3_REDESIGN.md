# 🏗️ Architecture V3 - AI-Powered Brand Design Agent

**Last Updated:** 2025-10-22

## 🎯 Vision

Transform your SaaS into a sophisticated AI brand design agent that generates pixel-perfect, brand-consistent social media content through natural conversation - without relying on templates.

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interface (Streamlit)                   │
│  Chat Interface | Brand Upload | Library | Preview & Export     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                      Core Agent Layer                            │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ Chat Planner    │  │  Layout Engine   │  │ Quality Scorer │ │
│  │ (GPT-4)         │→ │  (Slot-based)    │→ │ (Validation)   │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                   Brand Intelligence Layer                       │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ Brand Parser    │  │  Brand Brain     │  │ Contrast Mgr   │ │
│  │ (PDF→Tokens)    │→ │  (Knowledge)     │→ │ (Accessibility)│ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                   Generation & Rendering Layer                   │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ Image Gen       │  │  Design Renderer │  │ Export Bridge  │ │
│  │ (DALL-E 3)      │→ │  (Pillow/SVG)    │→ │ (Canva/Figma)  │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│              Infrastructure Layer (PostgreSQL + Supabase)        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Breakdown

### **1. Brand Intelligence Layer**

#### **A. Brand Parser** (`brand_parser.py`) 🆕
**Purpose:** Extract structured brand tokens from PDF brand books

**Features:**
- PDF text extraction (PyPDF2/pdfplumber)
- AI-powered analysis (GPT-4 Vision for visual elements)
- Color palette extraction (from embedded images)
- Typography detection
- Logo extraction and variant detection
- Layout system analysis

**Input:** PDF brand book
**Output:** Structured JSON brand tokens

**Fallback Strategy:**
- If PDF parsing fails → Manual form input
- If colors not detected → User color picker
- If fonts not found → System font suggestions

---

#### **B. Brand Brain** (`brand_brain.py`) ✅ (Already exists, enhance)
**Current:** Stores/retrieves tokens and policies
**Enhancement:** Add version control, brand evolution tracking

**New Features:**
- Brand guideline versioning
- A/B testing support for design variations
- Learning from user preferences
- Automatic token recommendations based on industry

---

#### **C. Contrast Manager** (`contrast_manager.py`) 🆕
**Purpose:** Ensure WCAG-compliant accessibility and visual hierarchy

**Features:**
- WCAG AA/AAA contrast ratio calculation
- Dynamic overlay opacity adjustment
- Text shadow/outline recommendations
- Color harmony validation
- Automatic color adjustments for readability

**Algorithm:**
```python
def calculate_contrast_ratio(fg, bg) -> float:
    # WCAG formula
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

def ensure_readable_text(text_color, bg_color, min_ratio=4.5):
    ratio = calculate_contrast_ratio(text_color, bg_color)
    if ratio < min_ratio:
        # Adjust text color to meet minimum
        return adjust_color_for_contrast(text_color, bg_color, min_ratio)
    return text_color
```

---

### **2. Core Agent Layer**

#### **D. Chat Planner** (`chat_agent_planner.py`) ✅ (Already exists, enhance)
**Current:** Conversational design planning
**Enhancement:** Add clarifying questions, multi-turn refinement

**New Features:**
- Intent classification (new design vs. iterate)
- Campaign-level planning (multi-post series)
- Platform-specific best practices
- Trend awareness (seasonal, industry)

**Conversation Flow:**
```
User: "Create a Black Friday sale post"
  ↓
Agent: "Great! A few quick questions:
        1. Which platform? (Instagram/Facebook/LinkedIn)
        2. What's the main offer? (% off, BOGO, etc.)
        3. Target audience? (B2B/B2C)
        4. Mood? (Urgent/Elegant/Fun)"
  ↓
User: "Instagram, 30% off, B2C, urgent"
  ↓
Agent: [Generates design plan with justified choices]
```

---

#### **E. Layout Engine** (`layout_engine.py`) 🆕
**Purpose:** Smart, slot-based composition system

**Features:**
- Template-free layout generation
- Rule-based slot system (hero, subhead, cta, badge, logo)
- Dynamic grid adaptation (12-column responsive)
- Visual weight distribution
- Golden ratio / rule of thirds application

**Layout Templates:**
```json
{
  "hero_with_badge": {
    "slots": [
      {"id": "background", "layer": 0, "area": "full"},
      {"id": "hero_text", "layer": 2, "area": {"x": 1, "y": 5, "w": 10, "h": 2}},
      {"id": "subhead", "layer": 2, "area": {"x": 1, "y": 8, "w": 10, "h": 1}},
      {"id": "badge", "layer": 3, "area": {"x": 8, "y": 2, "w": 3, "h": 2}},
      {"id": "cta_button", "layer": 3, "area": {"x": 2, "y": 10, "w": 8, "h": 1}},
      {"id": "logo", "layer": 4, "area": {"x": 10, "y": 0, "w": 2, "h": 2}}
    ],
    "rules": {
      "text_safe_zones": ["y: 4-11"],
      "logo_clearance": "1x logo height",
      "min_text_size": "80px for headline"
    }
  }
}
```

**Slot Matching Algorithm:**
```python
def select_layout_template(plan: DesignPlan) -> LayoutTemplate:
    """
    Choose optimal layout based on content needs
    """
    content_density = calculate_content_density(plan)

    if plan.product_image_needed:
        return get_template("product_showcase")
    elif content_density > 0.8:
        return get_template("text_heavy")
    elif plan.channel == "ig" and plan.aspect_ratio == "9x16":
        return get_template("story_immersive")
    else:
        return get_template("hero_with_badge")
```

---

#### **F. Design Renderer** (`design_renderer.py`) 🆕 (Replacement for renderer_grid.py)
**Purpose:** Advanced code-based rendering

**Rendering Modes:**
1. **Pillow Mode** (Current) - PNG output
2. **SVG Mode** (NEW) - Scalable vector graphics
3. **HTML/CSS Mode** (NEW) - Web-native rendering

**Features:**
- Multi-layer compositing
- Advanced text effects (gradients, shadows, outlines)
- Image filters and adjustments
- Animation keyframes (for video export)
- Export to multiple formats (PNG, SVG, PDF)

**Rendering Pipeline:**
```python
class DesignRenderer:
    def render(self, plan, layout, assets) -> RenderedDesign:
        canvas = self._create_canvas(layout.dimensions)

        # Layer 0: Background
        canvas = self._apply_background(canvas, assets.background)

        # Layer 1: Overlay/gradients
        canvas = self._apply_effects(canvas, layout.effects)

        # Layer 2: Content slots
        for slot in layout.slots:
            if slot.type == "text":
                canvas = self._render_text_slot(canvas, slot, plan)
            elif slot.type == "image":
                canvas = self._render_image_slot(canvas, slot, assets)

        # Layer 3: Accents (badges, shapes)
        canvas = self._render_accents(canvas, layout.accents)

        # Layer 4: Logo
        canvas = self._render_logo(canvas, assets.logo, layout.logo_position)

        return canvas
```

---

### **3. Generation & Rendering Layer**

#### **G. Image Generator** (`gen_openai.py`) ✅ (Already exists, enhance)
**Current:** DALL-E 3 integration with retry logic
**Enhancement:** Add prompt engineering, quality scoring

**New Features:**
- Prompt templates for social media
- Style transfer from reference images
- Face detection (ensure diverse representation)
- Background removal (for product shots)
- Upscaling (for HD quality)

**Enhanced Prompt Engineering:**
```python
def build_dalle_prompt(plan: DesignPlan, tokens: BrandTokens) -> str:
    """
    Build optimized prompt for DALL-E 3
    """
    base = plan.visual_concept

    # Add style modifiers based on brand
    if "professional" in tokens.policies.voice:
        base += ", clean professional photography, studio lighting"
    if "energetic" in tokens.policies.voice:
        base += ", dynamic composition, vibrant atmosphere"

    # Platform-specific optimization
    if plan.channel == "linkedin":
        base += ", corporate setting, business attire"
    elif plan.channel == "ig":
        base += ", lifestyle photography, authentic moments"

    # Technical specs
    base += ", high resolution, sharp focus, professional color grading"

    # Forbidden elements
    base += " --no text, no logos, no watermarks"

    return base
```

---

#### **H. Export Bridge** (`export_bridge.py`) 🆕
**Purpose:** Optional handoff to Canva/Figma for further editing

**Features:**
- Canva API integration (existing templates)
- Figma API integration (create editable designs)
- Layer preservation
- Font mapping
- Color palette sync

**Workflow:**
```python
class ExportBridge:
    def export_to_canva(self, design: RenderedDesign, brand_kit: BrandKit):
        """
        Create editable design in Canva
        """
        # 1. Create blank Canva design
        canva_design = canva_api.create_design(
            format=design.aspect_ratio,
            brand_kit_id=brand_kit.canva_id
        )

        # 2. Add elements layer by layer
        canva_api.add_image(canva_design.id, layer=0, url=design.background_url)
        canva_api.add_text(canva_design.id, layer=2, **design.headline_props)
        canva_api.add_shape(canva_design.id, layer=3, **design.cta_props)

        # 3. Return editable link
        return canva_design.editor_url

    def export_to_figma(self, design: RenderedDesign):
        """
        Create editable Figma frame
        """
        # Similar approach using Figma REST API
        pass
```

---

#### **I. Quality Scorer** (`quality_scorer.py`) 🆕
**Purpose:** Automated design quality validation

**Scoring Criteria:**
- **Readability** (30%) - Text contrast, size, hierarchy
- **Brand Consistency** (25%) - Color compliance, font usage
- **Composition** (20%) - Balance, whitespace, alignment
- **Impact** (15%) - Visual hierarchy, CTA prominence
- **Accessibility** (10%) - WCAG compliance, alt text

**Output:**
```json
{
  "overall_score": 87,
  "breakdown": {
    "readability": {"score": 92, "issues": []},
    "brand_consistency": {"score": 95, "issues": ["CTA color slightly off brand"]},
    "composition": {"score": 80, "issues": ["Text could use more breathing room"]},
    "impact": {"score": 85, "issues": ["Headline size could be larger"]},
    "accessibility": {"score": 90, "issues": ["Contrast ratio 4.2:1, recommend 4.5:1+"]}
  },
  "suggestions": [
    "Increase headline font size by 10px",
    "Adjust CTA background to brand accent color (#F59E0B)",
    "Add 20px padding around subhead"
  ]
}
```

---

## 📊 Data Structures

### **Brand Tokens Schema** (Enhanced)

```json
{
  "version": "2.0",
  "brand_id": "uuid",
  "colors": {
    "primary": {"hex": "#4F46E5", "name": "Indigo", "usage": "headlines, CTAs"},
    "secondary": {"hex": "#7C3AED", "name": "Purple", "usage": "accents, badges"},
    "accent": {"hex": "#F59E0B", "name": "Amber", "usage": "urgency, highlights"},
    "neutral": {
      "black": "#111111",
      "white": "#FFFFFF",
      "gray": ["#F3F4F6", "#D1D5DB", "#6B7280"]
    },
    "semantic": {
      "success": "#10B981",
      "warning": "#F59E0B",
      "error": "#EF4444",
      "info": "#3B82F6"
    }
  },
  "typography": {
    "heading": {
      "family": "Inter",
      "weights": [700, 800, 900],
      "scale": [72, 56, 40, 32],
      "line_height": 1.2,
      "letter_spacing": -0.02
    },
    "body": {
      "family": "Inter",
      "weights": [400, 500, 600],
      "size": [16, 18, 20],
      "line_height": 1.5
    },
    "fallbacks": ["system-ui", "sans-serif"]
  },
  "logo": {
    "variants": [
      {
        "name": "full_color",
        "url": "https://...",
        "background": "light",
        "format": "png",
        "dimensions": {"w": 400, "h": 100}
      },
      {
        "name": "white",
        "url": "https://...",
        "background": "dark",
        "format": "png"
      },
      {
        "name": "icon",
        "url": "https://...",
        "square": true
      }
    ],
    "rules": {
      "min_size_px": 128,
      "clear_space": "1x logo height",
      "allowed_positions": ["TL", "TR", "BR"],
      "forbidden_backgrounds": ["busy patterns", "low contrast"]
    }
  },
  "layout": {
    "grid": 12,
    "spacing_scale": [4, 8, 16, 24, 32, 48, 64],
    "border_radius": {"sm": 8, "md": 16, "lg": 24},
    "shadows": {
      "sm": "0 1px 2px rgba(0,0,0,0.1)",
      "md": "0 4px 6px rgba(0,0,0,0.1)",
      "lg": "0 10px 15px rgba(0,0,0,0.1)"
    }
  },
  "voice": {
    "traits": ["professional", "friendly", "innovative"],
    "tone": "confident but approachable",
    "vocabulary": {
      "prefer": ["empower", "transform", "streamline"],
      "avoid": ["revolutionary", "game-changing", "disrupt"]
    }
  },
  "policies": {
    "cta_whitelist": ["Get Started", "Learn More", "Try Free", "Join Now"],
    "forbidden_terms": ["guaranteed", "miraculous", "cheap"],
    "content_rules": [
      "Always include a clear value proposition",
      "Use data/numbers when possible",
      "Avoid superlatives without proof"
    ]
  }
}
```

---

### **Layout Template Schema**

```json
{
  "id": "hero_badge_cta_v1",
  "name": "Hero with Badge and CTA",
  "description": "Large headline with promotional badge and strong CTA",
  "aspect_ratios": ["1x1", "4x5"],
  "channels": ["ig", "fb"],
  "slots": [
    {
      "id": "background",
      "type": "image",
      "layer": 0,
      "area": "full",
      "fit": "cover",
      "filters": ["brightness(0.9)"]
    },
    {
      "id": "overlay",
      "type": "gradient",
      "layer": 1,
      "area": "full",
      "gradient": "linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.4) 100%)"
    },
    {
      "id": "headline",
      "type": "text",
      "layer": 2,
      "area": {"x": 1, "y": 5, "w": 10, "h": 2},
      "font_size": "clamp(60px, 8vw, 140px)",
      "font_weight": 800,
      "color": "#FFFFFF",
      "align": "center",
      "effects": ["drop-shadow"]
    },
    {
      "id": "subhead",
      "type": "text",
      "layer": 2,
      "area": {"x": 1, "y": 8, "w": 10, "h": 1},
      "font_size": "clamp(24px, 3vw, 60px)",
      "color": "#FFFFFF",
      "align": "center"
    },
    {
      "id": "badge",
      "type": "shape",
      "layer": 3,
      "area": {"x": 8, "y": 2, "w": 3, "h": 2},
      "shape": "circle",
      "background": "accent",
      "text": {"content": "30% OFF", "size": 32, "weight": 700}
    },
    {
      "id": "cta",
      "type": "button",
      "layer": 3,
      "area": {"x": 2, "y": 10, "w": 8, "h": 1},
      "background": "primary",
      "text_color": "#FFFFFF",
      "border_radius": 16,
      "font_size": 48,
      "font_weight": 700
    },
    {
      "id": "logo",
      "type": "image",
      "layer": 4,
      "area": {"x": 10, "y": 0, "w": 2, "h": 2},
      "fit": "contain",
      "opacity": 0.95
    }
  ],
  "rules": {
    "text_contrast_min": 4.5,
    "logo_clearance": "1x",
    "cta_prominence": "must be largest button",
    "safe_zones": ["top 10%", "bottom 10%"]
  }
}
```

---

## 🗄️ Database Schema Updates

```sql
-- Enhanced brand_kits table
ALTER TABLE brand_kits
ADD COLUMN tokens_v2 JSONB,  -- New schema
ADD COLUMN parsing_metadata JSONB,  -- PDF parsing details
ADD COLUMN version INTEGER DEFAULT 2,
ADD COLUMN parent_version UUID REFERENCES brand_kits(id),  -- Version control
ADD COLUMN ab_test_variant VARCHAR(50);

-- New table: layout_templates
CREATE TABLE layout_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  template_schema JSONB NOT NULL,
  aspect_ratios TEXT[] NOT NULL,
  channels TEXT[] NOT NULL,
  usage_count INTEGER DEFAULT 0,
  performance_score DECIMAL(3,2),  -- Based on engagement
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- New table: design_scores
CREATE TABLE design_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID REFERENCES assets(id),
  overall_score INTEGER NOT NULL,
  readability_score INTEGER,
  brand_consistency_score INTEGER,
  composition_score INTEGER,
  impact_score INTEGER,
  accessibility_score INTEGER,
  issues JSONB,
  suggestions JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- New table: brand_learning
CREATE TABLE brand_learning (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_kit_id UUID REFERENCES brand_kits(id),
  design_pattern VARCHAR(255),  -- e.g., "high_contrast", "minimal"
  user_feedback VARCHAR(50),  -- "liked", "disliked", "exported"
  context JSONB,  -- What was the design about
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX idx_layout_templates_aspect ON layout_templates USING GIN(aspect_ratios);
CREATE INDEX idx_layout_templates_channels ON layout_templates USING GIN(channels);
CREATE INDEX idx_design_scores_asset ON design_scores(asset_id);
CREATE INDEX idx_brand_learning_brand_kit ON brand_learning(brand_kit_id);
```

---

## 🚀 Deployment & Scaling Strategy

### **Architecture Patterns**

#### **1. Async Task Queue** (Redis + Celery)
```python
# For expensive operations
@celery_app.task
def generate_design_async(plan_id: UUID, org_id: UUID):
    """
    Background task for design generation
    """
    plan = get_design_plan(plan_id)

    # Step 1: Generate image (DALL-E - slow)
    bg_url = generate_image_async.delay(plan.prompt).get()

    # Step 2: Render layout (fast)
    design = render_design(plan, bg_url)

    # Step 3: Score quality (medium)
    score = score_design_quality(design)

    # Notify user via websocket
    notify_user(org_id, {"status": "complete", "design_url": design.url})
```

#### **2. Caching Strategy**
```python
# Redis cache for frequently accessed data
- Brand tokens: 1 hour TTL
- Layout templates: 24 hour TTL
- Generated images: 7 day TTL
- Font files: Permanent (CDN)

# Cache warming
@app.on_startup
def warm_cache():
    # Pre-load popular brand kits
    # Pre-generate layout thumbnails
    pass
```

#### **3. Rate Limiting**
```python
# DALL-E rate limits (5 images/min)
- Implement token bucket algorithm
- Queue overflow requests
- Provide ETA to users

# API rate limits
- 100 requests/min per org
- Burst allowance: 20 requests
```

#### **4. CDN Configuration**
```yaml
# Cloudflare / CloudFront
assets:
  - generated_images: cache 7 days
  - brand_logos: cache 30 days
  - fonts: cache 365 days

api:
  - /api/designs: no cache
  - /api/templates: cache 1 hour
```

#### **5. Monitoring**
```python
# Key metrics to track
- DALL-E API latency (p50, p95, p99)
- Design generation success rate
- Quality scores distribution
- User satisfaction (thumbs up/down)
- Export rate (to Canva/Figma)
- A/B test performance

# Alerts
- DALL-E rate limit exceeded
- Quality score < 70 (investigate)
- High error rate (> 5%)
```

---

## 🔄 User Journey (End-to-End)

### **Phase 1: Brand Onboarding**
```
1. User uploads brand book PDF
   ↓
2. brand_parser.py extracts tokens
   ↓
3. User reviews/edits tokens in UI
   ↓
4. User uploads logo variants
   ↓
5. Brand Brain stores everything
```

### **Phase 2: Design Creation**
```
1. User opens chat interface
   ↓
2. User: "Create a Black Friday Instagram post"
   ↓
3. chat_planner.py asks clarifying questions
   ↓
4. User provides details
   ↓
5. GPT-4 generates DesignPlan
   ↓
6. layout_engine.py selects optimal template
   ↓
7. gen_openai.py generates background (DALL-E)
   ↓
8. design_renderer.py composes final design
   ↓
9. quality_scorer.py validates output
   ↓
10. User sees design + quality score
```

### **Phase 3: Iteration**
```
1. User: "Make the text bigger"
   ↓
2. chat_planner.py understands intent
   ↓
3. Updates DesignPlan (headline font_size += 20%)
   ↓
4. Re-renders instantly (no DALL-E call needed)
   ↓
5. Shows updated design
```

### **Phase 4: Export**
```
Option A: Download PNG
Option B: Export to Canva (editable)
Option C: Export to Figma (for designers)
Option D: Generate variations (A/B test)
```

---

## 📦 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit | Rapid prototyping, chat UI |
| **Backend** | FastAPI (optional) | API for mobile/web clients |
| **Agent AI** | GPT-4 Turbo | Planning, reasoning, conversation |
| **Image AI** | DALL-E 3 | Background generation |
| **Rendering** | Pillow, svgwrite | Design composition |
| **PDF Parsing** | pdfplumber, PyPDF2 | Brand book extraction |
| **Vision AI** | GPT-4 Vision | Logo extraction, color detection |
| **Database** | PostgreSQL (Supabase) | Brand data, assets |
| **Storage** | Supabase Storage (S3) | Images, PDFs |
| **Cache** | Redis | Session, brand tokens |
| **Queue** | Celery + Redis | Async generation |
| **Monitoring** | Sentry, Datadog | Error tracking, metrics |

---

## 🎯 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Time to First Design** | < 2 min | From upload to first PNG |
| **Design Quality Score** | > 85/100 | Automated scorer |
| **User Satisfaction** | > 4.5/5 | Thumbs up/down |
| **Iteration Speed** | < 10 sec | Text changes, re-render |
| **Brand Consistency** | > 95% | Color/font compliance |
| **Accessibility** | 100% WCAG AA | Contrast ratios |
| **Export Rate** | > 60% | Users who download |
| **Return Rate** | > 70% | Users who create 2+ designs |

---

## 🚦 Implementation Roadmap

### **Week 1: Foundation**
- [x] Analyze existing code
- [ ] Create brand_parser.py
- [ ] Create layout_engine.py
- [ ] Create contrast_manager.py
- [ ] Database schema migration

### **Week 2: Core Features**
- [ ] Enhance chat_planner.py (clarifying questions)
- [ ] Create design_renderer.py (SVG support)
- [ ] Create quality_scorer.py
- [ ] Integration testing

### **Week 3: Polish & Export**
- [ ] Create export_bridge.py (Canva/Figma)
- [ ] A/B testing framework
- [ ] Performance optimization
- [ ] User testing

### **Week 4: Scale**
- [ ] Async queue setup (Celery)
- [ ] Redis caching
- [ ] CDN configuration
- [ ] Monitoring & alerts
- [ ] Production deployment

---

## 🔐 Security & Compliance

- **API Keys:** Store in environment variables, never commit
- **User Data:** GDPR-compliant (data deletion, export)
- **Rate Limiting:** Prevent abuse
- **Content Moderation:** OpenAI moderation API for all prompts
- **Brand Data:** Encrypted at rest (PostgreSQL TDE)
- **Access Control:** Row-level security (RLS) in Supabase

---

## 📚 References

- [Lovable.ai](https://lovable.ai) - Conversational design patterns
- [Artificial Studio](https://artificial.studio) - AI design tools
- [Canva Connect API](https://www.canva.com/developers/docs/connect/) - Integration docs
- [Figma REST API](https://www.figma.com/developers/api) - Programmatic design
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/) - Accessibility standards

---

**Next Steps:** Let's start implementing! 🚀
