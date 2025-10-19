# Quick Start Guide - Canva Integration

Get your Canva integration up and running in 5 minutes!

## Step 1: Canva App Setup (2 minutes)

1. Go to https://www.canva.com/developers/apps
2. Click **"Create an app"**
3. Fill in app details:
   - **App name:** Your App Name
   - **Description:** AI-powered design generation
4. In **Scopes**, enable:
   - ✅ asset:read
   - ✅ design:content:read
   - ✅ design:content:write
   - ✅ design:meta:read
   - ✅ profile:read
5. In **Redirect URIs**, add:
   ```
   http://localhost:8501/Canva_Callback
   ```
6. Save and copy your **Client ID** and **Client Secret**

## Step 2: Configure Environment (1 minute)

Update your `.env` file:

```env
CANVA_CLIENT_ID=OC-AZn3Gq75zGyH
CANVA_CLIENT_SECRET=your_actual_secret_here
CANVA_REDIRECT_URI=http://localhost:8501/Canva_Callback
CANVA_API_BASE=https://api.canva.com/rest/v1
```

## Step 3: Run Database Migration (30 seconds)

```bash
python run_migration.py
```

You should see:
```
✅ Migration completed successfully!
Created table: canva_tokens
```

## Step 4: Start the App (30 seconds)

```bash
streamlit run app/streamlit_app.py
```

## Step 5: Connect & Test (1 minute)

### Connect Canva

1. In the Streamlit app, go to **Canva Templates** page
2. Click **"🔗 Connect to Canva"** in the sidebar
3. Authorize the app in the popup
4. See success message ✅

### Test Design Generation

1. Go to **Generate v2** page
2. Verify "✅ Connected to Canva" in sidebar
3. Chat: *"Create an Instagram post for our new product launch"*
4. Review the generated plan
5. Click **"🚀 Create Design in Canva"**
6. Wait 30-60 seconds for:
   - AI background generation ✓
   - Canva design creation ✓
   - Brand validation ✓
7. Download your design!

## Common Issues

### "Canva not connected"
→ Go to Canva Templates page and click "Connect to Canva"

### "No template for ig_1x1"
→ Go to Canva Templates → Configure tab → Add template mapping

### "Invalid scope" error
→ Check that all 5 scopes are enabled in your Canva app

## Next Steps

1. **Create Brand Templates in Canva**
   - Open Canva
   - Create a design with placeholders: HEADLINE, SUBHEAD, CTA_TEXT, BG_IMAGE
   - Save as Brand Template

2. **Map Templates to Channels**
   - Go to Canva Templates page → Configure tab
   - Add mappings for Instagram, Facebook, LinkedIn, Twitter

3. **Generate Your First Design**
   - Use Generate v2 page
   - Try different channels and styles
   - Download and share!

## Need Help?

- 📖 Full docs: [CANVA_INTEGRATION.md](./CANVA_INTEGRATION.md)
- 🐛 Issues: Check logs in `app/logs/`
- 💬 Community: Canva Developers Forum

---

**You're all set!** Start generating brand-consistent designs automatically. 🎨
