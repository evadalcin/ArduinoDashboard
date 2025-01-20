import bson.json_util
import json
import threading
import serial
import time
from pymongo import MongoClient
from datetime import datetime
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

MONGODB_URL = 'mongodb://localhost:27017/'
DATABASE_NAME = 'arduino'
COLLECTION_NAME = 'arduino'
SETTINGS_COLLECTION = 'settings'

ARDUINO_PORT = 'COM7'
BAUD_RATE = 9600

try:
    client = MongoClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    settings_collection = db[SETTINGS_COLLECTION]
except Exception as e:
    print(f"MongoDB connection error: {e}")
    exit(1)

default_settings = {
    'temperatura': True,
    'umidita': True,
    'movimento': True,
    'suono': True,
    'luce': True,
    'distanza': True
}

if not settings_collection.find_one():
    settings_collection.insert_one(default_settings)


def arduino_reader():
    while True:
        try:
            with serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1) as ser:
                print(f"Connected to Arduino on port {ARDUINO_PORT}")

                while True:
                    try:
                        line = ser.readline().decode('utf-8').strip()
                        if line:
                            data = json.loads(line)
                            settings = settings_collection.find_one({}, {'_id': 0})

                            if settings:
                                # Filter data based on enabled sensors
                                filtered_data = {k: v for k, v in data.items() if k in settings and settings[k]}
                                filtered_data['timestamp'] = datetime.now()

                                # Add data validation
                                if validate_sensor_data(filtered_data):
                                    collection.insert_one(filtered_data)
                                    print(f"Saved data: {filtered_data}")
                                else:
                                    print("Invalid sensor data received")

                    except json.JSONDecodeError as e:
                        print(f"JSON parsing error: {e}")
                    except Exception as e:
                        print(f"Error processing Arduino data: {e}")

                    time.sleep(0.1)

        except serial.SerialException as e:
            print(f"Serial connection error: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error in arduino_reader: {e}")
            time.sleep(5)


def validate_sensor_data(data):
    try:
        if 'temperatura' in data and not (-40 <= float(data['temperatura']) <= 80):
            return False
        if 'umidita' in data and not (0 <= float(data['umidita']) <= 100):
            return False
        if 'movimento' in data and data['movimento'] not in ['Rilevato', 'Non rilevato']:
            return False
        if 'suono' in data and not (0 <= int(data['suono']) <= 1023):
            return False
        if 'luce' in data and not (0 <= int(data['luce']) <= 1023):
            return False
        if 'distanza' in data and not (0 <= float(data['distanza']) <= 400):
            return False
        return True
    except (ValueError, TypeError):
        return False


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sensor Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.4.0/p5.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Roboto', sans-serif;
        }

        body {
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
            padding: 2rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .dashboard-header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .dashboard-header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: #60a5fa;
            margin-bottom: 0.5rem;
        }

        .dashboard-header p {
            color: #94a3b8;
            font-size: 1.1rem;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 2rem;
            margin-top: 2rem;
        }

        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }

        .control-panel {
            background: #1e293b;
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        }

        .visualization-panel {
            background: #1e293b;
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        }

        #canvas-container {
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 1.5rem;
            position: relative;
            min-height: 300px;
        }

        #error-message {
            display: none;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(239, 68, 68, 0.9);
            padding: 1rem;
            border-radius: 0.5rem;
            color: white;
        }

        #data-display {
            background: #2d3748;
            border-radius: 0.5rem;
            padding: 1rem;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }

        .data-card {
            background: #374151;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
            transition: transform 0.2s;
        }

        .data-card:hover {
            transform: translateY(-2px);
        }

        .data-card h3 {
            color: #94a3b8;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .data-card .value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #60a5fa;
        }

        .data-card .unit {
            font-size: 0.875rem;
            color: #94a3b8;
            margin-left: 0.25rem;
        }

        .sensor-toggle {
            background: #2d3748;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
        }

        .sensor-toggle:hover {
            background: #374151;
            transform: translateX(5px);
        }

        .sensor-toggle span {
            font-size: 1rem;
            color: #e2e8f0;
        }

        .switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 26px;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #4b5563;
            transition: .4s;
            border-radius: 34px;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 20px;
            width: 20px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background-color: #60a5fa;
        }

        input:checked + .slider:before {
            transform: translateX(24px);
        }

        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            display: none;
        }

        .loading div {
            width: 10px;
            height: 10px;
            background: #60a5fa;
            border-radius: 50%;
            display: inline-block;
            margin: 0 5px;
            animation: bounce 0.5s infinite alternate;
        }

        .loading div:nth-child(2) { animation-delay: 0.1s; }
        .loading div:nth-child(3) { animation-delay: 0.2s; }

        @keyframes bounce {
            to { transform: translateY(-10px); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="dashboard-header">
            <h1>Smart Sensor Dashboard</h1>
        </div>

        <div class="dashboard-grid">
            <div class="control-panel">
                <h2 class="text-xl text-blue-400 mb-4">Sensor Controls</h2>
                <div class="sensor-toggle">
                    <span>Temperature</span>
                    <label class="switch">
                        <input type="checkbox" id="temperatura" checked onchange="updateSensorSettings()">
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="sensor-toggle">
                    <span>Humidity</span>
                    <label class="switch">
                        <input type="checkbox" id="umidita" checked onchange="updateSensorSettings()">
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="sensor-toggle">
                    <span>Movement</span>
                    <label class="switch">
                        <input type="checkbox" id="movimento" checked onchange="updateSensorSettings()">
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="sensor-toggle">
                    <span>Sound</span>
                    <label class="switch">
                        <input type="checkbox" id="suono" checked onchange="updateSensorSettings()">
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="sensor-toggle">
                    <span>Light</span>
                    <label class="switch">
                        <input type="checkbox" id="luce" checked onchange="updateSensorSettings()">
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="sensor-toggle">
                    <span>Distance</span>
                    <label class="switch">
                        <input type="checkbox" id="distanza" checked onchange="updateSensorSettings()">
                        <span class="slider"></span>
                    </label>
                </div>
            </div>

            <div class="visualization-panel">
                <div id="canvas-container">
                    <div class="loading">
                        <div></div>
                        <div></div>
                        <div></div>
                    </div>
                    <div id="error-message"></div>
                </div>
                <div id="data-display"></div>
            </div>
        </div>
    </div>

    <script>
        let tileCount = 20;
        let actStrokeCap;
        let angle = 0;
        let ripples = [];
        let sensorData = {
            temperatura: 0,
            umidita: 0,
            movimento: 'Non rilevato',
            suono: 0,
            luce: 0,
            distanza: 50
        };
        let lastMovementState = false;
        let baseSize = 500;
        let currentSize = baseSize;
        let connectionError = false;
        let retryCount = 0;
        const maxRetries = 5;

        class Ripple {
            constructor() {
                this.x = width / 2;
                this.y = height / 2;
                this.diameter = 0;
                this.alpha = 255;
                this.speed = 15;
            }

            update() {
                this.diameter += this.speed;
                this.alpha = map(this.diameter, 0, width, 255, 0);
                return this.alpha > 0;
            }

            draw() {
                noFill();
                stroke(255, 255, 255, this.alpha);
                strokeWeight(3);
                circle(this.x, this.y, this.diameter);
            }
        }

        function setup() {
            const canvas = createCanvas(baseSize, baseSize);
            canvas.parent('canvas-container');
            actStrokeCap = ROUND;
            frameRate(30);
            angleMode(DEGREES);
        }

        function updateCanvasSize() {
            let distanceNorm = constrain(sensorData.distanza, 0, 50);
            let newSize = map(distanceNorm, 0, 50, baseSize * 0.3, baseSize);

            if (Math.abs(currentSize - newSize) > 1) {
                currentSize = lerp(currentSize, newSize, 0.1);
                resizeCanvas(currentSize, currentSize);
            }
        }

        function showError(message) {
            const errorEl = document.getElementById('error-message');
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }

        function hideError() {
            document.getElementById('error-message').style.display = 'none';
        }

        function showLoading() {
            document.querySelector('.loading').style.display = 'block';
        }

        function hideLoading() {
            document.querySelector('.loading').style.display = 'none';
        }

        function draw() {
            updateCanvasSize();
            clear();
            background(15, 23, 42);
            strokeCap(actStrokeCap);

            if (sensorData.movimento === 'Rilevato' && !lastMovementState) {
                ripples.push(new Ripple());
                setTimeout(() => ripples.push(new Ripple()), 100);
                setTimeout(() => ripples.push(new Ripple()), 200);
            }
            lastMovementState = (sensorData.movimento === 'Rilevato');

            ripples = ripples.filter(ripple => {
                ripple.update();
                ripple.draw();
                return ripple.alpha > 0;
            });

            let tempNorm = map(sensorData.temperatura, 0, 40, 0, 1);
            let humidNorm = map(sensorData.umidita, 0, 100, 0, 1);
            let blueComponent = map(tempNorm, 0, 1, 255, 0);
            let greenComponent = map(humidNorm, 0, 1, 0, 255);

            let soundLevel = map(sensorData.suono, 0, 1023, 0, 50);
            angle += map(sensorData.suono, 0, 1023, 0.1, 2);

            for (let gridY = 0; gridY < tileCount; gridY++) {
                for (let gridX = 0; gridX < tileCount; gridX++) {
                    let posX = width / tileCount * gridX;
                    let posY = height / tileCount * gridY;

                    let waveX = sin(angle + (gridX + gridY) * 10) * soundLevel;
                    let waveY = cos(angle + (gridX + gridY) * 10) * soundLevel;

                    for (let ripple of ripples) {
                        let d = dist(posX, posY, ripple.x, ripple.y);
                        if (d < ripple.diameter && d > ripple.diameter - 50) {
                            let angle = atan2(posY - ripple.y, posX - ripple.x);
                            let push = map(d, ripple.diameter - 50, ripple.diameter, 20, 0);
                            waveX += cos(angle) * push;
                            waveY += sin(angle) * push;
                        }
                    }

                    posX += waveX;
                    posY += waveY;

                    let toggle = int(random(0, 2));
                    let lightIntensity = map(sensorData.luce, 0, 1023, 0.2, 1);

                    stroke(96 * lightIntensity, 165 * lightIntensity, 250 * lightIntensity);
                    strokeWeight(map(sensorData.luce, 0, 1023, 1, 5));

                    if (toggle == 0) {
                        line(posX, posY, posX + width / tileCount, posY + height / tileCount);
                    } else {
                        line(posX, posY + width / tileCount, posX + height / tileCount, posY);
                    }
                }
            }

            updateDataDisplay();
        }

        function updateDataDisplay() {
            const display = document.getElementById('data-display');
            display.innerHTML = `
                <div class="data-card">
                    <h3>Temperature</h3>
                    <div class="value">${sensorData.temperatura.toFixed(1)}<span class="unit">°C</span></div>
                </div>
                <div class="data-card">
                    <h3>Humidity</h3>
                    <div class="value">${sensorData.umidita.toFixed(1)}<span class="unit">
                </span></div>
                </div>
                <div class="data-card">
                    <h3>Movement</h3>
                    <div class="value">${sensorData.movimento}</div>
                </div>
                <div class="data-card">
                    <h3>Sound Level</h3>
                    <div class="value">${sensorData.suono}<span class="unit">dB</span></div>
                </div>
                <div class="data-card">
                    <h3>Light Level</h3>
                    <div class="value">${sensorData.luce}<span class="unit">lux</span></div>
                </div>
                <div class="data-card">
                    <h3>Distance</h3>
                    <div class="value">${sensorData.distanza.toFixed(1)}<span class="unit">cm</span></div>
                </div>
            `;
        }

        async function updateSensorSettings() {
            showLoading();
            const settings = {
                temperatura: document.getElementById('temperatura').checked,
                umidita: document.getElementById('umidita').checked,
                movimento: document.getElementById('movimento').checked,
                suono: document.getElementById('suono').checked,
                luce: document.getElementById('luce').checked,
                distanza: document.getElementById('distanza').checked
            };

            try {
                const response = await fetch('/api/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(settings)
                });

                if (!response.ok) {
                    throw new Error('Failed to update settings');
                }

                hideError();
            } catch (error) {
                console.error('Error updating sensor settings:', error);
                showError('Failed to update sensor settings. Please try again.');
            } finally {
                hideLoading();
            }
        }

        async function loadSensorSettings() {
            showLoading();
            try {
                const response = await fetch('/api/settings');
                if (!response.ok) {
                    throw new Error('Failed to load settings');
                }

                const settings = await response.json();
                for (const [sensor, enabled] of Object.entries(settings)) {
                    const element = document.getElementById(sensor);
                    if (element) {
                        element.checked = enabled;
                    }
                }

                hideError();
            } catch (error) {
                console.error('Error loading sensor settings:', error);
                showError('Failed to load sensor settings. Please refresh the page.');
            } finally {
                hideLoading();
            }
        }

        async function fetchSensorData() {
            try {
                const response = await fetch('/api/data/current');
                if (!response.ok) {
                    throw new Error('Failed to fetch sensor data');
                }

                const data = await response.json();
                sensorData = {
                    temperatura: data.temperatura || 0,
                    umidita: data.umidita || 0,
                    movimento: data.movimento || 'Non rilevato',
                    suono: data.suono || 0,
                    luce: data.luce || 0,
                    distanza: data.distanza || 50
                };

                if (connectionError) {
                    connectionError = false;
                    hideError();
                    retryCount = 0;
                }
            } catch (error) {
                console.error('Error fetching sensor data:', error);
                connectionError = true;
                retryCount++;

                if (retryCount <= maxRetries) {
                    showError(`Connection lost. Retrying... (${retryCount}/${maxRetries})`);
                } else {
                    showError('Connection lost. Please refresh the page.');
                }
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            loadSensorSettings();
            setInterval(fetchSensorData, 100);
        });

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                if (window.fetchInterval) {
                    clearInterval(window.fetchInterval);
                }
            } else {
                window.fetchInterval = setInterval(fetchSensorData, 100);
            }
        });
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/data/current')
def get_current_data():
    try:
        latest_data = collection.find_one(sort=[('timestamp', -1)])
        if latest_data:
            latest_data['_id'] = str(latest_data['_id'])
            return jsonify(latest_data)
        return jsonify({})
    except Exception as e:
        print(f"Error fetching current data: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/settings', methods=['GET'])
def get_settings():
    try:
        settings = settings_collection.find_one({}, {'_id': 0})
        return jsonify(settings or default_settings)
    except Exception as e:
        print(f"Error fetching settings: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/settings', methods=['POST'])
def update_settings():
    try:
        new_settings = request.json
        if not all(isinstance(v, bool) for v in new_settings.values()):
            return jsonify({'error': 'Invalid settings format'}), 400

        settings_collection.replace_one({}, new_settings, upsert=True)
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error updating settings: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def main():
    try:
        arduino_thread = threading.Thread(target=arduino_reader, daemon=True)
        arduino_thread.start()

        app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
    except Exception as e:
        print(f"Main application error: {e}")
    finally:
        print("Application shutting down...")


if __name__ == '__main__':
    main()