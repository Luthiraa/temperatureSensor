import streamlit as st
import paho.mqtt.client as mqtt
import json
from queue import Queue
from threading import Thread

# Streamlit app title
st.title("Real-Time Temperature Sensor Data")


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
        st.write("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
    else:
        st.error(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    # Decode the incoming MQTT message and add it to the queue
    try:
        message = msg.payload.decode()
        message_queue.put(message)
    except Exception as e:
        st.error(f"Error decoding message: {e}")

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
        st.error(f"Failed to connect to MQTT broker: {e}")

# Start the MQTT client in a thread
Thread(target=start_mqtt_client, daemon=True).start()

# Display incoming messages in real time
st.subheader("Live Data from MQTT Broker")
st.write("Subscribed to topic:", MQTT_TOPIC)

# Initialize a container for displaying messages
message_container = st.empty()

while True:
    if not message_queue.empty():
        message = message_queue.get()
        try:
            # Parse the message as JSON (if applicable)
            parsed_message = json.loads(message)
            message_container.json(parsed_message)
        except json.JSONDecodeError:
            message_container.text(message)


