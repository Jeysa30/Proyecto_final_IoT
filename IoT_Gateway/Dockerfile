FROM python:3.10-slim

WORKDIR /app

COPY sensor.proto .
COPY IoT_gateway.py .
COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt

# Genera los archivos gRPC
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. sensor.proto

CMD ["python", "IoT_gateway.py"]
