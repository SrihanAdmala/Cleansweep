#!/usr/bin/env python3
"""
CleanSweep Launcher — installs dependencies then starts the app.
Usage: python run.py
"""

import subprocess
import sys
import os
import webbrowser
import time
import platform

REQUIREMENTS = ["flask", "psutil"]
URL = "http://localhost:5000"


def check_and_install(packages):
    """Install missing packages."""
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            print(f"  Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
            print(f"  ✔ {pkg} installed")


def is_admin():
    """Check if running as admin (optional, for deeper Windows cleaning)."""
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def main():
    print("\n" + "═" * 55)
    print("  🧹  CleanSweep — Open Source PC Cleaner v1.0")
    print("═" * 55)

    if not is_admin():
        print("\n  ⚠  Not running as Administrator.")
        print("  Some system-level operations may be limited.")
        print("  For best results, run as Administrator/sudo.\n")

    print("  Checking dependencies...")
    check_and_install(REQUIREMENTS)
    print("  ✔ All dependencies ready\n")

    # Open browser after a short delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(URL)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    print(f"  Starting server at {URL}")
    print("  Press CTRL+C to stop\n")
    print("═" * 55 + "\n")

    # Import and run the Flask app
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    from app import app
    app.run(debug=False, port=5000, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
