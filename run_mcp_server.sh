#!/bin/bash
# Run the AI Sprint Companion MCP Server
# This script starts the MCP server for AI agents to connect to

echo "Starting AI Sprint Companion MCP Server..."
echo

cd "$(dirname "$0")"
cd backend

# Check if virtual environment exists
if [ -f "bin/python" ]; then
    echo "Using local virtual environment..."
    bin/python -m app.mcp_server
else
    echo "Using system Python..."
    python -m app.mcp_server
fi
@echo off
REM Run the AI Sprint Companion MCP Server
REM This script starts the MCP server for AI agents to connect to

echo Starting AI Sprint Companion MCP Server...
echo.

cd /d "%~dp0"
cd backend

REM Check if virtual environment exists
if exist "Scripts\python.exe" (
    echo Using local virtual environment...
    Scripts\python.exe -m app.mcp_server
) else (
    echo Using system Python...
    python -m app.mcp_server
)

