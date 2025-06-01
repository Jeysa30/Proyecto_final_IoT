CREATE TABLE sensores (
    id SERIAL PRIMARY KEY,
    id_sensor VARCHAR(50),
    tipo_sensor VARCHAR(50),
    valor NUMERIC,
    unidad VARCHAR(20),
    timestamp TIMESTAMP
);

CREATE TABLE actuadores (
    id SERIAL PRIMARY KEY,
    id_actuador VARCHAR(50),
    tipo_actuador VARCHAR(50),
    valor NUMERIC,
    unidad VARCHAR(20),
    timestamp TIMESTAMP
);