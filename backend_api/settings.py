"""Runtime configuration from environment (no secrets in repo)."""
import os

# Optional: require this header value on POST /iot/update and POST /bins when set
DEVICE_INGEST_SECRET = os.environ.get("DEVICE_INGEST_SECRET", "").strip()

# Optional: Bearer or raw token for admin maintenance routes
ADMIN_API_SECRET = os.environ.get("ADMIN_API_SECRET", "").strip()

# MQTT (optional bridge script)
MQTT_BROKER = os.environ.get("MQTT_BROKER", "").strip()
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC_TELEMETRY = os.environ.get("MQTT_TOPIC_TELEMETRY", "cleancity/+/telemetry").strip()

DEFAULT_TENANT_ID = os.environ.get("DEFAULT_TENANT_ID", "default").strip() or "default"

# Anomaly: fill % change in one reading vs previous stored value
ANOMALY_JUMP_THRESHOLD = int(os.environ.get("ANOMALY_JUMP_THRESHOLD", "30"))
