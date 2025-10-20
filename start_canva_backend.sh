#!/bin/bash

# Canva Backend Startup Script
# This script ensures ONLY ONE backend instance runs

echo "======================================"
echo "Canva Backend Startup Script"
echo "======================================"

# Kill all existing Canva backend processes
echo "1. Killing any existing backend processes..."
pkill -9 -f "canva-connect" 2>/dev/null
lsof -ti:3000,3001 | xargs kill -9 2>/dev/null
sleep 2

# Verify ports are clear
if lsof -ti:3000,3001 >/dev/null 2>&1; then
    echo "ERROR: Ports 3000 or 3001 are still in use!"
    echo "Please run: lsof -ti:3000,3001 | xargs kill -9"
    exit 1
fi

echo "✅ Ports 3000 and 3001 are clear"

# Start backend
echo "2. Starting Canva backend..."
cd canva-connect-api-starter-kit/demos/playground

echo "======================================"
echo "Backend is starting..."
echo "Frontend will be at: http://127.0.0.1:3000"
echo "Backend will be at: http://127.0.0.1:3001"
echo "======================================"
echo ""
echo "Press Ctrl+C to stop the backend"
echo ""

# Run npm start in foreground so you can see all logs
npm start
