# app.py

from flask import Flask, request, jsonify, render_template_string
import datetime, csv, os

app = Flask(__name__)
CSV_FILE = "ivms_data.csv"

# create CSV header if missing
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        # header names (informational only) - actual parsing uses column positions
        writer.writerow(["timestamp","latitude","longitude","speed","accel"])

API_KEY = "MY_SECRET_KEY_123"


@app.route('/')
def index():
    return "IVMS Flask server running."


@app.route('/api/data', methods=['POST'])
def receive():
    # ---- API KEY CHECK ----
    key = request.headers.get("X-API-KEY")
    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(force=True)
    lat = data.get("latitude")
    lon = data.get("longitude")
    speed = data.get("speed")
    accel = data.get("accel")

    ist = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
    timestamp = ist.isoformat()

    with open(CSV_FILE, "a", newline="") as f:
        csv.writer(f).writerow([timestamp, lat, lon, speed, accel])

    print(f"[{timestamp}] {lat},{lon} speed={speed} accel={accel}")
    return jsonify({"status": "ok"}), 200


# -----------------------------------------
# DASHBOARD HTML (served at /dashboard)
# -----------------------------------------
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>IVMS Dashboard</title>

    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>

    <style>

        body {
            font-family: Arial;
            margin: 0;
            padding: 0;
            transition: background 0.3s, color 0.3s;
        }

        /* NAVBAR */
        .navbar {
            width: 100%;
            background: #0d6efd;
            color: white;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 999;
        }

        .navbar-title {
            font-size: 22px;
            font-weight: bold;
        }

        .nav-links a {
            color: white;
            margin-left: 20px;
            text-decoration: none;
            font-size: 16px;
            font-weight: 500;
        }

        #theme-toggle {
            padding: 6px 12px;
            border-radius: 6px;
            border: none;
            background: white;
            color: #0d6efd;
            font-weight: bold;
            cursor: pointer;
        }

        /* MAIN CONTENT CENTERING */
        .content {
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }

        /* DARK MODE */
        body.dark {
            background: #121212;
            color: #e0e0e0;
        }

        body.dark .navbar {
            background: #1f1f1f;
        }

        body.dark #theme-toggle {
            background: #444;
            color: white;
        }

        /* TABLE */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 8px;
            text-align: center;
            word-break: break-word;
        }
        th {
            background: #f2f2f2;
        }
        body.dark th {
            background: #1f1f1f;
            color: white;
        }
        body.dark td {
            background: #1b1b1b;
            border-color: #444;
        }

        /* MAP */
        #map {
            height: 400px;
            width: 100%;
            margin-top: 20px;
            border: 2px solid #ccc;
            border-radius: 10px;
        }

        /* CHART */
        #chart-container {
            height: 400px;
            margin-top: 25px;
        }

        canvas {
            width: 100% !important;
            height: 100% !important;
            display: block;
        }

        /* STATUS CARDS */
        .stat-card {
            flex: 1;
            min-width: 200px;
            padding: 15px;
            border: 1px solid #ccc;
            border-radius: 12px;
            background: white;
            text-align: center;
            transition: 0.3s;
        }

        .stat-card h3 {
            margin-bottom: 10px;
        }

        body.dark .stat-card {
            background: #1f1f1f;
            border-color: #444;
        }

        /* ALERT BOX */
        #alerts-box {
            font-size: 16px;
            background: #fafafa;
        }

        body.dark #alerts-box {
            background: #1b1b1b;
            border-color: #444;
        }

        /* responsive */
        @media (max-width: 700px) {
            .navbar-title { font-size: 18px; }
            .nav-links a { margin-left: 8px; font-size: 14px; }
            .content { padding: 12px; }
        }

    </style>
</head>

<body>

<div class="navbar">
    <div class="navbar-title">📡 IVMS Live Dashboard</div>

    <div class="nav-links">
        <a href="#table">Table</a>
        <a href="#map">Map</a>
        <a href="#chart-section">Charts</a>
    </div>

    <button id="theme-toggle">🌙 Dark Mode</button>
</div>

<div class="content">

<h2 id="table">Live Data Table</h2>
<table id="data-table">
    <thead>
        <tr>
            <th>Timestamp</th>
            <th>Latitude</th>
            <th>Longitude</th>
            <th>Speed (km/h)</th>
            <th>Accel</th>
        </tr>
    </thead>
    <tbody></tbody>
</table>

<h2 id="map">📍 Live GPS Map</h2>
<div id="map"></div>

<h2>Vehicle Status</h2>

<div id="status-cards" style="display:flex; gap:20px; flex-wrap:wrap; margin-top:15px;">

    <div class="stat-card" id="speed-card">
        <h3>Speed</h3>
        <p id="live-speed">0 km/h</p>
    </div>

    <div class="stat-card" id="accel-card">
        <h3>Acceleration</h3>
        <p id="live-accel">0 m/s²</p>
    </div>

    <div class="stat-card" id="time-card">
        <h3>Last Update</h3>
        <p id="live-time">--</p>
    </div>

    <div class="stat-card" id="coord-card">
        <h3>Coordinates</h3>
        <p id="live-coords">-- , --</p>
    </div>

</div>

<h2 style="margin-top:35px;">Alerts</h2>

<div id="alerts-box" style="
     border:1px solid #ccc;
     padding:12px;
     border-radius:10px;
     min-height:60px;
     background:#fafafa;">
     <p id="alert-msg">No alerts</p>
</div>

<!-- Charts heading -->
<h2 id="chart-section">Speed & Acceleration Chart</h2>

<div id="chart-container">
    <canvas id="chart"></canvas>
</div>

</div>

<!-- ChartJS -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<!-- Leaflet JS -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
document.addEventListener("DOMContentLoaded", function () {

    let map = null;
    let marker = null;
    let routeLine = null;
    let routeCoords = [];

    /* DARK MODE */
    const themeBtn = document.getElementById("theme-toggle");

    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark");
        themeBtn.textContent = "☀ Light Mode";
    }

    themeBtn.addEventListener("click", () => {
        document.body.classList.toggle("dark");

        if (document.body.classList.contains("dark")) {
            themeBtn.textContent = "☀ Light Mode";
            localStorage.setItem("theme", "dark");
        } else {
            themeBtn.textContent = "🌙 Dark Mode";
            localStorage.setItem("theme", "light");
        }
    });

    /* MAP INIT */
    function initMap(lat, lon) {
        map = L.map('map').setView([lat, lon], 16);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19
        }).addTo(map);

        marker = L.marker([lat, lon]).addTo(map);
        routeLine = L.polyline([], { color: 'blue' }).addTo(map);

        setTimeout(() => map.invalidateSize(), 200);
    }

    /* CHART SETUP */
    const canvas = document.getElementById('chart');
    const ctx = canvas.getContext('2d');

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: "Speed (km/h)", borderColor: "blue", data: [], fill: false, tension: 0.1 },
                { label: "Accel (m/s²)", borderColor: "red", data: [], fill: false, tension: 0.1 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: {
                x: { display: true },
                y: { display: true, beginAtZero: true }
            }
        }
    });

    /* FETCH DATA */
    async function fetchData() {
        try {
            const res = await fetch('/latest');
            if (!res.ok) return;
            const data = await res.json();
            if (!Array.isArray(data) || data.length === 0) return;

            const latest = data[data.length - 1];

            /* ===== TABLE UPDATE ===== */
            const tbody = document.querySelector('#data-table tbody');
            tbody.innerHTML = "";
            data.slice(-20).forEach(row => {
                tbody.innerHTML += `
                    <tr>
                        <td>${row.timestamp}</td>
                        <td>${row.lat}</td>
                        <td>${row.lon}</td>
                        <td>${row.speed}</td>
                        <td>${row.accel}</td>
                    </tr>`;
            });

            /* ===== CHART UPDATE ===== */
            chart.data.labels = data.map(r => r.timestamp.slice(11,19));
            chart.data.datasets[0].data = data.map(r => r.speed);
            chart.data.datasets[1].data = data.map(r => r.accel);
            chart.update();

            /* ===== UPDATE LIVE STATUS CARDS ===== */
            const lat = parseFloat(latest.lat);
            const lon = parseFloat(latest.lon);
            document.getElementById("live-speed").innerText = latest.speed + " km/h";
            document.getElementById("live-accel").innerText = latest.accel + " m/s²";
            document.getElementById("live-time").innerText = latest.timestamp;
            document.getElementById("live-coords").innerText = lat + " , " + lon;

            /* ===== MAP UPDATE ===== */
            if (!map) {
                initMap(lat, lon);
            } else {
                if (marker) marker.setLatLng([lat, lon]);
                map.panTo([lat, lon]);
                setTimeout(() => map.invalidateSize(), 200);
            }

            /* ===== ALERT LOGIC ===== */
            let alerts = [];

            if (latest.speed > 80) {
                alerts.push("⚠ Overspeeding detected (>80 km/h)");
            }

            if (latest.accel > 5) {
                alerts.push("⚠ Harsh Acceleration");
            }

            if (latest.accel < -4) {
                alerts.push("⚠ Harsh Braking");
            }

            let now = new Date();
            let pktTime = new Date(latest.timestamp);
            let diffSec = (now - pktTime) / 1000;
            if (diffSec > 10) {
                alerts.push("⚠ No data received in last 10 seconds");
            }

            document.getElementById("alert-msg").innerHTML =
                alerts.length === 0 ? "No alerts" : alerts.join("<br>");

            /* ===== ROUTE LINE UPDATE ===== */
            routeCoords.push([lat, lon]);
            if (routeCoords.length > 200) routeCoords.shift();
            if (routeLine) routeLine.setLatLngs(routeCoords);

        } catch (err) {
            console.error("fetchData error:", err);
        }
    }

    // Polling
    setInterval(fetchData, 3000);
    fetchData();

}); // DOMContentLoaded end
</script>

</body>
</html>
"""

@app.route('/dashboard')
def dashboard():
    return render_template_string(dashboard_html)


@app.route('/latest')
def latest():
    rows = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header if present
            for row in reader:
                # guard: skip malformed rows
                if len(row) < 5:
                    continue
                try:
                    rows.append({
                        "timestamp": row[0],
                        "lat": float(row[1]),
                        "lon": float(row[2]),
                        "speed": float(row[3]),
                        "accel": float(row[4])
                    })
                except ValueError:
                    # skip rows that cannot be parsed as floats
                    continue
    return jsonify(rows[-50:])


if __name__ == '_main_':
    # For local development, host=0.0.0.0 makes it reachable on the LAN
    app.run(host='0.0.0.0', port=5000, debug=True)