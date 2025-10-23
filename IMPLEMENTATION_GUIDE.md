# 🚀 Implementation Guide - Architecture V3

**Last Updated:** 2025-10-22

This guide walks you through implementing the enhanced architecture step-by-step.

---

## 📋 Prerequisites

### **Required**
- Python 3.10+
- PostgreSQL 14+ (or Supabase account)
- OpenAI API key (GPT-4 + DALL-E 3 access)
- Git

### **Optional (for advanced features)**
- Canva Connect API credentials
- Figma API token
- Redis (for caching and queues)
- Celery (for async tasks)

---

## 🏗️ Step-by-Step Implementation

### **Phase 1: Database Migration (Week 1, Day 1)**

#### 1.1 Run Database Migration

```bash
# Navigate to project root
cd /Users/salmanawaisa/Desktop/Generative-Design-SaaS-Streamlit-MVP-

# Backup existing database first!
pg_dump your_database > backup_$(date +%Y%m%d).sql

# Run migration
psql -U your_user -d your_database -f database/migration_v3_enhanced_architecture.sql

# Verify migration
psql -U your_user -d your_database -c "SELECT * FROM layout_templates;"
```

**Expected Output:**
- 5 built-in layout templates
- New tables: `layout_templates`, `design_scores`, `brand_learning`, `design_exports`
- Enhanced columns in `brand_kits` and `assets`

---

### **Phase 2: Install Dependencies (Week 1, Day 1)**

#### 2.1 Install Python Packages

```bash
# Core dependencies
pip install pdfplumber>=0.10.0
pip install pillow>=10.0.0
pip install colorsys  # Usually built-in

# Optional: For advanced features
pip install redis>=5.0.0
pip install celery>=5.3.0
pip install svgwrite>=1.4.3  # For SVG export

# Update existing packages
pip install --upgrade openai anthropic streamlit
```

#### 2.2 Verify Installation

```python
# test_imports.py
try:
    import pdfplumber
    import PIL
    from app.core.brand_parser import BrandParser
    from app.core.layout_engine import LayoutEngine
    from app.core.contrast_manager import ContrastManager
    from app.core.quality_scorer import QualityScorer
    from app.core.export_bridge import ExportBridge
    print("✅ All modules imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
```

```bash
python test_imports.py
```

---

### **Phase 3: Configure Environment (Week 1, Day 1)**

#### 3.1 Update `.env` File

```bash
# Add these to your .env file

# OpenAI (required)
OPENAI_API_KEY=sk-...

# Canva (optional)
CANVA_API_KEY=your_canva_api_key
CANVA_API_BASE=https://api.canva.com/rest/v1

# Figma (optional)
FIGMA_API_TOKEN=your_figma_token

# Redis (optional, for production)
REDIS_URL=redis://localhost:6379/0

# Feature flags
ENABLE_PDF_PARSING=true
ENABLE_QUALITY_SCORING=true
ENABLE_CANVA_EXPORT=false
ENABLE_FIGMA_EXPORT=false
```

#### 3.2 Update `app/infra/config.py`

```python
# Add these to your settings class
class Settings(BaseSettings):
    # ... existing settings ...

    # V3 Features
    ENABLE_PDF_PARSING: bool = True
    ENABLE_QUALITY_SCORING: bool = True
    ENABLE_CANVA_EXPORT: bool = False
    ENABLE_FIGMA_EXPORT: bool = False

    # Export APIs
    CANVA_API_KEY: Optional[str] = None
    CANVA_API_BASE: str = "https://api.canva.com/rest/v1"
    FIGMA_API_TOKEN: Optional[str] = None

    # Redis (optional)
    REDIS_URL: Optional[str] = None
```

---

### **Phase 4: Test New Modules (Week 1, Days 2-3)**

#### 4.1 Test Brand Parser

```python
# test_brand_parser.py
from app.core.brand_parser import BrandParser
from pathlib import Path

# Download sample brand book or use your own
pdf_path = "path/to/sample_brand_book.pdf"

parser = BrandParser()
tokens, metadata = parser.parse_brand_book(pdf_path, "Test Brand")

print(f"✅ Parsed brand book!")
print(f"Confidence: {metadata.get('confidence_score')}")
print(f"Colors: {tokens.colors.primary.hex if tokens.colors else 'N/A'}")
print(f"Fonts: {tokens.typography['heading'].family if tokens.typography else 'N/A'}")
```

```bash
python test_brand_parser.py
```

#### 4.2 Test Layout Engine

```python
# test_layout_engine.py
from app.core.layout_engine import layout_engine
from app.core.chat_agent_planner import DesignPlan

# Create mock design plan
plan = DesignPlan(
    headline="Black Friday Sale",
    subhead="Save up to 50% on everything",
    cta_text="Shop Now",
    visual_concept="Modern shopping scene",
    channel="ig",
    aspect_ratio="1x1",
    palette_mode="primary",
    background_style="Vibrant shopping background",
    logo_position="TR"
)

# Get optimal layout
layout = layout_engine.select_optimal_layout(plan)

print(f"✅ Selected layout: {layout.name}")
print(f"Slots: {len(layout.slots)}")
print(f"Aspect ratios: {layout.aspect_ratios}")
```

```bash
python test_layout_engine.py
```

#### 4.3 Test Contrast Manager

```python
# test_contrast.py
from app.core.contrast_manager import contrast_manager

# Test contrast ratio
fg = "#FFFFFF"  # White text
bg = "#4F46E5"  # Brand primary

result = contrast_manager.check_contrast(fg, bg)

print(f"Contrast ratio: {result.ratio}:1")
print(f"WCAG AA: {'✅ Pass' if result.passes_aa else '❌ Fail'}")
print(f"WCAG AAA: {'✅ Pass' if result.passes_aaa else '❌ Fail'}")

# Test color adjustment
adjusted = contrast_manager.ensure_readable_text("#999999", bg)
print(f"Adjusted color: {adjusted}")
```

```bash
python test_contrast.py
```

#### 4.4 Test Quality Scorer

```python
# test_quality_scorer.py
from app.core.quality_scorer import score_design
from app.core.chat_agent_planner import DesignPlan

plan = DesignPlan(
    headline="Black Friday Sale",
    subhead="Save up to 50% on everything",
    cta_text="Shop Now",
    visual_concept="Modern shopping scene with authentic people shopping",
    channel="ig",
    aspect_ratio="1x1",
    palette_mode="primary",
    background_style="Professional retail environment, natural lighting",
    logo_position="TR"
)

score = score_design(plan)

print(f"Overall Score: {score.overall_score}/100")
print(f"Readability: {score.readability.score}/100")
print(f"Brand Consistency: {score.brand_consistency.score}/100")
print(f"Suggestions:")
for suggestion in score.suggestions:
    print(f"  - {suggestion}")
```

```bash
python test_quality_scorer.py
```

---

### **Phase 5: Integrate into Streamlit App (Week 1, Days 4-5)**

#### 5.1 Update Brand Onboarding Page

Edit `app/pages/1_Onboard_Brand_Kit.py`:

```python
# Add PDF upload section
uploaded_file = st.file_uploader("Upload Brand Book (PDF)", type=['pdf'])

if uploaded_file:
    # Save temporarily
    pdf_path = f"/tmp/{uploaded_file.name}"
    with open(pdf_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

    # Parse with progress
    with st.spinner("🔍 Analyzing brand book..."):
        from app.core.brand_parser import BrandParser

        parser = BrandParser()
        tokens_v2, metadata = parser.parse_brand_book(pdf_path, brand_name)

        st.success(f"✅ Parsed! Confidence: {metadata.get('confidence_score', 0):.0%}")

        # Display extracted tokens
        if tokens_v2.colors:
            st.write("**Colors:**")
            st.color_picker("Primary", tokens_v2.colors.primary.hex, disabled=True)
            st.color_picker("Secondary", tokens_v2.colors.secondary.hex, disabled=True)

        if tokens_v2.typography:
            st.write("**Typography:**")
            st.write(f"Heading: {tokens_v2.typography['heading'].family}")

        # Allow user to review/edit
        st.info("💡 Review extracted data and adjust if needed")

        # Save to database
        if st.button("Save Brand Kit"):
            # Save tokens_v2 to brand_kits.tokens_v2 column
            pass
```

#### 5.2 Enhance Chat Create Page

Edit `app/pages/3_Chat_Create.py`:

```python
# After design generation, add quality scoring

# Generate design (existing code)
design_image = renderer.render_design(...)

# NEW: Score design quality
with st.spinner("Scoring design quality..."):
    from app.core.quality_scorer import score_design

    score = score_design(plan, tokens)

    st.metric("Quality Score", f"{score.overall_score}/100")

    # Show breakdown
    with st.expander("📊 Score Breakdown"):
        col1, col2, col3 = st.columns(3)
        col1.metric("Readability", f"{score.readability.score}/100")
        col2.metric("Brand", f"{score.brand_consistency.score}/100")
        col3.metric("Accessibility", f"{score.accessibility.score}/100")

    # Show suggestions if score < 85
    if score.overall_score < 85:
        st.warning("💡 Suggestions:")
        for suggestion in score.suggestions:
            st.write(f"- {suggestion}")

# NEW: Add export options
st.markdown("---")
st.subheader("Export Options")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Download PNG"):
        # Existing download logic
        pass

with col2:
    if st.button("🎨 Edit in Canva"):
        from app.core.export_bridge import export_to_canva

        result = export_to_canva(plan, bg_url, logo_url)

        if result.success:
            st.success(f"✅ [Open in Canva]({result.editor_url})")
        else:
            st.error(f"Export failed: {result.error}")

with col3:
    if st.button("🎨 Edit in Figma"):
        # Similar to Canva
        pass
```

---

### **Phase 6: Production Optimizations (Week 2)**

#### 6.1 Set Up Redis Caching (Optional)

```python
# app/infra/cache.py
import redis
import json
from typing import Optional, Any
from app.infra.config import settings

class CacheManager:
    def __init__(self):
        if settings.REDIS_URL:
            self.client = redis.from_url(settings.REDIS_URL)
        else:
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None

        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except:
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        if not self.client:
            return

        try:
            self.client.setex(key, ttl, json.dumps(value))
        except:
            pass

cache = CacheManager()
```

**Usage:**

```python
# Cache brand tokens
from app.infra.cache import cache

# Try cache first
tokens = cache.get(f"brand_tokens:{brand_kit_id}")

if not tokens:
    # Load from database
    tokens, policies = brand_brain.get_brand_brain(brand_kit_id)
    # Cache for 1 hour
    cache.set(f"brand_tokens:{brand_kit_id}", tokens.to_dict(), ttl=3600)
```

#### 6.2 Set Up Async Tasks with Celery (Optional)

```python
# app/infra/celery_app.py
from celery import Celery
from app.infra.config import settings

celery_app = Celery(
    'brand_designer',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task
def generate_design_async(plan_id: str, org_id: str):
    """Background task for design generation"""
    # Load plan
    # Generate image (DALL-E - slow)
    # Render layout
    # Score quality
    # Save to database
    # Notify user
    pass
```

**Start Celery worker:**

```bash
celery -A app.infra.celery_app worker --loglevel=info
```

---

### **Phase 7: Monitoring & Logging (Week 2)**

#### 7.1 Enhanced Logging

```python
# app/infra/logging.py (enhance existing)
import logging
from datetime import datetime

def log_design_generation(plan, score, duration_ms):
    """Log design generation metrics"""
    logger.info(
        "Design generated",
        extra={
            "event": "design_generation",
            "headline": plan.headline,
            "channel": plan.channel,
            "quality_score": score.overall_score,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat()
        }
    )
```

#### 7.2 Error Tracking (Optional: Sentry)

```python
# app/infra/sentry.py
import sentry_sdk
from app.infra.config import settings

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=settings.APP_ENV
    )
```

---

## 🧪 Testing Checklist

### **Unit Tests**

- [ ] Brand parser extracts colors correctly
- [ ] Layout engine selects appropriate templates
- [ ] Contrast manager calculates ratios accurately
- [ ] Quality scorer detects issues
- [ ] Export bridge handles API errors

### **Integration Tests**

- [ ] End-to-end design generation
- [ ] PDF upload → Token extraction → Design creation
- [ ] Quality scoring → Suggestions → Iteration
- [ ] Export to Canva (if enabled)

### **User Acceptance Tests**

- [ ] Brand book upload flow is intuitive
- [ ] Chat interface responds quickly
- [ ] Quality scores are helpful
- [ ] Export options work seamlessly

---

## 📊 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| PDF parsing time | < 30s | TBD |
| Design generation | < 90s | TBD |
| Quality scoring | < 5s | TBD |
| Template selection | < 1s | TBD |
| Export to Canva | < 10s | TBD |

---

## 🐛 Troubleshooting

### **Issue: PDF parsing fails**
**Solution:**
```bash
# Install system dependencies
brew install poppler  # macOS
apt-get install poppler-utils  # Linux

# Reinstall pdfplumber
pip uninstall pdfplumber
pip install pdfplumber==0.10.3
```

### **Issue: GPT-4 Vision not available**
**Solution:**
- Ensure your OpenAI account has GPT-4 Vision access
- Fallback to text-only parsing if needed:
```python
parser = BrandParser()
tokens, metadata = parser.parse_brand_book(pdf_path, brand_name)

if metadata.get('confidence_score', 0) < 0.5:
    # Use manual input
    tokens = parser.fallback_manual_input()
```

### **Issue: Canva export fails**
**Solution:**
- Verify API credentials
- Check API endpoint URL
- Review Canva API logs
- Fallback to PNG download

---

## 🚀 Deployment

### **Development**
```bash
streamlit run app/streamlit_app.py
```

### **Production (Docker)**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Run
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501"]
```

```bash
docker build -t brand-designer .
docker run -p 8501:8501 --env-file .env brand-designer
```

---

## 📈 Next Steps

1. **Week 3:** User testing and feedback
2. **Week 4:** Performance optimization
3. **Month 2:** Advanced features (A/B testing, brand learning)
4. **Month 3:** Mobile app, API access

---

## 🆘 Support

- **Documentation:** See [ARCHITECTURE_V3_REDESIGN.md](ARCHITECTURE_V3_REDESIGN.md)
- **Issues:** GitHub Issues
- **Slack:** #brand-design-agent channel

---

**Happy Building!** 🎨✨
