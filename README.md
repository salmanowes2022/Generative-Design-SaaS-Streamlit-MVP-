# AI Design Assistant - Brand-Powered Social Media Design

Simple, fast AI-powered design generation with automatic brand compliance.

## What It Does

Upload your brand book once → Chat to create designs → Download professional PNG

## 3-Step Workflow

### 1. Upload Brand Book
- Upload PDF brand guidelines
- AI extracts: colors, fonts, voice, CTAs, forbidden terms, logo
- One-time setup

### 2. Create Designs
- Chat: "Create a Black Friday Instagram post"
- AI generates professional design with:
  - Large visible text (110px headlines)
  - Real people in backgrounds
  - Your brand colors
  - Your logo
  - Approved CTAs only
  - Text shadows for readability

### 3. Download
- PNG ready to post
- Saved in library automatically

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# Run the app
streamlit run app/streamlit_app.py
```

## System Architecture

### Pages (3):
- `1_Onboard_Brand_Kit.py` - Upload brand book
- `3_Chat_Create.py` - Create designs
- `4_Library.py` - View all designs

### Core Modules (10):
- `brandbook_analyzer.py` - Extract data from brand book PDFs
- `brand_brain.py` - Store & manage brand tokens
- `chat_agent_planner.py` - Conversational design planning
- `renderer_grid.py` - Template-free grid-based rendering
- `gen_openai.py` - DALL-E background generation
- `brandkit.py` - Brand kit management
- `logo_extractor.py` - Extract logos from PDFs
- `storage.py` - File storage
- `schemas.py` - Data models
- `brand_intelligence.py` - Analysis results

## Features

✅ Chat-based creation  
✅ Automatic brand book parsing  
✅ Professional typography (huge text!)  
✅ Real people in backgrounds  
✅ Brand color enforcement  
✅ Voice trait matching  
✅ Forbidden term avoidance  
✅ CTA whitelist  
✅ Logo placement  
✅ Fast (no validation delays)  
✅ Simple (3-step workflow)  

## Technology Stack

- **Frontend:** Streamlit
- **AI:** GPT-4, GPT-4 Vision, DALL-E 3
- **Rendering:** Pillow (Python)
- **Database:** PostgreSQL
- **Storage:** Supabase
- **Language:** Python 3.11+

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - User quick start guide
- [SIMPLIFIED_SYSTEM.md](SIMPLIFIED_SYSTEM.md) - System overview
- [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md) - What was removed & why

## Requirements

```
streamlit==1.32.0
openai==1.14.0
pillow==10.2.0
psycopg[binary]==3.1.18
supabase==2.7.4
pdfplumber==0.11.0
python-docx==1.1.0
```

## Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
DATABASE_URL=your_postgres_url
APP_ENV=development
```

## License

MIT
