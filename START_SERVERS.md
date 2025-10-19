# Quick Start Guide - Running Both Servers

## Backend Server is Already Running! ✅

The Canva OAuth backend is running in the background:
- **Backend API:** http://127.0.0.1:3001
- **Frontend:** http://127.0.0.1:3000

**Logs location:** `/tmp/canva-backend.log`

---

## Start Streamlit App

In your terminal, run:

```bash
streamlit run app/streamlit_app.py
```

This will start Streamlit on port 8501.

---

## Connect to Canva

1. Open Streamlit in your browser (usually http://localhost:8501)
2. Go to any page with Canva integration (Generate V2 or Canva Templates)
3. In the sidebar, look for "🔗 Canva"
4. Click "Connect to Canva"
5. A popup will open - authorize the app
6. After authorization, click "🔄 Check Status"
7. You should see "✅ Connected to Canva"

---

## If Backend Stops

Check if it's running:
```bash
curl http://127.0.0.1:3001/token
```

If you get "Connection refused", restart it:
```bash
cd canva-connect-api-starter-kit/demos/playground
nohup npm start > /tmp/canva-backend.log 2>&1 &
```

Check logs:
```bash
tail -f /tmp/canva-backend.log
```

---

## Stop Everything

Kill backend:
```bash
lsof -ti:3001 | xargs kill
```

Kill Streamlit:
```bash
# Press Ctrl+C in the terminal where streamlit is running
```

---

## Common Issues

### "Canva not connected" in Streamlit

1. Make sure backend is running: `curl http://127.0.0.1:3001/token`
2. Check Canva app settings have correct redirect URI: `http://127.0.0.1:3001/oauth/redirect`
3. Set "Return navigation" in Canva app to: `http://127.0.0.1:3000`
4. Try authorizing again

### Backend won't start (port in use)

```bash
lsof -ti:3000,3001 | xargs kill -9
cd canva-connect-api-starter-kit/demos/playground
npm start
```

---

**You're all set!** The backend is running, just start Streamlit and connect to Canva.
