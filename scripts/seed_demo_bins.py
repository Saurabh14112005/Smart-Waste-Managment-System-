
import sqlite3
import os
import sys
import random
from datetime import datetime

# Add root to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from backend_dashboard.config import DB_PATH, CITY_CENTER

def seed_bins():
    print(f"Seeding demo bins to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Sample data
    demo_bins = [
        (101, "City Market Plaza", 92, "Organic", "NORMAL", 23.245, 77.442, 32.5, 85, 88, 10, "COMMERCIAL", "default"),
        (102, "Greenwood Residential", 45, "Recyclable", "NORMAL", 23.235, 77.435, 28.1, 12, 95, 5, "RESIDENTIAL", "default"),
        (103, "Metro Hospital East", 78, "Hazardous", "NORMAL", 23.255, 77.452, 26.5, 45, 70, 2, "MEDICAL", "default"),
        (104, "Central Park Gate 3", 15, "Mixed", "NORMAL", 23.242, 77.458, 30.2, 8, 100, 15, "PARK", "default"),
        (105, "Tech-Hub Sector 5", 88, "Non-Recyclable", "NORMAL", 23.262, 77.428, 29.8, 120, 45, 8, "INDUSTRIAL", "default"),
        (106, "Old Town Station", 95, "Mixed", "CRITICAL", 23.228, 77.448, 34.0, 310, 30, 12, "PUBLIC", "default"),
    ]
    
    ts = datetime.now().isoformat()
    
    for b in demo_bins:
        c.execute("""
            INSERT OR REPLACE INTO bins 
            (id, location, fill_level, type, status, lat, lon, temp, gas_level, battery, moisture, zone, tenant_id, last_update)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (*b, ts))
        
        # Also add initial log entries
        c.execute("""
            INSERT INTO sensor_logs (bin_id, fill_level, temp, gas_level, timestamp)
            VALUES (?,?,?,?,?)
        """, (b[0], b[2], b[7], b[8], ts))
        
    conn.commit()
    conn.close()
    print("Demo bins seeded successfully!")

if __name__ == "__main__":
    seed_bins()
