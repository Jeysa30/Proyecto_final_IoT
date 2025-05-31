import asyncio
import websockets
import random
import json
from datetime import datetime

async def generate_glucose_data(sensor_id):
    """Genera un paquete de datos simulados de glucosa"""
    glucose_level = random.randint(70, 180)
    return json.dumps({
        "sensor_id": sensor_id,
        "value": glucose_level,
        "unit": "mg/dL",
        "timestamp": datetime.utcnow().isoformat()
    })

async def send_glucose_level():
    uri = "ws://iot-gateway:8765"
    sensor_id = "sg_sensor_3"

    print("[Sensor] Iniciando sensor de glucosa...", flush=True)

    while True:
        try:
            print("[Sensor] Intentando conectar al IoT Gateway...", flush=True)
            async with websockets.connect(uri) as websocket:
                print("[Sensor] ¡Conectado al IoT Gateway!", flush=True)
                while True:
                    data = await generate_glucose_data(sensor_id)
                    await websocket.send(data)
                    print(f"[Sensor] Enviado: {data}", flush=True)
                    await asyncio.sleep(2)
        except (ConnectionRefusedError, websockets.exceptions.InvalidURI,
                websockets.exceptions.InvalidHandshake,
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.WebSocketException) as e:
            print(f"[Sensor] Error de conexión WebSocket: {e}, reintentando en 3 segundos...", flush=True)
            await asyncio.sleep(3)
        except Exception as e:
            print(f"[Sensor] Error inesperado: {e}, reintentando en 3 segundos...", flush=True)
            await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(send_glucose_level())
