#!/usr/bin/env bash
# RamBooster Pro - Linux System Optimizer Launcher
# Compatible with Ubuntu, Debian, Fedora, Arch, Manjaro, Mint, Pop!_OS, openSUSE

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=================================================="
echo "      RAM Booster Pro — Linux Edition v1.0.0      "
echo "=================================================="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is required. Please install python3."
    exit 1
fi

# Check required dependencies
python3 -c "import webview, psutil, PIL" &> /dev/null
if [ $? -ne 0 ]; then
    echo "[INFO] Installing required dependencies (pywebview, psutil, Pillow)..."
    python3 -m pip install pywebview psutil Pillow --break-system-packages 2>/dev/null || python3 -m pip install pywebview psutil Pillow
fi

# Run application with root/pkexec if available for full drop_caches & sysctl control
if [ "$EUID" -ne 0 ]; then
    echo "[INFO] Running RamBooster Pro (User Mode). For root features, run with sudo."
fi

python3 "$DIR/web_app.py" "$@"
