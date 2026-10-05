#!/usr/bin/env python3
"""
Liest den DHT11-Sensor aus und sendet die Werte per POST an die lokale REST-API.

Verkabelung (Standard):
  DHT11 VCC  -> Pi Pin 1  (3.3V)
  DHT11 DATA -> Pi Pin 7  (GPIO4)
  DHT11 GND  -> Pi Pin 6  (GND)
  4,7 kOhm Pull-up-Widerstand zwischen VCC und DATA
"""

import time

import board
import adafruit_dht
import requests

# GPIO-Pin des DATA-Anschlusses (board.D4 = GPIO4 = Pi Pin 7)
SENSOR_PIN = board.D4

# Messintervall in Sekunden (DHT11 braucht mindestens 2 Sekunden)
INTERVAL = 2.0

API_URL = "http://localhost:5000/api/readings"

dhtDevice = adafruit_dht.DHT11(SENSOR_PIN, use_pulseio=False)


def send_to_api(temperature, humidity):
    try:
        requests.post(
            API_URL,
            json={"temperature": temperature, "humidity": humidity},
            timeout=3,
        )
    except requests.exceptions.RequestException as err:
        print(f"API nicht erreichbar: {err}")


def main():
    print("DHT11 Messung gestartet. Beenden mit Strg+C.")
    while True:
        try:
            temperature_c = dhtDevice.temperature
            humidity = dhtDevice.humidity

            if temperature_c is not None and humidity is not None:
                print(f"Temp: {temperature_c:.1f} C    Feuchte: {humidity:.0f} %")
                send_to_api(temperature_c, humidity)

        except RuntimeError as error:
            # Lesefehler sind bei DHT-Sensoren normal, einfach weiter versuchen
            print(f"Lesefehler: {error.args[0]}")
        except Exception as error:
            dhtDevice.exit()
            raise error

        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMessung beendet.")
        dhtDevice.exit()
