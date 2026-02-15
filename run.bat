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

REM Navigate to the script directory
cd /d "%~dp0"

REM Navigate to backend directory
cd backend

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Please create it first with: python -m venv venv
    echo Then install dependencies: venv\Scripts\pip.exe install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment and start server
echo [INFO] Starting AI Sprint Companion...
echo [INFO] Server will be available at: http://127.0.0.1:8000
echo [INFO] API Documentation at: http://127.0.0.1:8000/docs
echo [INFO] Press Ctrl+C to stop the server.
echo.

REM Start the application using venv Python
venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000

pause
