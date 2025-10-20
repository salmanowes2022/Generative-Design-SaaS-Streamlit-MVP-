# Final Steps to Complete Canva OAuth

## What I've Fixed

### 1. ✅ Updated Client Secret
- File: `canva-connect-api-starter-kit/demos/playground/.env`
- New secret: `cnvca-pLM0GaMYHjzyU0b94jBhzGePYrZ_eQ_Cw8fIKNknkAf2c2c137`
- This fixes the `{"code":"invalid_client","message":"Client secret is invalid"}` error

### 2. ✅ Fixed UUID Error in Streamlit
- File: `app/pages/2_Generate_V2.py` line 30
- Changed from: `st.session_state.user_id = "default_user"` (invalid)
- Changed to: `st.session_state.user_id = "00000000-0000-0000-0000-000000000011"` (valid UUID)
- This fixes the `InvalidTextRepresentation: invalid input syntax for type uuid: "default_user"` error

## What You Need to Do Now

### Step 1: Restart the Canva Backend

The backend needs to be restarted so it loads the new client secret from the `.env` file.

**In the terminal where you ran `npm start`:**

1. Press `Ctrl+C` to stop the backend
2. Wait 2 seconds
3. Run:
   ```bash
   cd /Users/salmanawaisa/Desktop/Generative-Design-SaaS-Streamlit-MVP-/canva-connect-api-starter-kit/demos/playground
   npm start
   ```

4. Wait for this output:
   ```
   Playground integration backend listening on port 3001
   ```

5. **Keep that terminal window open!**

### Step 2: Reload Your Streamlit App

Since I fixed the UUID error, you need to reload Streamlit to clear the old session state:

1. In your browser, press `Cmd+R` or `Ctrl+R` to reload the Streamlit app
2. This will clear the old `"default_user"` value and load the correct UUID

### Step 3: Test OAuth Flow

Now try the full OAuth flow:

1. Click **"Connect to Canva"** in the Streamlit sidebar
2. You'll be redirected to Canva's authorization page
3. Click **"Connect"** on Canva
4. You should see: **"Successfully authorized! This window will close automatically in 2 seconds."**
5. Return to Streamlit - connection status should show **"Connected to Canva"**

### Step 4: Monitor Backend Logs

In the terminal where the backend is running, you should see:

```
GET: /authorize
GET: /oauth/redirect?code=eyJ...
[DEBUG] OAuth callback received: { authorizationCode: '...', state: '...' }
Response status 200   ← SUCCESS! (not "invalid_client" error anymore)
GET: /success
```

## Success Criteria

✅ Backend shows: `Response status 200` (token exchange success)
✅ No more `"invalid_client"` errors
✅ No more UUID validation errors in Streamlit
✅ Canva connection status shows "Connected"
✅ You can proceed to generate designs!

## If Issues Persist

### Still Getting "Cannot GET /oauth/redirect"?

Those zombie bash processes might still be interfering. Run:
```bash
lsof -ti:3000,3001 | xargs kill -9 2>/dev/null
killall -9 node npm 2>/dev/null
```

Then start the backend again.

### Still Getting UUID Errors?

Clear your browser cache or try in an incognito/private window to ensure fresh session state.

---

**Everything is now fixed! Just restart the backend and test the OAuth flow.**
