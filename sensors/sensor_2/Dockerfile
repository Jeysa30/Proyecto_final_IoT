FROM python:3.10-slim

WORKDIR /app

COPY Presion_arterial_rest.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "Presion_arterial_rest.py"]