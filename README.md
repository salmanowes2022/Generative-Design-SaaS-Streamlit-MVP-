# Brand Asset Generator v2 🎨

AI-powered brand-consistent design generation with **Brand Brain** intelligence.

Transform chat messages into finished, on-brand designs automatically using OpenAI DALL-E 3 and Canva.

## 🚀 What's New in v2

### 🔗 Canva Connect API Integration (NEW!)
- **OAuth2 Authentication**: Secure user authorization with Canva
- **Template Management**: Browse and configure brand templates
- **Automated Design Creation**: AI backgrounds + Canva templates
- **Design Export**: High-quality PNG/JPG exports
- **User Workspace Access**: Profile, designs, and team integration

👉 **[Quick Start Guide](./QUICKSTART.md)** | **[Full Documentation](./CANVA_INTEGRATION.md)**

### Brand Brain Architecture
- **Design Tokens**: Colors, typography, logo rules, layouts, templates
- **Brand Policies**: Voice guidelines, forbidden terms
- **Intelligent Prompting**: Camera cues, negative space awareness
- **Color Science**: ΔE (CIE2000) color matching, WCAG contrast validation

### Non-Hybrid UX
**Chat → Plan → Create in Canva**

1. **Chat**: Natural language input (e.g., "Create an Instagram post for our product launch")
2. **Plan**: AI generates structured JSON plan with brand constraints
3. **Create**: Renders finished design directly in Canva (not manual overlay)

### Key Features

✅ **OCR Gate**: Automatically rejects AI backgrounds with accidental text
✅ **Logo Engine**: Luminance-based variant selection (light/dark/color)
✅ **Validator v2**: On-brand scoring (0-100) with ΔE color matching
✅ **Canva Renderer**: Native template autofill via Connect API
✅ **Planner Agent**: Strict JSON with constraints (headline ≤7 words, CTA whitelist)
✅ **OAuth2 Flow**: Secure Canva authentication with automatic token refresh

## 📦 Tech Stack

- **Frontend**: Streamlit (Python web framework)
- **AI**: OpenAI GPT-4 + DALL-E 3
- **Database**: PostgreSQL (Supabase)
- **Rendering**: Canva Connect API (OAuth2 + Autofill)
- **OCR**: Tesseract
- **Color Science**: ColorMath (ΔE calculations)
- **Payments**: Stripe
- **Integration**: Canva Connect API v1 with OAuth2

## 🏗️ Architecture

```
┌─────────────┐
│   User      │
│   Chat      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  Planner Agent v2               │
│  - Parse intent                 │
│  - Apply constraints            │
│  - Generate JSON plan           │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Brand Brain                    │
│  - Load tokens & policies       │
│  - Build AI prompt              │
│  - Check CTA whitelist          │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  AI Background Generation       │
│  - DALL-E 3 with brand context  │
│  - OCR validation (auto-retry)  │
│  - Negative space for logo      │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Canva Renderer                 │
│  - Select template              │
│  - Autofill placeholders        │
│  - Export PNG                   │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Validator v2                   │
│  - ΔE color matching            │
│  - WCAG contrast check          │
│  - Policy compliance            │
│  - On-brand score (0-100)       │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────┐
│  Finished   │
│  Design     │
└─────────────┘
```

## 🎯 Quick Start

### 1. Prerequisites

- Python 3.9+
- PostgreSQL database (or Supabase account)
- OpenAI API key
- Canva Developer account
- Tesseract OCR (for text detection)

### 2. Installation

```bash
# Clone repository
git clone <your-repo-url>
cd Generative-Design-SaaS-Streamlit-MVP-

# Install dependencies
pip install -r requirements.txt

# Install system dependencies (macOS)
brew install poppler tesseract

# Linux (Ubuntu/Debian)
sudo apt-get install poppler-utils tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### 3. Configuration

```bash
# Copy environment template
cp .env.sample .env

# Edit .env with your credentials
nano .env
```

**Required values:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `CANVA_CLIENT_ID` - Canva app client ID
- `CANVA_CLIENT_SECRET` - Canva app secret

### 4. Database Setup

```bash
# Run migrations
psql $DATABASE_URL < migrations/001_brand_brain_v2.sql

# Or in Supabase SQL Editor:
# 1. Open SQL Editor
# 2. Paste contents of migrations/001_brand_brain_v2.sql
# 3. Run
```

### 5. Run Application

```bash
streamlit run app/Home.py
```

Visit: `http://localhost:8501`

## 📚 Usage

### Onboarding a Brand

1. **Upload Brand Book PDF**
   - System extracts colors, typography, logo rules, voice guidelines
   - Uses GPT-4 Vision for visual analysis

2. **Provide Example Designs** (Optional)
   - Upload 3-5 existing brand designs
   - AI learns visual patterns and style DNA

3. **Review & Confirm**
   - Check extracted tokens (colors, fonts, templates)
   - Verify policies (voice traits, forbidden terms)
   - System saves to Brand Brain

### Creating Designs

1. **Navigate to Generate v2**
2. **Select brand kit** from sidebar
3. **Chat with AI**:
   ```
   "Create an Instagram story promoting our new product launch
   with an energetic, modern vibe"
   ```

4. **Review Plan**:
   - Headline: "New Product Drops" (6 words ✓)
   - Subhead: "Discover innovation at its finest" (5 words ✓)
   - CTA: "Shop Now" (in whitelist ✓)
   - Visual: "Modern tech product on sleek surface..."

5. **Click "Create in Canva"**
   - AI generates background (with OCR check)
   - Canva renders final design
   - Validator scores brand compliance

6. **Download or Edit**
   - Download PNG directly
   - Or open in Canva for tweaks

## 🎨 Creating Canva Templates

See [docs/HowTo_Templates.md](docs/HowTo_Templates.md) for detailed guide.

**Quick template requirements:**

```
Required placeholders:
- HEADLINE (text, ≤7 words)
- SUBHEAD (text, ≤16 words)
- CTA_TEXT (text, from whitelist)
- BG_IMAGE (image, AI-generated)
- PRIMARY_COLOR (color, from tokens)

Design requirements:
- Reserve logo safe zone (40px clearance)
- Ensure WCAG AA contrast (4.5:1)
- Support both light and dark backgrounds
- Grid-based layout (12 columns)
```

## 🧪 Testing

```bash
# Run full test suite
pytest tests/ -v

# Run specific test file
pytest tests/test_brand_brain_v2.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## 📖 Documentation

- **[Architecture v2](ARCHITECTURE_V2.md)** - Complete system architecture
- **[Template Guide](docs/HowTo_Templates.md)** - Creating Canva templates
- **[API Reference](docs/API.md)** - API endpoints (coming soon)
- **[Contributing](CONTRIBUTING.md)** - How to contribute (coming soon)

## 🔑 Key Concepts

### Design Tokens

Structured brand guidelines stored as JSONB:

```json
{
  "color": {
    "primary": "#4F46E5",
    "secondary": "#7C3AED",
    "min_contrast": 4.5
  },
  "type": {
    "heading": {"font": "Inter", "weight": 700},
    "body": {"font": "Inter", "weight": 400}
  },
  "logo": {
    "variants": ["light", "dark", "full_color"],
    "min_px": 120,
    "safe_zone_px": 40,
    "allowed_positions": ["top-right", "bottom-right"]
  },
  "templates": {
    "ig_1x1": "canva_template_id_here"
  },
  "cta_whitelist": ["Get Started", "Learn More"]
}
```

### Brand Policies

Voice and content guidelines:

```json
{
  "voice": ["professional", "friendly", "clear", "concise"],
  "forbid": ["cheap", "discount", "hurry", "limited time"]
}
```

### On-Brand Scoring

Validation produces 0-100 score:

```
Score = (Color × 0.40) + (Contrast × 0.30) + (Policy × 0.30)

Color Score:
- ΔE < 5: 100 (excellent)
- ΔE < 10: 90 (good)
- ΔE < 20: 70 (acceptable)
- ΔE > 20: <50 (poor)

Contrast Score:
- Ratio ≥ 4.5:1: 100 (WCAG AA)
- Ratio ≥ 3.0:1: 80 (WCAG Large)
- Ratio < 3.0:1: <70 (fail)

Policy Score:
- 100 - (10 × violations)
```

## 🛠️ Development

### Project Structure

```
.
├── app/
│   ├── core/
│   │   ├── brand_brain.py          # Tokens, policies, persistence
│   │   ├── prompt_builder_v2.py    # Enhanced prompting
│   │   ├── ocr_validator.py        # Text detection gate
│   │   ├── validator_v2.py         # ΔE, WCAG, scoring
│   │   ├── logo_engine.py          # Luminance-based placement
│   │   ├── renderer_canva.py       # Canva API integration
│   │   └── planner_v2.py           # Chat to JSON planner
│   ├── pages/
│   │   ├── 1_Onboard_Brand_Kit.py
│   │   └── 2_Generate_V2.py        # New chat-based UI
│   └── infra/
│       ├── db.py
│       └── logging.py
├── migrations/
│   └── 001_brand_brain_v2.sql
├── tests/
│   └── test_brand_brain_v2.py
├── docs/
│   └── HowTo_Templates.md
├── requirements.txt
├── .env.sample
└── README.md
```

### Adding New Features

1. **New token type**: Update `BrandTokens` dataclass in `brand_brain.py`
2. **New validation**: Add method to `ValidatorV2` class
3. **New template placeholder**: Update template contract in docs
4. **New channel**: Add to `planner_v2._get_default_aspect_ratio()`

### Database Migrations

```bash
# Create new migration
touch migrations/002_your_feature.sql

# Add SQL statements
# Run via psql or Supabase SQL Editor
```

## 🐛 Troubleshooting

### OCR Gate Rejecting Clean Images

**Problem**: OCR detects noise as text

**Solution**: Adjust threshold in `.env`:
```
OCR_CONFIDENCE_THRESHOLD=70  # Increase from default 60
OCR_MIN_TEXT_LENGTH=5        # Increase from default 3
```

### Canva "Template Not Found"

**Problem**: Template ID incorrect or not shared

**Solution**:
1. Verify template ID in URL
2. Check template is set to "Anyone with link"
3. Ensure all placeholders named correctly (case-sensitive)

### Low On-Brand Scores

**Problem**: Designs scoring <70 consistently

**Solution**:
1. Review extracted tokens - may need manual adjustment
2. Check if brand guidelines are comprehensive
3. Verify DALL-E is respecting color prompts
4. Consider adjusting scoring weights in `ValidatorV2`

### Rate Limiting

**Problem**: OpenAI 429 errors

**Solution**:
- Increase `OPENAI_RETRY_DELAY` in `.env`
- Reduce `num_images` in generation
- Upgrade OpenAI tier
- Implement request queuing

## 📊 Monitoring

### Agent Audit Log

All Brand Brain decisions logged to `agent_audit` table:

```sql
SELECT
  action,
  payload->>'user_message' as message,
  result->>'plan' as plan,
  duration_ms,
  created_at
FROM agent_audit
WHERE org_id = 'your-org-id'
ORDER BY created_at DESC
LIMIT 10;
```

### Validation Metrics

```sql
SELECT
  AVG(on_brand_score) as avg_score,
  COUNT(*) FILTER (WHERE on_brand_score >= 90) as excellent,
  COUNT(*) FILTER (WHERE on_brand_score >= 70) as good,
  COUNT(*) FILTER (WHERE on_brand_score < 70) as needs_work
FROM assets
WHERE org_id = 'your-org-id'
  AND created_at > NOW() - INTERVAL '30 days';
```

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Areas needing help:**
- Additional Canva templates
- More validation rules
- Figma integration
- Multi-language support

## 📄 License

[MIT License](LICENSE)

## 🙏 Acknowledgments

- OpenAI for DALL-E 3 and GPT-4
- Canva for design API
- Streamlit for rapid prototyping
- ColorMath for color science

## 📧 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/your-repo/issues)
- **Email**: support@yourdomain.com

---

Built with ❤️ by [Your Name]

**Brand Brain v2** - Designs that feel like your designer made them, because the AI learned from your brand.
