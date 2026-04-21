@echo off
REM Backend Setup Script for SokoYetu (Windows)
REM This script sets up the development environment with all dependencies

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║         SokoYetu Backend - Development Environment Setup       ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Check Python version
echo [1/6] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Found %PYTHON_VERSION%
echo.

REM Create virtual environment
echo [2/6] Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated
echo.

REM Install dependencies
echo [4/6] Installing Python dependencies...
cd backend
python -m pip install --upgrade pip setuptools wheel > nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    exit /b 1
)
echo ✅ Dependencies installed
echo.

REM Setup environment file
echo [5/6] Setting up environment configuration...
if not exist ".env" (
    copy .env.example .env
    echo ✅ Created .env from .env.example
    echo ⚠️  Please update .env with your credentials
) else (
    echo ✅ .env file already exists
)
echo.

REM Initialize database
echo [6/6] Initializing database...
python << EOF
from database import engine, Base
from models import *

Base.metadata.create_all(bind=engine)
print("✅ Database tables created!")
EOF
echo.

echo ╔════════════════════════════════════════════════════════════════╗
echo ✅ SETUP COMPLETE!
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo Next steps:
echo 1. Edit backend\.env with your M-Pesa, Email, and SMS credentials
echo 2. Run tests: pytest
echo 3. Start server: uvicorn main:app --reload
echo.
pause
