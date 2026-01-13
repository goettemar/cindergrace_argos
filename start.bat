@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Determine repository root (directory of this script)
set "REPO_DIR=%~dp0"
pushd "%REPO_DIR%" >NUL

set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

echo [INFO] Starte Setup...

if not exist "%VENV_PY%" (
    echo [INFO] Virtuelle Umgebung nicht gefunden. Erstelle %VENV_DIR% ...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [FEHLER] Konnte virtuelle Umgebung nicht erstellen.
        goto :error
    )
)

echo [INFO] Fuehre installer.py mit virtuellem Python aus...
call "%VENV_PY%" installer.py
if errorlevel 1 (
    echo [FEHLER] Installer ist fehlgeschlagen.
    goto :error
)

echo [INFO] Setup abgeschlossen. Starte Gradio-Server...
call "%VENV_PY%" app.py
if errorlevel 1 (
    echo [FEHLER] Gradio-Server wurde mit Fehler beendet.
    goto :error
)

popd >NUL
exit /B 0

:error
popd >NUL
exit /B 1
