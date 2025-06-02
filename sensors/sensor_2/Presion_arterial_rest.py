import random
import time
from datetime import datetime
import requests
from flask import Flask, jsonify
import threading

# Configuración del sensor
SENSOR_ID = "bp_sensor_2"
GATEWAY_URL = "http://iot-gateway:5000"  # Asumimos que el gateway tendrá un endpoint REST
GATEWAY_HEALTH_URL = f"{GATEWAY_URL}/health"
LOCAL_PORT = 8080  # Puerto para la API local del sensor

app = Flask(__name__)

def generate_blood_pressure():
    """Genera datos simulados de presión arterial"""
    systolic = random.randint(115, 140)  # Presión sistólica (mmHg) 90
    diastolic = random.randint(79, 90)  # Presión diastólica (mmHg) 60
    return {
        "sensor_id": SENSOR_ID,
        "systolic": systolic,
        "diastolic": diastolic,
        "unit": "mmHg",
        "timestamp": datetime.utcnow().isoformat()
    }

def wait_for_gateway():
    """Espera hasta que el gateway esté disponible"""
    print("[Sensor] Esperando a que el IoT Gateway esté disponible...", flush=True)
    while True:
        try:
            response = requests.get(GATEWAY_HEALTH_URL, timeout=3)
            if response.status_code == 200:
                print("[Sensor] ¡Conectado al IoT Gateway!", flush=True)
                return
        except requests.RequestException:
            print("[Sensor] Gateway no disponible aún. Reintentando en 5 segundos...", flush=True)
        time.sleep(5)

def send_to_gateway():
    """Envía datos al gateway periódicamente"""
    while True:
        data = generate_blood_pressure()
        try:
            response = requests.post(f"{GATEWAY_URL}/blood-pressure", json=data, timeout=5)
            print(f"[Sensor] Enviado: {response.status_code} | {data}", flush=True)

        except Exception as e:
            print(f"[Sensor] Error al enviar datos al gateway: {e}. Esperando reconexión...", flush=True)
            wait_for_gateway()

        time.sleep(4)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/data', methods=['GET'])
def get_current_data():
    return jsonify(generate_blood_pressure())

if __name__ == '__main__':
    # Iniciar el hilo para enviar datos al gateway
    threading.Thread(target=send_to_gateway, daemon=True).start()
    
    # Iniciar el servidor Flask
    app.run(host='0.0.0.0', port=LOCAL_PORT)