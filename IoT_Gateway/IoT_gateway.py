import paho.mqtt.client as mqtt
from concurrent import futures
import grpc
import sensor_pb2
import sensor_pb2_grpc
from flask import Flask, request, jsonify
import threading
import asyncio
import websockets
import json
import datetime 

### GRPC ###

class TemperatureSensorServicer(sensor_pb2_grpc.TemperatureSensorServicer):
    def SendTemperature(self, request, context):
        #print(f"[gRPC] Recibido: Sensor {request.sensor_id}, Temp: {request.temperature}°C")
        print(f"[gRPC] Received from {request.sensor_id}: {request.temperature}°C at {request.timestamp}", flush=True)
        sensor_data["temperature"].append(request.temperature)
        return sensor_pb2.Acknowledgement(message="Temperatura recibida correctamente.")

def serve_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    sensor_pb2_grpc.add_TemperatureSensorServicer_to_server(TemperatureSensorServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Servidor gRPC en puerto 50051...")
    server.start()
    server.wait_for_termination()

### REST ### 

# Configuración del servidor REST
rest_app = Flask(__name__)

@rest_app.route('/blood-pressure', methods=['POST'])

def handle_blood_pressure():
    data = request.json
    print(f"[REST] Received blood pressure data: {data}", flush=True)
    sensor_data["blood_pressure"].append(data)
    return jsonify({"status": "success", "message": "Blood pressure data received"})


@rest_app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

def serve_rest():
    rest_app.run(host='0.0.0.0', port=5000)

### WEBSOCKET ###

# --- Websocket Sensor ---
async def websocket_server(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        print(f"[WebSocket] Recibido: Sensor {data['sensor']}, BPM: {data['value']}", flush=True)
        sensor_data["heart_rate"].append(data['value'])

def serve_websocket():
    async def start_server():
        print("[WebSocket] Servidor iniciado en puerto 8765")
        async with websockets.serve(websocket_server, "0.0.0.0", 8765):
            await asyncio.Future()  # run forever

    asyncio.run(start_server())

### MQTT ###
# --- Configuración MQTT ---
MQTT_BROKER = "mosquitto"  # Nombre del servicio en Docker
MQTT_PORT = 1883
MQTT_TOPIC = "iot/health_data"

# Almacenamiento de datos (ejemplo)
sensor_data = {
    "temperature": [],
    "blood_pressure": [],
    "heart_rate": []
}


# --- Cliente MQTT ---
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 180)

# MQTT - Publicador de datos agrupados
def publish_to_mqtt():
    """Publica datos agrupados a MQTT periódicamente"""
    while True:
        threading.Event().wait(15)

        if not (sensor_data["temperature"] or sensor_data["blood_pressure"] or sensor_data["blood_pressure"]):
            continue  # No hay datos que publicar aún

        avg_temp = (
            sum(sensor_data["temperature"]) / len(sensor_data["temperature"])
            if sensor_data["temperature"] else 0
        )
        last_bp = (
            sensor_data["blood_pressure"][-1]
            if sensor_data["blood_pressure"] else {"systolic": None, "diastolic": None, "heart_rate": None}
        )

        payload = {
            "avg_temperature": round(avg_temp, 2),
            "last_blood_pressure": {
                "systolic": last_bp.get("systolic"),
                "diastolic": last_bp.get("diastolic"),
                "heart_rate": last_bp.get("heart_rate")
            },
            "timestamp": datetime.datetime.now().isoformat()
        }

        mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))
        print(f"[MQTT] Publishedd: {payload}", flush=True)

        # Limpiar datos acumulados después de publicar
        sensor_data["temperature"].clear()
        sensor_data["blood_pressure"].clear()
        sensor_data["heart_rate"].clear()



if __name__ == '__main__':
    # Iniciar servidores en hilos separados
    import threading
    threading.Thread(target=publish_to_mqtt, daemon=True).start()
    
    grpc_thread = threading.Thread(target=serve_grpc, daemon=True)
    rest_thread = threading.Thread(target=serve_rest, daemon=True)
    websocket_thread = threading.Thread(target=serve_websocket, daemon=True)

    grpc_thread.start()
    rest_thread.start()
    websocket_thread.start()

    
    grpc_thread.join()
    rest_thread.join()
    websocket_thread.join()