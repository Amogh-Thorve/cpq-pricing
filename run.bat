@echo off
title CPQ Platform Launcher
cd /d "%~dp0"
echo ============================================================
echo Starting CPQ Platform (Backend + Frontend)
echo ============================================================

:: 1. Run database migrations
echo [1/3] Running database migrations...
cd backend
set PYTHONPATH=..
python -m alembic upgrade head
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Database migrations failed. Please check your PostgreSQL connection.
    pause
    exit /b %ERRORLEVEL%
)
cd ..

:: 2. Start Backend API in a new window
echo [2/3] Starting backend API server...
start "CPQ Backend API" cmd /k "echo Starting Backend API... && python backend/run.py"

:: 3. Start Frontend App in a new window
echo [3/3] Starting frontend Next.js server...
start "CPQ Frontend App" cmd /k "echo Starting Frontend App... && cd frontend && npm run dev"

echo ============================================================
echo Startup commands dispatched!
echo - Backend API: http://localhost:8000/docs
echo - Frontend App: http://localhost:3000
echo ============================================================
pause
