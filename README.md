# Smart Waste Management (CleanCity AI)

Production-oriented stack: **FastAPI** (ingestion + AI + routing), **SQLite**, **Streamlit** command center, **ESP32** reference firmware.

## Quick Start (Full Stack Launcher)

The fastest way to launch both the FastAPI backend and the React frontend dev server on Windows:

```powershell
.\scripts\start_fullstack.bat
```

This activates the virtual environment, launches FastAPI on port 8000, starts the React dashboard dev server on port 3000, and opens the console in your default browser.

### Starting Components Individually

1. **FastAPI Backend (Port 8000)**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python -m uvicorn backend_api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **React Dashboard (Port 3000)**:
   ```powershell
   cd frontend_react
   npm install
   npm run dev -- --port 3000
   ```

*(The old Streamlit dashboard is preserved in `backend_dashboard/app.py` for legacy reference, but all active operations have been migrated to the new React SPA).*

## Data & AI

- Bins: **`POST /bins`**, **`POST /bins/bulk`**, **`POST /bins/import-csv`** (see `/docs`). Devices: **`POST /iot/update`** (unknown `bin_id` + lat/lon/location auto-registers). Optional **`tenant_id`**, **`GET /telemetry?tenant_id=`**. MQTT: **`python -m iot_gateway.mqtt_bridge`**.
- Telemetry is **not** randomly simulated in Python; values change only from your API/hardware/dashboard actions.
- Vision: place trained **`ai_engine/models/waste_model.h5`** and ensure TensorFlow loads (Windows: MSVC++ x64 redistributable).

Full capability matrix: **`docs/FEATURES.md`**.

## Environment (IoT / ops)

| Variable | Purpose |
|----------|---------|
| `DEVICE_INGEST_SECRET` | If set, `POST /bins`, `/bins/bulk`, `/bins/import-csv`, `/iot/update` require header **`X-Device-Token`**. |
| `ADMIN_API_SECRET` | If set, enables **`POST /admin/prune-sensor-logs`** and **`POST /admin/rollup-sensor-logs-hourly`** with header **`X-Admin-Token`**. |
| `DEFAULT_TENANT_ID` | Default `tenant_id` when device omits it (default `default`). |
| `ANOMALY_JUMP_THRESHOLD` | Fill % jump to flag `SUDDEN_FILL_JUMP` (default `30`). |
| `MQTT_BROKER` / `MQTT_PORT` / `MQTT_TOPIC_TELEMETRY` / `CLEANCITY_API_URL` | For **`python -m iot_gateway.mqtt_bridge`**. |
