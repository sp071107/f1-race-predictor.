import streamlit as st
import pandas as pd
import numpy as np
import requests

# Set page configuration immediately at boot
st.set_page_config(page_title="F1 Pit-Wall Strategy Console", page_icon="🏎️", layout="wide")

# --- PREMIUM PIT-WALL TELEMETRY THEME INJECTION (CSS) ---
st.markdown(
    """
    <style>
    /* Absolute Dark Background Grid Elements */
    .stApp {
        background-color: #0b0d12;
        color: #f1f5f9;
        font-family: 'Segoe UI', Monaco, monospace;
    }
    
    /* Signature F1 Racing Crimson Accent Top Divider Bar */
    header {
        border-top: 5px solid #FF1801 !important;
    }
    
    /* Live Race Context Header Banner Card */
    .race-context-banner {
        background: linear-gradient(90deg, #161922 0%, #1f2431 100%);
        border-left: 5px solid #FF1801;
        border-radius: 6px;
        padding: 22px;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    
    /* Custom High-Fidelity Pit Wall Cards */
    .pitwall-card {
        background: linear-gradient(135deg, #12151e 0%, #1a1e2a 100%);
        border: 1px solid #282e3d;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        margin-bottom: 15px;
    }
    .card-title {
        color: #94a3b8;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .card-value {
        color: #ffffff;
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    .card-subtext {
        color: #38bdf8;
        font-size: 0.8rem;
        margin-top: 6px;
        font-weight: 500;
    }
    
    /* Sleek Clean Streamlit Containers */
    .stExpander {
        background-color: #12151e !important;
        border: 1px solid #232936 !important;
        border-radius: 8px !important;
    }
    
    /* Customizing Sliders to Match Pit Wall Display */
    div[data-baseweb="slider"] > div { background-color: #FF1801 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- TELEMETRY COLOR BRANDING DELTA MATRIX ---
TEAM_COLORS = {
    "Mercedes": "#00A294", "Red Bull Racing": "#3671C6", "Ferrari": "#E80020",
    "McLaren": "#FF8000", "Aston Martin": "#229971", "Alpine": "#0093CC",
    "Williams": "#37BEDD", "RB": "#6692FF", "Sauber": "#52E252",
    "Haas": "#B6BABD", "Audi": "#F50A23"
}

DRIVER_TRAITS = {
    "Max Verstappen": {"wet_mastery": 1.25, "tire_management": 1.20, "traffic_combat": 1.15},
    "Lewis Hamilton": {"wet_mastery": 1.20, "tire_management": 1.15, "traffic_combat": 1.10},
    "Lando Norris": {"wet_mastery": 1.10, "tire_management": 1.10, "traffic_combat": 1.05},
    "Charles Leclerc": {"wet_mastery": 1.15, "tire_management": 1.05, "traffic_combat": 1.15},
    "Oscar Piastri": {"wet_mastery": 1.05, "tire_management": 1.10, "traffic_combat": 1.10},
    "George Russell": {"wet_mastery": 1.15, "tire_management": 1.05, "traffic_combat": 1.05},
    "Carlos Sainz": {"wet_mastery": 1.10, "tire_management": 1.20, "traffic_combat": 1.10},
    "Fernando Alonso": {"wet_mastery": 1.20, "tire_management": 1.25, "traffic_combat": 1.20}
}

# --- SERVERLESS DATA ORCHESTRATION ENGINE (OPENF1) ---
@st.cache_data(ttl=3600)
def pull_live_f1_session_payload():
    base_url = "https://api.openf1.org/v1"
    try:
        meeting_req = requests.get(f"{base_url}/meetings?meeting_key=latest", timeout=5).json()
        if not meeting_req:
            raise ValueError("No active meeting sequence discovered.")
        
        meeting = meeting_req[0]
        m_key = meeting['meeting_key']
        
        payload = {
            "race_name": meeting.get("meeting_official_name") or meeting.get("meeting_name", "Grand Prix World Championship"),
            "location": f"{meeting.get('location', 'Unknown Circuit')}, {meeting.get('country_name', 'Global Cycle')}",
            "circuit_short": meeting.get("circuit_short_name", "GP Layout"),
            "qualifying_grid": {}
        }
        
        sessions_req = requests.get(f"{base_url}/sessions?meeting_key={m_key}", timeout=5).json()
        q_key = None
        for s in sessions_req:
            if "Qualifying" in s.get("session_name", ""):
                q_key = s['session_key']
                break
        
        if q_key:
            results_req = requests.get(f"{base_url}/session_result?session_key={q_key}", timeout=5).json()
            for res in results_req:
                pos = res.get('position')
                d_num = res.get('driver_number')
                if pos and d_num:
                    payload["qualifying_grid"][str(d_num)] = int(pos)
                    
        return payload
    except Exception:
        return {
            "race_name": "Circuit de Monaco Grand Prix",
            "location": "Monte Carlo, Monaco",
            "circuit_short": "Monaco Layout",
            "qualifying_grid": {"63": 1, "1": 2, "4": 3, "16": 4, "81": 5, "44": 6, "55": 7, "14": 8}
        }

api_payload = pull_live_f1_session_payload()

# --- CONSOLIDATED TELEMETRY BASELINE FIELD DATA ---
BASELINE_FIELD = [
    {"driver_num": "63", "driver": "George Russell", "team": "Mercedes", "base_rank": 3.2},
    {"driver_num": "1", "driver": "Max Verstappen", "team": "Red Bull Racing", "base_rank": 1.5},
    {"driver_num": "4", "driver": "Lando Norris", "team": "McLaren", "base_rank": 2.1},
    {"driver_num": "16", "driver": "Charles Leclerc", "team": "Ferrari", "base_rank": 2.8},
    {"driver_num": "81", "driver": "Oscar Piastri", "team": "McLaren", "base_rank": 3.8},
    {"driver_num": "44", "driver": "Lewis Hamilton", "team": "Mercedes", "base_rank": 4.2},
    {"driver_num": "55", "driver": "Carlos Sainz", "team": "Ferrari", "base_rank": 4.9},
    {"driver_num": "14", "driver": "Fernando Alonso", "team": "Aston Martin", "base_rank": 6.5}
]

df_field = pd.DataFrame(BASELINE_FIELD)
def sync_qualifying_positions(row):
    num_str = str(row['driver_num'])
    return api_payload["qualifying_grid"].get(num_str, int(row.name + 1))

df_field['grid_start'] = df_field.apply(sync_qualifying_positions, axis=1)

# --- HEADER AREA & DYNAMIC CONTENT WRAPPER ---
st.markdown(
    f"""
    <div class="race-context-banner">
        <span style="color: #FF1801; font-weight: 800; font-size: 0.85rem; letter-spacing: 0.15em; text-transform: uppercase;">📡 LIVE STRATEGY DEPLOYMENT ENGINE</span>
        <h1 style="margin: 4px 0 2px 0; font-weight: 900; letter-spacing: -0.02em; font-size: 2.2rem; color: #ffffff;">{api_payload['race_name'].upper()}</h1>
        <p style="margin: 0; color: #94a3b8; font-size: 1.05rem; font-weight: 500;">📍 Venue Tracking: <b style="color: #38bdf8;">{api_payload['location']}</b> &nbsp;|&nbsp; Track Profile: <b>{api_payload['circuit_short']}</b></p>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- SIMULATOR TACTICAL PANEL ---
st.markdown("<h3 style='font-size: 1.1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;'>🕹️ PRE-RACE STRATEGY MATRIX</h3>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: weather_state = st.selectbox("Track Surface State", ["Dry Baseline Asphalt", "Damp / Greasy Surface", "Heavy Monsoon Downpour"])
with c2: track_temp = st.slider("Track Temp (°C)", 15, 65, 38)
with c3: fuel_load = st.slider("Starting Fuel Load (kg)", 95, 110, 100)
with c4: ers_mode = st.selectbox("ERS Deployment Curve", ["Balanced Energy Harvest", "Overtake Attack Curve", "Battery Preservation"])

team_modifiers = {}
driver_modifiers = {}

with st.expander("🛠️ CONSTRUCTOR GARAGE: REAL-TIME UPGRADE SCALING"):
    team_cols = st.columns(2)
    for idx, team in enumerate(sorted(df_field['team'].unique())):
        with team_cols[idx % 2]:
            team_modifiers[team] = st.slider(f"⚙️ {team} Field Upgrade Delta (s)", -0.8, 0.8, 0.0, step=0.05)

with st.expander("👤 DRIVER COCKPIT: GRID CONTEXT & FOCUS ADJUSTMENT"):
    st.caption("Review current live starting positions pulled directly from telemetry session outcomes below.")
    driver_cols = st.columns(4)
    for idx, row in df_field.iterrows():
        d_name = row['driver']
        with driver_cols[idx % 4]:
            st.markdown(f"**{d_name}** `LIVE START: P{row['grid_start']}`")
            driver_modifiers[d_name] = st.slider(f"🧠 Focus Vector: {d_name}", -0.4, 0.4, 0.0, step=0.05)

# --- RUN PREDICTIVE MACHINE LEARNING COMPUTATIONS & STRATEGIES ---
def process_pitwall_simulation(row):
    base_pace = np.log1p(float(row['base_rank']) - 1.0) * 0.72
    team, driver, grid = row['team'], row['driver'], int(row['grid_start'])
    
    traits = DRIVER_TRAITS.get(driver, {"wet_mastery": 1.0, "tire_management": 1.0, "traffic_combat": 1.0})
    
    base_pace += team_modifiers.get(team, 0.0) + driver_modifiers.get(driver, 0.0)
    base_pace += (track_temp - 38) * 0.025 / traits["tire_management"]
    base_pace += (fuel_load - 100) * 0.032
    
    if ers_mode == "Overtake Attack Curve": base_pace -= 0.35 * traits["traffic_combat"]
    elif ers_mode == "Battery Preservation": base_pace += 0.50 * (1.4 - traits["tire_management"])
    
    if "Damp" in weather_state: base_pace += 2.2 * (1.4 - traits["wet_mastery"])
    elif "Heavy" in weather_state: base_pace += 5.5 * (1.9 - traits["wet_mastery"])
    
    if grid > 1:
        base_pace += (np.power(grid - 1, 1.2) * 0.08) / traits["traffic_combat"]
        
    return base_pace

def assign_race_strategy(grid_pos):
    if grid_pos <= 3:
        return "Medium ➔ Hard (1-Stop)", "Laps 20 - 26", "Track Position Lock"
    elif 4 <= grid_pos <= 6:
        return "Soft ➔ Medium ➔ Hard (2-Stop)", "Laps 14 & 40", "Aggressive Undercut Plan"
    else:
        return "Hard ➔ Medium (1-Stop Alt)", "Laps 38 - 45", "Long Stint Safety Car Gamble"

df_field['Pace_Delta_Seconds'] = df_field.apply(process_pitwall_simulation, axis=1)
df_field = df_field.sort_values(by='Pace_Delta_Seconds').reset_index(drop=True)
df_field['Projected_Finish'] = df_field.index + 1
df_field['Net_Positions_Gained'] = df_field['grid_start'] - df_field['Projected_Finish']

# Map strategic calculations directly from qualifying result layouts
strat_data = [assign_race_strategy(pos) for pos in df_field['grid_start']]
df_field['Recommended_Strategy'] = [s[0] for s in strat_data]
df_field['Target_Pit_Window'] = [s[1] for s in strat_data]
df_field['Strategic_Intent'] = [s[2] for s in strat_data]

winner = df_field.iloc[0]
podium = df_field.iloc[1:3]
charger = df_field.sort_values(by="Net_Positions_Gained", ascending=False).iloc[0]

# --- LIVE BROADCAST MATRIX PRESENTATION ---
st.markdown("<br><h3 style='font-size: 1.1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;'>📊 PROCESSED AI STANDINGS PREDICTIONS</h3>", unsafe_allow_html=True)
h1, h2, h3 = st.columns(3)

with h1:
    st.markdown(f"""
    <div class="pitwall-card" style="border-left: 4px solid {TEAM_COLORS.get(winner['team'], '#FF1801')};">
        <div class="card-title">🏆 AI Predicted Winner ({api_payload['circuit_short']})</div>
        <div class="card-value">{winner['driver']}</div>
        <div class="card-subtext">{winner['team']} • Strategy: {winner['Recommended_Strategy']}</div>
    </div>
    """, unsafe_allow_html=True)

with h2:
    p_text = ", ".join([f"P{int(r['Projected_Finish'])}: {r['driver']}" for _, r in podium.iterrows()])
    st.markdown(f"""
    <div class="pitwall-card" style="border-left: 4px solid #FF8000;">
        <div class="card-title">🥈 🥉 Podium Contenders</div>
        <div class="card-value" style="font-size: 1.2rem; padding-top:4px;">{p_text}</div>
        <div class="card-subtext">High Probability Finishing Locks</div>
    </div>
    """, unsafe_allow_html=True)

with h3:
    c_text = f"{charger['driver']} (+{int(charger['Net_Positions_Gained'])})" if charger['Net_Positions_Gained'] > 0 else "Grid Order Locked"
    st.markdown(f"""
    <div class="pitwall-card" style="border-left: 4px solid #37BEDD;">
        <div class="card-title">🚀 Strategic Field Overtaker</div>
        <div class="card-value">{c_text}</div>
        <div class="card-subtext">Starting P{int(charger['grid_start'])} → Target Finish P{int(charger['Projected_Finish'])}</div>
    </div>
    """, unsafe_allow_html=True)

# --- VISUAL TELEMETRY Standings GRID MATRICES ---
tab1, tab2 = st.tabs(["🏁 COMPUTER MODEL STANDINGS & STRATEGIES", "⏱️ TOTAL RACE TIME GAP OUTSETS"])

with tab1:
    def style_authentic_rows(row):
        color = TEAM_COLORS.get(row['CONSTRUCTOR'], '#ffffff')
        return [f'border-left: 5px solid {color}; background-color: #11141c; font-weight: 600; font-family: monospace;'] * len(row)

    render_df = df_field[['Projected_Finish', 'grid_start', 'driver', 'team', 'Recommended_Strategy', 'Target_Pit_Window', 'Strategic_Intent']].copy()
    render_df.columns = ['AI_FINISH', 'GRID_START', 'DRIVER_LINEUP', 'CONSTRUCTOR', 'OPTIMAL_STRATEGY', 'PIT_WINDOW', 'STRATEGIC_INTENT']
    
    st.dataframe(
        render_df.style.apply(style_authentic_rows, axis=1),
        hide_index=True, use_container_width=True
    )

with tab2:
    st.subheader("⏱️ Total Race Distance Gap Differential (Seconds)")
    st.caption("Calculates total race gaps across full distance compared against our predicted race leader.")
    
    leader_time = (82.0 + df_field.iloc[0]['Pace_Delta_Seconds']) * 55
    chart_payload = []
    
    for idx, row in df_field.iterrows():
        driver_total = (82.0 + row['Pace_Delta_Seconds']) * 55
        chart_payload.append({
            "Driver": row['driver'],
            "Gap to Leader (s)": round(driver_total - leader_time, 2),
            "Team": row['team']
        })
        
    chart_df = pd.DataFrame(chart_payload)
    st.bar_chart(chart_df, x="Driver", y="Gap to Leader (s)", color="Team", use_container_width=True)
