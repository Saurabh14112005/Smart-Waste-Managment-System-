# Feature matrix & upgrade roadmap

Use this as the single checklist to drive “hackathon winning level” work. **No dummy paths remain** in the Python stack: no random IoT walk, no synthetic sklearn classifier, no fake dashboard KPIs.

Legend: **Done** = implemented with real or honest behaviour; **Next** = suggested upgrade.

---

## 1. IoT & data layer (section complete — v1 production patterns)

| # | Delivered in repo | Details |
|---|-------------------|---------|
| 1.1 | **Bin registration + bulk + CSV** | `POST /bins`, `POST /bins/bulk`, `POST /bins/import-csv` (UTF-8 CSV); shared **Pydantic validation** (`backend_api/bin_validation.py`). Streamlit **City Map → expander** posts CSV to API. |
| 1.2 | **Telemetry + optional auth + MQTT bridge** | `POST /iot/update` (auto-register with lat/lon/location); **`X-Device-Token`** enforced when `DEVICE_INGEST_SECRET` is set. **`python -m iot_gateway.mqtt_bridge`** forwards MQTT JSON → REST (configure `MQTT_BROKER`, `CLEANCITY_API_URL`). **TLS**: terminate at reverse proxy / `uvicorn` SSL flags (see FastAPI deploy docs). |
| 1.3 | **History + retention + rollup + rule anomaly** | Each `/iot/update` appends **`sensor_logs`** with optional **`anomaly_flags`** (e.g. `SUDDEN_FILL_JUMP` vs `ANOMALY_JUMP_THRESHOLD`). **`POST /admin/prune-sensor-logs`** (requires `ADMIN_API_SECRET` + `X-Admin-Token`) prunes raw logs. **`POST /admin/rollup-sensor-logs-hourly`** fills **`sensor_logs_hourly`**. |
| 1.4 | **Schema migrations + multi-tenant** | Startup **`_migrate_schema`**: `bins.tenant_id`, `sensor_logs.anomaly_flags`, `sensor_logs_hourly`, `schema_migrations`. **`GET /telemetry?tenant_id=`** and **`GET /route?tenant_id=`**; dashboard **tenant filter**. |
| 1.5 | **Hardware** | `sketch_may12a`: ultrasonic + DHT + gas + **ADC battery**, JSON includes **location/lat/lon/zone**, **ESP32 task watchdog**, **ArduinoOTA** hostname `cleancity-bin-1`. Calibration: adjust **`BIN_HEIGHT_CM`** (documented in sketch). |

**PostgreSQL / Alembic:** SQLite + `tenant_id` is fully wired; for managed DB see **`docs/DEPLOY_POSTGRES.md`**. Alembic-style versioned SQL can be added later; today migrations are **idempotent PRAGMA-driven** in code.

| # | Feature | Current behaviour | Upgrade to winning level |
|---|---------|---------------------|---------------------------|
| 1.x follow-up | LoRa / edge | HTTP + optional MQTT bridge | LoRaWAN NS + signed binary payloads |
| 1.x follow-up | DB | SQLite file | PostgreSQL pool + Alembic revisions (see deploy doc) |
| 1.x follow-up | Auth | Shared secret headers | mTLS per device + JWT scopes |

---

## 2. AI — waste type classification

| # | Feature | Current behaviour | Upgrade to winning level |
|---|---------|---------------------|---------------------------|
| 2.1 | Model inference | Keras `.h5` only; `/predict` returns **503** if missing | Train/export MobileNet/EfficientNet; versioned models; batch infer |
| 2.2 | Input pipeline | 224×224 RGB | EXIF, lens correction, class imbalance handling |
| 2.3 | Explainability | Confidence + guidance text | Grad-CAM / saliency thumbnails in dashboard |

---

## 3. Routing & fleet

| # | Feature | Current behaviour | Upgrade to winning level |
|---|---------|---------------------|---------------------------|
| 3.1 | Priority route | Greedy on fill + gas − distance; cap `truck_capacity` | OR-Tools / VRP; time windows; road network (OSRM) |
| 3.2 | Metrics | Distance, time, **estimated** fuel L & CO₂ kg from distance constants | Fleet-specific fuel curves; live traffic API |
| 3.3 | Depot | Fixed in `config.py` | Per-depot config; multi-depot pickup |

---

## 4. Alerts & operations

| # | Feature | Current behaviour | Upgrade to winning level |
|---|---------|---------------------|---------------------------|
| 4.1 | Overflow UI | Streamlit alerts from fill ≥80% + status keywords | PagerDuty / SMS / WhatsApp; escalation rules |
| 4.2 | `alerts_engine` | Logger-based stub | Wire notifier to queue + webhooks |

---

## 5. Dashboard (Streamlit)

| # | Feature | Current behaviour | Upgrade to winning level |
|---|---------|---------------------|---------------------------|
| 5.1 | City map | Folium markers + route polyline | Mapbox + live vehicle layer |
| 5.2 | KPIs | Counts / mean fill / latest `last_update` from DB | SLA cards, trend sparklines from `sensor_logs` |
| 5.3 | Vision page | Upload → `/predict` | Batch folder, audit log of predictions |
| 5.4 | Community reports | SQLite `complaints` | Moderation workflow, GIS geocode |

---

## 6. Backend API

| # | Feature | Current behaviour | Upgrade to winning level |
|---|---------|---------------------|---------------------------|
| 6.1 | Surface | REST `/docs` | OpenAPI RBAC scopes; rate limits |
| 6.2 | CORS | `allow_origins=["*"]` | Locked to known frontends |
| 6.3 | Health | DB + `ai_backend` | Dependency checks (disk, model version) |

---

---

## 8. Analytics

| # | Feature | Current behaviour | Upgrade to winning level |
|---|---------|---------------------|---------------------------|
| 8.1 | `OverflowPredictor` | Deterministic hours-to-95% from fill + rate param | Fit fill-rate per bin from `sensor_logs` regression |

---

## 9. Security & scale (cross-cutting)

| # | Topic | Current | Next |
|---|--------|---------|------|
| 9.1 | Auth | None | JWT / API keys per municipality |
| 9.2 | Transport | HTTP local | HTTPS + reverse proxy |
| 9.3 | DB | SQLite file | PostgreSQL + read replicas |

---

## Removed / cleaned in this pass

- Random IoT simulation and fake bin seeding.
- Sklearn demo model + training script + `image_features` helper.
- Duplicate `backend_dashboard/requirements.txt`, redundant `Hardware_Setup.md`, old hackathon-only doc.
- Hardcoded dashboard metrics (94% / 99.9%).
- Plotly/OpenCV/sklearn/joblib from `requirements.txt` where unused by app code.
- Arduino `random()` battery and non-schema JSON field.

---

## Suggested order of attack (one-by-one)

1. **Populate real bins** (`POST /bins` or device auto-register) + verify map/route.  
2. **Ship `waste_model.h5`** + stable TensorFlow env.  
3. **Wire `alerts_engine` to SMS/email**.  
4. **Replace greedy route with OR-Tools VRP** (small graph first).  
5. **PostgreSQL + auth** for “city-wide” story.
