#!/bin/bash

# Make this file executable: chmod +x START_APP.command

echo "==================================================="
echo "   🧠 AI FLASHCARD GENERATOR - ONE CLICK START"
echo "==================================================="
echo ""
echo "    Just wait... The magic is happening! ✨"
echo "    Your browser will open automatically."
echo "    Press Ctrl+C to stop the server"
echo "==================================================="
echo ""

# Try different Python commands
if command -v python3 &> /dev/null; then
    python3 start_app.py
elif command -v python &> /dev/null; then
    python start_app.py
else
    echo "❌ Python not found!"
    echo ""
    echo "💡 Please install Python first:"
    echo "   On Mac: brew install python3"
    echo "   On Ubuntu: sudo apt install python3"
    echo ""
    echo "Then double-click this file again!"
    echo ""
    read -p "Press Enter to exit..."
fi