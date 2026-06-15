import streamlit as st
import pandas as pd
import numpy as np
import requests
import datetime

# Set page configuration immediately at boot
st.set_page_config(page_title="F1 Monitored | Pit-Wall Hub", page_icon="🏎️", layout="wide")

# --- PREMIUM PIT-WALL TELEMETRY THEME INJECTION (CSS) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    
    .stApp {
        background-color: #0b0d12;
        color: #f1f5f9;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    header {
        border-top: 5px solid #FF1801 !important;
    }
    
    /* Container Enhancements */
    .race-context-banner {
        background: linear-gradient(135deg, #11141d 0%, #1a1f2c 100%);
        border: 1px solid #232936;
        border-left: 6px solid #FF1801;
        border-radius: 12px;
        padding: 26px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    .command-card {
        background: linear-gradient(145deg, #131722 0%, #1a1e2d 100%);
        border: 1px solid #242b3d;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 15px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .command-card:hover {
        transform: translateY(-2px);
        border-color: #38bdf8;
    }
    .card-label {
        color: #64748b;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 6px;
    }
    .card-main {
        font-size: 1.6rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.02em;
    }
    .card-detail {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #38bdf8;
        margin-top: 4px;
    }

    .hero-container {
        background: radial-gradient(circle at top right, rgba(255,24,1,0.08) 0%, rgba(11,13,18,0) 70%), 
                    linear-gradient(145deg, #11131a 0%, #161924 100%);
        border: 1px solid #282e3d;
        border-radius: 14px;
        padding: 35px;
        margin-bottom: 30px;
        position: relative;
        overflow: hidden;
    }
    .hero-container::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 4px; height: 100%;
        background: #FF1801;
    }

    .brief-badge {
        display: inline-block;
        background: #1e2433;
        border: 1px solid #333c51;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 10px;
        width: 100%;
    }
    
    .stExpander {
        background-color: #12151e !important;
        border: 1px solid #232936 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #11141c;
        padding: 6px;
        border-radius: 10px;
    }
    div[data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        color: #64748b !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        font-weight: 700 !important;
        transition: all 0.15s ease;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FF1801 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(255, 24, 1, 0.3);
    }
    div[data-baseweb="slider"] > div { background-color: #FF1801 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- PERFORMANCE COEFFICIENTS ---
TEAM_META = {
    "Mercedes": {"color": "#00A294", "base_pace_rank": 1.1},
    "Ferrari": {"color": "#E80020", "base_pace_rank": 1.4},
    "McLaren": {"color": "#FF8000", "base_pace_rank": 1.5},
    "Red Bull Racing": {"color": "#3671C6", "base_pace_rank": 2.2},
    "Alpine": {"color": "#0093CC", "base_pace_rank": 3.4},
    "Racing Bulls": {"color": "#6692FF", "base_pace_rank": 3.8},
    "Haas F1 Team": {"color": "#B6BABD", "base_pace_rank": 4.1},
    "Williams": {"color": "#37BEDD", "base_pace_rank": 4.5},
    "Audi": {"color": "#F50A23", "base_pace_rank": 5.2},
    "Aston Martin": {"color": "#229971", "base_pace_rank": 5.5},
    "Cadillac": {"color": "#DEB887", "base_pace_rank": 5.8}
}

# --- CHAMPIONSHIP STANDINGS DATA SETS ---
DRIVERS_STANDINGS_2026 = [
    {"Pos": 1, "Driver": "K. ANTONELLI", "Team": "Mercedes", "Points": 156},
    {"Pos": 2, "Driver": "L. HAMILTON", "Team": "Ferrari", "Points": 90},
    {"Pos": 3, "Driver": "G. RUSSELL", "Team": "Mercedes", "Points": 88},
    {"Pos": 4, "Driver": "C. LECLERC", "Team": "Ferrari", "Points": 75},
    {"Pos": 5, "Driver": "O. PIASTRI", "Team": "McLaren", "Points": 58},
    {"Pos": 6, "Driver": "L. NORRIS", "Team": "McLaren", "Points": 58},
    {"Pos": 7, "Driver": "M. VERSTAPPEN", "Team": "Red Bull Racing", "Points": 43},
    {"Pos": 8, "Driver": "P. GASLY", "Team": "Alpine", "Points": 35},
    {"Pos": 9, "Driver": "I. HADJAR", "Team": "Red Bull Racing", "Points": 26},
    {"Pos": 10, "Driver": "L. LAWSON", "Team": "Racing Bulls", "Points": 24},
    {"Pos": 11, "Driver": "O. BEARMAN", "Team": "Haas F1 Team", "Points": 18},
    {"Pos": 12, "Driver": "F. COLAPINTO", "Team": "Alpine", "Points": 15},
    {"Pos": 13, "Driver": "A. LINDBLAD", "Team": "Racing Bulls", "Points": 11},
    {"Pos": 14, "Driver": "C. SAINZ", "Team": "Williams", "Points": 6},
    {"Pos": 15, "Driver": "A. ALBON", "Team": "Williams", "Points": 5},
    {"Pos": 16, "Driver": "E. OCON", "Team": "Haas F1 Team", "Points": 3},
    {"Pos": 17, "Driver": "G. BORTOLETO", "Team": "Audi", "Points": 2},
    {"Pos": 18, "Driver": "F. ALONSO", "Team": "Aston Martin", "Points": 1},
    {"Pos": 19, "Driver": "S. PEREZ", "Team": "Cadillac", "Points": 0},
    {"Pos": 20, "Driver": "N. HULKENBERG", "Team": "Audi", "Points": 0},
    {"Pos": 21, "Driver": "V. BOTTAS", "Team": "Cadillac", "Points": 0},
    {"Pos": 22, "Driver": "L. STROLL", "Team": "Aston Martin", "Points": 0}
]

CONSTRUCTORS_STANDINGS_2026 = [
    {"Pos": 1, "Team": "Mercedes", "Points": 244},
    {"Pos": 2, "Team": "Ferrari", "Points": 165},
    {"Pos": 3, "Team": "McLaren", "Points": 116},
    {"Pos": 4, "Team": "Red Bull Racing", "Points": 69},
    {"Pos": 5, "Team": "Alpine", "Points": 50},
    {"Pos": 6, "Team": "Racing Bulls", "Points": 35},
    {"Pos": 7, "Team": "Haas F1 Team", "Points": 21},
    {"Pos": 8, "Williams": "Williams", "Points": 11},
    {"Pos": 9, "Team": "Audi", "Points": 2},
    {"Pos": 10, "Team": "Aston Martin", "Points": 1},
    {"Pos": 11, "Team": "Cadillac", "Points": 0}
]

# --- SERVERLESS DATA ORCHESTRATION ENGINE (OPENF1 DIRECT CAPTURE) ---
@st.cache_data(ttl=1800)
def pull_authentic_field_payload():
    base_url = "https://api.openf1.org/v1"
    try:
        meeting_req = requests.get(f"{base_url}/meetings?meeting_key=latest", timeout=5).json()
        if not meeting_req:
            raise ValueError("Telemetry feed offline.")
        meeting = meeting_req[0]
        m_key = meeting['meeting_key']
        
        payload = {
            "race_name": meeting.get("meeting_official_name") or meeting.get("meeting_name", "Grand Prix World Championship"),
            "location": f"{meeting.get('location', 'Unknown Track')}, {meeting.get('country_name', 'Global Cycle')}",
            "circuit_short": meeting.get("circuit_short_name", "GP Layout"),
            "drivers": []
        }
        
        sessions_req = requests.get(f"{base_url}/sessions?meeting_key={m_key}", timeout=5).json()
        q_key = None
        for s in sessions_req:
            if "Qualifying" in s.get("session_name", ""):
                q_key = s['session_key']
                break
        
        if not q_key:
            raise ValueError("Qualifying data frame unassigned.")
            
        results_req = requests.get(f"{base_url}/session_result?session_key={q_key}", timeout=5).json()
        drivers_req = requests.get(f"{base_url}/drivers?session_key={q_key}", timeout=5).json()
        
        driver_directory = {
            str(d['driver_number']): {
                "name": d.get('broadcast_name', 'Unknown Lineup'),
                "team": d.get('team_name', 'Independent')
            } for d in drivers_req
        }
        
        for res in results_req:
            pos = res.get('position')
            d_num = str(res.get('driver_number'))
            if pos and d_num in driver_directory:
                meta = driver_directory[d_num]
                payload["drivers"].append({
                    "driver_num": d_num,
                    "driver": meta["name"],
                    "team": meta["team"],
                    "grid_start": int(pos)
                })
        return payload

    except Exception:
        return {
            "race_name": "Circuit de Barcelona-Catalunya Grand Prix",
            "location": "Montmeló, Spain",
            "circuit_short": "Catalunya Layout",
            "drivers": [
                {"driver_num": "12", "driver": "K. ANTONELLI", "team": "Mercedes", "grid_start": 1},
                {"driver_num": "44", "driver": "L. HAMILTON", "team": "Ferrari", "grid_start": 2},
                {"driver_num": "63", "driver": "G. RUSSELL", "team": "Mercedes", "grid_start": 3},
                {"driver_num": "16", "driver": "C. LECLERC", "team": "Ferrari", "grid_start": 4},
                {"driver_num": "1", "driver": "L. NORRIS", "team": "McLaren", "grid_start": 5},
                {"driver_num": "81", "driver": "O. PIASTRI", "team": "McLaren", "grid_start": 6},
                {"driver_num": "3", "driver": "M. VERSTAPPEN", "team": "Red Bull Racing", "grid_start": 7},
                {"driver_num": "14", "driver": "F. ALONSO", "team": "Aston Martin", "grid_start": 18}
            ]
        }

api_payload = pull_authentic_field_payload()
df_field = pd.DataFrame(api_payload["drivers"])

# --- APP LAYOUT BANNER ---
st.markdown(
    f"""
    <div class="race-context-banner">
        <span style="color: #FF1801; font-weight: 800; font-size: 0.75rem; letter-spacing: 0.2em; text-transform: uppercase; font-family: 'JetBrains Mono';">🛰️ LIVE TELEMETRY STREAM</span>
        <h1 style="margin: 6px 0 4px 0; font-weight: 900; letter-spacing: -0.03em; font-size: 2.4rem; color: #ffffff;">{api_payload['race_name'].upper()}</h1>
        <p style="margin: 0; color: #94a3b8; font-size: 1rem;">📍 Venue Matrix: <span style="color: #38bdf8; font-weight: 600;">{api_payload['location']}</span></p>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- APP NAVIGATION TABS ---
tab_home, tab_predictor, tab_chatbot = st.tabs(["🏠 COMMAND HOME", "📊 STRATEGY PREDICTOR ENGINE", "🎙️ AI RACE ENGINEER FEED"])

# ==========================================
# 🏠 TAB 1: THE COMMAND HOME
# ==========================================
with tab_home:
    hero_col, side_brief = st.columns([5, 3])
    
    with hero_col:
        st.markdown(
            """
            <div class="hero-container">
                <h2 style='margin: 0 0 12px 0; font-weight: 800; color: #ffffff; font-size: 1.8rem; letter-spacing: -0.01em;'>Pit-Wall Cockpit Activated.</h2>
                <p style='margin: 0 0 20px 0; color: #94a3b8; font-size: 1.05rem; line-height: 1.6;'>
                    Welcome to your tactical operational hub. This console parses raw Formula 1 sensor feeds and live event loops 
                    into actionable engineering insight. Use the controller matrices above to step through race modeling or 
                    issue commands straight to your AI digital Race Engineer.
                </p>
                <div style="font-family: 'JetBrains Mono'; font-size: 0.8rem; color: #64748b;">
                    SYSTEM STATUS: <span style="color: #22c55e;">● ONLINE</span> &nbsp;&nbsp;|&nbsp;&nbsp; INGESTION LATENCY: <span style="color: #38bdf8;">14ms</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with side_brief:
        st.markdown("<h3 style='font-size: 0.85rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 12px;'>⚡ STRATEGIST QUICK PANEL</h3>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="brief-badge">
                <span style="color: #ffb703; font-weight: 700; font-size: 0.85rem; display:block;">⚠️ DEGRADATION THREAT</span>
                <span style="color: #cbd5e1; font-size: 0.85rem;">Asphalt track temperatures exceeding 35°C will severely drop tyre atomic cohesion.</span>
            </div>
            <div class="brief-badge">
                <span style="color: #38bdf8; font-weight: 700; font-size: 0.85rem; display:block;">🔋 ERS OVERTAKE VECTOR</span>
                <span style="color: #cbd5e1; font-size: 0.85rem;">Ensure tactical energy harvesting is complete prior to Sector 2 activation points.</span>
            </div>
            """, unsafe_allow_html=True
        )

    # --- LIVE KPI CARDS ---
    st.markdown("<h3 style='font-size: 0.85rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 15px;'>📋 CURRENT SESSION PROGRESSION METRICS</h3>", unsafe_allow_html=True)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.markdown(f'<div class="command-card" style="border-left: 4px solid #38bdf8;"><div class="card-label">Circuit Profile</div><div class="card-main">{api_payload["circuit_short"]}</div><div class="card-detail">Live Layout Map Loaded</div></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'<div class="command-card" style="border-left: 4px solid #a855f7;"><div class="card-label">Active Field</div><div class="card-main">{len(df_field)} Drivers</div><div class="card-detail">Transponder Mapping Clear</div></div>', unsafe_allow_html=True)
    with kpi3:
        st.markdown('<div class="command-card" style="border-left: 4px solid #22c55e;"><div class="card-label">Session Status</div><div class="card-main">Qualifying</div><div class="card-detail">Grid Array Compiled</div></div>',
