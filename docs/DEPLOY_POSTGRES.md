# PostgreSQL / multi-city (next infra step)

The application **currently uses SQLite** (`backend_dashboard/smart_bins.db`) with **`tenant_id`** on every bin row so multiple municipalities can share one API process while you stay on a single file DB.

## Why move to PostgreSQL

- City-wide HA, concurrent writes from thousands of devices  
- Native row-level security per `tenant_id`  
- Managed backups and point-in-time recovery  

## Migration outline (manual)

1. **Export** bins and logs (CSV or `sqlite3 .dump`).  
2. **Create** Postgres schema mirroring tables: `bins`, `sensor_logs`, `sensor_logs_hourly`, `complaints`, `schema_migrations` (same columns as SQLite).  
3. **Point** a future `DATABASE_URL=postgresql+psycopg://...` at a small SQLAlchemy layer (replace `sqlite3` calls in `db_manager` + `iot_gateway/sensor_simulator.py` with connection pool).  
4. **Re-deploy** workers (FastAPI, MQTT bridge, Streamlit) with the same env secrets (`DEVICE_INGEST_SECRET`, `ADMIN_API_SECRET`).

Until that refactor lands, scale vertically and split tenants by **process** (one SQLite file per city) if needed.
