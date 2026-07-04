@echo off
title DrainGuard AI Platform Launcher
echo ===================================================
echo             DRAINGUARD AI LAUNCH SYSTEM
echo ===================================================
echo.
echo [+] Starting unified Python FastAPI server...
echo     This will host both the API and the React Dashboard!
echo.
start cmd.exe /k "title DrainGuard API Server && echo Starting Unified Server... && python run_backend.py"

echo [+] [Developer mode] Launching React Vite Dev Server (Hot-Reload)...
start cmd.exe /k "title DrainGuard Dev Server && echo Starting React Dev Server... && cd frontend && npm run dev"

echo.
echo ===================================================
echo [!] Unified platform launch initiated!
echo.
echo - Main Application:   http://localhost:8000
echo - Swagger API Docs:   http://localhost:8000/docs
echo.
echo - Dev App (Hot-Reload): http://localhost:5173
echo ===================================================
echo.
pause
