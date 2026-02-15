#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║        CleanSweep — One-Click Installer              ║
║        https://github.com/cleansweep/cleansweep      ║
║        License: MIT                                  ║
╚══════════════════════════════════════════════════════╝

Save this file anywhere, then run:
    python install.py

What this does:
  1. Checks your Python version
  2. Downloads CleanSweep from GitHub
  3. Installs Python dependencies
  4. Creates a desktop shortcut
  5. Optionally launches the app
"""

import sys
import os
import platform
import subprocess
import shutil
import json
import stat
import urllib.request
import urllib.error
import zipfile
import io
import tempfile
from pathlib import Path

# ─────────────────────────────────────────────────────────
#  CONFIG  ←  update these if you fork the repo
# ─────────────────────────────────────────────────────────
GITHUB_USER   = "cleansweep"
GITHUB_REPO   = "cleansweep"
GITHUB_BRANCH = "main"
APP_NAME      = "CleanSweep"
APP_VERSION   = "1.0.0"
INSTALL_PORT  = 5000

REPO_ZIP_URL  = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"
REQUIREMENTS  = ["flask>=2.3.0", "psutil>=5.9.0"]

OS = platform.system()   # Windows | Darwin | Linux

# ─────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
DIM    = "\033[2m"

def _win_color_init():
    """Enable ANSI colors on Windows."""
    if OS == "Windows":
        try:
            import ctypes
            kernel = ctypes.windll.kernel32
            kernel.SetConsoleMode(kernel.GetStdHandle(-11), 7)
        except Exception:
            pass

def banner():
    _win_color_init()
    print(f"""
{CYAN}{'═' * 54}
  🧹  {BOLD}{APP_NAME} Installer{RESET}{CYAN}  v{APP_VERSION}
  Free & Open Source PC Cleaner
{'═' * 54}{RESET}""")

def step(n, total, msg):
    print(f"\n{BOLD}{CYAN}[{n}/{total}]{RESET} {msg}")

def ok(msg):    print(f"  {GREEN}✔{RESET}  {msg}")
def warn(msg):  print(f"  {YELLOW}⚠{RESET}  {msg}")
def err(msg):   print(f"  {RED}✖{RESET}  {msg}")
def info(msg):  print(f"  {DIM}→{RESET}  {msg}")

def ask(prompt, default="y"):
    ans = input(f"\n  {prompt} [{default.upper()}/{'n' if default=='y' else 'Y'}]: ").strip().lower()
    if not ans:
        return default == "y"
    return ans in ("y", "yes")

def die(msg):
    err(msg)
    print(f"\n{RED}Installation failed.{RESET}")
    sys.exit(1)


# ─────────────────────────────────────────────────────────
#  STEP 1 — Python version check
# ─────────────────────────────────────────────────────────

def check_python():
    v = sys.version_info
    info(f"Python {v.major}.{v.minor}.{v.micro} detected")
    if v < (3, 8):
        die(f"Python 3.8+ required. You have {v.major}.{v.minor}. Download at https://python.org")
    ok(f"Python version OK ({v.major}.{v.minor}.{v.micro})")
    return True


# ─────────────────────────────────────────────────────────
#  STEP 2 — Choose install directory
# ─────────────────────────────────────────────────────────

def choose_install_dir():
    if OS == "Windows":
        default = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / APP_NAME
    elif OS == "Darwin":
        default = Path.home() / "Applications" / APP_NAME
    else:
        default = Path.home() / f".local/share/{APP_NAME.lower()}"

    print(f"\n  Default install location: {BOLD}{default}{RESET}")
    use_default = ask("Install to this location?", "y")

    if use_default:
        return default

    custom = input(f"  Enter custom path: ").strip()
    if not custom:
        return default
    return Path(custom)


# ─────────────────────────────────────────────────────────
#  STEP 3 — Download from GitHub
# ─────────────────────────────────────────────────────────

def download_and_extract(install_dir: Path):
    """Download the repo zip and extract to install_dir."""

    # If the folder already has app.py, offer to skip re-download
    if (install_dir / "app.py").exists():
        if ask("Existing installation found. Re-download?", "n"):
            info("Skipping download, using existing files.")
            return
        else:
            shutil.rmtree(install_dir, ignore_errors=True)

    install_dir.mkdir(parents=True, exist_ok=True)

    info(f"Downloading {APP_NAME} from GitHub...")
    info(f"URL: {REPO_ZIP_URL}")

    try:
        req = urllib.request.Request(
            REPO_ZIP_URL,
            headers={"User-Agent": f"{APP_NAME}-Installer/{APP_VERSION}"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            total = int(response.headers.get("Content-Length", 0))
            data = b""
            chunk = 8192
            downloaded = 0
            while True:
                buf = response.read(chunk)
                if not buf:
                    break
                data += buf
                downloaded += len(buf)
                if total:
                    pct = int(downloaded / total * 40)
                    bar = "█" * pct + "░" * (40 - pct)
                    print(f"\r  {CYAN}[{bar}]{RESET} {downloaded//1024}KB", end="", flush=True)

        print()  # newline after progress bar
        ok(f"Downloaded {len(data)//1024} KB")

    except urllib.error.URLError as e:
        # Fallback: if no internet, try to use local files next to this script
        warn(f"Download failed ({e}). Looking for local copy...")
        script_dir = Path(__file__).parent
        if (script_dir / "app.py").exists():
            info("Found local files next to installer — copying them.")
            for item in script_dir.iterdir():
                if item.name != "install.py":
                    dest = install_dir / item.name
                    if item.is_dir():
                        shutil.copytree(str(item), str(dest), dirs_exist_ok=True)
                    else:
                        shutil.copy2(str(item), str(dest))
            ok("Copied local files successfully.")
            return
        die(f"No internet and no local files found. Check your connection and try again.")

    # Extract zip
    info("Extracting files...")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        # GitHub zips have a top-level folder like "cleansweep-main/"
        members = zf.namelist()
        prefix = members[0].split("/")[0] + "/" if members else ""

        for member in members:
            # Strip the top-level folder
            rel = member[len(prefix):]
            if not rel:
                continue
            target = install_dir / rel
            if member.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)

    ok(f"Extracted to {install_dir}")


# ─────────────────────────────────────────────────────────
#  STEP 4 — Install Python dependencies
# ─────────────────────────────────────────────────────────

def install_dependencies():
    info("Installing Python packages: " + ", ".join(REQUIREMENTS))
    for pkg in REQUIREMENTS:
        try:
            name = pkg.split(">=")[0].split("==")[0]
            __import__(name)
            ok(f"{name} already installed")
        except ImportError:
            info(f"Installing {pkg}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                warn(f"pip install {pkg} failed: {result.stderr.strip()}")
            else:
                ok(f"{pkg} installed")


# ─────────────────────────────────────────────────────────
#  STEP 5 — Create desktop shortcut
# ─────────────────────────────────────────────────────────

def create_shortcut(install_dir: Path):
    python_exe = sys.executable
    runner = install_dir / "run.py"

    if OS == "Windows":
        # Create .bat launcher on Desktop
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop"

        bat_content = f"""@echo off
title {APP_NAME}
cd /d "{install_dir}"
"{python_exe}" "{runner}"
"""
        shortcut_path = desktop / f"{APP_NAME}.bat"
        shortcut_path.write_text(bat_content)
        ok(f"Desktop shortcut created: {shortcut_path}")

        # Also try creating a proper .lnk if pywin32 available
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            lnk_path = str(desktop / f"{APP_NAME}.lnk")
            shortcut = shell.CreateShortCut(lnk_path)
            shortcut.Targetpath = python_exe
            shortcut.Arguments = f'"{runner}"'
            shortcut.WorkingDirectory = str(install_dir)
            shortcut.IconLocation = python_exe
            shortcut.Description = f"{APP_NAME} — Open Source PC Cleaner"
            shortcut.save()
            ok(f"Windows shortcut (.lnk) created: {lnk_path}")
        except Exception:
            pass  # .bat already works fine

        # Start Menu entry
        try:
            startmenu = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs"
            if startmenu.exists():
                sm_bat = startmenu / f"{APP_NAME}.bat"
                sm_bat.write_text(bat_content)
                ok(f"Start Menu entry created")
        except Exception:
            pass

    elif OS == "Darwin":
        # Create .command file on Desktop (double-clickable on macOS)
        desktop = Path.home() / "Desktop"
        desktop.mkdir(exist_ok=True)
        cmd_path = desktop / f"{APP_NAME}.command"
        cmd_content = f"""#!/bin/bash
cd "{install_dir}"
"{python_exe}" "{runner}"
"""
        cmd_path.write_text(cmd_content)
        os.chmod(cmd_path, os.stat(cmd_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        ok(f"Desktop launcher created: {cmd_path}")

        # Also create a .app bundle
        try:
            app_bundle = Path.home() / "Applications" / f"{APP_NAME}.app"
            macos_dir = app_bundle / "Contents/MacOS"
            macos_dir.mkdir(parents=True, exist_ok=True)
            (app_bundle / "Contents/Resources").mkdir(exist_ok=True)

            script_path = macos_dir / APP_NAME
            script_path.write_text(f"""#!/bin/bash
cd "{install_dir}"
"{python_exe}" "{runner}"
""")
            os.chmod(script_path, 0o755)

            plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>{APP_NAME}</string>
  <key>CFBundleExecutable</key><string>{APP_NAME}</string>
  <key>CFBundleIdentifier</key><string>com.cleansweep.app</string>
  <key>CFBundleVersion</key><string>{APP_VERSION}</string>
  <key>CFBundlePackageType</key><string>APPL</string>
</dict>
</plist>"""
            (app_bundle / "Contents/Info.plist").write_text(plist)
            ok(f"macOS .app bundle created: {app_bundle}")
        except Exception as e:
            warn(f"Could not create .app bundle: {e}")

    else:  # Linux
        # Create .desktop file
        desktop_file_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={APP_NAME}
Comment=Open Source PC Cleaner
Exec={python_exe} "{runner}"
Path={install_dir}
Icon=utilities-system-monitor
Terminal=false
Categories=System;Utility;
"""
        # User applications dir
        apps_dir = Path.home() / ".local/share/applications"
        apps_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = apps_dir / f"{APP_NAME.lower()}.desktop"
        desktop_file.write_text(desktop_file_content)
        os.chmod(desktop_file, 0o755)
        ok(f"Application launcher created: {desktop_file}")

        # Also add to Desktop if it exists
        desktop = Path.home() / "Desktop"
        if desktop.exists():
            desk_copy = desktop / f"{APP_NAME.lower()}.desktop"
            shutil.copy2(desktop_file, desk_copy)
            os.chmod(desk_copy, 0o755)
            ok(f"Desktop icon created: {desk_copy}")

        # Create shell script in ~/.local/bin for CLI launch
        bin_dir = Path.home() / ".local/bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        cli_script = bin_dir / "cleansweep"
        cli_script.write_text(f"""#!/bin/bash
cd "{install_dir}"
"{python_exe}" "{runner}"
""")
        os.chmod(cli_script, 0o755)
        ok(f"CLI command created: {cli_script}  (run: cleansweep)")


# ─────────────────────────────────────────────────────────
#  STEP 6 — Write install manifest
# ─────────────────────────────────────────────────────────

def write_manifest(install_dir: Path):
    manifest = {
        "app": APP_NAME,
        "version": APP_VERSION,
        "install_dir": str(install_dir),
        "python": sys.executable,
        "os": OS,
        "port": INSTALL_PORT,
        "installed_by": f"install.py v{APP_VERSION}"
    }
    manifest_path = install_dir / ".cleansweep_install.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    # Hidden on Windows
    if OS == "Windows":
        try:
            subprocess.run(["attrib", "+H", str(manifest_path)], capture_output=True)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────
#  UNINSTALL HELPER
# ─────────────────────────────────────────────────────────

def uninstall_mode():
    print(f"\n{YELLOW}UNINSTALL MODE{RESET}")
    manifest_candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / APP_NAME / ".cleansweep_install.json",
        Path.home() / ".local/share" / APP_NAME.lower() / ".cleansweep_install.json",
        Path.home() / "Applications" / APP_NAME / ".cleansweep_install.json",
    ]

    manifest_path = None
    for p in manifest_candidates:
        if p.exists():
            manifest_path = p
            break

    if not manifest_path:
        err("Could not find installation manifest. Please delete the install folder manually.")
        return

    with open(manifest_path) as f:
        m = json.load(f)

    install_dir = Path(m["install_dir"])
    info(f"Found installation at: {install_dir}")
    if ask(f"Remove {APP_NAME} from {install_dir}?", "y"):
        shutil.rmtree(install_dir, ignore_errors=True)
        ok("Installation removed.")

        # Remove shortcuts
        if OS == "Windows":
            for p in [Path.home() / "Desktop" / f"{APP_NAME}.bat",
                      Path.home() / "Desktop" / f"{APP_NAME}.lnk",
                      Path(os.environ.get("APPDATA","")) / f"Microsoft/Windows/Start Menu/Programs/{APP_NAME}.bat"]:
                if p.exists():
                    p.unlink()
                    ok(f"Removed: {p}")
        elif OS == "Darwin":
            for p in [Path.home() / "Desktop" / f"{APP_NAME}.command",
                      Path.home() / "Applications" / f"{APP_NAME}.app"]:
                if p.exists():
                    if p.is_dir():
                        shutil.rmtree(p)
                    else:
                        p.unlink()
                    ok(f"Removed: {p}")
        else:
            for p in [Path.home() / ".local/share/applications" / f"{APP_NAME.lower()}.desktop",
                      Path.home() / ".local/bin/cleansweep",
                      Path.home() / "Desktop" / f"{APP_NAME.lower()}.desktop"]:
                if p.exists():
                    p.unlink()
                    ok(f"Removed: {p}")

        ok(f"{APP_NAME} uninstalled successfully.")


# ─────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────

def main():
    banner()

    # Handle --uninstall flag
    if "--uninstall" in sys.argv or "-u" in sys.argv:
        uninstall_mode()
        return

    TOTAL_STEPS = 6

    # ── Step 1: Python version
    step(1, TOTAL_STEPS, "Checking Python version")
    check_python()

    # ── Step 2: Choose install dir
    step(2, TOTAL_STEPS, "Choosing install location")
    install_dir = choose_install_dir()
    info(f"Will install to: {install_dir}")

    # ── Step 3: Download
    step(3, TOTAL_STEPS, "Downloading CleanSweep from GitHub")
    download_and_extract(install_dir)

    # ── Step 4: Dependencies
    step(4, TOTAL_STEPS, "Installing dependencies")
    install_dependencies()

    # ── Step 5: Desktop shortcut
    step(5, TOTAL_STEPS, "Creating desktop shortcut")
    try:
        create_shortcut(install_dir)
    except Exception as e:
        warn(f"Could not create shortcut: {e}")

    # ── Step 6: Manifest
    step(6, TOTAL_STEPS, "Finalizing installation")
    write_manifest(install_dir)
    ok("Install manifest saved")

    # ── Done
    print(f"""
{CYAN}{'═' * 54}
{GREEN}{BOLD}  ✅  {APP_NAME} installed successfully!{RESET}
{CYAN}{'═' * 54}{RESET}

  {BOLD}To launch:{RESET}
  • Double-click the desktop icon, or
  • Run: {BOLD}python "{install_dir / 'run.py'}"{RESET}
  • Then open: {BOLD}http://localhost:{INSTALL_PORT}{RESET}

  {BOLD}To uninstall:{RESET}
  • Run: {BOLD}python install.py --uninstall{RESET}

{DIM}  {APP_NAME} is free, open source software (MIT License).
  Source: https://github.com/{GITHUB_USER}/{GITHUB_REPO}{RESET}
""")

    if ask("Launch CleanSweep now?", "y"):
        print(f"  {GREEN}Starting {APP_NAME}...{RESET}\n")
        import webbrowser, threading, time
        def open_browser():
            time.sleep(2)
            webbrowser.open(f"http://localhost:{INSTALL_PORT}")
        threading.Thread(target=open_browser, daemon=True).start()

        runner = install_dir / "run.py"
        os.chdir(install_dir)
        subprocess.run([sys.executable, str(runner)])


if __name__ == "__main__":
    main()
