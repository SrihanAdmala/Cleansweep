#!/bin/bash
# CleanSweep launcher for macOS / Linux

echo ""
echo " ══════════════════════════════════════════════════"
echo "   CleanSweep — Open Source PC Cleaner"
echo " ══════════════════════════════════════════════════"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo " ERROR: python3 not found. Please install Python 3."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if running as sudo for deeper cleaning
if [ "$EUID" -eq 0 ]; then
    echo " Running as root — full cleaning enabled"
else
    echo " Running as user — some system-level operations limited"
    echo " For full cleaning: sudo bash $0"
fi
echo ""

cd "$SCRIPT_DIR"
python3 run.py
