from chalice import Chalice
import psycopg2
import os

app = Chalice(app_name='apiRest')

DB_CONFIG = {
    'dbname': 'midb',
    'user': 'postgres',
    'password': 'basedatos',
    'host': '172.31.31.96',
    'port': '5432'
}

@app.route('/')
def index():
    return {'hello': 'world'}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.route('/sensors', methods=['GET'])
def list_sensors():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_sensor, tipo_sensor, valor, unidad, timestamp FROM sensores")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{'id_sensor': r[0], 'tipo': r[1], 'valor': r[2], 'unidad': r[3], 'timestamp': r[4].isoformat()} for r in rows]

@app.route('/sensors', methods=['POST'])
def create_sensor():
    req = app.current_request
    data = req.json_body
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sensores (id_sensor, tipo_sensor, valor, unidad, timestamp) VALUES (%s, %s, %s, %s, NOW())",
        (data['id_sensor'], data['tipo_sensor'], data['valor'], data['unidad'])
    )
    conn.commit()
    cur.close()
    conn.close()
    return {'message': 'Sensor registrado correctamente'}

@app.route('/sensors/{sensor_id}/events', methods=['GET'])
def get_sensor_events(sensor_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT tipo_sensor, valor, unidad, timestamp FROM sensores WHERE id_sensor = %s", (sensor_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{'tipo': r[0], 'valor': r[1], 'unidad': r[2], 'timestamp': r[3].isoformat()} for r in rows]

@app.route('/actuators', methods=['GET'])
def list_actuators():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_actuador, tipo_actuador, valor, unidad, timestamp FROM actuadores")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{'id_actuador': r[0], 'tipo': r[1], 'valor': r[2], 'unidad': r[3], 'timestamp': r[4].isoformat()} for r in rows]

@app.route('/actuators', methods=['POST'])
def create_actuator():
    req = app.current_request
    data = req.json_body
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO actuadores (id_actuador, tipo_actuador, valor, unidad, timestamp) VALUES (%s, %s, %s, %s, NOW())",
        (data['id_actuador'], data['tipo_actuador'], data['valor'], data['unidad'])
    )
    conn.commit()
    cur.close()
    conn.close()
    return {'message': 'Actuador registrado correctamente'}
