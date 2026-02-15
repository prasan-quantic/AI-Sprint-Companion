@echo off
REM ============================================================================
REM AI Sprint Companion - MCP Server Launcher (Windows)
REM ============================================================================
REM This script starts the MCP (Model Context Protocol) server for AI agents
REM to connect to and use the Sprint Companion tools.
REM ============================================================================

echo ============================================
echo   AI Sprint Companion MCP Server
echo ============================================
echo.

REM Change to the script's directory
cd /d "%~dp0"

REM Change to backend directory
cd backend

REM Check if virtual environment exists in backend\venv
if exist "venv\Scripts\python.exe" (
    echo [INFO] Using virtual environment: backend\venv
    echo [INFO] Starting MCP Server...
    echo.

    REM Set PYTHONHOME and PYTHONPATH to fix "Could not find platform independent libraries" error
    set "PYTHONHOME="
    set "PYTHONPATH=%~dp0backend"

    REM Activate the virtual environment and run the server
    call venv\Scripts\activate.bat
    python -m app.mcp_server
    goto :end
)

REM Check if virtual environment exists in backend\Scripts (alternative location)
if exist "Scripts\python.exe" (
    echo [INFO] Using virtual environment: backend\Scripts
    echo [INFO] Starting MCP Server...
    echo.

    REM Set PYTHONHOME and PYTHONPATH to fix path issues
    set "PYTHONHOME="
    set "PYTHONPATH=%~dp0backend"

    call Scripts\activate.bat
    python -m app.mcp_server
    goto :end
)

REM Fallback to system Python
echo [INFO] No virtual environment found, using system Python...
echo [INFO] Starting MCP Server...
echo.
set "PYTHONPATH=%~dp0backend"
python -m app.mcp_server

:end
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] MCP Server exited with error code %ERRORLEVEL%
    echo.
    echo Possible solutions:
    echo   1. Make sure Python is installed and in PATH
    echo   2. Create a virtual environment: python -m venv venv
    echo   3. Install dependencies: pip install -r requirements.txt
    echo   4. Install MCP SDK: pip install mcp
    echo.
    pause
)
