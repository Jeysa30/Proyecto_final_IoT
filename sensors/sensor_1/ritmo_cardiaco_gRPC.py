import grpc
import time
import random
from datetime import datetime

import sensor_pb2
import sensor_pb2_grpc

def generate_heart_rate():
    return random.randint(40, 120)  # Rango típico

def wait_for_gateway(channel, stub):
    print("[Sensor] Esperando a que el IoT Gateway esté disponible...", flush=True)
    while True:
        try:
            # Llamado 'vacío' para verificar la conexión (heartbeat)
            grpc.channel_ready_future(channel).result(timeout=5)
            print("[Sensor] ¡Conectado al IoT Gateway!", flush=True)
            return
        except grpc.FutureTimeoutError:
            print("[Sensor] Gateway no disponible aún. Reintentando en 5 segundos...", flush=True)
            time.sleep(5)

def run():
    channel = grpc.insecure_channel('iot-gateway:50051')
    stub = sensor_pb2_grpc.HeartRateSensorStub(channel)

    wait_for_gateway(channel, stub)

    while True:
        hr_data = sensor_pb2.HeartRateData(
            sensor_id="hr_sensor_1",
            heart_rate=generate_heart_rate(),
            unit="BPM",
            timestamp=datetime.utcnow().isoformat()
        )

        try:
            ack = stub.SendHeartRate(hr_data)
            print(f"[Sensor] Enviado: {hr_data.heart_rate} {hr_data.unit} | Respuesta: {ack.message}", flush=True)
        except grpc.RpcError as e:
            print(f"[Sensor] Error al enviar datos: {e}. Reintentando conexión...", flush=True)
            wait_for_gateway(channel, stub)  # Intentamos reconectar
        time.sleep(5)

if __name__ == "__main__":
    run()
