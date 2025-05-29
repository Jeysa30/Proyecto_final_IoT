FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
COPY nivel_glucosa_websocket.py .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "nivel_glucosa_websocket.py"]
