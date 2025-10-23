# OpenAI API Quota Issue - Fix Guide

## Problem

You're seeing this error:
```
Error code: 429 - You exceeded your current quota, please check your plan and billing details.
```

This means your OpenAI API key has run out of credits or hit rate limits.

---

## Solution Options

### Option 1: Add Credits to Your OpenAI Account (Recommended)

1. **Go to OpenAI Platform:**
   - Visit: https://platform.openai.com/account/billing

2. **Check Your Balance:**
   - Look at "Current balance" in the billing overview
   - If it shows $0.00, you need to add credits

3. **Add Credits:**
   - Click "Add payment method" if you haven't already
   - Click "Add to credit balance"
   - Add at least $10-20 for testing (brand parsing uses GPT-4 Vision which costs more)

4. **Verify:**
   - Wait 1-2 minutes for credits to appear
   - Check your balance shows the added amount

### Option 2: Use a Different API Key

If you have another OpenAI account with credits:

1. **Get New API Key:**
   - Visit: https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy the key (starts with `sk-`)

2. **Update .env File:**
   ```bash
   # Open your .env file
   nano .env

   # Update this line:
   OPENAI_API_KEY=sk-your-new-key-here

   # Save and exit (Ctrl+X, then Y, then Enter)
   ```

3. **Restart Streamlit:**
   ```bash
   # Stop the current Streamlit app (Ctrl+C)
   # Start it again
   streamlit run app/streamlit_app.py
   ```

### Option 3: Upgrade to Paid Plan

If you're on a free trial that expired:

1. **Visit Billing Settings:**
   - https://platform.openai.com/account/billing/overview

2. **Set Up Paid Plan:**
   - Add payment method
   - Set usage limits (recommended: $50-100/month for development)

3. **Enable Auto-recharge (Optional):**
   - Set threshold (e.g., when balance < $10)
   - Auto-add amount (e.g., $20)

---

## Cost Estimates

Here's what your brand parsing operations cost:

### Current Usage (From Logs):
- **PDF Pages:** 31 pages
- **Vision API Calls:** 20 pages analyzed (before quota hit)
- **Cost per Vision Call:** ~$0.01-0.03 per image
- **Estimated Cost:** $0.20-0.60 per brand book

### Recommended Budget:
- **Light Testing (5-10 brand books):** $10
- **Development (50 brand books):** $50
- **Production (unlimited):** $100-200/month

### Cost Breakdown:
```
GPT-4 Vision (brand parsing):     $0.01-0.03 per image
GPT-4 Turbo (chat, design):       $0.01-0.03 per request
DALL-E 3 (image generation):      $0.040-0.080 per image
Total per design cycle:           $0.10-0.30
```

---

## Temporary Workaround: Skip Vision Analysis

If you need to test immediately without credits, you can temporarily disable vision analysis:

### Edit brandbook_analyzer.py:

```python
# Line ~250 in app/core/brandbook_analyzer.py
# Change this:
max_pages = 20  # Analyze first 20 pages

# To this:
max_pages = 0  # Skip vision analysis, use text-only
```

**Limitations of text-only:**
- Won't extract colors from images
- Won't detect logos visually
- Lower accuracy for brand guidelines
- Still useful for text-based brand books

---

## Checking Your Current Status

### 1. Check OpenAI Account Status:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | grep error
```

If you see an error about quota, you need to add credits.

### 2. Check Your Balance Programmatically:

Create a test script:
```python
#!/usr/bin/env python3
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

try:
    # Test with a minimal request
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print("✅ API key is working!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error: {e}")
```

Run it:
```bash
python3 test_openai.py
```

---

## Rate Limits vs Quota Limits

**Two types of 429 errors:**

### Rate Limit (too many requests per minute):
```
Error: Rate limit exceeded
```
**Solution:** Wait 60 seconds and retry. The app has automatic retry logic.

### Quota Limit (no credits):
```
Error: You exceeded your current quota
```
**Solution:** Add credits to your account (see Option 1 above).

Your error is **Quota Limit** - you need to add credits.

---

## After Adding Credits

Once you've added credits:

1. **Wait 1-2 minutes** for the credits to appear in your account

2. **Verify balance:**
   - https://platform.openai.com/account/billing/overview
   - Should show your added amount

3. **Restart Streamlit:**
   ```bash
   # Stop current app (Ctrl+C in terminal)
   streamlit run app/streamlit_app.py
   ```

4. **Try brand onboarding again:**
   - Upload your PDF brand book
   - It should now process successfully

---

## Monitoring Usage

### Set Up Usage Alerts:

1. **Go to Billing Settings:**
   - https://platform.openai.com/account/billing/limits

2. **Set Hard Limit:**
   - Recommended: $50-100 for development
   - This prevents unexpected charges

3. **Set Email Alerts:**
   - Get notified at 75% and 90% of limit
   - Gives you time to add more credits

### Check Usage:
```bash
# View usage in OpenAI dashboard
open https://platform.openai.com/account/usage
```

---

## Production Recommendations

For production use:

1. **Use Caching:**
   - Store parsed brand guidelines in database
   - Only re-parse when brand book changes
   - Your system already does this! ✅

2. **Optimize API Calls:**
   - Reduce `max_pages` from 20 to 10 for faster brands
   - Use text-only for simple brand books
   - Only use vision for complex brand books

3. **Set Monthly Budget:**
   - Start with $100/month
   - Monitor usage in first month
   - Adjust based on actual usage

4. **Use Fallbacks:**
   - Your system already falls back to text-only if vision fails ✅
   - Consider manual brand entry for users without PDFs

---

## Next Steps

**Right now, you should:**

1. ✅ Add $10-20 credits to your OpenAI account
2. ✅ Verify balance appears in billing dashboard
3. ✅ Restart Streamlit app
4. ✅ Try uploading brand book again

**The database constraint error has been fixed**, so once you add OpenAI credits, brand onboarding should work perfectly!

---

## Questions?

- **OpenAI Billing:** https://platform.openai.com/account/billing
- **OpenAI Pricing:** https://openai.com/pricing
- **API Usage Docs:** https://platform.openai.com/docs/guides/rate-limits

---

**Status:** Database fixes applied ✅
**Action Needed:** Add OpenAI credits 💳
