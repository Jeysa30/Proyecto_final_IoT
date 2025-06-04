import random
import time
from datetime import datetime
import requests

# Configuración del sensor
SENSOR_ID = "bp_sensor_2"
GATEWAY_URL = "http://iot-gateway:5000"  # Conexión con el endpoint REST del gateway
GATEWAY_HEALTH_URL = f"{GATEWAY_URL}/health"

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

        time.sleep(4) # Envía cada 4 segundos al gateway

if __name__ == '__main__':
    send_to_gateway()