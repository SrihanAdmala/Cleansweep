"""
CleanSweep - Open Source PC Cleaner Backend
License: MIT
"""

import os
import sys
import platform
import shutil
import glob
import subprocess
import tempfile
import ctypes
import time
import threading
import json
import stat
from pathlib import Path
from flask import Flask, jsonify, render_template, Response, stream_with_context
import queue

app = Flask(__name__)

OS = platform.system()  # 'Windows', 'Darwin', 'Linux'

# ─────────────────────────────────────────────
#  PATH DEFINITIONS
# ─────────────────────────────────────────────

def get_clean_targets():
    targets = {}
    home = Path.home()

    if OS == "Windows":
        windir = Path(os.environ.get("WINDIR", "C:\\Windows"))
        localappdata = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local"))
        appdata = Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
        temp = Path(os.environ.get("TEMP", localappdata / "Temp"))

        targets = {
            "User Temp Files": [temp],
            "Windows Temp": [windir / "Temp"],
            "Prefetch": [windir / "Prefetch"],
            "Recent Files": [appdata / "Microsoft/Windows/Recent"],
            "Thumbnail Cache": [localappdata / "Microsoft/Windows/Explorer"],
            "Windows Error Reports": [
                localappdata / "Microsoft/Windows/WER",
                Path("C:/ProgramData/Microsoft/Windows/WER"),
            ],
            "Windows Update Cache": [Path("C:/Windows/SoftwareDistribution/Download")],
            "DirectX Shader Cache": [localappdata / "D3DSCache"],
            "Chrome Cache": [
                localappdata / "Google/Chrome/User Data/Default/Cache",
                localappdata / "Google/Chrome/User Data/Default/Code Cache",
                localappdata / "Google/Chrome/User Data/Default/GPUCache",
            ],
            "Edge Cache": [
                localappdata / "Microsoft/Edge/User Data/Default/Cache",
                localappdata / "Microsoft/Edge/User Data/Default/Code Cache",
            ],
            "Firefox Cache": list((localappdata / "Mozilla/Firefox/Profiles").glob("*/cache2")) if (localappdata / "Mozilla/Firefox/Profiles").exists() else [],
            "Teams Cache": [localappdata / "Microsoft/Teams/Cache"],
            "Discord Cache": [appdata / "discord/Cache", appdata / "discord/Code Cache"],
            "Spotify Cache": [localappdata / "Spotify/Data"],
            "Log Files": [windir / "Logs"],
            "Crash Dumps": [localappdata / "CrashDumps"],
            "Font Cache": [localappdata / "FontCache"],
        }

    elif OS == "Darwin":  # macOS
        targets = {
            "User Cache": [home / "Library/Caches"],
            "System Log Files": [Path("/var/log")],
            "User Log Files": [home / "Library/Logs"],
            "Temporary Files": [Path("/tmp"), Path("/var/tmp")],
            "Chrome Cache": [home / "Library/Caches/Google/Chrome"],
            "Firefox Cache": [home / "Library/Caches/Firefox"],
            "Safari Cache": [home / "Library/Caches/com.apple.Safari"],
            "Trash": [home / ".Trash"],
            "iOS Device Backups": [home / "Library/Application Support/MobileSync/Backup"],
            "Xcode Cache": [home / "Library/Developer/Xcode/DerivedData"],
            "pip Cache": [home / "Library/Caches/pip"],
        }

    else:  # Linux
        targets = {
            "User Cache": [home / ".cache"],
            "Temporary Files": [Path("/tmp"), Path("/var/tmp")],
            "System Logs": [Path("/var/log")],
            "User Logs": [home / ".local/share/recently-used.xbel"],
            "Thumbnail Cache": [home / ".cache/thumbnails"],
            "Chrome Cache": [home / ".cache/google-chrome", home / ".config/google-chrome/Default/Cache"],
            "Firefox Cache": list((home / ".mozilla/firefox").glob("*/cache2")) if (home / ".mozilla/firefox").exists() else [],
            "pip Cache": [home / ".cache/pip"],
            "apt Cache": [Path("/var/cache/apt/archives")],
            "npm Cache": [home / ".npm/_cacache"],
            "Trash": [home / ".local/share/Trash"],
            "Coredumps": [Path("/var/crash"), home / ".local/share/apport/coredump"],
        }

    return targets


# ─────────────────────────────────────────────
#  UTILITY FUNCTIONS
# ─────────────────────────────────────────────

def get_dir_size(path):
    """Return total size of a directory in bytes."""
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_dir_size(entry.path)
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError):
        pass
    return total


def format_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def force_remove(path):
    """Remove file or directory with retry on Windows."""
    def onerror(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass

    try:
        p = Path(path)
        if p.is_file() or p.is_symlink():
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)
            return True
        elif p.is_dir():
            shutil.rmtree(path, onerror=onerror)
            return True
    except Exception:
        pass
    return False


def clean_directory_contents(directory, delete_subfolders=True):
    """Clean the contents of a directory without removing the directory itself."""
    freed = 0
    errors = 0
    items_removed = 0

    d = Path(directory)
    if not d.exists():
        return 0, 0, 0

    try:
        for item in d.iterdir():
            try:
                item_size = get_dir_size(item) if item.is_dir() else item.stat().st_size
                if item.is_dir() and delete_subfolders:
                    if force_remove(str(item)):
                        freed += item_size
                        items_removed += 1
                    else:
                        errors += 1
                elif item.is_file():
                    if force_remove(str(item)):
                        freed += item_size
                        items_removed += 1
                    else:
                        errors += 1
            except (PermissionError, OSError):
                errors += 1
    except (PermissionError, OSError):
        errors += 1

    return freed, errors, items_removed


# ─────────────────────────────────────────────
#  SCAN
# ─────────────────────────────────────────────

@app.route("/api/scan")
def scan():
    targets = get_clean_targets()
    results = []
    total_size = 0

    for category, paths in targets.items():
        cat_size = 0
        exists = False
        for p in paths:
            pp = Path(p)
            if pp.exists():
                exists = True
                cat_size += get_dir_size(str(pp))

        if exists:
            total_size += cat_size
            results.append({
                "category": category,
                "size": cat_size,
                "size_human": format_bytes(cat_size),
                "paths": [str(p) for p in paths],
            })

    results.sort(key=lambda x: x["size"], reverse=True)

    return jsonify({
        "total": total_size,
        "total_human": format_bytes(total_size),
        "categories": results,
        "os": OS
    })


# ─────────────────────────────────────────────
#  CLEAN (Streaming SSE)
# ─────────────────────────────────────────────

@app.route("/api/clean")
def clean():
    def generate():
        targets = get_clean_targets()
        total_freed = 0
        total_errors = 0

        for category, paths in targets.items():
            freed = 0
            errors = 0
            items = 0

            for p in paths:
                pp = Path(p)
                if pp.exists():
                    f, e, i = clean_directory_contents(str(pp))
                    freed += f
                    errors += e
                    items += i

            total_freed += freed
            total_errors += errors

            data = json.dumps({
                "category": category,
                "freed": freed,
                "freed_human": format_bytes(freed),
                "items": items,
                "errors": errors,
            })
            yield f"data: {data}\n\n"
            time.sleep(0.05)

        # Extra OS-specific cleanup
        if OS == "Windows":
            try:
                # Flush DNS
                subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=10)
                yield f"data: {json.dumps({'category': 'DNS Cache', 'freed': 0, 'freed_human': '0 B', 'items': 1, 'errors': 0})}\n\n"
            except Exception:
                pass

            try:
                # Empty recycle bin
                import winreg
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1)
                yield f"data: {json.dumps({'category': 'Recycle Bin', 'freed': 0, 'freed_human': '0 B', 'items': 1, 'errors': 0})}\n\n"
            except Exception:
                pass

        elif OS == "Darwin":
            try:
                subprocess.run(["dscacheutil", "-flushcache"], capture_output=True, timeout=10)
                yield f"data: {json.dumps({'category': 'DNS Cache', 'freed': 0, 'freed_human': '0 B', 'items': 1, 'errors': 0})}\n\n"
            except Exception:
                pass

        elif OS == "Linux":
            try:
                subprocess.run(["sudo", "sync"], capture_output=True, timeout=10)
                yield f"data: {json.dumps({'category': 'Sync Disk Buffers', 'freed': 0, 'freed_human': '0 B', 'items': 1, 'errors': 0})}\n\n"
            except Exception:
                pass

        # DONE event
        yield f"data: {json.dumps({'done': True, 'total_freed': total_freed, 'total_freed_human': format_bytes(total_freed), 'errors': total_errors})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ─────────────────────────────────────────────
#  SYSTEM INFO
# ─────────────────────────────────────────────

@app.route("/api/sysinfo")
def sysinfo():
    import psutil

    disk = psutil.disk_usage("/")
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.5)

    # Startup items (Windows only)
    startup_items = []
    if OS == "Windows":
        try:
            import winreg
            reg_paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            ]
            for hkey, path in reg_paths:
                try:
                    key = winreg.OpenKey(hkey, path)
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_items.append({"name": name, "value": value})
                            i += 1
                        except OSError:
                            break
                except Exception:
                    pass
        except Exception:
            pass

    # Top large files in home
    large_files = []
    try:
        home = Path.home()
        all_files = []
        for root, dirs, files in os.walk(home):
            # Skip hidden dirs and common large-but-useful dirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                       ['node_modules', '.git', 'venv', '__pycache__', 'AppData']]
            for fname in files:
                fp = Path(root) / fname
                try:
                    sz = fp.stat().st_size
                    if sz > 50 * 1024 * 1024:  # > 50MB
                        all_files.append({"path": str(fp), "size": sz, "size_human": format_bytes(sz)})
                except Exception:
                    pass
        large_files = sorted(all_files, key=lambda x: x["size"], reverse=True)[:20]
    except Exception:
        pass

    return jsonify({
        "os": OS,
        "os_version": platform.version(),
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": cpu,
        "ram_total": mem.total,
        "ram_total_human": format_bytes(mem.total),
        "ram_used": mem.used,
        "ram_used_human": format_bytes(mem.used),
        "ram_percent": mem.percent,
        "disk_total": disk.total,
        "disk_total_human": format_bytes(disk.total),
        "disk_used": disk.used,
        "disk_used_human": format_bytes(disk.used),
        "disk_free": disk.free,
        "disk_free_human": format_bytes(disk.free),
        "disk_percent": disk.percent,
        "startup_items": startup_items,
        "large_files": large_files,
    })


# ─────────────────────────────────────────────
#  OPTIMIZATIONS
# ─────────────────────────────────────────────

@app.route("/api/optimize")
def optimize():
    results = []

    if OS == "Windows":
        # Flush DNS
        try:
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=15)
            results.append({"task": "Flush DNS Cache", "status": "done"})
        except Exception as e:
            results.append({"task": "Flush DNS Cache", "status": "failed", "error": str(e)})

        # Release/Renew IP
        try:
            subprocess.run(["ipconfig", "/release"], capture_output=True, timeout=15)
            subprocess.run(["ipconfig", "/renew"], capture_output=True, timeout=30)
            results.append({"task": "Refresh IP Configuration", "status": "done"})
        except Exception as e:
            results.append({"task": "Refresh IP Configuration", "status": "failed", "error": str(e)})

        # Empty Recycle Bin
        try:
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1)
            results.append({"task": "Empty Recycle Bin", "status": "done"})
        except Exception as e:
            results.append({"task": "Empty Recycle Bin", "status": "failed", "error": str(e)})

        # Run Disk Cleanup (silent)
        try:
            subprocess.Popen(["cleanmgr", "/sagerun:1"], shell=False)
            results.append({"task": "Windows Disk Cleanup", "status": "started"})
        except Exception as e:
            results.append({"task": "Windows Disk Cleanup", "status": "failed", "error": str(e)})

    elif OS == "Darwin":
        try:
            subprocess.run(["sudo", "dscacheutil", "-flushcache"], capture_output=True, timeout=15)
            subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], capture_output=True, timeout=15)
            results.append({"task": "Flush DNS Cache", "status": "done"})
        except Exception as e:
            results.append({"task": "Flush DNS Cache", "status": "failed", "error": str(e)})

        try:
            subprocess.run(["sudo", "purge"], capture_output=True, timeout=15)
            results.append({"task": "Purge Inactive Memory", "status": "done"})
        except Exception as e:
            results.append({"task": "Purge Inactive Memory", "status": "failed", "error": str(e)})

    else:  # Linux
        try:
            subprocess.run(["sudo", "sync"], capture_output=True, timeout=10)
            results.append({"task": "Sync Disk Buffers", "status": "done"})
        except Exception as e:
            results.append({"task": "Sync Disk Buffers", "status": "failed", "error": str(e)})

        try:
            subprocess.run(["sudo", "systemctl", "restart", "systemd-resolved"], capture_output=True, timeout=15)
            results.append({"task": "Flush DNS Cache", "status": "done"})
        except Exception as e:
            results.append({"task": "Flush DNS Cache", "status": "failed", "error": str(e)})

    return jsonify({"results": results})


# ─────────────────────────────────────────────
#  SERVE FRONTEND
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    print("\n" + "═" * 55)
    print("  🧹  CleanSweep — Open Source PC Cleaner")
    print("═" * 55)
    print(f"  OS Detected : {OS} {platform.release()}")
    print(f"  Open browser: http://localhost:5000")
    print("═" * 55 + "\n")
    app.run(debug=False, port=5000, threaded=True)
