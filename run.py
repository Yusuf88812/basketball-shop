#!/usr/bin/env python3
"""
🏀 Basketball Shop — One-Command Launcher
Run: python run.py
"""
import subprocess
import sys
import os


def install_deps():
    print("📦 Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
    print("✅ Dependencies installed!")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Install dependencies
    try:
        install_deps()
    except Exception as e:
        print(f"⚠️ Error installing deps: {e}")
        print("Try: pip install -r requirements.txt")

    # Create upload directory
    os.makedirs("static/uploads", exist_ok=True)

    print()
    print("=" * 50)
    print("  🏀 Basketball Shop is starting...")
    print("=" * 50)
    print()
    print("  🌐 Store:  http://localhost:8000")
    print("  🔐 Admin:  http://localhost:8000/admin")
    print("  👤 Login:  admin / admin123")
    print()
    print("=" * 50)
    print()

    # Start server
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
