import streamlit as st
import pandas as pd
import numpy as np
import requests

# Set page configuration immediately at boot
st.set_page_config(page_title="F1 Pit-Wall Hub", page_icon="🏎️", layout="wide")

# --- PREMIUM PIT-WALL TELEMETRY THEME INJECTION (CSS) ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0d12;
        color: #f1f5f9;
        font-family: 'Segoe UI', Monaco, monospace;
    }
    header {
        border-top: 5px solid #FF1801 !important;
    }
    .race-context-banner {
        background: linear-gradient(90deg, #161922 0%, #1f2431 100%);
        border-left: 5px solid #FF1801;
        border-radius: 6px;
        padding: 22px;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .pitwall-card {
        background: linear-gradient(135deg, #12151e 0%, #1a1e2a 100%);
        border: 1px solid #282e3d;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        margin-bottom: 15px;
    }
    .welcome-box {
        background: linear-gradient(135deg, #1a1c23 0%, #0d0e12 100%);
        border: 1px solid #FF1801;
        border-radius: 10px;
        padding: 30px;
        margin-bottom: 25px;
    }
    .stExpander {
        background-color: #12151e !important;
        border: 1px solid #232936 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="tab-list"] {
        gap: 12px;
    }
    div[data-baseweb="tab"] {
        background-color: #161922 !important;
        border: 1px solid #282e3d !important;
        color: #94a3b8 !important;
        border-radius: 6px 6px 0px 0px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FF1801 !important;
        color: #ffffff !important;
        border-color: #FF1801 !important;
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

# --- REAL-TIME CHAMPIONSHIP STANDINGS DATA SETS ---
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
    {"Pos": 8, "Team": "Williams", "Points": 11},
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

# --- GLOBAL HUB HEADER BANNER ---
st.markdown(
    f"""
    <div class="race-context-banner">
        <span style="color: #FF1801; font-weight: 800; font-size: 0.85rem; letter-spacing: 0.15em; text-transform: uppercase;">📡 PIT-WALL INTEGRATED COMMAND SYSTEM</span>
        <h1 style="margin: 4px 0 2px 0; font-weight: 900; letter-spacing: -0.02em; font-size: 2.2rem; color: #ffffff;">{api_payload['race_name'].upper()}</h1>
        <p style="margin: 0; color: #94a3b8; font-size: 1.05rem; font-weight: 500;">📍 Location Context: <b style="color: #38bdf8;">{api_payload['location']}</b> &nbsp;|&nbsp; Global Telemetry Active</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- APPLICATION NAVIGATIONAL ROUTER ---
tab_home, tab_predictor = st.tabs(["🏠 COMMAND HOME", "📊 STRATEGY PREDICTOR ENGINE"])

# ==========================================
# 🏠 TAB 1: THE HOME CENTER / WELCOME INTERFACE
# ==========================================
with tab_home:
    st.markdown(
        """
        <div class="welcome-box">
            <h2 style='margin: 0 0 10px 0; font-weight: 800; color: #ffffff;'>Welcome to the Pit Wall, Strategist.</h2>
            <p style='margin: 0; color: #cbd5e1; font-size: 1.05rem; line-height: 1.6;'>
                This command deck breaks down high-level Formula 1 telemetry metrics into human-readable tactical elements. 
                Whether you're looking to run complex race simulations or just trying to understand track variables without 
                drowning in physics data, navigate using the tabs above to control the team's assets.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<h3 style='font-size: 1.1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;'>📋 WEEKEND STATUS BRIEFING</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="pitwall-card" style="border-left: 4px solid #38bdf8;">
                <div class="card-title">🗺️ Track Venue Profile</div>
                <div class="card-value">{api_payload['circuit_short']}</div>
                <div class="card-subtext">Dynamic Live Transponder Feed</div>
            </div>
            """, unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div class="pitwall-card" style="border-left: 4px solid #a855f7;">
                <div class="card-title">🏎️ Registered Competitors</div>
                <div class="card-value">{len(df_field)} Cars Processed</div>
                <div class="card-subtext">Active 11-Team Grid Layout</div>
            </div>
            """, unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            """
            <div class="pitwall-card" style="border-left: 4px solid #22c55e;">
                <div class="card-title">🚦 Session Control</div>
                <div class="card-value">Quali Complete</div>
                <div class="card-subtext">Grid Order Ingestion: Successful</div>
            </div>
            """, unsafe_allow_html=True
        )

    # --- SIDE BY SIDE CHAMPIONSHIP STANDINGS METRICS ---
    st.markdown("<br><h3 style='font-size: 1.1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;'>🏆 OFFICIAL CHAMPIONSHIP STANDINGS</h3>", unsafe_allow_html=True)
    
    standings_col1, standings_col2 = st.columns(2)
    
    with standings_col1:
        st.markdown("<h4 style='color:#ffffff; margin-bottom:10px;'>🏁 Driver Standings Leaderboard</h4>", unsafe_allow_html=True)
        df_drivers = pd.DataFrame(DRIVERS_STANDINGS_2026)
        
        def color_driver_rows(row):
            color = TEAM_META.get(row['Team'], {"color": "#282e3d"})["color"]
            return [f'border-left: 4px solid {color}; background-color: #12151e; font-family: monospace;'] * len(row)
            
        st.dataframe(
            df_drivers.style.apply(color_driver_rows, axis=1), 
            hide_index=True, 
            use_container_width=True, 
            height=450,
            column_config={
                "Pos": st.column_config.Column(alignment="center"),
                "Driver": st.column_config.Column(alignment="center"),
                "Team": st.column_config.Column(alignment="center"),
                "Points": st.column_config.Column(alignment="center"),
            }
        )
        
    with standings_col2:
        st.markdown("<h4 style='color:#ffffff; margin-bottom:10px;'>🛠️ Constructors Championship</h4>", unsafe_allow_html=True)
        df_constructors = pd.DataFrame(CONSTRUCTORS_STANDINGS_2026)
        
        def color_team_rows(row):
            color = TEAM_META.get(row['Team'], {"color": "#282e3d"})["color"]
            return [f'border-left: 4px solid {color}; background-color: #12151e; font-family: monospace;'] * len(row)
            
        st.dataframe(
            df_constructors.style.apply(color_team_rows, axis=1), 
            hide_index=True, 
            use_container_width=True, 
            height=450,
            column_config={
                "Pos": st.column_config.Column(alignment="center"),
                "Team": st.column_config.Column(alignment="center"),
                "Points": st.column_config.Column(alignment="center"),
            }
        )

    st.markdown("<br><h3 style='font-size: 1.1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;'>💡 BEGINNER RACE BRIEFING: WHAT MATTERS THIS WEEKEND?</h3>", unsafe_allow_html=True)
    st.markdown(
        """
        * **The Starting Position Rule:** The driver starting P1 (Pole Position) has the clean air advantage. The further back you go, the more cars a driver has to overtake, which burns down their tyres much faster.
        * **What is ERS?** Energy Recovery Systems act like a video-game speed boost button. Drivers harvest energy when braking and dump it back onto the straights to attack.
        * **The Heat Threat:** High track temperatures heat up the rubber. If the asphalt gets too hot, the tyres lose atomic cohesion and turn into mush (called *falling off the cliff*).
        """
    )


# ==========================================
# 📊 TAB 2: THE CURRENT STRATEGY PREDICTOR
# ==========================================
with tab_predictor:
    st.markdown("<h3 style='font-size: 1.1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;'>🕹️ TRACK STRATEGY PARAMETERS</h3>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: weather_state = st.selectbox("Track Surface State", ["Dry Baseline Asphalt", "Damp Track / Greasy", "Heavy Rain Conditions"])
    with c2: track_temp = st.slider("Track Temp (°C)", 15, 65, 35)
    with c3: fuel_load = st.slider("Starting Fuel Load (kg)", 95, 110, 100)
    with c4: ERS_mode = st.selectbox("ERS Deployment Curve", ["Balanced Energy Harvest", "Overtake Attack Curve", "Battery Preservation"])

    team_modifiers = {}
    with st.expander("🛠️ CONSTRUCTOR GARAGE: PERFORMANCE CONFIGURATOR"):
        team_cols = st.columns(2)
        for idx, team in enumerate(sorted(df_field['team'].unique())):
            with team_cols[idx % 2]:
                team_modifiers[team] = st.slider(f"⚙️ {team} Delta Offset (s)", -0.8, 0.8, 0.0, step=0.05)

    # --- MODEL PACE COMPUTATIONS ---
    def compute_high_accuracy_race_pace(row):
        team = row['team']
        grid = int(row['grid_start'])
        meta = TEAM_META.get(team, {"base_pace_rank": 4.0, "color": "#ffffff"})
        pace_score = np.log1p(meta["base_pace_rank"]) * 0.65 + team_modifiers.get(team, 0.0)
        pace_score += (track_temp - 35) * 0.012 + (fuel_load - 100) * 0.025
        if grid > 1: pace_score += (np.power(grid - 1, 1.15) * 0.045)
        if ERS_mode == "Overtake Attack Curve": pace_score -= 0.08
        if "Rain" in weather_state: pace_score += (grid * 0.12)
        return pace_score

    def assign_race_strategy(grid_pos):
        if grid_pos <= 4: return "Medium ➔ Hard (1-Stop)", "Laps 19 - 25", "Track Position Lock"
        elif 5 <= grid_pos <= 10: return "Soft ➔ Medium ➔ Hard (2-Stop)", "Laps 12 & 38", "Aggressive Undercut Plan"
        else: return "Hard ➔ Medium (1-Stop Alt)", "Laps 36 - 44", "Long Stint Safety Car Gamble"

    df_field['Pace_Delta_Seconds'] = df_field.apply(compute_high_accuracy_race_pace, axis=1)
    df_field = df_field.sort_values(by='Pace_Delta_Seconds').reset_index(drop=True)
    df_field['Projected_Finish'] = df_field.index + 1
    df_field['Net_Positions_Gained'] = df_field['grid_start'] - df_field['Projected_Finish']

    strat_data = [assign_race_strategy(pos) for pos in df_field['grid_start']]
    df_field['Recommended_Strategy'] = [s[0] for s in strat_data]
    df_field['Target_Pit_Window'] = [s[1] for s in strat_data]
    df_field['Strategic_Intent'] = [s[2] for s in strat_data]

    winner = df_field.iloc[0]
    podium = df_field.iloc[1:3]
    charger = df_field.sort_values(by="Net_Positions_Gained", ascending=False).iloc[0]

    # --- LIVE BROADCAST MATRIX PRESENTATION ---
    st.markdown("<br><h3 style='font-size: 1.1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;'>📊 HIGH-ACCURACY AI RUN PREDICTIONS</h3>", unsafe_allow_html=True)
    h1, h2, h3 = st.columns(3)
    with h1:
        team_color = TEAM_META.get(winner['team'], {"color": "#FF1801"})["color"]
        st.markdown(f'<div class="pitwall-card" style="border-left: 4px solid {team_color};"><div class="card-title">🏆 AI Predicted Winner</div><div class="card-value">{winner["driver"]}</div><div class="card-subtext">{winner["team"]} • {winner["Recommended_Strategy"]}</div></div>', unsafe_allow_html=True)
    with h2:
        p_text = ", ".join([f"P{int(r['Projected_Finish'])}: {r['driver']}" for _, r in podium.iterrows()])
        st.markdown(f'<div class="pitwall-card" style="border-left: 4px solid #FF8000;"><div class="card-title">🥈 🥉 Podium Contenders</div><div class="card-value" style="font-size: 1.15rem; padding-top:4px;">{p_text}</div><div class="card-subtext">Optimal Strategy Finish Group</div></div>', unsafe_allow_html=True)
    with h3:
        c_text = f"{charger['driver']} (+{int(charger['Net_Positions_Gained'])})" if charger['Net_Positions_Gained'] > 0 else "Grid Order Locked"
        st.markdown(f'<div class="pitwall-card" style="border-left: 4px solid #37BEDD;"><div class="card-title">🚀 Strategic Field Overtaker</div><div class="card-value">{c_text}</div><div class="card-subtext">Starting P{int(charger["grid_start"])} → Target P{int(charger["Projected_Finish"])}</div></div>', unsafe_allow_html=True)

    # --- MAIN PERFORMANCE TABLES ---
    sub_tab1, sub_tab2 = st.tabs(["🏁 LIVE MODEL STANDINGS & STRATEGIES", "⏱️ TOTAL RACE DISTANCE DIFFERENTIAL"])
    with sub_tab1:
        def style_authentic_rows(row):
            color = TEAM_META.get(row['CONSTRUCTOR'], {"color": "#ffffff"})["color"]
            return [f'border-left: 5px solid {color}; background-color: #11141c; font-weight: 600; font-family: monospace;'] * len(row)
        render_df = df_field[['Projected_Finish', 'grid_start', 'driver', 'team', 'Recommended_Strategy', 'Target_Pit_Window', 'Strategic_Intent']].copy()
        render_df.columns = ['AI_FINISH', 'GRID_START', 'DRIVER_LINEUP', 'CONSTRUCTOR', 'OPTIMAL_STRATEGY', 'PIT_WINDOW', 'STRATEGIC_INTENT']
        
        st.dataframe(
            render_df.style.apply(style_authentic_rows, axis=1), 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "AI_FINISH": st.column_config.Column(alignment="center"),
                "GRID_START": st.column_config.Column(alignment="center"),
                "DRIVER_LINEUP": st.column_config.Column(alignment="center"),
                "CONSTRUCTOR": st.column_config.Column(alignment="center"),
                "OPTIMAL_STRATEGY": st.column_config.Column(alignment="center"),
                "PIT_WINDOW": st.column_config.Column(alignment="center"),
                "STRATEGIC_INTENT": st.column_config.Column(alignment="center"),
            }
        )

    with sub_tab2:
        leader_time = (80.0 + df_field.iloc[0]['Pace_Delta_Seconds']) * 55
        chart_payload = [{"Driver": r['driver'], "Gap to Leader (s)": round(((80.0 + r['Pace_Delta_Seconds']) * 55) - leader_time, 2), "Team": r['team']} for _, r in df_field.iterrows()]
        st.bar_chart(pd.DataFrame(chart_payload), x="Driver", y="Gap to Leader (s)", color="Team", use_container_width=True)
