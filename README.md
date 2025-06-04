# Proyecto Final: Aplicación IoT con AWS 

### Integrantes 

- Valeria Fernanda Gustin Martinez
- Jeysa Nahara Blandon Martinez

## Descripción

Este proyecto consiste en una solución básica de IoT utilizando servicios de AWS. Se simulan sensores que publican datos por MQTT hacia AWS IoT Core. Los datos son recibidos por un subscriber en una instancia EC2, almacenados en una base de datos PostgreSQL, y gestionados a través de una API REST creada con AWS Chalice. También se configuran notificaciones automáticas usando AWS IoT Rules y SNS.

## Componentes principales

- Simulación de sensores con MQTT.
- AWS IoT Core para recepción y enrutamiento de mensajes.
- Instancia EC2 con un subscriber que guarda los eventos en PostgreSQL.
- API REST con AWS Chalice para interactuar con sensores, actuadores y eventos.
- Notificaciones por correo usando AWS SNS y reglas de IoT.
- Modelo estrella representando un proceso del sector elegido.

## Cómo ejecutar

1. **Simulador de sensores**:
   - Ejecutar el script Python que publica en los topics MQTT configurados.
2. **Subscriber en EC2**:
   - Iniciar el servicio que escucha los topics y guarda los datos en PostgreSQL.
3. **API REST (AWS Chalice)**:
   - Desplegar con el comando `chalice deploy`.
4. **Notificaciones por correo**:
   - Configuradas desde la consola de AWS IoT Core y Amazon SNS.

## Estructura del proyecto

📂API_REST

📂Base_Datos

📂IoT_Gateway

📂sensors

- 📂sensor_1
- 📂sensor_2
- 📂sensor_3

📂Subscriber

📄README.md

📄Documentación_Proyecto_IoT_Final.pdf

## Documentación

Toda la información detallada sobre el diseño, implementación, pruebas y configuración se encuentra en el documento:

> `Documentación_Proyecto_IoT_Final.pdf`