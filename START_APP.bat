@echo off
title AI Flashcard Generator
color 0A

echo ===================================================
echo    🧠 AI FLASHCARD GENERATOR - ONE CLICK START
echo ===================================================
echo.
echo    Just wait... The magic is happening! ✨
echo    Your browser will open automatically.
echo.
echo    Press Ctrl+C to stop the server
echo ===================================================
echo.

REM Try to run Python
python start_app.py

REM If Python not found in PATH, try common Python installations
if errorlevel 1 (
    echo Trying to find Python...
    py start_app.py
)

REM If still not found, show error message
if errorlevel 1 (
    echo.
    echo ❌ Python not found!
    echo.
    echo 💡 Please install Python first:
    echo    1. Go to https://python.org
    echo    2. Download and install Python 3.10+
    echo    3. Make sure to check "Add Python to PATH"
    echo.
    echo    Then double-click this file again!
    echo.
    pause
)

REM If the script finishes normally, don't close immediately
if not errorlevel 1 (
    echo.
    echo 👋 Server stopped. Goodbye!
    pause
)