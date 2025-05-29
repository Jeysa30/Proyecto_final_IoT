import asyncio
import websockets
import random
import json
from datetime import datetime

async def send_glucose_level():
    uri = "ws://iot-gateway:8765"
    sensor_id = "sg_sensor_3"

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                while True:
                    glucose_level = random.randint(70, 180)  # Valores típicos en mg/dL
                    data = {
                        "sensor_id": sensor_id,
                        "value": glucose_level,
                        "unit": "mg/dL",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send(json.dumps(data))
                    print(f"[Sensor] Enviado: {data}", flush=True)
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"[Sensor] Error de conexión: {e}, reintentando en 3 segundos...", flush=True)
            await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(send_glucose_level())
