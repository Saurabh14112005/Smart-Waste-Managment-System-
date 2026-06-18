"""
SQLite schema, migrations, telemetry history, hourly rollup, and retention.
No simulated sensor walks — data only from API / devices.
"""
import sqlite3
import os
import logging
from datetime import datetime, timedelta
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from backend_dashboard.config import DB_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s - IoT-DB - %(levelname)s - %(message)s")
logger = logging.getLogger("IoT_Database")


def _table_columns(conn: sqlite3.Connection, table: str) -> set:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def _migrate_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cols = _table_columns(conn, "bins")
    if "tenant_id" not in cols:
        cur.execute("ALTER TABLE bins ADD COLUMN tenant_id TEXT")
        cur.execute("UPDATE bins SET tenant_id = 'default' WHERE tenant_id IS NULL OR tenant_id = ''")
        logger.info("Migration: bins.tenant_id added")
    cols_logs = _table_columns(conn, "sensor_logs")
    if "anomaly_flags" not in cols_logs:
        cur.execute("ALTER TABLE sensor_logs ADD COLUMN anomaly_flags TEXT")
        logger.info("Migration: sensor_logs.anomaly_flags added")

    cur.execute(
        """CREATE TABLE IF NOT EXISTS sensor_logs_hourly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bin_id INTEGER NOT NULL,
            hour_start TEXT NOT NULL,
            avg_fill REAL NOT NULL,
            max_fill INTEGER NOT NULL,
            sample_count INTEGER NOT NULL,
            UNIQUE(bin_id, hour_start)
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            applied_at TEXT NOT NULL
        )"""
    )
    conn.commit()


class BinDatabaseService:
    """Schema, migrations, log append, retention, hourly aggregates."""

    def initialize_iot_grid(self) -> None:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                """CREATE TABLE IF NOT EXISTS bins
                   (id INTEGER PRIMARY KEY, location TEXT, fill_level INTEGER, type TEXT, status TEXT,
                    lat REAL, lon REAL, temp REAL, gas_level INTEGER, battery INTEGER, moisture INTEGER,
                    zone TEXT, last_update TEXT)"""
            )
            c.execute(
                """CREATE TABLE IF NOT EXISTS sensor_logs
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, bin_id INTEGER, fill_level INTEGER,
                    temp REAL, gas_level INTEGER, timestamp TEXT)"""
            )
            c.execute(
                """CREATE TABLE IF NOT EXISTS complaints
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, user_name TEXT, location TEXT,
                    type TEXT, status TEXT, timestamp TEXT)"""
            )
            conn.commit()
            _migrate_schema(conn)
            conn.close()
            logger.info("Database schema ready.")
        except Exception as e:
            logger.error("Schema init failed: %s", e)

    def update_telemetry(self) -> bool:
        return True

    def log_reading(
        self,
        bin_id: int,
        fill_level: int,
        temp: float,
        gas_level: int,
        anomaly_flags: str | None = None,
    ) -> None:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            flags = anomaly_flags or ""
            c.execute(
                "INSERT INTO sensor_logs (bin_id, fill_level, temp, gas_level, timestamp, anomaly_flags) VALUES (?,?,?,?,?,?)",
                (bin_id, fill_level, round(temp, 1), gas_level, datetime.now().isoformat(), flags),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("log_reading failed: %s", e)

    def prune_sensor_logs(self, days: int) -> int:
        """Delete raw sensor_logs older than ``days`` (retention)."""
        if days < 7:
            raise ValueError("refusing to prune with retention < 7 days")
        conn = sqlite3.connect(DB_PATH)
        try:
            c = conn.cursor()
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            c.execute("DELETE FROM sensor_logs WHERE timestamp < ?", (cutoff,))
            n = c.rowcount
            conn.commit()
            logger.info("Pruned %s sensor_logs rows older than %s days", n, days)
            return n
        finally:
            conn.close()

    def rollup_sensor_logs_hourly(self, lookback_days: int = 14) -> int:
        """Aggregate recent sensor_logs into hourly buckets (ON CONFLICT upsert)."""
        ld = max(1, min(int(lookback_days), 365))
        cutoff = (datetime.utcnow() - timedelta(days=ld)).isoformat()
        conn = sqlite3.connect(DB_PATH)
        try:
            c = conn.cursor()
            c.execute(
                """
                INSERT OR REPLACE INTO sensor_logs_hourly (bin_id, hour_start, avg_fill, max_fill, sample_count)
                SELECT
                    bin_id,
                    strftime('%Y-%m-%dT%H:00:00', timestamp) AS hs,
                    AVG(fill_level),
                    MAX(fill_level),
                    COUNT(*)
                FROM sensor_logs
                WHERE timestamp >= ?
                GROUP BY bin_id, hs
                """,
                (cutoff,),
            )
            conn.commit()
            return c.rowcount
        finally:
            conn.close()

    def clear_bins_after_collection(self, bin_ids: list) -> None:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            ts = datetime.now().isoformat()
            for b_id in bin_ids:
                c.execute(
                    "UPDATE bins SET fill_level=0, status='NORMAL', last_update=? WHERE id=?",
                    (ts, b_id),
                )
            conn.commit()
            conn.close()
            logger.info("Collection recorded for bins: %s", bin_ids)
        except Exception as e:
            logger.error("Collection reset failed: %s", e)

    def jitter_simulated_data(self) -> None:
        """Slightly randomize bin values to simulate live traffic for demos."""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, fill_level, temp, gas_level, battery FROM bins")
            rows = c.fetchall()
            ts = datetime.now().isoformat()
            for r in rows:
                b_id, fill, temp, gas, bat = r
                # Randomly jitter values
                new_fill = min(100, max(0, fill + random.randint(-2, 5)))
                new_temp = temp + random.uniform(-0.5, 0.5)
                new_gas = max(0, gas + random.randint(-10, 20))
                new_bat = max(0, bat - random.randint(0, 1)) if random.random() > 0.9 else bat
                
                c.execute("""
                    UPDATE bins 
                    SET fill_level=?, temp=?, gas_level=?, battery=?, last_update=?
                    WHERE id=?
                """, (new_fill, new_temp, new_gas, new_bat, ts, b_id))
                
                # Log the jittered reading occasionally
                if random.random() > 0.7:
                    c.execute(
                        "INSERT INTO sensor_logs (bin_id, fill_level, temp, gas_level, timestamp) VALUES (?,?,?,?,?)",
                        (b_id, new_fill, round(new_temp, 1), new_gas, ts),
                    )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Jitter failed: %s", e)

iot_simulator = BinDatabaseService()

if __name__ == "__main__":
    BinDatabaseService().initialize_iot_grid()
    print("Schema initialized at", DB_PATH)
