#!/usr/bin/env bash
# Build Script to compile RamBooster Pro into a standalone Linux Binary via PyInstaller

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "[BUILD] Building RamBooster Pro standalone Linux executable..."

pip install pyinstaller pywebview psutil Pillow --break-system-packages 2>/dev/null || pip install pyinstaller pywebview psutil Pillow

python3 -m PyInstaller \
    --noconfirm \
    --onefile \
    --windowed \
    --name "RamBoosterPro-Linux" \
    --add-data "ram_booster:ram_booster" \
    --add-data "web:web" \
    --hidden-import webview \
    --hidden-import psutil \
    --hidden-import PIL \
    --clean \
    web_app.py

echo "[SUCCESS] Linux executable built at dist/RamBoosterPro-Linux"
