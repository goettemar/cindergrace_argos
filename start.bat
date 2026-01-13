@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Cindergrace Argos Start Script for Windows
REM Creates venv, installs dependencies, starts app

REM Determine repository root (directory of this script)
set "REPO_DIR=%~dp0"
pushd "%REPO_DIR%" >NUL

set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

echo [INFO] Starting setup...

REM Create virtual environment if not exists
if not exist "%VENV_PY%" (
    echo [INFO] Virtual environment not found. Creating %VENV_DIR% ...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Could not create virtual environment.
        goto :error
    )
)

REM Run installer
echo [INFO] Running installer.py...
call "%VENV_PY%" installer.py
if errorlevel 1 (
    echo [ERROR] Installer failed.
    goto :error
)

REM Start application
echo [INFO] Setup complete. Starting Gradio server...
call "%VENV_PY%" app.py
if errorlevel 1 (
    echo [ERROR] Gradio server exited with error.
    goto :error
)

popd >NUL
exit /B 0

:error
popd >NUL
pause
exit /B 1
