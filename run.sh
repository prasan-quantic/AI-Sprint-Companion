#!/bin/bash
# ============================================
# AI Sprint Companion - Local Run Script
# For Linux/macOS
# ============================================

set -e

echo ""
echo "========================================"
echo "  AI Sprint Companion - Local Runner"
echo "========================================"
echo ""

# Navigate to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH."
    echo "Please install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "[INFO] Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "[INFO] Installing dependencies..."
pip install fastapi uvicorn python-multipart jinja2 aiofiles pydantic-settings httpx openai python-docx PyPDF2

echo ""
echo "[INFO] Starting AI Sprint Companion..."
echo "[INFO] Server will be available at: http://127.0.0.1:8000"
echo "[INFO] API Documentation at: http://127.0.0.1:8000/docs"
echo "[INFO] Press Ctrl+C to stop the server."
echo ""

# Start the application
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
@echo off
REM ============================================
REM AI Sprint Companion - Local Run Script
REM For Windows
REM ============================================

echo.
echo ========================================
echo   AI Sprint Companion - Local Runner
echo ========================================
echo.

REM Check if Python is available
where py >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Navigate to backend directory
cd /d "%~dp0backend"

REM Check if virtual environment exists, create if not
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    py -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade pip
echo [INFO] Upgrading pip...
py -m pip install --upgrade pip >nul 2>nul

REM Install dependencies
echo [INFO] Installing dependencies...
py -m pip install fastapi uvicorn python-multipart jinja2 aiofiles pydantic-settings httpx openai python-docx PyPDF2

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [INFO] Starting AI Sprint Companion...
echo [INFO] Server will be available at: http://127.0.0.1:8000
echo [INFO] API Documentation at: http://127.0.0.1:8000/docs
echo [INFO] Press Ctrl+C to stop the server.
echo.

REM Start the application
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

pause

