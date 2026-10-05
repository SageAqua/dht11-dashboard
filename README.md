# DHT11 Temperatur-Dashboard für Raspberry Pi

Liest einen DHT11-Sensor aus, speichert die Werte über eine REST-API in einer
SQLite-Datenbank und zeigt sie live in einem Web-Dashboard an.

---

## 1. Hardware & Verkabelung

Benötigt:
- Raspberry Pi (getestet auf Pi 3 Model B und Pi 4 Model B)
- DHT11 Temperatur-/Feuchtigkeitssensor
- 4,7 kΩ Widerstand (Pull-up)
- Breadboard + Jumperkabel

| DHT11 | Raspberry Pi |
|---|---|
| VCC | Pin 1 (3.3V) |
| DATA | Pin 7 (GPIO4) |
| GND | Pin 6 (GND) |

**Wichtig:** Der 4,7 kΩ Pull-up-Widerstand gehört zwischen **VCC und DATA**.
Ohne ihn wird der Sensor meist nicht erkannt.

**Wichtig:** Alles muss auf **einem durchgehenden Breadboard** stecken.
Zwei nebeneinanderliegende Breadboards sind elektrisch NICHT verbunden.

---

## 2. Installation

Dateien auf den Pi kopieren und ausführen:

```bash
unzip dht11-dashboard.zip
cd dht11-dashboard
sudo bash install.sh
```

Das Script erledigt automatisch:
- Systempakete + Python-Bibliotheken installieren
- Projektdateien nach `~/dht11-dashboard/` kopieren
- Zwei systemd-Services anlegen (starten automatisch beim Booten)
- Services starten und Status prüfen

Am Ende wird die Dashboard-URL angezeigt.

---

## 3. Benutzung

**Dashboard im Browser:**
```
http://<pi-ip-adresse>:5000
```

IP-Adresse herausfinden:
```bash
hostname -I
```

**REST-API Endpunkte:**

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/api/readings` | Letzte 50 Messwerte als JSON |
| GET | `/api/readings?limit=10` | Anzahl begrenzen |
| GET | `/api/readings/latest` | Nur der aktuellste Messwert |
| POST | `/api/readings` | Neuen Messwert speichern |

Beispiel POST:
```bash
curl -X POST http://localhost:5000/api/readings \
  -H "Content-Type: application/json" \
  -d '{"temperature": 22.5, "humidity": 48}'
```

---

## 4. Services verwalten

```bash
# Status prüfen
systemctl status sensor-api.service
systemctl status sensor-reader.service

# Live-Ausgabe des Sensors ansehen
journalctl -u sensor-reader.service -f

# Neu starten
sudo systemctl restart sensor-api.service sensor-reader.service

# Stoppen
sudo systemctl stop sensor-api.service sensor-reader.service

# Autostart deaktivieren
sudo systemctl disable sensor-api.service sensor-reader.service
```

---

## 5. Manuell starten (ohne Services, zum Testen)

Zwei Terminals nötig:

```bash
# Terminal 1
cd ~/dht11-dashboard
sudo python3 api.py

# Terminal 2
cd ~/dht11-dashboard
sudo python3 temperatur.py
```

---

## 6. Troubleshooting

### "DHT sensor not found, check wiring"

In dieser Reihenfolge prüfen:

1. **Pull-up-Widerstand vorhanden?** 4,7 kΩ zwischen VCC und DATA.
2. **Alles auf einem Breadboard?** Zwei Boards sind nicht verbunden.
3. **Pin-Zuordnung richtig?** Beine des DHT11 von der Gitterseite aus:
   VCC – DATA – NC – GND.
4. **GPIO4 testen:**
   ```bash
   python3 -c "
   import digitalio, board
   pin = digitalio.DigitalInOut(board.D4)
   pin.direction = digitalio.Direction.INPUT
   for i in range(10): print(pin.value)
   "
   ```
   - Immer `True` → Pull-up funktioniert
   - Immer `False` → Kurzschluss / DATA liegt auf GND
   - Wechselt wild → Pull-up fehlt oder Verbindung unterbrochen
5. **Sensor defekt.** DHT11-Billigsensoren fallen häufig aus.
   Wenn alle Punkte oben stimmen: anderen Sensor testen.

### Dashboard nicht erreichbar

```bash
systemctl status sensor-api.service
journalctl -u sensor-api.service -n 30
```

Prüfen ob der Port belegt ist:
```bash
sudo ss -tlnp | grep 5000
```

### Chart springt stark

Ist bereits gelöst: feste Achsenbereiche (10–40 °C, 0–100 %) und
deaktivierte Animation. Der DHT11 hat nur 1 °C Auflösung, kleine
Schwankungen sind normal.

---

## 7. Dateien

| Datei | Zweck |
|---|---|
| `api.py` | Flask REST-API + Dashboard + SQLite |
| `temperatur.py` | Liest DHT11 aus, sendet per POST an API |
| `install.sh` | Automatische Installation + systemd-Setup |
| `sensordata.db` | SQLite-Datenbank (wird automatisch erstellt) |

---

## 8. Technischer Aufbau

```
DHT11 Sensor
     │  (GPIO4, 1-Wire-ähnliches Protokoll)
     ▼
temperatur.py  ──POST /api/readings──►  api.py (Flask)
                                            │
                                            ▼
                                      sensordata.db (SQLite)
                                            │
                                            ▼
Browser  ◄──GET /api/readings (JSON)──  Dashboard (HTML/Chart.js)
```
