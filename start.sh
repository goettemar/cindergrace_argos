#!/bin/bash
# Cindergrace Argos Startskript fuer Linux
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PY=".venv/bin/python"

echo "[INFO] Starte Setup..."

# Virtuelle Umgebung erstellen falls nicht vorhanden
if [ ! -f "$VENV_PY" ]; then
    echo "[INFO] Virtuelle Umgebung nicht gefunden. Erstelle .venv ..."
    python3 -m venv .venv
fi

echo "[INFO] Fuehre installer.py aus..."
"$VENV_PY" installer.py

echo "[INFO] Setup abgeschlossen. Starte Gradio-Server..."
"$VENV_PY" app.py
