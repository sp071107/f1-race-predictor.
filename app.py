import streamlit as st
import json
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="F1 Pit-Wall Live Predictor", page_icon="🏎️", layout="wide")

# 🏎️ OFFICIAL F1 BRANDING HEX COLOR MATRIX
TEAM_COLORS = {
    "Mercedes": "#00A294",
    "Red Bull Racing": "#3671C6",
    "Ferrari": "#E80020",
    "McLaren": "#FF8000",
    "Aston Martin": "#229971",
    "Alpine": "#0093CC",
    "Williams": "#37BEDD",
    "RB": "#6692FF",
    "Sauber": "#52E252",
    "Audi": "#F50A23",
    "Haas": "#B6BABD"
}

# --- HIGH-FIDELITY CSS PIT WALL THEME INJECTION ---
st.markdown(
    """
    <style>
    /* Main Background & Font Styling */
    .stApp {
        background-color: #0e1117;
        color: #e2e8f0;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Top F1 Accent Line */
    header {
        border-top: 5px solid #FF1801 !important;
    }
    
    /* Custom Pit-Wall Metric Cards */
    .pitwall-card {
        background: linear-gradient(135deg, #161922 0%, #1e2230 100%);
        border-left: 4px solid #FF1801;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        margin-bottom: 15px;
    }
    .pitwall-card-winner { border-left-color: #E80020; }
    .pitwall-card-podium { border-left-color: #FF8000; }
    .pitwall-card-charge { border-left-color: #37BEDD; }
    
    .card-title {
        color: #94a3b8;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .card-value {
        color: #ffffff;
        font-size: 1.4rem;
        font-weight: 800;
    }
    .card-subtext {
        color: #38bdf8;
        font-size: 0.8rem;
        margin-top: 6px;
    }
    
    /* Sleek Container & Expander styling */
    .stExpander {
        background-color: #161922 !important;
        border: 1px solid #2d3142 !important;
        border-radius: 8px !important;
    }
    
    /* Streamlit Slider custom coloring */
    div[data-baseweb="slider"] > div { background-color: #ff1801 !important; }
    
    /* Dataframe layout adjustment */
    .dataframe {
        border: 1px solid #2d3142 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- CIRCUIT SPECS & DATA ASSETS ---
CIRCUIT_DB = {
    "catalunya": {"name": "Circuit de Barcelona-Catalunya", "bias": "Aero-Heavy", "base_laps": 66, "base_lap_time": 75.0, "overtake_difficulty": 0.7, "fuel_penalty_per_kg": 0.035, "thermal_sensitivity": 0.04},
    "monaco": {"name": "Circuit de Monaco", "bias": "Mechanical-Grip", "base_laps": 78, "base_lap_time": 72.0, "overtake_difficulty": 0.95, "fuel_penalty_per_kg": 0.022, "thermal_sensitivity": 0.01},
    "baku": {"name": "Baku City Circuit", "bias": "Top-Speed", "base_laps": 51, "base_lap_time": 103.0, "overtake_difficulty": 0.3, "fuel_penalty_per_kg": 0.040, "thermal_sensitivity": 0.025},
    "default": {"name": "Grand Prix Premium Circuit", "bias": "Balanced", "base_laps": 55, "base_lap_time": 90.0, "overtake_difficulty": 0.5, "fuel_penalty_per_kg": 0.030, "thermal_sensitivity": 0.02}
}

DRIVER_TRAITS = {
    "Max Verstappen": {"wet_mastery": 1.25, "tire_management": 1.20, "traffic_combat": 1.15},
    "Lewis Hamilton": {"wet_mastery": 1.20, "tire_management": 1.15, "traffic_combat": 1.10},
    "Fernando Alonso": {"wet_mastery": 1.15, "tire_management": 1.25, "traffic_combat": 1.20},
    "Kimi Antonelli": {"wet_mastery": 1.35, "tire_management": 1.20, "traffic_combat": 1.10}
}

DEFAULT_PREDICTIONS = [
    {"grid": 1, "driver": "Kimi Antonelli", "team": "Mercedes", "predicted_finish": 1.2, "circuit": "catalunya"},
    {"grid": 2, "driver": "Max Verstappen", "team": "Red Bull Racing", "predicted_finish": 2.0, "circuit": "catalunya"},
    {"grid": 3, "driver": "Lando Norris", "team": "McLaren", "predicted_finish": 2.5, "circuit": "catalunya"},
    {"grid": 4, "driver": "Charles Leclerc", "team": "Ferrari", "predicted_finish": 3.1, "circuit": "catalunya"},
    {"grid": 5, "driver": "Oscar Piastri", "team": "McLaren", "predicted_finish": 4.0, "circuit": "catalunya"},
    {"grid": 6, "driver": "Lewis Hamilton", "team": "Ferrari", "predicted_finish": 4.8, "circuit": "catalunya"},
    {"grid": 7, "driver": "George Russell", "team": "Mercedes", "predicted_finish": 5.2, "circuit": "catalunya"},
    {"grid": 8, "driver": "Carlos Sainz", "team": "Williams", "predicted_finish": 6.5, "circuit": "catalunya"}
]

# --- UI APP HEADER ---
col_logo, col_title = st.columns([1, 11])
with col_logo:
    st.markdown("<h1 style='color: #FF1801; font-size: 3.5rem; margin-top: -10px;'>🏁</h1>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='letter-spacing: -0.03em; font-weight: 900; margin-bottom: 0px;'>F1 STRATEGY PIT-WALL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 0.95rem; margin-top: -5px; font-weight: 500;'>Predictive Telemetry & Real-Time Race Delta Matrix</p>", unsafe_allow_html=True)

try:
    raw_data = DEFAULT_PREDICTIONS
    df = pd.DataFrame(raw_data)
    unique_teams = sorted(df['team'].unique())
    unique_drivers = sorted(df['driver'].unique())

    # --- SIMULATION CONFIGURATION PANEL ---
    st.markdown("<h3 style='font-size: 1.1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; font-weight:700;'>🕹️ ENVIRONMENT CONTROLS</h3>", unsafe_allow_html=True)
    
    env_card = st.container()
    with env_card:
        env_col1, env_col2, env_col3, env_col4 = st.columns(4)
        with env_col1:
            weather_state = st.selectbox("Track Surface", ["Dry Baseline", "Damp / Greasy", "Heavy Monsoon Wet"])
        with env_col2:
            track_temp = st.slider("Track Temp (°C)", 15, 60, 35)
        with env_col3:
            fuel_load = st.slider("Fuel Target (kg)", 95, 110, 100)
        with env_col4:
            ers_mode = st.selectbox("ERS Deployment Curve", ["Balanced Harvest", "Overtake Mode Peak", "Battery Conserve"])

    # Accordions designed cleanly to match dark garage spaces
    team_modifiers = {}
    driver_modifiers = {}

    with st.expander("🛠️ CONSTRUCTOR GARAGE: PERFORMANCE CONFIGURATOR"):
        team_cols = st.columns(2)
        for idx, team in enumerate(unique_teams):
            col_target = team_cols[idx % 2]
            with col_target:
                # Use delta feedback text instead of basic numbers
                raw_team_val = st.slider(f"⚙️ {team} Upgrade Package", -1.0, 1.0, 0.0, step=0.05, key=f"t_{team}")
                team_modifiers[team] = raw_team_val

    with st.expander("👤 DRIVER COCKPIT: LIVE TELEMETRY BIAS"):
        driver_cols = st.columns(4)
        for idx, driver in enumerate(unique_drivers):
            col_target = driver_cols[idx % 4]
            with col_target:
                raw_driver_val = st.slider(f"🧠 {driver} Form Focus", -0.5, 0.5, 0.0, step=0.05, key=f"d_{driver}")
                driver_modifiers[driver] = raw_driver_val

    # --- SIMULATION ENGINE MATHEMATICS ---
    track_key = raw_data[0].get("circuit", "catalunya")
    track = CIRCUIT_DB.get(track_key, CIRCUIT_DB["default"])

    def calculate_lap_pace_delta(row):
        base_pace = np.log1p(float(row['predicted_finish']) - 1.0) * 0.75 
        team, driver, grid = row['team'], row['driver'], int(row['grid'])
        traits = DRIVER_TRAITS.get(driver, {"wet_mastery": 1.0, "tire_management": 1.0, "traffic_combat": 1.0})
        
        base_pace += team_modifiers.get(team, 0.0) + driver_modifiers.get(driver, 0.0)
        base_pace += (track_temp - 35) * track["thermal_sensitivity"] / traits["tire_management"]
        base_pace += (fuel_load - 100) * track["fuel_penalty_per_kg"]

        if ers_mode == "Overtake Mode Peak": base_pace -= 0.40 * traits["traffic_combat"]
        elif ers_mode == "Battery Conserve": base_pace += 0.55 * (1.5 - traits["tire_management"])

        if weather_state == "Damp / Greasy": base_pace += 2.5 * (1.5 - traits["wet_mastery"])
        elif weather_state == "Heavy Monsoon Wet": base_pace += 6.0 * (2.0 - traits["wet_mastery"])

        if grid > 1:
            base_pace += (np.power(grid - 1, 1.25) * 0.09) * (track["overtake_difficulty"] / traits["traffic_combat"])
        return base_pace

    df['Lap Pace Delta (s)'] = df.apply(calculate_lap_pace_delta, axis=1)
    df = df.sort_values(by='Lap Pace Delta (s)').reset_index(drop=True)
    df['ML Predicted Finish'] = df.index + 1  
    df['Net Positions Change'] = df['grid'] - df['ML Predicted Finish']
    
    winner = df.iloc[0]
    podium = df.iloc[1:3]
    top_charger = df.sort_values(by="Net Positions Change", ascending=False).iloc[0]

    # --- TELEMETRY DASHBOARD DISPLAY (HIGH-DESIGN HTML KPI CARDS) ---
    st.markdown("<br><h3 style='font-size: 1.1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; font-weight:700;'>📊 PIT-WALL INTELLIGENCE BROADCAST</h3>", unsafe_allow_html=True)
    h1, h2, h3 = st.columns(3)
    
    with h1:
        st.markdown(f"""
        <div class="pitwall-card pitwall-card-winner">
            <div class="card-title">🏆 Predicted Race Winner</div>
            <div class="card-value">{winner['driver']}</div>
            <div class="card-subtext">{winner['team']} • Base Lap Delta: {winner['Lap Pace Delta (s)']:.3f}s</div>
        </div>
        """, unsafe_allow_html=True)
        
    with h2:
        podium_text = ", ".join([f"P{int(r['ML Predicted Finish'])}: {r['driver']}" for _, r in podium.iterrows()])
        st.markdown(f"""
        <div class="pitwall-card pitwall-card-podium">
            <div class="card-title">🥈 🥉 Podium Locks</div>
            <div class="card-value" style="font-size: 1.15rem; margin-top:4px;">{podium_text}</div>
            <div class="card-subtext">High Probability Strategic Windows Lock</div>
        </div>
        """, unsafe_allow_html=True)
        
    with h3:
        charge_text = f"{top_charger['driver']} (+{int(top_charger['Net Positions Change'])})" if top_charger['Net Positions Change'] > 0 else "Field Gaps Stable"
        st.markdown(f"""
        <div class="pitwall-card pitwall-card-charge">
            <div class="card-title">🚀 Advanced Field Overtaker</div>
            <div class="card-value">{charge_text}</div>
            <div class="card-subtext">Starting P{int(top_charger['grid'])} → Target P{int(top_charger['ML Predicted Finish'])}</div>
        </div>
        """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🏁 LIVE STANDINGS MATRIX", "⏱️ TYRE WEAR & GAP TELEMETRY"])

    with tab1:
        # Dynamically inject authentic team colors on the sidebar border of rows using styling functions
        def style_team_rows(row):
            color = TEAM_COLORS.get(row['team'], '#ffffff')
            return [f'border-left: 5px solid {color}; background-color: #161922; font-weight: 600;'] * len(row)

        render_table = df[['ML Predicted Finish', 'grid', 'driver', 'team', 'Lap Pace Delta (s)', 'Net Positions Change']].copy()
        render_table.columns = ['P_FINISH', 'GRID_START', 'DRIVER', 'team', 'LAP_DELTA', 'POSITION_CHANGE']
        
        styled_df = render_table.style.apply(style_team_rows, axis=1).format({
            "LAP_DELTA": "{:+.3f}s", 
            "POSITION_CHANGE": "{:+d}"
        })
        
        st.dataframe(styled_df, hide_index=True, use_container_width=True)

    with tab2:
        leader_total = (track['base_lap_time'] + df.iloc[0]['Lap Pace Delta (s)']) * track['base_laps']
        chart_data = []
        
        for idx, row in df.iterrows():
            total_time = (track['base_lap_time'] + row['Lap Pace Delta (s)']) * track['base_laps']
            chart_data.append({
                "Driver": row['driver'],
                "Gap to Leader (s)": round(total_time - leader_total, 2),
                "Team": row['team']
            })
            
        chart_df = pd.DataFrame(chart_data)
        st.bar_chart(chart_df, x="Driver", y="Gap to Leader (s)", color="Team", use_container_width=True)
                
except Exception as e:
    st.error(f"System Error: {str(e)}")
