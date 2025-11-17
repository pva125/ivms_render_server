# app.py

from flask import Flask, request, jsonify, render_template_string
import datetime, csv, os

app = Flask(__name__)
CSV_FILE = "ivms_data.csv"

# create CSV header if missing
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp","latitude","longitude","speed_kmph","accel_magnitude"])

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

    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
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
    <style>
        body { font-family: Arial; margin: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
        th { background-color: #f2f2f2; }
        #chart-container { width: 100%; height: 400px; margin-top: 20px; }
    </style>
</head>

<body>

<h1>📡 IVMS Real-Time Dashboard</h1>

<h2>Live Data Table</h2>
<table id="data-table">
    <thead>
        <tr>
            <th>Timestamp</th>
            <th>Latitude</th>
            <th>Longitude</th>
            <th>Speed (km/h)</th>
            <th>Accel Magnitude</th>
        </tr>
    </thead>
    <tbody></tbody>
</table>

<h2>Speed & Acceleration Chart</h2>
<div id="chart-container">
    <canvas id="chart"></canvas>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<script>
async function fetchData() {
    const res = await fetch('/latest');
    const data = await res.json();

    // Update table
    const tbody = document.querySelector('#data-table tbody');
    tbody.innerHTML = "";
    data.slice(-20).forEach(row => {
        const tr = `<tr>
            <td>${row.timestamp}</td>
            <td>${row.lat}</td>
            <td>${row.lon}</td>
            <td>${row.speed}</td>
            <td>${row.accel}</td>
        </tr>`;
        tbody.innerHTML += tr;
    });

    // Update chart
    chart.data.labels = data.map(r => r.timestamp.slice(11,19));
    chart.data.datasets[0].data = data.map(r => r.speed);
    chart.data.datasets[1].data = data.map(r => r.accel);
    chart.update();
}

// Chart.js setup
const ctx = document.getElementById('chart');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: "Speed (km/h)",
                data: [],
                borderColor: "blue"
            },
            {
                label: "Accel (m/s²)",
                data: [],
                borderColor: "red"
            }
        ]
    }
});

setInterval(fetchData, 3000);
fetchData();
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
            next(reader)  # skip header
            for row in reader:
                rows.append({
                    "timestamp": row[0],
                    "lat": float(row[1]),
                    "lon": float(row[2]),
                    "speed": float(row[3]),
                    "accel": float(row[4])
                })
    return jsonify(rows[-50:])


if __name__ == '__main__':
    # For local development, host=0.0.0.0 makes it reachable on the LAN
    app.run(host='0.0.0.0', port=5000, debug=True)