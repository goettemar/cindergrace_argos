#!/bin/bash
# Cindergrace Argos Start Script for Linux
# Creates venv, installs dependencies, starts app

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PY=".venv/bin/python"

echo "[INFO] Starting setup..."

# Create virtual environment if not exists
if [ ! -f "$VENV_PY" ]; then
    echo "[INFO] Virtual environment not found. Creating .venv ..."
    python3 -m venv .venv
fi

# Run installer
echo "[INFO] Running installer.py..."
"$VENV_PY" installer.py

# Start application
echo "[INFO] Setup complete. Starting Gradio server..."
"$VENV_PY" app.py
