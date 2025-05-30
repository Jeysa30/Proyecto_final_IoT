FROM python:3.10-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    python3-dev \
    libssl-dev \
    libffi-dev \
    libprotobuf-dev \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*
    
COPY sensor.proto .
COPY IoT_gateway.py .
COPY requirements.txt .
COPY start.sh .
COPY Gateway_IoT_Salud-Policy .
COPY Gateway_IoT_Salud.cert.pem .
COPY Gateway_IoT_Salud.private.key .
COPY Gateway_IoT_Salud.public.key .

RUN pip install --no-cache-dir -r requirements.txt

# Genera los archivos gRPC
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. sensor.proto

RUN chmod +x start.sh
CMD ["./start.sh"]
