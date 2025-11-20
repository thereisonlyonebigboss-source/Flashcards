#!/bin/bash

echo "🚀 AI Flashcard Generator - Unix/Linux/Mac Setup Script"
echo "========================================================"

# Check Python installation
echo "Step 1: Checking Python installation..."
if command -v python3 &> /dev/null; then
    echo "✅ Python3 found: $(python3 --version)"
else
    echo "❌ Python3 not found! Please install Python 3.10+"
    echo "   On Mac: brew install python3"
    echo "   On Ubuntu: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Create virtual environment
echo ""
echo "Step 2: Creating virtual environment..."
if [ -d "venv" ]; then
    echo "✅ Virtual environment already exists"
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Step 3: Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"

# Install requirements
echo ""
echo "Step 4: Installing web requirements..."
pip install -r web_requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install requirements"
    exit 1
fi
echo "✅ Requirements installed successfully!"

# Llama setup instructions
echo ""
echo "Step 5: Llama Setup Instructions"
echo "================================="
echo ""
echo "🤖 Choose ONE of these options:"
echo ""
echo "Option A - OLLAMA (Recommended for beginners):"
echo "  1. Visit https://ollama.ai/"
echo "  2. Download and install Ollama"
echo "  3. Run: ollama pull llama2"
echo ""
echo "Option B - Local Llama Installation:"
echo "  1. Visit https://github.com/facebookresearch/llama"
echo "  2. Follow installation instructions"
echo ""

# Ask if user wants to test Llama
read -p "Have you installed Llama? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please install Llama first, then run this script again."
    exit 1
fi

echo ""
echo "Step 6: Starting the web application..."
echo "🌐 Open your browser and go to: http://localhost:5000"
echo "📍 Press Ctrl+C to stop the server"
echo ""

python3 web_app.py

echo ""
echo "Thank you for using AI Flashcard Generator!"