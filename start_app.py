#!/usr/bin/env python3
"""
🚀 AI Flashcard Generator - One Click Launcher
Just run this file and it does EVERYTHING automatically!
No setup required!
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

# Colors for console output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color):
    """Print colored text."""
    print(f"{color}{text}{Colors.ENDC}")

def print_header():
    """Print the app header."""
    print("\n" + "="*60)
    print_colored("🧠 AI FLASHCARD GENERATOR - AUTO LAUNCHER", Colors.BOLD + Colors.BLUE)
    print("="*60)
    print_colored("Just one click and you're ready to go!", Colors.GREEN)
    print("")

def install_package(package_name, import_name=None):
    """Install a package using pip."""
    if import_name is None:
        import_name = package_name

    try:
        __import__(import_name)
        print_colored(f"✅ {package_name} already installed", Colors.GREEN)
        return True
    except ImportError:
        print_colored(f"📦 Installing {package_name}...", Colors.YELLOW)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print_colored(f"✅ {package_name} installed successfully", Colors.GREEN)
            return True
        except subprocess.CalledProcessError:
            print_colored(f"❌ Failed to install {package_name}", Colors.RED)
            return False

def check_ollama():
    """Check if Ollama is available."""
    try:
        result = subprocess.run(['ollama', 'list'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print_colored("✅ Ollama is installed and running", Colors.GREEN)
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    print_colored("❌ Ollama not found", Colors.RED)
    print_colored("💡 Please install Ollama first:", Colors.YELLOW)
    print_colored("   1. Go to https://ollama.ai/", Colors.YELLOW)
    print_colored("   2. Download and install Ollama", Colors.YELLOW)
    print_colored("   3. Run: ollama pull llama2", Colors.YELLOW)
    return False

def open_browser_delayed():
    """Open browser after a short delay."""
    time.sleep(3)  # Give the server time to start
    try:
        webbrowser.open('http://localhost:5000')
        print_colored("🌐 Browser opened to http://localhost:5000", Colors.GREEN)
    except:
        print_colored("⚠️  Could not open browser automatically", Colors.YELLOW)
        print_colored("   Please open http://localhost:5000 in your browser", Colors.YELLOW)

def main():
    """Main launcher function."""
    print_header()

    # Check if running on Windows
    is_windows = sys.platform.startswith('win')

    if is_windows:
        print_colored("🪟 Detected Windows system", Colors.BLUE)

    # Step 1: Install all required packages
    print_colored("📦 Checking and installing dependencies...", Colors.BLUE)

    packages = [
        ('flask', 'flask'),
        ('pandas', 'pandas'),
        ('openpyxl', 'openpyxl'),
        ('requests', 'requests'),
        ('werkzeug', 'werkzeug'),
    ]

    all_installed = True
    for package, import_name in packages:
        if not install_package(package, import_name):
            all_installed = False

    if not all_installed:
        print_colored("❌ Some dependencies failed to install", Colors.RED)
        print_colored("💡 Try running this script as administrator", Colors.YELLOW)
        input("Press Enter to exit...")
        return

    # Step 2: Check Ollama
    print_colored("\n🤖 Checking Ollama installation...", Colors.BLUE)
    if not check_ollama():
        input("\nPress Enter after installing Ollama, or Ctrl+C to exit...")
        if not check_ollama():
            print_colored("❌ Ollama is still not available", Colors.RED)
            input("Press Enter to exit...")
            return

    # Step 3: Create web_app.py if it doesn't exist
    web_app_path = Path('web_app.py')
    if not web_app_path.exists():
        print_colored("❌ web_app.py not found!", Colors.RED)
        print_colored("💡 Make sure you're running this from the Flashcards folder", Colors.YELLOW)
        input("Press Enter to exit...")
        return

    # Step 4: Start the web application
    print_colored("\n🚀 Starting AI Flashcard Generator...", Colors.BLUE)
    print_colored("   The app will open in your browser automatically", Colors.GREEN)
    print_colored("   Press Ctrl+C to stop the server", Colors.YELLOW)
    print("")

    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser_delayed)
    browser_thread.daemon = True
    browser_thread.start()

    # Start the Flask app
    try:
        # Set environment variables for Flask
        os.environ['FLASK_APP'] = 'web_app.py'
        os.environ['FLASK_ENV'] = 'production'

        # Run the web app
        subprocess.run([sys.executable, 'web_app.py'])
    except KeyboardInterrupt:
        print_colored("\n👋 Thanks for using AI Flashcard Generator!", Colors.GREEN)
    except Exception as e:
        print_colored(f"❌ Error starting the application: {e}", Colors.RED)
        input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n👋 Setup cancelled by user", Colors.YELLOW)
    except Exception as e:
        print_colored(f"\n❌ Unexpected error: {e}", Colors.RED)
        input("Press Enter to exit...")