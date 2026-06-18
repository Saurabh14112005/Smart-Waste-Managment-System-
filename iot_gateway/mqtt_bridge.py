#!/usr/bin/env python3
"""
Optional MQTT → REST bridge: subscribes to telemetry topics and POSTs JSON to CleanCity API.

Environment:
  MQTT_BROKER       e.g. 192.168.1.50
  MQTT_PORT         default 1883
  MQTT_TOPIC_TELEMETRY  default cleancity/+/telemetry
  CLEANCITY_API_URL default http://127.0.0.1:8000/iot/update
  DEVICE_INGEST_SECRET  optional X-Device-Token header

Run:  python -m iot_gateway.mqtt_bridge
"""
from __future__ import annotations

import json
import logging
import os
import sys

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Install paho-mqtt: pip install paho-mqtt", file=sys.stderr)
    sys.exit(1)

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - MQTT - %(levelname)s - %(message)s")
log = logging.getLogger("mqtt_bridge")

BROKER = os.environ.get("MQTT_BROKER", "").strip()
PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC = os.environ.get("MQTT_TOPIC_TELEMETRY", "cleancity/+/telemetry").strip()
API_URL = os.environ.get("CLEANCITY_API_URL", "http://127.0.0.1:8000/iot/update").strip()
TOKEN = os.environ.get("DEVICE_INGEST_SECRET", "").strip()


def on_message(_cli, _userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        headers = {"Content-Type": "application/json"}
        if TOKEN:
            headers["X-Device-Token"] = TOKEN
        r = requests.post(API_URL, json=payload, headers=headers, timeout=15)
        if r.status_code >= 400:
            log.warning("POST %s: %s %s", r.status_code, r.text[:200], msg.topic)
        else:
            log.info("Forwarded %s -> %s", msg.topic, r.status_code)
    except Exception as e:
        log.exception("Forward failed: %s", e)


def on_connect(client, _userdata, _flags, rc):
    if rc != 0:
        log.error("MQTT connect failed rc=%s", rc)
        return
    client.subscribe(TOPIC)
    log.info("Subscribed to %s", TOPIC)


def main():
    if not BROKER:
        log.error("Set MQTT_BROKER in the environment.")
        sys.exit(1)
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    log.info("Connecting to %s:%s …", BROKER, PORT)
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    main()
