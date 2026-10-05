#!/bin/bash
set -e

echo "=============================================="
echo " DHT11 Dashboard - Schnellinstallation"
echo "=============================================="
echo

TARGET_USER="${SUDO_USER:-pi}"
TARGET_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)
INSTALL_DIR="$TARGET_HOME/dht11-dashboard"

apt-get update -qq
apt-get install -y -qq git

echo "[1/3] Dashboard herunterladen ..."

if [ -d "$INSTALL_DIR/.git" ]; then
    sudo -u "$TARGET_USER" git -C "$INSTALL_DIR" pull
else
    rm -rf "$INSTALL_DIR"

    sudo -u "$TARGET_USER" git clone \
        https://github.com/DEIN-GITHUB-NAME/dht11-dashboard.git \
        "$INSTALL_DIR"
fi

echo "[2/3] Installation starten ..."
cd "$INSTALL_DIR"
bash install.sh

echo
echo "[3/3] Fertig."
