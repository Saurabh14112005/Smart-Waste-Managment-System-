# CleanCity AI - Global Configuration Manifest
import os

# --- SYSTEM CONSTANTS ---
PROJECT_NAME = "CleanCity AI"
VERSION = "2.5.0-PRO"
REFRESH_INTERVAL = 5  

# --- SIMULATOR CONSTANTS ---
FILL_RATE_MARKET = (5, 12)      # Rapid growth
FILL_RATE_RESIDENTIAL = (1, 5)  # Slow growth
GAS_THRESHOLD = 80             # ppm
TEMP_THRESHOLD = 50            # Celsius
BATTERY_CRITICAL = 15          # %

# --- GEOGRAPHICAL CONFIG ---
CITY_CENTER = [23.24, 77.44]
DEPOT_LOCATION = [23.24, 77.45]
MAP_ZOOM = 13

# --- PATH CONFIG ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(os.path.dirname(__file__), "smart_bins.db")

# --- UI CONSTANTS ---
THEME_COLOR = "#2EA043"
CRITICAL_COLOR = "#FF4B4B"
WARNING_COLOR = "#FFA500"

# --- ENGINE STATUS (Simulation) ---
ENGINE_CHECK_INTERVAL = 10 
