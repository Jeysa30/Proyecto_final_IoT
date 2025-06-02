from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
import sys
import threading
import psycopg2
import json
from utils.command_line_utils import CommandLineUtils

cmdData = CommandLineUtils.parse_sample_input_pubsub()

received_count = 0
received_all_event = threading.Event()

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

# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    global received_count
    print("Received message from topic '{}': {}".format(topic, payload))

    try:
        data = json.loads(payload.decode())

        # JSON tiene sensor_id, valor, timestamp
        sensor_type = data.get("sensor_type")
        sensor_info = data.get("data", {})
        sensor_id = sensor_info.get("sensor_id")
        unit = sensor_info.get("unit")
        timestamp = sensor_info.get("timestamp")

        if sensor_type == "heart_rate":
            value = sensor_info.get("heart_rate")
        elif sensor_type == "glucose_level":
            value = sensor_info.get("value")
        elif sensor_type == "blood_pressure":
            systolic = sensor_info.get("systolic")
            diastolic = sensor_info.get("diastolic")
            value = f"systolic: {systolic}/diastolic: {diastolic}" 

        # Inserta en la base de datos
        cursor.execute(
            "INSERT INTO sensores (id_sensor, tipo_sensor, valor,unidad, timestamp) VALUES (%s, %s, %s, %s, %s)",
            (sensor_id, sensor_type, value, unit, timestamp)
        )
        conn.commit()
        print("Datos insertados en la base de datos.")

    except Exception as e:
        conn.rollback()
        print("[ERROR] al procesar mensaje o insertar en DB:", e)

    received_count += 1
    if received_count == cmdData.input_count:
        received_all_event.set()

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

    # Guardar en la base de datos
    conn = psycopg2.connect(
        host="172.31.31.96",
        port="5432",
        database="midb",
        user="postgres",
        password="basedatos"
    )
    cursor = conn.cursor()

    # Suscripción al tópico MQTT
    topic = "rpm/hospital/piso_2/#"
    print("Subscribing to topic '{}'...".format(topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))

    received_all_event.wait()
    print("{} message(s) received.".format(received_count))

    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")