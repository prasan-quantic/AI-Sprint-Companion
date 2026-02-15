@echo off
echo ============================================
echo   Bootstrap Trello Board for AI Sprint Companion
echo ============================================
echo.

REM Set your Trello API credentials here
REM Get your API key from: https://trello.com/app-key
REM Generate token from the same page by clicking "Generate a Token"
set TRELLO_KEY=20db82f915c1115f6593ab49d43016f4
set TRELLO_TOKEN=ATTAb304644439b12189d40236f0de0ef07c63d3227267e14d3f3009080f67fb945d9371A785

REM Optional: Set a custom board name (default: "AI Sprint Companion")
REM set TRELLO_BOARD_NAME=My Custom Board Name

echo [INFO] Running Trello Bootstrap Script...
echo.

"C:\Users\vijet\IdeaProjects\Capstone AI Project\backend\venv\Scripts\python.exe" "C:\Users\vijet\IdeaProjects\Capstone AI Project\tools\bootstrap_trello.py"

echo.
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Script failed with error code %ERRORLEVEL%
) else (
    echo [SUCCESS] Script completed successfully!
)

echo.
pause

