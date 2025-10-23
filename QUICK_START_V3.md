# ⚡ Quick Start Guide - Architecture V3

**Get up and running in 30 minutes!**

---

## 🎯 What You're Building

An AI-powered brand design agent that:
- ✅ Parses PDF brand books automatically
- ✅ Generates pixel-perfect social media posts
- ✅ Validates designs with quality scores (0-100)
- ✅ Exports to Canva/Figma for editing
- ✅ Ensures WCAG accessibility compliance

---

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL or Supabase account
- OpenAI API key (GPT-4 + DALL-E 3 access)
- 30 minutes

---

## 🚀 Installation (5 minutes)

### Step 1: Install System Dependencies

**macOS:**
```bash
brew install poppler tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install poppler-utils tesseract-ocr
```

**Windows:**
```powershell
choco install poppler tesseract
```

### Step 2: Install Python Packages

```bash
cd /Users/salmanawaisa/Desktop/Generative-Design-SaaS-Streamlit-MVP-

# Install all dependencies
pip install -r requirements_v3.txt

# Or install only V3 essentials
pip install pdfplumber pillow openai streamlit psycopg[binary] supabase
```

### Step 3: Verify Installation

```bash
python -c "import pdfplumber, PIL, openai; print('✅ All packages installed!')"
```

---

## 🗄️ Database Setup (5 minutes)

### Option A: Local PostgreSQL

```bash
# Backup existing database
pg_dump your_database > backup_$(date +%Y%m%d).sql

# Run migration
psql -U your_user -d your_database -f database/migration_v3_enhanced_architecture.sql

# Verify
psql -U your_user -d your_database -c "SELECT COUNT(*) FROM layout_templates;"
```

**Expected Output:** `5` (built-in templates)

### Option B: Supabase

1. Go to your Supabase project
2. Navigate to **SQL Editor**
3. Copy/paste contents of `database/migration_v3_enhanced_architecture.sql`
4. Click **Run**
5. Verify in **Table Editor** → see `layout_templates`, `design_scores`, etc.

---

## ⚙️ Configuration (5 minutes)

### Update `.env` File

```bash
# Add these lines to your .env file

# OpenAI (REQUIRED)
OPENAI_API_KEY=sk-proj-...

# Database (REQUIRED)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Supabase (if using)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...

# Feature Flags (V3)
ENABLE_PDF_PARSING=true
ENABLE_QUALITY_SCORING=true
ENABLE_LAYOUT_ENGINE=true

# Export Features (OPTIONAL)
ENABLE_CANVA_EXPORT=false
CANVA_API_KEY=
ENABLE_FIGMA_EXPORT=false
FIGMA_API_TOKEN=

# Performance (OPTIONAL)
REDIS_URL=redis://localhost:6379/0
```

---

## 🧪 Test New Features (10 minutes)

### Test 1: Brand Parser

Create `test_v3_features.py`:

```python
from app.core.brand_parser import BrandParser

# Test with a sample PDF (create one or download)
parser = BrandParser()

try:
    tokens, metadata = parser.parse_brand_book(
        pdf_path="sample_brand_book.pdf",
        brand_name="Test Brand"
    )

    print("✅ Brand Parser Working!")
    print(f"   Confidence: {metadata.get('confidence_score', 0):.0%}")
    if tokens.colors:
        print(f"   Primary Color: {tokens.colors.primary.hex}")
    if tokens.typography:
        print(f"   Heading Font: {tokens.typography['heading'].family}")

except Exception as e:
    print(f"❌ Brand Parser Error: {e}")
    print("   Using fallback tokens instead")
```

**Run:**
```bash
python test_v3_features.py
```

### Test 2: Layout Engine

```python
from app.core.layout_engine import layout_engine
from app.core.chat_agent_planner import DesignPlan

# Create test design plan
plan = DesignPlan(
    headline="Black Friday Sale",
    subhead="Up to 50% off everything",
    cta_text="Shop Now",
    visual_concept="Modern shopping scene",
    channel="ig",
    aspect_ratio="1x1",
    palette_mode="primary",
    background_style="Vibrant retail environment",
    logo_position="TR"
)

# Get optimal layout
layout = layout_engine.select_optimal_layout(plan)

print("✅ Layout Engine Working!")
print(f"   Selected: {layout.name}")
print(f"   Slots: {len(layout.slots)}")
print(f"   Channels: {', '.join(layout.channels)}")
```

### Test 3: Quality Scorer

```python
from app.core.quality_scorer import score_design

score = score_design(plan)

print("✅ Quality Scorer Working!")
print(f"   Overall: {score.overall_score}/100")
print(f"   Readability: {score.readability.score}/100")
print(f"   Brand Consistency: {score.brand_consistency.score}/100")
print(f"   Suggestions: {len(score.suggestions)}")
```

### Test 4: Contrast Manager

```python
from app.core.contrast_manager import contrast_manager

result = contrast_manager.check_contrast(
    foreground="#FFFFFF",
    background="#4F46E5"
)

print("✅ Contrast Manager Working!")
print(f"   Ratio: {result.ratio}:1")
print(f"   WCAG AA: {'✅ Pass' if result.passes_aa else '❌ Fail'}")
```

**Run All Tests:**
```bash
python test_v3_features.py
```

**Expected Output:**
```
✅ Brand Parser Working!
✅ Layout Engine Working!
✅ Quality Scorer Working!
✅ Contrast Manager Working!
```

---

## 🎨 Integration into Streamlit (5 minutes)

### Update Brand Upload Page

Edit `app/pages/1_Onboard_Brand_Kit.py`:

```python
import streamlit as st
from app.core.brand_parser import BrandParser

st.title("📖 Upload Brand Kit")

# Add PDF upload
uploaded_file = st.file_uploader(
    "Upload Brand Book (PDF)",
    type=['pdf'],
    help="Upload your brand guidelines PDF for automatic extraction"
)

if uploaded_file:
    # Save temp file
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        pdf_path = tmp_file.name

    # Parse brand book
    with st.spinner("🔍 Analyzing brand book with AI..."):
        parser = BrandParser()
        tokens, metadata = parser.parse_brand_book(pdf_path, brand_name)

        st.success(f"✅ Extraction complete! Confidence: {metadata.get('confidence_score', 0):.0%}")

    # Display extracted data
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Colors")
        if tokens.colors:
            st.color_picker("Primary", tokens.colors.primary.hex, disabled=True)
            st.color_picker("Secondary", tokens.colors.secondary.hex, disabled=True)
            st.color_picker("Accent", tokens.colors.accent.hex, disabled=True)

    with col2:
        st.subheader("Typography")
        if tokens.typography:
            st.text(f"Heading: {tokens.typography['heading'].family}")
            st.text(f"Body: {tokens.typography['body'].family}")

    # Save button
    if st.button("💾 Save Brand Kit", type="primary"):
        # Save to database (use existing brand_kit_manager)
        # ... your existing save logic ...
        st.success("Brand kit saved!")
```

### Update Chat Create Page

Edit `app/pages/3_Chat_Create.py`:

```python
# After design generation, add quality scoring

from app.core.quality_scorer import score_design

# ... existing design generation code ...

# NEW: Score the design
with st.spinner("📊 Scoring design quality..."):
    score = score_design(plan, tokens)

    # Display score
    score_col1, score_col2, score_col3 = st.columns(3)

    score_col1.metric("Overall Quality", f"{score.overall_score}/100")
    score_col2.metric("Readability", f"{score.readability.score}/100")
    score_col3.metric("Accessibility", f"{score.accessibility.score}/100")

    # Show suggestions if score < 85
    if score.overall_score < 85:
        with st.expander("💡 Improvement Suggestions", expanded=True):
            for suggestion in score.suggestions:
                st.info(suggestion)

# NEW: Export options
st.markdown("---")
st.subheader("📤 Export Options")

export_col1, export_col2, export_col3 = st.columns(3)

with export_col1:
    if st.button("📥 Download PNG", use_container_width=True):
        # Your existing download logic
        pass

with export_col2:
    if st.button("🎨 Edit in Canva", use_container_width=True):
        from app.core.export_bridge import export_to_canva

        result = export_to_canva(plan, bg_url, logo_url)

        if result.success:
            st.success(f"✅ [Open in Canva]({result.editor_url})")
        else:
            st.error(f"Export failed: {result.error}")

with export_col3:
    if st.button("📊 View Details", use_container_width=True):
        with st.expander("Design Details", expanded=True):
            st.json(plan.to_dict())
```

---

## 🏃 Run the App (2 minutes)

```bash
streamlit run app/streamlit_app.py
```

Open browser to `http://localhost:8501`

---

## ✅ Verification Checklist

Test these flows:

### 1. Brand Upload Flow
- [ ] Upload a PDF brand book
- [ ] See extracted colors and fonts
- [ ] Review/edit extracted data
- [ ] Save brand kit successfully

### 2. Design Creation Flow
- [ ] Select brand kit in chat
- [ ] Request: "Create a Black Friday Instagram post"
- [ ] See design plan generated
- [ ] Click "Generate Design"
- [ ] See quality score (should be 70-95)
- [ ] See improvement suggestions

### 3. Export Flow
- [ ] Download PNG works
- [ ] Export to Canva (if enabled)
- [ ] Design opens in Canva editor

---

## 🎯 Success Metrics

After setup, you should see:

| Metric | Expected |
|--------|----------|
| PDF parsing time | < 30 seconds |
| Design generation time | < 90 seconds |
| Quality score range | 75-95 |
| Template selection | Instant (<1s) |
| Layout slots | 4-6 per design |

---

## 🐛 Common Issues & Fixes

### Issue: "pdfplumber not found"
```bash
pip install pdfplumber==0.11.0
```

### Issue: "poppler not installed"
```bash
# macOS
brew install poppler

# Ubuntu
sudo apt-get install poppler-utils
```

### Issue: "GPT-4 Vision not available"
**Fix:** Check your OpenAI account has GPT-4 Vision access. Fallback to text-only parsing if needed.

### Issue: "Database migration failed"
```bash
# Rollback
psql -d your_db -c "DROP TABLE IF EXISTS layout_templates CASCADE;"

# Re-run migration
psql -d your_db -f database/migration_v3_enhanced_architecture.sql
```

### Issue: "Quality scores always low"
**Fix:** Review the suggestions. Common issues:
- Headline too long (> 7 words)
- CTA not in approved list
- Contrast ratio too low

---

## 📚 Next Steps

Now that V3 is running:

1. **Test with real brand books** - Upload your company's brand guidelines
2. **Generate 10+ designs** - Get familiar with the flow
3. **Review quality scores** - Learn what makes a good design
4. **Customize layouts** - Create your own templates in `layout_engine.py`
5. **Enable exports** - Set up Canva API credentials
6. **Monitor performance** - Check generation times and optimize

---

## 📖 Documentation

- **Full Architecture:** [ARCHITECTURE_V3_REDESIGN.md](ARCHITECTURE_V3_REDESIGN.md)
- **Implementation Guide:** [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- **Summary:** [ARCHITECTURE_V3_SUMMARY.md](ARCHITECTURE_V3_SUMMARY.md)

---

## 🆘 Need Help?

1. Check [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for detailed steps
2. Review error logs in terminal
3. Test individual modules with provided test scripts
4. Open an issue with error details

---

## 🎉 You're Ready!

Your AI-powered brand design agent is now live with:

- ✅ Automatic brand book parsing
- ✅ Template-free layout generation
- ✅ Quality scoring & validation
- ✅ WCAG accessibility compliance
- ✅ Export to Canva/Figma

**Start creating amazing designs!** 🚀✨

---

**Time to complete:** ~30 minutes
**Difficulty:** Intermediate
**Next milestone:** Generate 10 designs and reach 90+ quality scores
