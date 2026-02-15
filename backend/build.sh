#!/usr/bin/env bash
# Build script for Render.com deployment
# This script is executed during the build phase

set -o errexit  # Exit on error

echo "=========================================="
echo "  AI Sprint Companion - Build Script"
echo "=========================================="

# Upgrade pip
echo "[1/3] Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "[2/3] Installing dependencies..."
pip install -r requirements.txt

# Run any database migrations (if needed in the future)
echo "[3/3] Running post-install tasks..."
# python -m app.migrations  # Uncomment if you add database migrations

echo "=========================================="
echo "  Build completed successfully!"
echo "=========================================="

