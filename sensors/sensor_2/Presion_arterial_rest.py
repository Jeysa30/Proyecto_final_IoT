import random
import time
import requests
from flask import Flask, jsonify
import threading

# Configuración del sensor
SENSOR_ID = "bp_sensor_2"
GATEWAY_URL = "http://iot-gateway:5000"  # Asumimos que el gateway tendrá un endpoint REST
LOCAL_PORT = 8080  # Puerto para la API local del sensor

app = Flask(__name__)

def generate_blood_pressure():
    """Genera datos simulados de presión arterial"""
    systolic = random.randint(90, 140)  # Presión sistólica (mmHg)
    diastolic = random.randint(60, 90)  # Presión diastólica (mmHg)
    heart_rate = random.randint(60, 100)  # Frecuencia cardíaca (bpm)
    return {
        "systolic": systolic,
        "diastolic": diastolic,
        "heart_rate": heart_rate,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def send_to_gateway():
    """Envía datos al gateway periódicamente"""
    while True:
        try:
            data = generate_blood_pressure()
            response = requests.post(f"{GATEWAY_URL}/blood-pressure", json=data)
            print(f"Datos enviados al gateway. Respuesta: {response.status_code}", flush=True)
        except Exception as e:
            print(f"Error al enviar datos al gateway: {e}")

        
        time.sleep(10)  # Enviar cada 30 segundos

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