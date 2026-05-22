#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo
echo "======================================"
echo "      SDRForge System Installer"
echo "======================================"
echo

echo "[*] Installing system dependencies..."

sudo apt update

sudo apt install -y \
    python3 \
    python3-pip \
    git \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    python3-dev \
    libffi-dev \
    libssl-dev 

echo
echo "[*] Installing Python requirements system-wide..."

pip install --break-system-packages --upgrade pip setuptools wheel

pip install --break-system-packages -r requirements.txt

echo
echo "======================================"
echo "[+] SDRForge installation complete."
echo "======================================"
echo
echo "Run with:"
echo
echo "python3 SDRForge.py"
echo