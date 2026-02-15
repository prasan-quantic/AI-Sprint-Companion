@echo off
REM ============================================================================
REM AI Sprint Companion - MCP Agent Test Runner (Windows)
REM ============================================================================
REM This script runs the MCP Agent Tester to verify all MCP server tools
REM are working correctly.
REM ============================================================================

echo ============================================
echo   AI Sprint Companion MCP Agent Test
echo ============================================
echo.

REM Change to the script's directory
cd /d "%~dp0"

REM Clear Python environment variables that might cause issues
set "PYTHONHOME="
set "PYTHONPATH=%~dp0backend"

REM Check for virtual environment in project root (.venv)
if exist ".venv\Scripts\python.exe" (
    echo [INFO] Using virtual environment: .venv
    echo [INFO] Running MCP Agent Tests...
    echo.
    ".venv\Scripts\python.exe" -m app.mcp_agent_test
    goto :check_result
)

REM Check for virtual environment in backend\venv
if exist "backend\venv\Scripts\python.exe" (
    echo [INFO] Using virtual environment: backend\venv
    echo [INFO] Running MCP Agent Tests...
    echo.
    cd backend
    "venv\Scripts\python.exe" -m app.mcp_agent_test
    goto :check_result
)

REM Check for virtual environment in backend (Scripts directly)
if exist "backend\Scripts\python.exe" (
    echo [INFO] Using virtual environment: backend\Scripts
    echo [INFO] Running MCP Agent Tests...
    echo.
    cd backend
    "Scripts\python.exe" -m app.mcp_agent_test
    goto :check_result
)

REM Fallback to system Python
echo [INFO] No virtual environment found, using system Python
echo [INFO] Running MCP Agent Tests...
echo.
cd backend
python -m app.mcp_agent_test

:check_result
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] MCP Agent Tests failed with error code %ERRORLEVEL%
    echo.
    echo Possible solutions:
    echo   1. Make sure Python is installed and in PATH
    echo   2. Create a virtual environment: python -m venv .venv
    echo   3. Install dependencies: pip install -r backend\requirements.txt
    echo   4. Set AI_PROVIDER=mock for testing without API keys
) else (
    echo.
    echo [SUCCESS] All MCP Agent Tests passed!
)

:end
echo.
pause

