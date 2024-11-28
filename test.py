import streamlit as st
import paho.mqtt.client as mqtt
import json
from queue import Queue
from threading import Thread
import pandas as pd
import time

# Streamlit app title
st.title("Real-Time Sensor Data Dashboard")

# MQTT Configuration
MQTT_HOST = "b6bdb89571144b3d8e5ca4bbe666ddb5.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "Luthiraa"
MQTT_PASSWORD = "theboss1010"
MQTT_TOPIC = "sensors/bme680/data"

# A queue to store incoming MQTT messages
message_queue = Queue()

# MQTT callback functions
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    # Decode the incoming MQTT message and add it to the queue
    try:
        message = msg.payload.decode()
        message_queue.put(message)
    except Exception as e:
        print(f"Error decoding message: {e}")

# Function to start MQTT client in a separate thread
def start_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.tls_set()  # Enable TLS for secure connection

    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_start()  # Start the loop in a separate thread
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")

# Start the MQTT client in a thread
Thread(target=start_mqtt_client, daemon=True).start()

# Initialize placeholders for real-time data visualization
st.subheader("Live Sensor Data")
col1, col2 = st.columns(2)
with col1:
    st.markdown("### Temperature Over Time")
    temperature_chart = st.line_chart([])
with col2:
    st.markdown("### Humidity Over Time")
    humidity_chart = st.line_chart([])

pressure_gauge = st.empty()
gas_gauge = st.empty()

# DataFrame to store sensor data
sensor_data = pd.DataFrame(columns=["timestamp", "temperature", "humidity", "pressure", "gas"])

# Real-time data processing and visualization
while True:
    if not message_queue.empty():
        message = message_queue.get()
        try:
            # Parse the message as JSON
            parsed_message = json.loads(message)

            # Extract sensor values
            temperature = parsed_message.get("temperature")
            humidity = parsed_message.get("humidity")
            pressure = parsed_message.get("pressure")
            gas = parsed_message.get("gas")
            timestamp = time.time()

            # Add new data to the DataFrame
            new_row = pd.DataFrame([{
                "timestamp": timestamp,
                "temperature": temperature,
                "humidity": humidity,
                "pressure": pressure,
                "gas": gas,
            }])

            # Use pd.concat to add the new row to the DataFrame
            sensor_data = pd.concat([sensor_data, new_row], ignore_index=True)

            # Update the line charts
            temperature_chart.line_chart(sensor_data[["temperature"]])
            humidity_chart.line_chart(sensor_data[["humidity"]])

            # Update metrics for pressure and gas
            pressure_gauge.metric(
                label="Pressure (hPa)",
                value=f"{pressure:.2f}" if pressure else "N/A",
            )
            gas_gauge.metric(
                label="Gas (ohms)",
                value=f"{gas:.2f}" if gas else "N/A",
            )
        except json.JSONDecodeError:
            st.error("Failed to parse JSON payload")
    
    # Small delay to reduce CPU usage
    time.sleep(0.1)
