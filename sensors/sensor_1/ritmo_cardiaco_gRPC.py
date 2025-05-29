import grpc
import time
import random
from datetime import datetime

import sensor_pb2
import sensor_pb2_grpc

def generate_heart_rate():
    return random.randint(60, 100)  # Rango típico

def run():
    channel = grpc.insecure_channel('iot-gateway:50051')
    stub = sensor_pb2_grpc.HeartRateSensorStub(channel)

    while True:
        hr_data = sensor_pb2.HeartRateData(
            sensor_id="hr_sensor_1",
            heart_rate=generate_heart_rate(),
            unit="BPM",
            timestamp=datetime.utcnow().isoformat()
        )

        ack = stub.SendHeartRate(hr_data)
        print(f"[Sensor] Enviado: {hr_data.heart_rate} {hr_data.unit} | Respuesta: {ack.message}", flush=True)
        time.sleep(5)

if __name__ == "__main__":
    run()