from concurrent import futures
import grpc
import sensor_pb2
import sensor_pb2_grpc
from flask import Flask, request, jsonify
import threading
import asyncio
import websockets
import json
import sys
import datetime

from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
from utils.command_line_utils import CommandLineUtils

cmdData = CommandLineUtils.parse_sample_input_pubsub()

# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))

def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))

# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)

# Callback when the connection successfully connects
def on_connection_success(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionSuccessData)
    print("Connection Successful with return code: {} session present: {}".format(callback_data.return_code, callback_data.session_present))

# Callback when a connection attempt fails
def on_connection_failure(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionFailureData)
    print("Connection failed with error code: {}".format(callback_data.error))

# Callback when a connection has been disconnected or shutdown successfully
def on_connection_closed(connection, callback_data):
    print("Connection closed")

### --- MQTT: Publicar --- ###
def MQTT_publish(sensor_type, data):
    topic = "data/rpm/paciente_id/sensor"
    message = {
    "sensor_type": sensor_type,
    "data": data,
    "timestamp": datetime.datetime.now().isoformat()
    }

    message_json = json.dumps(message)
    print(f"[MQTT] Publicando mensaje a tópico '{topic}': {message_json}")

    try:
        mqtt_connection.publish(
            topic=topic,
            payload=message_json,
            qos=mqtt.QoS.AT_LEAST_ONCE
        )
        print("[MQTT] Mensaje publicado correctamente")

    except Exception as e:
        print(f"[ERROR] Falló publicación MQTT: {e}", flush=True)

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
            #"timestamp": request.timestamp
        })
        MQTT_publish("heart_rate", request.heart_rate)
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
    MQTT_publish("blood_pressure", data)
    return jsonify({"status": "success", "message": "Presión arterial recibida"})

@rest_app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

def serve_rest():
    print("[REST] Servidor REST iniciado en puerto 5000")
    rest_app.run(host='0.0.0.0', port=5000)

### --- WebSocket: Nivel de Glucosa --- ###
async def websocket_server(websocket):
    async for message in websocket:
        data = json.loads(message)
        print(f"[WebSocket] Recibido: Sensor {data['sensor_id']}, Nivel de glucosa recibido: {data}", flush=True)
        sensor_data["glucose_level"].append(data['value'])
        MQTT_publish("glucose_level", data['value'])

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
    # Create the proxy options if the data is present in cmdData
    proxy_options = None
    if cmdData.input_proxy_host is not None and cmdData.input_proxy_port != 0:
        proxy_options = http.HttpProxyOptions(
            host_name=cmdData.input_proxy_host,
            port=cmdData.input_proxy_port)

    # Create a MQTT connection from the command line data
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=cmdData.input_endpoint,
        port=cmdData.input_port,
        cert_filepath=cmdData.input_cert,
        pri_key_filepath=cmdData.input_key,
        ca_filepath=cmdData.input_ca,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=cmdData.input_clientId,
        clean_session=False,
        keep_alive_secs=30,
        http_proxy_options=proxy_options,
        on_connection_success=on_connection_success,
        on_connection_failure=on_connection_failure,
        on_connection_closed=on_connection_closed)
    
    if not cmdData.input_is_ci:
        print(f"Connecting to {cmdData.input_endpoint} with client ID '{cmdData.input_clientId}'...")
    else:
        print("Connecting to endpoint with client ID")
    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    grpc_thread = threading.Thread(target=serve_grpc, daemon=True)
    rest_thread = threading.Thread(target=serve_rest, daemon=True)
    websocket_thread = threading.Thread(target=serve_websocket, daemon=True)

    grpc_thread.start()
    rest_thread.start()
    websocket_thread.start()

    grpc_thread.join()
    rest_thread.join()
    websocket_thread.join()

    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")