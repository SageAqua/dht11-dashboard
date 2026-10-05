#!/usr/bin/env python3
"""
REST-API + Dashboard fuer DHT11-Sensordaten.

Endpunkte:
  POST /api/readings        -> neuen Messwert speichern (JSON: temperature, humidity)
  GET  /api/readings        -> letzte 50 Messwerte als JSON
  GET  /api/readings/latest -> aktuellster Messwert als JSON
  GET  /                    -> Dashboard (HTML)
"""

import os
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "sensordata.db")


def init_db():
    conn = sqlite3.connect(DB)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL
        )"""
    )
    conn.commit()
    conn.close()


@app.route("/api/readings", methods=["POST"])
def add_reading():
    data = request.get_json(silent=True)
    if not data or "temperature" not in data or "humidity" not in data:
        return jsonify({"error": "temperature und humidity erforderlich"}), 400

    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO readings (timestamp, temperature, humidity) VALUES (?, ?, ?)",
        (datetime.now().isoformat(), data["temperature"], data["humidity"]),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 201


@app.route("/api/readings", methods=["GET"])
def get_readings():
    limit = request.args.get("limit", default=50, type=int)
    conn = sqlite3.connect(DB)
    cur = conn.execute(
        "SELECT timestamp, temperature, humidity FROM readings ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = [
        {"timestamp": r[0], "temperature": r[1], "humidity": r[2]}
        for r in cur.fetchall()
    ]
    conn.close()
    return jsonify(rows)


@app.route("/api/readings/latest", methods=["GET"])
def get_latest():
    conn = sqlite3.connect(DB)
    cur = conn.execute(
        "SELECT timestamp, temperature, humidity FROM readings ORDER BY id DESC LIMIT 1"
    )
    row = cur.fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "keine Daten vorhanden"}), 404
    return jsonify({"timestamp": row[0], "temperature": row[1], "humidity": row[2]})


@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Temperatur Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    background: radial-gradient(circle at top, #1a1f2e 0%, #0d1017 100%);
    color: #e8e8ec;
    margin: 0;
    padding: 32px 20px;
    min-height: 100vh;
  }
  .wrap { max-width: 900px; margin: 0 auto; }
  h1 { text-align:center; font-size:1.5em; font-weight:600; color:#9aa5b8; margin-bottom:22px; letter-spacing:0.5px; }
  .status { display:flex; justify-content:center; align-items:center; gap:8px; margin-bottom:24px; font-size:0.85em; color:#6b7488; }
  .dot { width:8px; height:8px; border-radius:50%; background:#4ade80; box-shadow:0 0 8px #4ade80; animation:pulse 2s infinite; }
  .dot.off { background:#f97362; box-shadow:0 0 8px #f97362; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
  .cards { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:24px; }
  @media (max-width:600px){ .cards{ grid-template-columns:1fr; } }
  .card {
    background:linear-gradient(145deg,#1e2433,#161b26);
    border:1px solid #2a3142; border-radius:20px;
    padding:26px 20px; text-align:center;
    box-shadow:0 8px 24px rgba(0,0,0,0.3);
  }
  .card .value { font-size:3em; font-weight:700; line-height:1; margin:4px 0; }
  .card .label { color:#6b7488; font-size:0.8em; text-transform:uppercase; letter-spacing:1px; }
  .temp .value { color:#f97362; }
  .hum .value { color:#5cc8f2; }
  .chart-card {
    background:linear-gradient(145deg,#1e2433,#161b26);
    border:1px solid #2a3142; border-radius:20px;
    padding:20px; margin-bottom:24px;
  }
  .chart-card h3 { margin:0 0 14px 4px; font-size:0.9em; color:#9aa5b8; font-weight:600; }
  table { width:100%; border-collapse:collapse; background:#161b26; border-radius:14px; overflow:hidden; }
  th, td { padding:10px 16px; text-align:left; font-size:0.9em; }
  th { background:#1e2433; color:#6b7488; font-weight:600; text-transform:uppercase; font-size:0.72em; letter-spacing:0.5px; }
  tr:nth-child(even) { background:rgba(255,255,255,0.02); }
  td { color:#c2c8d4; border-top:1px solid #232a38; }
  .updated { text-align:center; color:#4a5262; font-size:0.8em; margin-top:16px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Temperatur Dashboard</h1>
  <div class="status"><span class="dot" id="dot"></span> <span id="statusText">Live verbunden</span></div>

  <div class="cards">
    <div class="card temp">
      <div class="value" id="temp">--</div>
      <div class="label">Temperatur &deg;C</div>
    </div>
    <div class="card hum">
      <div class="value" id="hum">--</div>
      <div class="label">Luftfeuchtigkeit %</div>
    </div>
  </div>

  <div class="chart-card">
    <h3>Verlauf</h3>
    <canvas id="chart" height="90"></canvas>
  </div>

  <table>
    <thead><tr><th>Zeit</th><th>Temperatur</th><th>Feuchte</th></tr></thead>
    <tbody id="history"></tbody>
  </table>

  <div class="updated" id="updated">wird geladen ...</div>
</div>

<script>
const ctx = document.getElementById('chart').getContext('2d');
const chart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      { label: 'Temperatur C', data: [], borderColor: '#f97362',
        backgroundColor: 'rgba(249,115,98,0.08)', cubicInterpolationMode: 'monotone',
        fill: true, pointRadius: 0, borderWidth: 2, yAxisID: 'y' },
      { label: 'Feuchte %', data: [], borderColor: '#5cc8f2',
        backgroundColor: 'rgba(92,200,242,0.08)', cubicInterpolationMode: 'monotone',
        fill: true, pointRadius: 0, borderWidth: 2, yAxisID: 'y1' }
    ]
  },
  options: {
    responsive: true,
    animation: false,
    interaction: { mode: 'index', intersect: false },
    plugins: { legend: { labels: { color: '#9aa5b8' } } },
    scales: {
      x: { ticks: { color:'#4a5262', maxTicksLimit:8 }, grid: { color:'#1e2433' } },
      y: { position:'left', min:10, max:40, ticks:{ color:'#f97362', stepSize:5 },
           grid:{ color:'#1e2433' }, title:{ display:true, text:'Temperatur C', color:'#f97362' } },
      y1:{ position:'right', min:0, max:100, ticks:{ color:'#5cc8f2', stepSize:20 },
           grid:{ display:false }, title:{ display:true, text:'Feuchte %', color:'#5cc8f2' } }
    }
  }
});

async function update() {
  try {
    const res = await fetch('/api/readings');
    const data = await res.json();

    document.getElementById('dot').classList.remove('off');
    document.getElementById('statusText').innerText = 'Live verbunden';

    if (data.length === 0) {
      document.getElementById('updated').innerText = 'Noch keine Messwerte vorhanden.';
      return;
    }

    document.getElementById('temp').innerText = data[0].temperature.toFixed(1);
    document.getElementById('hum').innerText  = data[0].humidity.toFixed(0);

    const chrono = [...data].reverse();
    chart.data.labels = chrono.map(r => new Date(r.timestamp).toLocaleTimeString());
    chart.data.datasets[0].data = chrono.map(r => r.temperature);
    chart.data.datasets[1].data = chrono.map(r => r.humidity);
    chart.update('none');

    document.getElementById('history').innerHTML = data.slice(0, 15).map(r =>
      '<tr><td>' + new Date(r.timestamp).toLocaleTimeString() +
      '</td><td>' + r.temperature.toFixed(1) + ' C' +
      '</td><td>' + r.humidity.toFixed(0) + ' %</td></tr>'
    ).join('');

    document.getElementById('updated').innerText =
      'Letztes Update: ' + new Date().toLocaleTimeString();
  } catch (e) {
    document.getElementById('dot').classList.add('off');
    document.getElementById('statusText').innerText = 'Keine Verbindung';
    document.getElementById('updated').innerText = 'Server nicht erreichbar ...';
  }
}
update();
setInterval(update, 3000);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
