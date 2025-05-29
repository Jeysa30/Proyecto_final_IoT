from concurrent import futures
import grpc
import sensor_pb2
import sensor_pb2_grpc
from flask import Flask, request, jsonify
import threading
import asyncio
import websockets
import json

### --- Almacenamiento Temporal de Datos --- ###
sensor_data = {
    "heart_rate": [],
    "blood_pressure": [],
    "glucose_level": []
}

### --- GRPC: Ritmo Cardiaco --- ###
class HeartRateSensorServicer(sensor_pb2_grpc.HeartRateSensorServicer):
    def SendHeartRate(self, request, context):
        print(f"[gRPC] Ritmo cardíaco recibido: {request.heart_rate} {request.unit} de {request.sensor_id} a las {request.timestamp}", flush=True)
        sensor_data["heart_rate"].append({
            "sensor_id": request.sensor_id,
            "heart_rate": request.heart_rate,
            "unit": request.unit,
            "timestamp": request.timestamp
        })
        return sensor_pb2.Acknowledgement(message="Ritmo cardíaco recibido correctamente.")

def serve_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    sensor_pb2_grpc.add_HeartRateSensorServicer_to_server(HeartRateSensorServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("[gRPC] Servidor iniciado en puerto 50051...", flush=True)
    server.start()
    server.wait_for_termination()

### --- REST: Presión Arterial --- ###
rest_app = Flask(__name__)

@rest_app.route('/blood-pressure', methods=['POST'])
def handle_blood_pressure():
    data = request.json
    print(f"[REST] Presión arterial recibida: {data}", flush=True)
    sensor_data["blood_pressure"].append(data)
    return jsonify({"status": "success", "message": "Presión arterial recibida"})

@rest_app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

def serve_rest():
    rest_app.run(host='0.0.0.0', port=5000)

### --- WebSocket: Nivel de Glucosa --- ###
async def websocket_server(websocket):

    async for message in websocket:
        data = json.loads(message)
        print(f"[WebSocket] Recibido: Sensor {data['sensor_id']}, Nivel de glucosa recibido: {data}", flush=True)
        sensor_data["glucose_level"].append(data['value'])

def serve_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start_server():
        print("[WebSocket] Servidor iniciado en puerto 8765")
        async with websockets.serve(websocket_server, "0.0.0.0", 8765):
            await asyncio.Future()

    loop.run_until_complete(start_server())
    loop.run_forever()

### --- Inicio de servidores --- ###
if __name__ == '__main__':
    grpc_thread = threading.Thread(target=serve_grpc, daemon=True)
    rest_thread = threading.Thread(target=serve_rest, daemon=True)
    websocket_thread = threading.Thread(target=serve_websocket, daemon=True)

    grpc_thread.start()
    rest_thread.start()
    websocket_thread.start()

    grpc_thread.join()
    rest_thread.join()
    websocket_thread.join()