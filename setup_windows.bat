@echo off
echo 🚀 AI Flashcard Generator - Windows Setup Script
echo =============================================

echo.
echo Step 1: Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
echo ✅ Python found!

echo.
echo Step 2: Creating virtual environment...
if exist venv (
    echo ✅ Virtual environment already exists
) else (
    python -m venv venv
    echo ✅ Virtual environment created
)

echo.
echo Step 3: Activating virtual environment...
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated

echo.
echo Step 4: Installing web requirements...
pip install -r web_requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install requirements
    pause
    exit /b 1
)
echo ✅ Requirements installed successfully!

echo.
echo Step 5: Checking Llama installation...
echo.
echo 🤖 Llama Setup Options:
echo.
echo Option A - OLLAMA (Recommended for beginners):
echo   1. Visit https://ollama.ai/
echo   2. Download and install Ollama
echo   3. Run: ollama pull llama2
echo.
echo Option B - Local Llama Installation:
echo   1. Visit https://github.com/facebookresearch/llama
echo   2. Follow installation instructions
echo.
echo Press any key to continue after installing Llama...
pause >nul

echo.
echo Step 6: Starting the web application...
echo 🌐 Your web browser should open automatically
echo 📍 If not, open http://localhost:5000 in your browser
echo.
echo Press Ctrl+C to stop the server
echo.

python web_app.py

echo.
echo Thank you for using AI Flashcard Generator!
pause