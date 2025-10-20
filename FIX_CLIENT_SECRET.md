# Fix Client Secret Error

## Current Error
```
{"code":"invalid_client","message":"Client secret is invalid for OC-AZn3Gq75zGyH"}
```

## The Problem
The `CANVA_CLIENT_SECRET` in your `.env` file doesn't match the actual secret in your Canva app settings.

**Current Client ID:** `OC-AZn3Gq75zGyH`
**Current Client Secret (in .env):** `cnvcaYUxTdyVMecu6ui8wZf8BL6ywsowyz72nH-OcR2N6Q4U0cd1a6b3`

## How to Fix

### Step 1: Get the Correct Client Secret from Canva

1. Go to your Canva Developer Portal: https://www.canva.com/developers/apps
2. Click on your app (the one with Client ID: `OC-AZn3Gq75zGyH`)
3. Go to the **"Authentication"** tab
4. Find **"Client secret"** section
5. If you don't see the secret (it's hidden), you'll need to generate a new one:
   - Click **"Generate new secret"** or **"Regenerate secret"**
   - **COPY THE NEW SECRET IMMEDIATELY** - you won't be able to see it again!

### Step 2: Update the .env File

Edit this file:
```
/Users/salmanawaisa/Desktop/Generative-Design-SaaS-Streamlit-MVP-/canva-connect-api-starter-kit/demos/playground/.env
```

Replace line 14 with your new client secret:
```bash
CANVA_CLIENT_SECRET=YOUR_NEW_SECRET_HERE
```

### Step 3: Restart the Backend

In the terminal where you started `npm start`:

1. Press `Ctrl+C` to stop the backend
2. Wait 2 seconds
3. Run `npm start` again

### Step 4: Try OAuth Flow Again

Now go back to Streamlit and click "Connect to Canva" again.

## Alternative: Use Existing Secret

If you have the correct client secret saved somewhere else (like a password manager or notes), you can use that instead of regenerating.

Just make sure you update line 14 in the `.env` file with the correct secret.

## After Updating

You should see in the backend logs:
```
GET: /oauth/redirect?code=...
Response status 200 on https://api.canva.com/rest/v1/oauth/token
GET: /success
```

Instead of the "invalid_client" error.

---

**Please get the correct client secret from Canva and update the .env file, then restart the backend.**
