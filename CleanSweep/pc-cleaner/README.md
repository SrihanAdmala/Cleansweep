# 🧹 CleanSweep — Open Source PC Cleaner

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-00e5a0?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge)

**Free. Open Source. No telemetry. No tracking. Your data stays on your machine.**

[⬇️ Download Installer](#-installation) · [📖 Features](#-features) · [🐛 Report Bug](https://github.com/cleansweep/cleansweep/issues) · [💡 Contribute](#-contributing)

</div>

---

## ⬇️ Installation

### ✅ Option 1 — One-Click Installer *(Recommended)*

**Step 1.** Download the installer:

> 👉 **[`CleanSweep-install.py`](https://github.com/cleansweep/cleansweep/releases/latest/download/CleanSweep-install.py)**

**Step 2.** Run it:

```bash
python CleanSweep-install.py
```

The installer will automatically:
- ✔ Download CleanSweep from GitHub
- ✔ Install Python dependencies (Flask, psutil)
- ✔ Create a desktop shortcut
- ✔ Launch the app in your browser

> **Windows:** Right-click → *Run as Administrator* for the deepest cleaning.
> **macOS/Linux:** `sudo python CleanSweep-install.py` for system-level access.

To uninstall later:
```bash
python CleanSweep-install.py --uninstall
```

---

### 📦 Option 2 — Portable ZIP

1. **[⬇ Download latest release ZIP](https://github.com/cleansweep/cleansweep/releases/latest)**
2. Extract anywhere you like
3. Run:
   ```bash
   python run.py
   ```
4. Open **http://localhost:5000**

---

### 🐍 Option 3 — pip Install

```bash
pip install cleansweep
cleansweep
```

---

### 🔧 Option 4 — Clone & Run

```bash
git clone https://github.com/cleansweep/cleansweep.git
cd cleansweep
pip install -r requirements.txt
python run.py
```

---

## ✨ Features

### 🗑️ Junk Cleaner

| Category               | Windows | macOS | Linux |
|------------------------|:-------:|:-----:|:-----:|
| User Temp Files        | ✅ | ✅ | ✅ |
| System Temp            | ✅ | ✅ | ✅ |
| Browser Cache (Chrome) | ✅ | ✅ | ✅ |
| Browser Cache (Firefox)| ✅ | ✅ | ✅ |
| Browser Cache (Edge)   | ✅ | — | — |
| Windows Update Cache   | ✅ | — | — |
| Prefetch Files         | ✅ | — | — |
| Windows Error Reports  | ✅ | — | — |
| DirectX Shader Cache   | ✅ | — | — |
| Thumbnail Cache        | ✅ | — | ✅ |
| Discord / Teams / Spotify Cache | ✅ | — | — |
| Log Files              | ✅ | ✅ | ✅ |
| Crash Dumps            | ✅ | — | — |
| iOS Device Backups     | — | ✅ | — |
| Xcode DerivedData      | — | ✅ | — |
| pip / npm Cache        | ✅ | ✅ | ✅ |
| apt Cache              | — | — | ✅ |
| Trash / Recycle Bin    | ✅ | ✅ | ✅ |

### ⚡ Optimizer
- DNS cache flush (all platforms)
- IP configuration refresh (Windows)
- Empty Recycle Bin (Windows)
- Purge inactive memory (macOS)
- Sync disk buffers (Linux)

### 📊 Dashboard
- Live CPU, RAM & Disk metrics with usage bars
- OS detection

### 📋 Startup & Large Files
- View startup programs (Windows Registry)
- Scan home directory for files >50MB

---

## 🚀 Running with Full Permissions

For maximum cleaning depth, run as Administrator/root:

```bash
# Windows — Command Prompt as Administrator
python run.py

# macOS / Linux
sudo python run.py
```

---

## 🛡️ Safety

CleanSweep **only** deletes files in known safe junk locations:
- Temp directories (`%TEMP%`, `/tmp`, `/var/tmp`)
- Browser cache subfolders
- Windows caches (Prefetch, WER, Update downloads)
- Application caches (Spotify, Discord, Teams)

It **never** touches:
- ❌ Documents, Desktop, Downloads
- ❌ Personal files of any kind
- ❌ Installed applications
- ❌ Registry (read-only for startup viewer)

---

## 🔧 Project Structure

```
cleansweep/
├── install.py              ← 📥 One-click installer (the file to share!)
├── app.py                  ← Flask REST API — all cleaning logic
├── run.py                  ← Smart launcher with auto-dependency setup
├── setup.py                ← pip package setup
├── pyproject.toml          ← Modern Python packaging config
├── requirements.txt        ← Python dependencies
├── CleanSweep.bat          ← Windows double-click launcher
├── cleansweep.sh           ← macOS/Linux shell launcher
├── README.md
├── templates/
│   └── index.html          ← Full dark dashboard UI (single file)
└── .github/
    └── workflows/
        └── release.yml     ← Auto-publishes releases on git tag push
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

**Ideas wanted:**
- Brave, Opera, Vivaldi browser cache support
- Package as standalone `.exe` / `.app` / AppImage
- Scheduled/automatic cleaning
- macOS Login Items support
- Cleaning history & stats
- i18n / translations

---

## ❓ FAQ

**Is it safe?**
Yes. CleanSweep only cleans from known junk locations and cannot touch personal files.

**Does it need internet?**
Only on first run to install pip dependencies. Fully offline after that.

**Does it send any data?**
Never. Zero analytics, zero telemetry.

**Can I schedule automatic cleaning?**
Not yet — it's on the roadmap!

---

## 📄 License

MIT — free to use, modify, and distribute.

---

<div align="center">

Made with ❤️ by the open source community

[⭐ Star on GitHub](https://github.com/cleansweep/cleansweep) · [📥 Download](https://github.com/cleansweep/cleansweep/releases/latest)

</div>
