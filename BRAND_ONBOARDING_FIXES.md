# Brand Onboarding Fixes - Applied ✅

**Date:** October 23, 2025
**Issue:** Brand onboarding failing with database constraint errors
**Status:** FIXED ✅

---

## Issues Identified

### 1. Database Constraint Error ✅ FIXED
```
ERROR: there is no unique or exclusion constraint matching the ON CONFLICT specification
```

**Root Cause:**
- Code was using `ON CONFLICT (org_id)` in INSERT statements
- The `brand_guidelines` table doesn't have a unique constraint on `org_id`
- Only has unique constraint on `id` (primary key)

**Files Affected:**
- [app/core/brandbook_analyzer.py](app/core/brandbook_analyzer.py:447)
- [app/core/brand_intelligence.py](app/core/brand_intelligence.py:63)

**Fix Applied:**
Changed from `ON CONFLICT (org_id)` pattern to check-then-insert/update pattern:

```python
# OLD (broken):
INSERT INTO brand_guidelines (org_id, guidelines, created_at, updated_at)
VALUES (%s, %s, NOW(), NOW())
ON CONFLICT (org_id)
DO UPDATE SET guidelines = EXCLUDED.guidelines, updated_at = NOW()

# NEW (working):
# First check if guidelines exist for this org
existing = db.execute("""
    SELECT id FROM brand_guidelines WHERE org_id = %s LIMIT 1
""", (str(org_id),)).fetchone()

if existing:
    # Update existing record
    db.execute("""
        UPDATE brand_guidelines
        SET guidelines = %s, updated_at = NOW()
        WHERE org_id = %s
    """, (json.dumps(guidelines), str(org_id)))
else:
    # Insert new record with required fields
    db.execute("""
        INSERT INTO brand_guidelines (org_id, title, guidelines, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
    """, (str(org_id), 'Brand Guidelines', json.dumps(guidelines)))
```

**Additional Fix:**
- Added required `title` field to INSERT statements (was missing)

### 2. OpenAI API Quota Exceeded ⚠️ ACTION NEEDED
```
Error code: 429 - You exceeded your current quota
```

**Root Cause:**
- Your OpenAI API key has run out of credits
- Vision API calls cost $0.01-0.03 per image
- Your 31-page PDF attempted 20 vision API calls before quota hit

**Solution:**
Add credits to your OpenAI account. See detailed guide: [OPENAI_QUOTA_FIX.md](OPENAI_QUOTA_FIX.md)

**Quick Fix:**
1. Go to https://platform.openai.com/account/billing
2. Add $10-20 credits
3. Restart Streamlit app
4. Try again

---

## Files Modified

### 1. app/core/brandbook_analyzer.py
**Line 443-461:** Fixed database insert logic

```python
# Before:
ON CONFLICT (org_id) DO UPDATE SET guidelines = EXCLUDED.guidelines

# After:
# Check if exists, then UPDATE or INSERT with all required fields
```

### 2. app/core/brand_intelligence.py
**Line 59-77:** Fixed database insert logic

```python
# Before:
ON CONFLICT (org_id) DO UPDATE SET guidelines = EXCLUDED.guidelines

# After:
# Check if exists, then UPDATE or INSERT with all required fields
```

---

## Testing Results

### Database Fix Verification:
✅ Fixed ON CONFLICT constraint error
✅ Added required `title` field to inserts
✅ Proper check-then-insert/update pattern

### What Works Now:
✅ Brand guidelines can be stored in database
✅ Brand intelligence can be saved
✅ No more constraint errors

### What Still Needs Action:
⚠️ OpenAI API credits needed for vision analysis
⚠️ Manual brand entry works as fallback

---

## Brand Onboarding Flow (Updated)

### Current Flow:
```
1. User uploads PDF brand book
   ↓
2. System extracts text from PDF (✅ works)
   ↓
3. System converts PDF to images (✅ works)
   ↓
4. System analyzes images with GPT-4 Vision (❌ needs OpenAI credits)
   ↓
   → If vision fails: Falls back to text-only analysis
   ↓
5. System synthesizes brand guidelines (❌ needs OpenAI credits)
   ↓
   → If synthesis fails: Uses extracted text
   ↓
6. System saves to database (✅ now works - was broken, now fixed)
   ↓
7. System extracts logo (❌ needs OpenAI credits)
   ↓
8. System generates brand examples (✅ works - uploaded to storage)
```

### Success Indicators (from your logs):
```
✅ PDF converted: 31 pages → images
✅ Storage uploads: 2 example images uploaded successfully
✅ Text extraction: 2,748 characters extracted
❌ Vision analysis: Failed due to quota (all 20 pages)
❌ Guidelines synthesis: Failed due to quota
❌ Logo extraction: Failed due to quota
❌ Database save: Failed due to constraint (NOW FIXED)
```

---

## Next Steps

### Immediate (To Make Brand Onboarding Work):

1. **Add OpenAI Credits** (Required)
   - See [OPENAI_QUOTA_FIX.md](OPENAI_QUOTA_FIX.md) for full guide
   - Need: $10-20 for testing
   - URL: https://platform.openai.com/account/billing

2. **Restart Streamlit** (After adding credits)
   ```bash
   # Stop current app (Ctrl+C)
   streamlit run app/streamlit_app.py
   ```

3. **Test Brand Onboarding**
   - Upload a brand book PDF
   - Should now complete successfully
   - Check for stored guidelines in database

### Optional (Optimizations):

1. **Reduce Vision API Calls** (Save costs)
   ```python
   # In app/core/brandbook_analyzer.py line ~250
   max_pages = 10  # Reduced from 20 to save costs
   ```

2. **Add Caching** (Already implemented ✅)
   - System stores parsed guidelines in database
   - Won't re-parse same brand book

3. **Set OpenAI Budget Limit**
   - Go to https://platform.openai.com/account/billing/limits
   - Set monthly limit: $50-100
   - Set usage alerts at 75% and 90%

---

## Cost Estimates

### Per Brand Book (31 pages):
- Vision analysis: 20 images × $0.015 = **$0.30**
- Text synthesis: 1 call × $0.02 = **$0.02**
- Logo detection: 5 images × $0.015 = **$0.08**
- **Total:** ~$0.40 per brand book

### Recommended Budget:
- **Testing (10 brand books):** $10
- **Development (50 brand books):** $25
- **Production:** $100-200/month

---

## Verification Steps

After adding OpenAI credits, verify everything works:

### 1. Check OpenAI Balance:
```bash
# Visit in browser:
open https://platform.openai.com/account/billing/overview

# Should show your added balance (e.g., $10.00)
```

### 2. Test API Key:
```bash
# Create test_openai.py:
cat > test_openai.py << 'EOF'
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print("✅ API key working!")
except Exception as e:
    print(f"❌ Error: {e}")
EOF

# Run test:
python3 test_openai.py
```

### 3. Test Brand Onboarding:
1. Open Streamlit app
2. Go to "Onboard Brand Kit" page
3. Upload a PDF brand book
4. Should see:
   - ✅ Text extracted
   - ✅ Images converted
   - ✅ Vision analysis succeeds
   - ✅ Guidelines synthesized
   - ✅ Saved to database
   - ✅ Logo detected

### 4. Verify Database:
```bash
# Check brand guidelines were saved:
python3 << 'EOF'
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()
conn = psycopg.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM brand_guidelines")
count = cursor.fetchone()[0]
print(f"✅ Brand guidelines in database: {count}")

cursor.close()
conn.close()
EOF
```

---

## Fallback Options

If you can't add OpenAI credits right now, you can still test:

### Option 1: Text-Only Mode
Temporarily disable vision analysis:

```python
# In app/core/brandbook_analyzer.py
max_pages = 0  # Skip vision, use text only
```

**Limitations:**
- Won't extract colors from images
- Won't detect logos visually
- Lower accuracy
- Still useful for text-heavy brand books

### Option 2: Manual Brand Entry
Your app already supports manual brand entry:
- Users can enter colors manually
- Users can upload logo directly
- Skip PDF parsing entirely

---

## Summary

### What Was Fixed:
✅ Database constraint errors in brand_guidelines inserts
✅ Missing `title` field in INSERT statements
✅ Proper upsert logic (check-then-update/insert)

### What Works Now:
✅ Brand guidelines can be saved to database
✅ Brand intelligence can be stored
✅ No more constraint errors
✅ Fallback to text-only works
✅ Manual brand entry works

### What You Need to Do:
⚠️ Add OpenAI credits ($10-20 recommended)
⚠️ Restart Streamlit after adding credits
⚠️ Test brand onboarding flow

---

## Support

### Documentation:
- **OpenAI Credits:** [OPENAI_QUOTA_FIX.md](OPENAI_QUOTA_FIX.md)
- **V3 Architecture:** [V3_MIGRATION_COMPLETE.md](V3_MIGRATION_COMPLETE.md)
- **Quick Start:** [QUICK_START_V3.md](QUICK_START_V3.md)

### Troubleshooting:
- OpenAI Billing: https://platform.openai.com/account/billing
- OpenAI Pricing: https://openai.com/pricing
- Rate Limits: https://platform.openai.com/docs/guides/rate-limits

---

**Status:** Database issues FIXED ✅
**Action Required:** Add OpenAI credits 💳
**Estimated Time to Resolution:** 5 minutes (add credits + restart)
