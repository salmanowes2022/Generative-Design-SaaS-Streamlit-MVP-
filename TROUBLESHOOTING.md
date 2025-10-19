# Canva Integration - Troubleshooting Guide

## Solution to the 400 Error

### The Problem
You were getting a `400 - Client error` when trying to connect to Canva from Streamlit.

### Root Cause
Streamlit's page-based routing (`/Canva_Callback`) wasn't compatible with Canva's OAuth redirect requirements.

### The Fix
We now use a **bridge approach** that leverages the working backend server for OAuth:

1. **Backend Server** (port 3001) handles OAuth flow
2. **Streamlit** (port 8501) uses the backend's tokens
3. **No direct OAuth** in Streamlit - cleaner and more reliable!

---

## How to Use the Fixed Integration

### Step 1: Start Both Servers

**Terminal 1 - Backend Server:**
```bash
cd canva-connect-api-starter-kit/demos/playground
npm start
```

You should see:
```
Playground integration backend listening on port 3001
```

**Terminal 2 - Streamlit App:**
```bash
streamlit run app/streamlit_app.py
```

### Step 2: Connect to Canva

1. In Streamlit, go to any page with Canva integration (Generate v2 or Canva Templates)
2. In the sidebar, click "🔗 Connect to Canva"
3. Click the authorization link that appears
4. **Important:** Open it in a NEW TAB (right-click → "Open link in new tab")
5. Authorize the app in Canva
6. You'll be redirected to `http://127.0.0.1:3001/success`
7. Go back to Streamlit and click "🔄 Check Connection Status"
8. You should see "✅ Connected to Canva"

### Step 3: Generate Designs!

Now you can create designs using the Generate v2 page.

---

## Common Issues & Solutions

### Issue 1: "Backend server not responding"

**Error:** Connection refused when checking auth status

**Solution:**
```bash
# Make sure backend is running
cd canva-connect-api-starter-kit/demos/playground
npm start
```

### Issue 2: "No token available"

**Error:** Failed to get access token

**Solution:**
1. Click "Disconnect" in Streamlit (if shown)
2. Stop and restart the backend server
3. Click "Connect to Canva" again
4. Complete the full authorization flow

### Issue 3: Backend shows "invalid_scope" error

**Error:** OAuth redirect shows scope error

**Solution:**
This was already fixed! The scopes in the backend code now match what's enabled in your Canva app. If you still see this:

1. Check your Canva app has these scopes enabled:
   - asset:read
   - design:content:read
   - design:content:write
   - design:meta:read
   - profile:read

2. Make sure redirect URI in Canva app is: `http://127.0.0.1:3001/oauth/redirect`

### Issue 4: "Template not found"

**Error:** No template configured for ig_1x1

**Solution:**
1. Go to Canva Templates page in Streamlit
2. Browse your templates
3. In the "Configure" tab, add template mappings:
   - Channel: Instagram
   - Aspect Ratio: 1:1
   - Template ID: (paste from Canva)
4. Click "Save Mapping"

### Issue 5: Backend not starting

**Error:** `npm start` fails

**Solution:**
```bash
# Install dependencies
cd canva-connect-api-starter-kit/demos/playground
npm install

# Try again
npm start
```

---

## Architecture Overview

```
┌─────────────────────────────────────┐
│    Streamlit App (Port 8501)        │
│    - Generate v2 page                │
│    - Canva Templates page            │
└──────────────┬──────────────────────┘
               │
               │ Uses OAuth Bridge
               ▼
┌─────────────────────────────────────┐
│   Backend Server (Port 3001)        │
│   - Handles OAuth flow              │
│   - Stores tokens in database       │
│   - Provides token API               │
└──────────────┬──────────────────────┘
               │
               │ HTTPS
               ▼
┌─────────────────────────────────────┐
│         Canva Connect API            │
│         api.canva.com                │
└─────────────────────────────────────┘
```

### Key Files

**Bridge Implementation:**
- `app/core/canva_oauth_bridge.py` - Connects Streamlit to backend OAuth

**Backend OAuth (Already Working):**
- `canva-connect-api-starter-kit/demos/playground/backend/routes/auth.ts`
- `canva-connect-api-starter-kit/demos/common/backend/services/auth.ts`

**Updated Pages:**
- `app/pages/2_Generate_V2.py` - Uses bridge
- `app/pages/6_Canva_Templates.py` - Uses bridge

---

## Verifying Everything Works

### Test Checklist

1. **Backend Server Running:**
   ```bash
   curl http://127.0.0.1:3001/token
   ```
   Should return `Unauthorized` (that's correct - no token yet)

2. **Connect to Canva:**
   - Go to Streamlit
   - Click "Connect to Canva"
   - Complete authorization
   - Check "✅ Connected to Canva" appears

3. **Get Token:**
   ```bash
   curl http://127.0.0.1:3001/token
   ```
   Should return an access token (long string)

4. **Create Design:**
   - Go to Generate v2 page
   - Create a design plan
   - Click "Create Design in Canva"
   - Should see design created successfully

---

## Quick Reference

### Backend Server
- **URL:** http://127.0.0.1:3001
- **OAuth Endpoints:**
  - `/authorize` - Start OAuth flow
  - `/oauth/redirect` - OAuth callback
  - `/token` - Get access token
  - `/isauthorized` - Check auth status
  - `/revoke` - Disconnect

### Streamlit App
- **URL:** http://localhost:8501
- **Pages:**
  - Generate v2 - Create designs
  - Canva Templates - Manage templates

### Environment Variables
```env
CANVA_CLIENT_ID=OC-AZn3Gq75zGyH
CANVA_CLIENT_SECRET=cnvcaYUxTdyVMecu6ui8wZf8BL6ywsowyz72nH-OcR2N6Q4U0cd1a6b3
CANVA_REDIRECT_URI=http://127.0.0.1:3001/oauth/redirect
```

---

## Still Having Issues?

1. **Check both servers are running:**
   - Backend on port 3001
   - Streamlit on port 8501

2. **Check browser console** for errors (F12 → Console tab)

3. **Check logs:**
   - Backend: In the terminal where `npm start` is running
   - Streamlit: In the terminal where `streamlit run` is running

4. **Try a fresh start:**
   ```bash
   # Stop both servers (Ctrl+C)

   # Clear cookies in browser

   # Restart backend
   cd canva-connect-api-starter-kit/demos/playground
   npm start

   # Restart Streamlit (new terminal)
   streamlit run app/streamlit_app.py
   ```

---

**The integration now works perfectly with this bridge approach!** 🎉
