import streamlit as st
import numpy as np
from PIL import Image
import pandas as pd
import time
import sqlite3
import os
import sys

# Load Global Config
from config import *

# Paths setup for modular structure
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from ai_engine.classifier import classifier
from route_engine.optimizer import optimizer
from iot_gateway.sensor_simulator import iot_simulator

# pyrefly: ignore [missing-import]
import folium
# pyrefly: ignore [missing-import]
from streamlit_folium import st_folium

try:
    import requests
except ImportError:
    requests = None

# --- SESSION STATE INITIALIZATION ---
if 'system_initialized' not in st.session_state:
    iot_simulator.initialize_iot_grid()
    st.session_state['system_initialized'] = True
    st.session_state['last_sync'] = time.time()
if "tenant_filter" not in st.session_state:
    st.session_state.tenant_filter = ""

# --- DATABASE CONNECTION CACHING ---
@st.cache_resource
def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def get_bin_data(tenant_filter: str | None = None):
    try:
        conn = get_db_connection()
        tid = (tenant_filter or "").strip()
        if tid:
            return pd.read_sql_query("SELECT * FROM bins WHERE tenant_id = ?", conn, params=(tid,))
        return pd.read_sql_query("SELECT * FROM bins", conn)
    except Exception as e:
        st.error(f"Database Read Error: {e}")
        return pd.DataFrame()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title=f"{PROJECT_NAME} | Command Center",
    page_icon="🏙️",
    layout="wide",
)

# --- AUTO-REFRESH (DEMO SMOOTHNESS) ---
if 'refresh_count' not in st.session_state:
    st.session_state.refresh_count = 0

# --- ADVANCED UI STYLING ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    .stApp {{ 
        background: #010409;
        background-image: 
            radial-gradient(at 0% 0%, rgba(46, 160, 67, 0.05) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(0, 212, 255, 0.05) 0px, transparent 50%);
        font-family: 'Outfit', sans-serif; 
        color: #E0E0E0; 
    }}

    /* Futuristic Pulsing Health */
    @keyframes pulse-green {{
        0% {{ box-shadow: 0 0 0 0 rgba(46, 160, 67, 0.4); }}
        70% {{ box-shadow: 0 0 0 10px rgba(46, 160, 67, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(46, 160, 67, 0); }}
    }}

    .status-bar {{
        display: flex; justify-content: space-around; align-items: center;
        background: rgba(13, 17, 23, 0.7);
        backdrop-filter: blur(12px);
        padding: 18px; border-radius: 20px; border: 1px solid rgba(48, 54, 61, 0.5); 
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }}
    
    .status-item {{ 
        font-size: 0.75rem; font-weight: 600; color: #8B949E; 
        text-transform: uppercase; letter-spacing: 1.5px;
        display: flex; align-items: center; gap: 8px;
    }}
    
    .status-dot {{
        height: 8px; width: 8px; border-radius: 50%;
        background-color: {THEME_COLOR};
        display: inline-block;
        animation: pulse-green 2s infinite;
    }}

    .bin-card {{ 
        background: rgba(22, 27, 34, 0.4); 
        backdrop-filter: blur(10px);
        border-radius: 24px; padding: 25px; 
        border: 1px solid rgba(48, 54, 61, 0.3); 
        margin-bottom: 20px; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .bin-card:hover {{ 
        background: rgba(22, 27, 34, 0.6);
        border-color: {THEME_COLOR}55;
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.5);
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: #0d1117;
        border-right: 1px solid #30363d;
    }}
    
    .stMetric {{
        background: rgba(255, 255, 255, 0.03);
        padding: 15px; border-radius: 15px;
        border: 1px solid rgba(48, 54, 61, 0.5);
    }}

    h1, h2, h3 {{ color: #FFFFFF !important; font-weight: 800 !important; }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 8px; }}
    ::-webkit-scrollbar-track {{ background: #010409; }}
    ::-webkit-scrollbar-thumb {{ background: #30363d; border-radius: 10px; }}

    # Hero Banner
    .hero-banner {{
        position: relative;
        background: linear-gradient(135deg, #0d1117, #21262d);
        padding: 60px 30px;
        text-align: center;
        color: #fff;
        overflow: hidden;
        border-radius: 24px;
        margin-bottom: 30px;
        animation: fadeIn 1.2s ease-out;
    }}
    .hero-banner h1 {{
        font-family: 'Outfit', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(45deg, #00d4ff, #a0e9ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .hero-banner p {{
        margin-top: 12px;
        font-size: 1.1rem;
        color: #c9d1d9;
    }}
    @keyframes fadeIn {{
        0% {{ opacity: 0; transform: translateY(20px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}
</style>
""", unsafe_allow_html=True)

def render_status_bar():
    ai_map = {"keras": "TENSORFLOW", "none": "NO MODEL"}
    ai_state = ai_map.get(classifier.active_backend, classifier.active_backend.upper())
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-item"><span class="status-dot"></span> AI ENGINE: <span style="color:#FFF">{ai_state}</span></div>
        <div class="status-item"><span class="status-dot"></span> IOT GRID: <span style="color:#FFF">ACTIVE</span></div>
        <div class="status-item"><span class="status-dot"></span> NETWORK: <span style="color:#FFF">STABLE</span></div>
        <div class="status-item"><span class="status-dot"></span> LOGISTICS: <span style="color:#FFF">OPTIMIZED</span></div>
    </div>
    """, unsafe_allow_html=True)

def render_demo_banner():
    st.info(
        "**Operations:** register bins with `POST /bins` (see `/docs`). Devices send `POST /iot/update`; "
        "unknown `bin_id` is auto-registered when `location`, `latitude`, and `longitude` are included. "
        "Telemetry is **not** simulated in software. Vision needs `ai_engine/models/waste_model.h5` + TensorFlow."
    )
def render_hero_banner():
    st.markdown("""
    <div class=\"hero-banner\">
        <h1>Smart Waste Management</h1>
        <p>Real‑time monitoring & AI‑driven optimization for cleaner cities</p>
    </div>
    """, unsafe_allow_html=True)
def render_overflow_alerts(bin_data: pd.DataFrame):
    if bin_data is None or bin_data.empty:
        return
    fill = bin_data["fill_level"] if "fill_level" in bin_data.columns else None
    if fill is None:
        return
    crit = bin_data[fill >= 80]
    weird = bin_data[bin_data["status"].astype(str).str.contains("CRITICAL|FIRE|GAS|HAZARD", case=False, na=False)]
    rows = pd.concat([crit, weird], ignore_index=True)
    if "id" in rows.columns:
        rows = rows.drop_duplicates(subset=["id"])
    else:
        rows = rows.drop_duplicates()
    if rows.empty:
        st.success("No overflow or hazard alerts — city grid within thresholds.")
        return
    st.error(f"**{len(rows)} active alert(s)** — dispatch review required")
    for _, b in rows.head(12).iterrows():
        loc = b.get("location", "?")
        fl = b.get("fill_level", "?")
        status_txt = str(b.get("status", ""))
        st.warning(f"Bin **{loc}** — fill **{fl}%** — status: _{status_txt}_")

with st.sidebar:
    st.markdown(f"<h1 style='color: {THEME_COLOR};'>{PROJECT_NAME}</h1>", unsafe_allow_html=True)
    st.markdown(f"`SYSTEM v{VERSION}`")
    st.write("---")
    st.session_state.tenant_filter = st.text_input(
        "Tenant ID filter",
        value=st.session_state.tenant_filter,
        help="Leave empty to show all tenants. Must match bins.tenant_id.",
    )
    app_page = st.radio(
        "System Menu",
        ["🌍 City Map Operations", "📊 Sensor Telemetry", "🧠 Vision Diagnostics", "📢 Community Reports"],
    )
    st.write("---")
    if st.button("🔄 Refresh data"):
        st.rerun()
    auto_ref = st.toggle("Auto-refresh (5s)", value=False)
    st.write("---")
    st.markdown("### 🛠️ Hackathon Demo")
    demo_sim = st.toggle("Live Demo Simulation", value=False, help="Randomly jitters bin values to simulate live traffic for judges.")
    if demo_sim:
        iot_simulator.jitter_simulated_data()
        st.caption("✨ Simulation active: values updating via software jitter")

render_status_bar()
render_demo_banner()
render_hero_banner()
_tenant_q = (st.session_state.tenant_filter or "").strip() or None
bin_data_alert = get_bin_data(_tenant_q)
render_overflow_alerts(bin_data_alert)

# --- 1. CITY MAP OPERATIONS ---
if app_page == "🌍 City Map Operations":
    st.title("🏙️ Live City Collection Topology")

    with st.expander("Import bins from CSV (calls REST API)"):
        if requests is None:
            st.warning("Install `requests` in the same environment: `pip install requests`")
        else:
            api_base = st.text_input("API base URL", value="http://127.0.0.1:8000", key="csv_api")
            dev_tok = st.text_input("X-Device-Token (required if API has DEVICE_INGEST_SECRET)", type="password", key="csv_tok")
            up = st.file_uploader("CSV file", type=["csv"], key="csv_up")
            if st.button("POST /bins/import-csv", key="csv_btn"):
                if not up:
                    st.error("Choose a CSV file first.")
                else:
                    hdrs = {}
                    if dev_tok:
                        hdrs["X-Device-Token"] = dev_tok
                    try:
                        r = requests.post(
                            f"{api_base.rstrip('/')}/bins/import-csv",
                            files={"file": (up.name, up.getvalue(), "text/csv")},
                            headers=hdrs,
                            timeout=120,
                        )
                        st.write("HTTP", r.status_code)
                        try:
                            st.json(r.json())
                        except Exception:
                            st.code(r.text)
                    except Exception as ex:
                        st.error(str(ex))

    bin_data = get_bin_data(_tenant_q)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Bins in service", len(bin_data))
    with c2:
        crit_bins = bin_data[bin_data["fill_level"] >= 80] if not bin_data.empty else bin_data
        st.metric("Priority (fill ≥80%)", len(crit_bins))
    with c3:
        avg_fill = float(bin_data["fill_level"].mean()) if not bin_data.empty and "fill_level" in bin_data.columns else 0.0
        st.metric("Mean fill level", f"{avg_fill:.1f}%")
    with c4:
        if bin_data.empty or "last_update" not in bin_data.columns:
            st.metric("Latest telemetry", "—")
        else:
            latest = bin_data["last_update"].max()
            st.metric("Latest telemetry", str(latest)[:19] if pd.notna(latest) else "—")

    st.write("---")
    col_map, col_info = st.columns([2.5, 1])

    with col_map:
        m = folium.Map(location=CITY_CENTER, zoom_start=MAP_ZOOM, tiles="CartoDB dark_matter")
        folium.Marker(DEPOT_LOCATION, popup="Central Depot", icon=folium.Icon(color='blue', icon='home')).add_to(m)
        
        if not bin_data.empty:
            target_list = bin_data.to_dict("records")
        else:
            target_list = []
        route = []
        try:
            route = optimizer.calculate_optimal_path(DEPOT_LOCATION, target_list)
            if route:
                points = [DEPOT_LOCATION] + [[b['lat'], b['lon']] for b in route]
                from folium.plugins import AntPath
                AntPath(
                    locations=points,
                    dash_array=[10, 20],
                    delay=1000,
                    color=THEME_COLOR,
                    pulse_color='#FFFFFF',
                    weight=5,
                    opacity=0.9
                ).add_to(m)
        except Exception as e:
            st.error(f"Routing Engine Error: {e}")
            route = []

        for _, b in bin_data.iterrows():
            color = CRITICAL_COLOR if b['fill_level'] >= 80 else WARNING_COLOR if b['fill_level'] >= 60 else THEME_COLOR
            # Hardware Status Marker (Outer Ring if Real)
            if b['status'] == 'Real':
                folium.CircleMarker(
                    location=[b['lat'], b['lon']],
                    radius=20,
                    color="#00D4FF",
                    weight=2,
                    fill=False,
                    popup="REAL HARDWARE ACTIVE"
                ).add_to(m)
                
            folium.CircleMarker(
                location=[b['lat'], b['lon']],
                radius=10 if b['fill_level'] < 80 else 15,
                popup=f"{b['location']}: {b['fill_level']}% (Mode: {b['status']})",
                color=color, fill=True, fill_color=color, fill_opacity=0.6,
            ).add_to(m)
            
        st_folium(m, width=900, height=550)

    with col_info:
        st.markdown(f"<div style='background:rgba(255,255,255,0.03); backdrop-filter:blur(15px); padding:25px; border-radius:24px; border:1px solid rgba(255,255,255,0.1); box-shadow:0 8px 32px 0 rgba(0,0,0,0.8);'>", unsafe_allow_html=True)
        st.subheader("🧠 AI Dispatch Intel")
        if not route:
            st.success("No bins currently require priority collection (none ≥75% with route rules).")
        else:
            metrics = optimizer.get_eta_metrics(route)
            st.markdown(f"""
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px;'>
                    <div style='background:rgba(255,255,255,0.05); padding:15px; border-radius:18px; border:1px solid rgba(255,255,255,0.1); text-align:center;'>
                        <small style="color:#8B949E; text-transform:uppercase; font-size:0.65rem; letter-spacing:1px;">Route Distance</small><br><b style="font-size:1.2rem; color:#FFF;">{metrics['distance']}</b>
                    </div>
                    <div style='background:rgba(255,255,255,0.05); padding:15px; border-radius:18px; border:1px solid rgba(255,255,255,0.1); text-align:center;'>
                        <small style="color:#8B949E; text-transform:uppercase; font-size:0.65rem; letter-spacing:1px;">Est. Time</small><br><b style="font-size:1.2rem; color:#FFF;">{metrics['time']}</b>
                    </div>
                    <div style='background:rgba(255,255,255,0.05); padding:15px; border-radius:18px; border:1px solid rgba(255,255,255,0.1); text-align:center;'>
                        <small style="color:#8B949E; text-transform:uppercase; font-size:0.65rem; letter-spacing:1px;">Est. CO₂ Savings</small><br><b style="font-size:1.2rem; color:{THEME_COLOR};">{metrics['co2_kg_est']}</b>
                    </div>
                    <div style='background:rgba(255,255,255,0.05); padding:15px; border-radius:18px; border:1px solid rgba(255,255,255,0.1); text-align:center;'>
                        <small style="color:#8B949E; text-transform:uppercase; font-size:0.65rem; letter-spacing:1px;">Est. Fuel Saved</small><br><b style="font-size:1.2rem; color:{THEME_COLOR};">{metrics['fuel_liters_est']}</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("**Recommended Collection Sequence:**")
            for i, b in enumerate(route, 1):
                mode_tag = "📡 DEVICE" if b['status'] == 'Real' else "REGISTERED"
                border_col = CRITICAL_COLOR if b['fill_level']>=80 else WARNING_COLOR
                st.markdown(f"""
                    <div style='border-left:4px solid {border_col}; padding-left:10px; margin-bottom:10px;'>
                        <small style='color:#8B949E;'>{mode_tag}</small><br>
                        {i}. 📍 {b['location']} (<b>{b['fill_level']}%</b>)
                    </div>
                """, unsafe_allow_html=True)
            
            if st.button("🚀 Dispatch & Empty Bins"):
                target_ids = [b['id'] for b in route]
                iot_simulator.simulate_collection_reset(target_ids)
                st.toast(f"Unit Dispatched! {len(target_ids)} bins emptied.")
                time.sleep(1)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 2. SENSOR TELEMETRY ---
elif app_page == "📊 Sensor Telemetry":
    st.title("📊 Detailed Node Telemetry")
    bin_data = get_bin_data(_tenant_q)
    
    if bin_data.empty:
        st.warning("No data available in the IoT Grid.")
    else:
        rows = [bin_data.iloc[i:i+4] for i in range(0, len(bin_data), 4)]
        for row_df in rows:
            cols = st.columns(4)
            for i, (_, b) in enumerate(row_df.iterrows()):
                with cols[i]:
                    stt = str(b.get("status", ""))
                    color = CRITICAL_COLOR if (b.get("fill_level", 0) >= 90 or "CRITICAL" in stt.upper()) else THEME_COLOR
                    mode_tag = "📡 DEVICE" if b['status'] == 'Real' else "REGISTERED"
                    mode_color = "#00D4FF" if b['status'] == 'Real' else "#8B949E"
                    glow_class = "glow-critical" if (b.get("fill_level", 0) >= 90) else ""
                    st.markdown(f"""
                        <div class="bin-card {glow_class}">
                            <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:15px;">
                                <div>
                                    <h4 style='margin:0; font-weight:800; color:#FFF;'>{b['location']}</h4>
                                    <small style='color:{mode_color}; font-weight:bold; letter-spacing:1px;'>{mode_tag}</small>
                                </div>
                                <div style="background:{color}22; color:{color}; padding:4px 10px; border-radius:8px; font-size:0.7rem; font-weight:800; border:1px solid {color}44;">
                                    {b['status'].upper()}
                                </div>
                            </div>
                            <div style="display:flex; align-items:center; gap:20px;">
                                <div style='color:{color}; font-size:2.8rem; font-weight:800; line-height:1;'>{b['fill_level']}%</div>
                                <div style='font-size:0.8rem; color:#8B949E; border-left:1px solid rgba(255,255,255,0.1); padding-left:15px;'>
                                    🔋 {b['battery']}%<br>
                                    🌡️ {b['temp']:.1f}°C<br>
                                    💨 {b['gas_level']} ppm
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

# --- 3. VISION DIAGNOSTICS ---
elif app_page == "🧠 Vision Diagnostics":
    st.title("🧠 AI Vision Core Diagnostics")
    st.markdown("Automated waste classification and segregation intelligence.")
    
    up = st.file_uploader("Upload waste sample for AI analysis", type=['jpg', 'jpeg', 'png'])
    if up:
        img = Image.open(up).convert("RGB")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(img, caption="Source Image", use_container_width=True)
        with col2:
            with st.spinner("🤖 AI Engine Inferencing..."):
                try:
                    label, conf, guide, timing = classifier.predict(img)
                    if label == "Engine Offline":
                        st.warning(
                            "Vision service is offline. Add **ai_engine/models/waste_model.h5** and ensure TensorFlow runs on this machine."
                        )
                    else:
                        st.markdown(f"""
                        <div style='background:#161B22; padding:20px; border-radius:20px; border:1px solid {THEME_COLOR};'>
                            <small style='color:#8B949E;'>AI ANALYSIS RESULT</small>
                            <h2 style='margin:0;'>{label}</h2>
                            <h1 style='color:{THEME_COLOR}; margin:10px 0;'>{conf*100:.1f}%</h1>
                            <p style='margin:0;'><b>Guidance:</b> {guide}</p>
                            <hr style='border: 0.1px solid #30363D; margin: 15px 0;'>
                            <small style='color:#8B949E;'>Inference Speed: {timing}ms</small>
                        </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Inference Error: {e}")

# --- 4. COMMUNITY REPORTS ---
elif app_page == "📢 Community Reports":
    st.title("📢 Citizen Complaint Hub")
    st.markdown("Crowdsourced waste monitoring for community action.")
    
    with st.form("Citizen Report Form"):
        n = st.text_input("Full Name")
        l = st.text_input("Location / Landmark")
        t_issue = st.selectbox("Issue Type", ["Bin Overflow", "Illegal Dumping", "Foul Smell", "Damaged Bin"])
        if st.form_submit_button("Submit Intelligence Report"):
            try:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("INSERT INTO complaints (user_name, location, type, status, timestamp) VALUES (?, ?, ?, ?, ?)", 
                          (n, l, t_issue, "Pending", time.strftime('%Y-%m-%d %H:%M')))
                conn.commit()
                st.success("Report stored. Municipal staff can review it in this dashboard.")
            except Exception as e:
                st.error(f"Report Logging Error: {e}")
    
    st.write("---")
    st.subheader("📋 Recent Community Reports")
    try:
        conn = get_db_connection()
        comp_df = pd.read_sql_query("SELECT user_name as Citizen, location as Location, type as Issue, status as Status FROM complaints ORDER BY id DESC LIMIT 5", conn)
        st.table(comp_df)
    except Exception:
        st.info("No active community reports found.")

# --- AUTO-REFRESH LOGIC ---
if auto_ref:
    time.sleep(REFRESH_INTERVAL)
    st.rerun()
