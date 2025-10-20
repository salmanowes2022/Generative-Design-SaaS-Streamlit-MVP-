# START CANVA BACKEND - MANUAL INSTRUCTIONS

## The Problem
There are zombie background processes that keep restarting and stealing ports 3000/3001.
You need to manually start the backend in a new terminal window that I cannot control.

## Step-by-Step Instructions

### 1. Open a NEW Terminal Window
- Press `Cmd + Space` and type "Terminal"
- OR use iTerm2 if you have it
- This MUST be a new terminal window, not this one

### 2. Navigate to the Backend Directory
```bash
cd /Users/salmanawaisa/Desktop/Generative-Design-SaaS-Streamlit-MVP-/canva-connect-api-starter-kit/demos/playground
```

### 3. Kill Any Existing Processes (Just in Case)
```bash
lsof -ti:3000,3001 | xargs kill -9 2>/dev/null
killall -9 node npm 2>/dev/null
```

Wait 3 seconds, then verify ports are clear:
```bash
lsof -ti:3000,3001
```
Should return nothing (empty output).

### 4. Start the Backend
```bash
npm start
```

You should see output like:
```
┌────────────────────────────┬───────────────────────┐
│ Development URL (Frontend) │ http://127.0.0.1:3000 │
├────────────────────────────┼───────────────────────┤
│ Base URL (Backend)         │ http://127.0.0.1:3001 │
└────────────────────────────┴───────────────────────┘

Playground integration backend listening on port 3001
```

### 5. Leave This Terminal Window Open
**DO NOT CLOSE IT!** The backend needs to keep running.

All logs will appear in this window, which will help us debug any OAuth issues.

### 6. Test the Backend is Working

Open a NEW terminal (keep the backend running) and run:
```bash
curl -I http://127.0.0.1:3001/oauth/redirect 2>&1 | grep HTTP
```

You should see:
```
HTTP/1.1 302 Found
```

If you see "Cannot GET", the backend is not running correctly.

### 7. Try OAuth Flow in Streamlit

Now go back to your Streamlit app and click "Connect to Canva".

You should see logs appearing in the backend terminal window showing:
- `GET: /authorize`
- `GET: /oauth/redirect?code=...`
- `Response status 200` (token exchange)
- `GET: /success`

## If It Still Doesn't Work

If you still get "Cannot GET /oauth/redirect" error:

1. In the terminal where backend is running, press `Ctrl+C` to stop it
2. Run: `lsof -ti:3000,3001 | xargs kill -9 2>/dev/null`
3. Wait 5 seconds
4. Run: `npm start` again
5. Try OAuth flow again

## Success Criteria

✅ Backend terminal shows: "Playground integration backend listening on port 3001"
✅ Curl test returns: "HTTP/1.1 302 Found"
✅ Clicking "Connect to Canva" redirects to Canva (not "Cannot GET")
✅ After authorizing on Canva, you see "Success" page
✅ Streamlit shows "Connected to Canva"

---

**Please start the backend manually following these instructions and let me know what happens!**
