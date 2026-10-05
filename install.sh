#!/bin/bash
#
# Automatische Installation: DHT11 Sensor + REST-API + Dashboard
# Aufruf:  sudo bash install.sh
#

set -e

echo "=============================================="
echo " DHT11 Dashboard - Installation"
echo "=============================================="
echo

# --- Pruefen ob als root ausgefuehrt --------------------------------------
if [ "$EUID" -ne 0 ]; then
  echo "FEHLER: Bitte mit sudo starten:  sudo bash install.sh"
  exit 1
fi

# --- Zielbenutzer und Zielverzeichnis bestimmen ---------------------------
TARGET_USER="${SUDO_USER:-pi}"
TARGET_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)
INSTALL_DIR="$TARGET_HOME/dht11-dashboard"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Benutzer:        $TARGET_USER"
echo "[*] Installationsort: $INSTALL_DIR"
echo

# --- Systempakete ---------------------------------------------------------
echo "[1/6] Systempakete aktualisieren und installieren ..."
apt-get update -qq
apt-get install -y -qq python3-pip libgpiod3 || apt-get install -y -qq python3-pip libgpiod2 || true

# --- Python-Bibliotheken --------------------------------------------------
echo "[2/6] Python-Bibliotheken installieren ..."
pip3 install --break-system-packages -q \
  adafruit-circuitpython-dht \
  flask \
  requests

# --- Dateien kopieren -----------------------------------------------------
echo "[3/6] Projektdateien nach $INSTALL_DIR kopieren ..."
mkdir -p "$INSTALL_DIR"

if [ "$SCRIPT_DIR" != "$INSTALL_DIR" ]; then
  cp "$SCRIPT_DIR/api.py" "$INSTALL_DIR/"
  cp "$SCRIPT_DIR/temperatur.py" "$INSTALL_DIR/"
  cp "$SCRIPT_DIR/README.md" "$INSTALL_DIR/" 2>/dev/null || true
else
  echo "    Dateien befinden sich bereits im Zielverzeichnis - Kopieren uebersprungen."
fi

chown -R "$TARGET_USER":"$TARGET_USER" "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/api.py" "$INSTALL_DIR/temperatur.py"

# --- systemd Service: API -------------------------------------------------
echo "[4/6] systemd-Service fuer API/Dashboard anlegen ..."
cat > /etc/systemd/system/sensor-api.service <<EOF
[Unit]
Description=DHT11 REST-API und Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 -u $INSTALL_DIR/api.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# --- systemd Service: Sensor ---------------------------------------------
echo "[5/6] systemd-Service fuer Sensor-Auslesung anlegen ..."
cat > /etc/systemd/system/sensor-reader.service <<EOF
[Unit]
Description=DHT11 Sensor auslesen und an API senden
After=sensor-api.service
Requires=sensor-api.service

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 -u $INSTALL_DIR/temperatur.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# --- Services aktivieren --------------------------------------------------
echo "[6/6] Services aktivieren und starten ..."
systemctl daemon-reload
systemctl enable --now sensor-api.service
sleep 2
systemctl enable --now sensor-reader.service
sleep 3

# --- Ergebnis -------------------------------------------------------------
IP=$(hostname -I | awk '{print $1}')

echo
echo "=============================================="
echo " Installation abgeschlossen"
echo "=============================================="
echo
echo " Dashboard:      http://$IP:5000"
echo " REST-API (GET): http://$IP:5000/api/readings"
echo
echo " Status pruefen:"
echo "   systemctl status sensor-api.service"
echo "   systemctl status sensor-reader.service"
echo
echo " Live-Ausgabe des Sensors:"
echo "   journalctl -u sensor-reader.service -f"
echo
echo "----------------------------------------------"
systemctl is-active --quiet sensor-api.service \
  && echo " [OK]   API laeuft" \
  || echo " [WARN] API laeuft NICHT - pruefe: journalctl -u sensor-api.service -n 30"
systemctl is-active --quiet sensor-reader.service \
  && echo " [OK]   Sensor-Reader laeuft" \
  || echo " [WARN] Sensor-Reader laeuft NICHT - pruefe: journalctl -u sensor-reader.service -n 30"
echo "----------------------------------------------"
echo
