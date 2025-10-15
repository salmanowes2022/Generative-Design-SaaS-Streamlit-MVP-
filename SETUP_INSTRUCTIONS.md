# Setup Instructions - Complete Brand Intelligence System

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Dependencies
```bash
# Core dependencies (if not already installed)
pip install pdf2image PyPDF2 Pillow

# Install poppler (required for pdf2image)
# On Mac:
brew install poppler

# On Ubuntu/Debian:
sudo apt-get install poppler-utils

# On Windows:
# Download from: https://github.com/oschwartz10612/poppler-windows/releases
# Add to PATH
```

### Step 2: Create Database Table
```bash
# Run this SQL in your Supabase SQL Editor:
# File: database/add_brand_guidelines_table.sql
```

Or copy-paste this:
```sql
CREATE TABLE IF NOT EXISTS brand_guidelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    guidelines JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(org_id)
);

CREATE INDEX IF NOT EXISTS idx_brand_guidelines_org_id ON brand_guidelines(org_id);

ALTER TABLE brand_guidelines ENABLE ROW LEVEL SECURITY;
```

### Step 3: Start Your App
```bash
streamlit run app/streamlit_app.py
```

### Step 4: Upload Your Brand Book
1. Navigate to **🏁 Onboard Brand Kit** page
2. Scroll to **"📖 Upload Brand Book (PDF)"**
3. Upload your brand guidelines PDF
4. Enter your brand name
5. Click **"🧠 Analyze Brand Book"**
6. Wait 2-5 minutes for analysis
7. Done! ✅

---

## 📖 Using the Complete System

### Priority 1: Brand Book (Recommended)
**Best for**: Companies with documented brand guidelines

**Steps**:
1. Go to **🏁 Onboard Brand Kit**
2. Upload brand book PDF
3. Get complete brand knowledge extracted automatically

**What you get**:
- All colors with HEX codes
- Typography rules
- Imagery guidelines
- Brand voice and tone
- Layout principles
- Usage do's and don'ts

### Priority 2: Design Examples
**Best for**: Companies with existing designs but no formal brand book

**Steps**:
1. Go to **🏁 Onboard Brand Kit**
2. Scroll to **"🎨 Upload Brand Example Images"**
3. Upload 4-5 of your best past designs
4. Click **"🧠 Analyze Brand Examples"**

**What you get**:
- Visual style patterns
- Color palette extraction
- Composition rules
- Brand signature
- Design guidelines

### Priority 3: Basic Brand Kit
**Best for**: Quick start or new brands

**Steps**:
1. Go to **🏁 Onboard Brand Kit**
2. Fill out the form with colors and style descriptors
3. Click **"🚀 Create Brand Kit"**

**What you get**:
- Color palette
- Style keywords
- Basic guidelines

---

## 🎯 Recommended Setup Flow

### For Maximum Brand Accuracy:
```
1. Upload Brand Book PDF       → 100% official guidelines
2. Upload 4-5 Design Examples   → Real execution patterns
3. Create Basic Brand Kit       → Fallback settings
4. Generate Designs             → AI uses all three!
```

### Time Investment:
- Brand Book Upload: 5 minutes (one-time)
- Design Examples Upload: 2 minutes (one-time)
- Basic Brand Kit: 2 minutes (one-time)
- **Total: ~10 minutes for complete setup**

---

## 🔍 Testing the System

### Test 1: Check Brand Book Upload
```bash
# After uploading brand book, check database:
# In Supabase SQL Editor:
SELECT org_id, guidelines FROM brand_guidelines;

# You should see your extracted guidelines as JSON
```

### Test 2: Generate a Design
1. Go to **Chat** page
2. Say: "Create a social media post for our new product"
3. Watch logs for:
   ```
   INFO - ✅ Found brand book guidelines - using as primary source
   INFO - Found X examples for deep analysis
   INFO - Using AI-generated brand-aware prompt
   ```
4. Check generated design matches your brand!

### Test 3: View in Library
1. Go to **📚 Library** page
2. See your generated design
3. Verify it matches your brand colors and style

---

## 🐛 Troubleshooting

### Problem: pdf2image not working
**Error**: `pdf2image: Unable to get page count`

**Solutions**:
```bash
# Mac:
brew install poppler

# Ubuntu:
sudo apt-get install poppler-utils

# Verify installation:
which pdfinfo  # Should show path
```

### Problem: PyPDF2 import error
**Error**: `ModuleNotFoundError: No module named 'PyPDF2'`

**Solution**:
```bash
pip install PyPDF2
```

### Problem: Brand book not analyzing
**Check**:
1. Is PDF valid and readable?
2. Are dependencies installed?
3. Check logs for specific errors
4. Try with a smaller PDF (under 10 pages)

### Problem: Generated designs don't match brand
**Solutions**:
1. Check if brand book was successfully uploaded:
   - Go to Brand Kit page
   - Check if guidelines are stored
2. Verify brand book has clear guidelines (not just text)
3. Add design examples to complement brand book
4. Check confidence scores in logs

### Problem: Database table error
**Error**: `relation "brand_guidelines" does not exist`

**Solution**:
Run the SQL from `database/add_brand_guidelines_table.sql` in Supabase

---

## 📊 Monitoring & Logs

### Key Log Messages to Watch:

**Brand Book Loading**:
```
INFO - Checking for brand book guidelines for org {id}
INFO - ✅ Found brand book guidelines - using as primary source
```

**Visual Example Analysis**:
```
INFO - Found 4 examples for deep analysis
INFO - Brand analysis confidence: 90%
```

**Prompt Generation**:
```
INFO - Using AI-generated brand-aware prompt from deep analysis
INFO - Built brand-aware prompt: Subject: ...
```

**Issues**:
```
ERROR - Error analyzing brand book: {error}
ERROR - Brand analysis failed: {error}
WARNING - No brand book uploaded - will use examples and brand kit
```

---

## 🔄 Updating Brand Guidelines

### To Update Brand Book:
1. Upload new PDF (will replace old one)
2. Re-analyze
3. New guidelines stored automatically

### To Add More Examples:
1. Upload additional design examples
2. System re-analyzes all examples
3. Updates patterns automatically

### To Modify Brand Kit:
1. Go to Brand Kit page
2. Create new brand kit (can have multiple)
3. Select which one to use

---

## 📈 Performance Tips

### For Faster Analysis:
- Keep brand books under 20 pages (only first 20 analyzed anyway)
- Use high-quality PDFs (better extraction)
- Ensure good image quality in examples

### For Better Results:
- Include diverse pages in brand book (colors, typography, imagery examples)
- Upload variety of design examples (different layouts, use cases)
- Provide clear, professional designs as examples

### For Cost Optimization:
- Brand book analysis: ~$0.50-$2.00 per analysis (one-time)
- Design example analysis: ~$0.10-$0.30 per image (one-time)
- Generation: ~$0.04 per image (per generation)

---

## 🎓 Best Practices

### Brand Book PDFs:
✅ **DO**:
- Include pages with color swatches
- Show typography examples
- Include imagery guidelines
- Show logo variations
- Provide do's and don'ts

❌ **DON'T**:
- Upload massive files (>50MB)
- Use low-quality scans
- Include irrelevant pages
- Use password-protected PDFs

### Design Examples:
✅ **DO**:
- Use final, approved designs
- Include variety (social media, ads, web, print)
- Choose designs that represent your brand well
- Use high-resolution images

❌ **DON'T**:
- Upload drafts or work-in-progress
- Include off-brand experiments
- Use low-quality images
- Upload too many similar examples

---

## 🔐 Security & Privacy

### Data Storage:
- Brand books: Pages converted to images, stored temporarily
- Guidelines: Extracted text/rules stored in database (JSONB)
- Examples: Stored in Supabase Storage
- All data: Tied to your org_id, not shared

### API Usage:
- OpenAI API: Used for analysis (GPT-4 Vision, GPT-4)
- Data sent: PDF page images, design examples
- Data retained: Per OpenAI's data retention policy (30 days)

---

## 📞 Support

### Issues or Questions:
1. Check logs for specific errors
2. Review this documentation
3. Check [COMPLETE_BRAND_SYSTEM.md](COMPLETE_BRAND_SYSTEM.md) for details
4. See [QUICK_START.md](QUICK_START.md) for usage guide

### Common Resources:
- [Brand Intelligence](BRAND_INTELLIGENCE.md) - Deep analysis system
- [Complete System](COMPLETE_BRAND_SYSTEM.md) - Overview of all features
- [Quick Start](QUICK_START.md) - Usage instructions

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Dependencies installed (`pdf2image`, `PyPDF2`, `poppler`)
- [ ] Database table created (`brand_guidelines`)
- [ ] Streamlit app running
- [ ] Brand book uploaded successfully
- [ ] Design examples uploaded (optional)
- [ ] Basic brand kit created (optional)
- [ ] Test generation works
- [ ] Generated design matches brand
- [ ] Logs show brand guidelines being used

---

## 🎉 You're Ready!

Your complete brand intelligence system is now set up. The AI has:
- ✅ Your official brand guidelines (from brand book)
- ✅ Visual execution patterns (from examples)
- ✅ Learning capability (from usage)

**Start generating perfectly on-brand designs!** 🚀
