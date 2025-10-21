# Quick Start Guide - AI Design Assistant

## System Status

✅ **All modules integrated and tested successfully!**

The system has been evolved with 5 new AI-powered modules for smarter, more flexible design generation.

## What's New

### 1. Chat-Based Design Creation (💬 Chat Create)
- Natural language design requests
- Multi-turn conversations with brand awareness
- Automatic design plan generation
- Quality scoring and auto-improvement

### 2. Brand Book Parser
- Upload PDF/DOCX brand guidelines
- AI extraction of brand tokens (colors, fonts, logos)
- Automatic policy detection (voice, forbidden terms)

### 3. Template-Free Grid Renderer
- No Canva templates required
- Pure Python rendering with Pillow
- 12-column responsive grid system
- Brand-compliant layouts

### 4. Quality Scoring System
- 5-dimensional evaluation
- Text contrast (30%), CTA prominence (25%), Layout balance (20%), Brand accuracy (15%), Visual hierarchy (10%)
- Automatic improvement suggestions
- Quality gates for production

### 5. Template Validator
- Diagnose Canva template issues
- Validate autofill capability
- Actionable fix suggestions

## Installation

### 1. Install New Dependencies

\`\`\`bash
pip install pdfplumber python-docx
\`\`\`

All other dependencies are already in requirements.txt.

### 2. Verify Installation

\`\`\`bash
python -c "from app.core.brandbook_parser import BrandBookParser; from app.core.chat_agent_planner import ChatAgentPlanner; from app.core.renderer_grid import GridRenderer; print('✅ All modules loaded successfully!')"
\`\`\`

## Quick Start

### Option 1: Use the Chat Interface (Recommended)

1. **Start the app:**
   \`\`\`bash
   cd app
   streamlit run streamlit_app.py
   \`\`\`

2. **Navigate to Chat Create:**
   - Click the **💬 Chat Create** button on the home page
   - Or go directly to the "3_Chat_Create" page

3. **Start creating:**
   \`\`\`
   User: "Create a Black Friday Instagram post for 30% off sale"

   Assistant: [Generates design plan with brand-compliant copy and visuals]

   [Click "Generate Design" → AI creates complete design with quality scoring]
   \`\`\`

### Option 2: Parse a Brand Book

1. **Navigate to Onboard Brand Kit**

2. **Upload your brand book** (PDF, DOCX, or TXT):
   \`\`\`
   Sample: sample_brandbook.txt (included in repo)
   \`\`\`

3. **AI automatically extracts:**
   - Brand colors (primary, secondary, accent)
   - Fonts (heading, body)
   - Logo requirements
   - Voice & personality traits
   - Forbidden terms
   - Approved CTAs

## Testing

### Run the Test Suite

\`\`\`bash
python test_new_features.py
\`\`\`

This tests:
- ✅ Brand book parsing
- ✅ Chat agent planning
- ✅ Grid rendering
- ✅ Quality scoring
- ⚠️ Template validation (manual - requires Canva access token)

## Two Rendering Paths

### Path 1: Canva Integration (Existing)
- Uses Canva templates with autofill
- Requires template configuration in Canva
- **Status:** Working with asset upload, but template needs data field configuration

### Path 2: Grid Renderer (New)
- Template-free rendering
- Pure Python with Pillow
- **Status:** ✅ Fully functional and tested

## Navigation Updates

The home page now includes:

\`\`\`
[🏁 Setup Brand Kit] [💬 Chat Create] [🎨 Generate Assets] [📚 View Library]
\`\`\`

New features highlighted:
- 💬 **Chat-Based Design** - Conversational AI assistant
- 📖 **Brand Book Parsing** - Upload PDFs/DOCX to auto-extract
- ✅ **Quality Scoring** - 5-dimensional quality evaluation

## Support

- **Full Documentation:** INTEGRATION_GUIDE.md
- **Test Suite:** \`python test_new_features.py\`
- **Sample Data:** sample_brandbook.txt

---

**✨ You're ready to create human-quality designs with AI!**
