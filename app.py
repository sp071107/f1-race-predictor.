import streamlit as st
import json
import pandas as pd
import os

st.set_page_config(page_title="F1 AI Race Predictor Pro", page_icon="🏎️", layout="wide")

# --- CORE CIRCUIT INTELLIGENCE DATABASE ---
CIRCUIT_DB = {
    "catalunya": {
        "name": "Circuit de Barcelona-Catalunya", "bias": "Aero-Heavy", 
        "sc_prob": "35%", "tyre_wear": "High (Lateral)"
    },
    "monaco": {
        "name": "Circuit de Monaco", "bias": "Mechanical-Grip", 
        "sc_prob": "80%", "tyre_wear": "Very Low"
    },
    "baku": {
        "name": "Baku City Circuit", "bias": "Top-Speed", 
        "sc_prob": "90%", "tyre_wear": "Medium"
    },
    "default": {
        "name": "Grand Prix Premium Circuit", "bias": "Balanced", 
        "sc_prob": "45%", "tyre_wear": "Medium"
    }
}

# --- EXTENDED DRIVER PROFILE REGISTRY (Weather Masteries) ---
DRIVER_TRAITS = {
    "Max Verstappen": {"wet_mastery": 1.2},
    "Lewis Hamilton": {"wet_mastery": 1.2},
    "Fernando Alonso": {"wet_mastery": 1.0},
    "Franco Colapinto": {"wet_mastery": 0.8},  
    "Gabriel Bortoleto": {"wet_mastery": 0.8},
    "Kimi Antonelli": {"wet_mastery": 0.9}
}

# --- AUTOMATIC DATA COMPILATION LAYER ---
# Directly injects the missing drivers and their correct team configurations 
# into the runtime state if the baseline JSON file is incomplete.
DEFAULT_PREDICTIONS = [
    {"grid": 1, "driver": "Kimi Antonelli", "team": "Mercedes", "predicted_finish": 1.2, "circuit": "catalunya"},
    {"grid": 2, "driver": "Max Verstappen", "team": "Red Bull Racing", "predicted_finish": 2.0, "circuit": "catalunya"},
    {"grid": 3, "driver": "Lando Norris", "team": "McLaren", "predicted_finish": 2.5, "circuit": "catalunya"},
    {"grid": 4, "driver": "Charles Leclerc", "team": "Ferrari", "predicted_finish": 3.1, "circuit": "catalunya"},
    {"grid": 5, "driver": "Oscar Piastri", "team": "McLaren", "predicted_finish": 4.0, "circuit": "catalunya"},
    {"grid": 6, "driver": "Lewis Hamilton", "team": "Ferrari", "predicted_finish": 4.8, "circuit": "catalunya"},
    {"grid": 7, "driver": "George Russell", "team": "Mercedes", "predicted_finish": 5.2, "circuit": "catalunya"},
    {"grid": 8, "driver": "Carlos Sainz", "team": "Williams", "predicted_finish": 6.5, "circuit": "catalunya"},
    {"grid": 9, "driver": "Franco Colapinto", "team": "Alpine", "predicted_finish": 7.1, "circuit": "catalunya"},
    {"grid": 10, "driver": "Pierre Gasly", "team": "Alpine", "predicted_finish": 7.8, "circuit": "catalunya"},
    {"grid": 11, "driver": "Gabriel Bortoleto", "team": "Audi", "predicted_finish": 8.4, "circuit": "catalunya"},
    {"grid": 12, "driver": "Nico Hülkenberg", "team": "Audi", "predicted_finish": 8.9, "circuit": "catalunya"},
    {"grid": 13, "driver": "Alexander Albon", "team": "Williams", "predicted_finish": 9.5, "circuit": "catalunya"},
    {"grid": 14, "driver": "Yuki Tsunoda", "team": "RB", "predicted_finish": 10.2, "circuit": "catalunya"},
    {"grid": 15, "driver": "Liam Lawson", "team": "RB", "predicted_finish": 11.0, "circuit": "catalunya"},
    {"grid": 16, "driver": "Lance Stroll", "team": "Aston Martin", "predicted_finish": 12.1, "circuit": "catalunya"},
    {"grid": 17, "driver": "Fernando Alonso", "team": "Aston Martin", "predicted_finish": 12.5, "circuit": "catalunya"},
    {"grid": 18, "driver": "Oliver Bearman", "team": "Haas", "predicted_finish": 13.8, "circuit": "catalunya"},
    {"grid": 19, "driver": "Esteban Ocon", "team": "Haas", "predicted_finish": 14.2, "circuit": "catalunya"}
]

st.title("🏎️ Formula 1 Race Principal Simulation Console")
st.caption("Advanced dynamic telemetry simulation platform with built-in 2026 driver grid layouts.")
st.markdown("---")

try:
    # Attempt to load baseline data, fallback to compiled list if missing or empty
    if os.path.exists("predictions.json") and os.path.getsize("predictions.json") > 0:
        with open("predictions.json", "r") as f:
            raw_data = json.load(f)
    else:
        raw_data = DEFAULT_PREDICTIONS
        
    df = pd.DataFrame(raw_data)
    
    # Verify that Franco and Gabriel are hard-coded into the runtime data frame if missing
    existing_drivers = df['driver'].tolist()
    if "Franco Colapinto" not in existing_drivers:
        df = pd.concat([df, pd.DataFrame([{"grid": 9, "driver": "Franco Colapinto", "team": "Alpine", "predicted_finish": 7.1, "circuit": "catalunya"}])], ignore_index=True)
    if "Gabriel Bortoleto" not in existing_drivers:
        df = pd.concat([df, pd.DataFrame([{"grid": 11, "driver": "Gabriel Bortoleto", "team": "Audi", "predicted_finish": 8.4, "circuit": "catalunya"}])], ignore_index=True)

    # Unique metadata parsing for UI controls
    unique_teams = sorted(df['team'].unique())
    unique_drivers = sorted(df['driver'].unique())

    # --- SIDEBAR CONTROL CENTER ---
    st.sidebar.header("🕹️ Strategy Control Unit")
    
    # 1. Environmental Controls
    st.sidebar.subheader("🌦️ Race Climate Engine")
    weather_state = st.sidebar.selectbox("Track Surface Condition", ["Dry Baseline", "Damp / Greasy", "Heavy Monsoon Wet"])
    track_temp = st.sidebar.slider("Track Temperature (°C)", 15, 60, 35)

    # 2. Dynamic Team Upgrade Modifiers
    st.sidebar.subheader("🛠️ Constructor Development Pace")
    team_modifiers = {}
    for team in unique_teams:
        team_modifiers[team] = st.sidebar.slider(
            f"{team} Dev Delta", 
            min_value=-2.0, 
            max_value=2.0, 
            value=0.0, 
            step=0.1
        )

    # 3. Dynamic Driver Momentum Filters
    st.sidebar.subheader("👤 Driver Form Adjustments")
    driver_modifiers = {}
    for driver in unique_drivers:
        driver_modifiers[driver] = st.sidebar.slider(
            f"{driver} Performance Index", 
            min_value=0.5, 
            max_value=1.5, 
            value=1.0, 
            step=0.05
        )

    # --- MATHEMATICAL COMPUTE MATRIX ---
    def execute_live_simulation(row):
        pred = float(row['predicted_finish'])
        team = row['team']
        driver = row['driver']
        
        if team in team_modifiers:
            pred += team_modifiers[team]
            
        if driver in driver_modifiers:
            pred *= driver_modifiers[driver]
            
        driver_profile = DRIVER_TRAITS.get(driver, {"wet_mastery": 0.5})
        wet_skill = driver_profile["wet_mastery"]

        if weather_state == "Damp / Greasy":
            pred -= (0.5 * wet_skill)
        elif weather_state == "Heavy Monsoon Wet":
            pred -= (1.0 * wet_skill)
            if "catalunya" in row.get("circuit", "catalunya") and CIRCUIT_DB["catalunya"]["bias"] == "Aero-Heavy":
                pred -= 0.4
                
        return max(1.0, min(20.0, pred))

    # Re-compute standings
    df['ML Predicted Finish'] = df.apply(execute_live_simulation, axis=1)
    df = df.sort_values(by="ML Predicted Finish").reset_index(drop=True)
    
    df['Net Positions Change'] = df['grid'] - df['ML Predicted Finish']
    winner = df.iloc[0]
    podium = df.iloc[1:3]
    top_charger = df.sort_values(by="Net Positions Change", ascending=False).iloc[0]

    # --- UI RENDER LAYOUT ---
    track_key = raw_data[0].get("circuit", "catalunya") if raw_data else "catalunya"
    track = CIRCUIT_DB.get(track_key, CIRCUIT_DB["default"])
    
    with st.expander(f"🏟️ LIVE TRACK INTELLIGENCE PROFILE: {track['name'].upper()}", expanded=True):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Track Focus Bias", track["bias"])
        m2.metric("Safety Car Probability", track["sc_prob"])
        m3.metric("Tire Wear Degradation", track["tyre_wear"])
        m4.metric("Current Track Surface Temp", f"{track_temp}°C")

    st.subheader("📊 Live Predictive Strategy Insights")
    h1, h2, h3 = st.columns(3)
    
    with h1:
        st.error(f"🏆 PROJECTED WINNER\n\n**{winner['driver']}**\n\n*Team: {winner['team']} | Expected Finish: P{winner['ML Predicted Finish']:.1f}*")
    with h2:
        st.warning(f"🥈 / 🥉 TARGETED PODIUM LOCKS\n\n" + "\n\n".join([f"• **{r['driver']}** ({r['team']}) - P{r['ML Predicted Finish']:.1f}" for _, r in podium.iterrows()]))
    with h3:
        if top_charger['Net Positions Change'] > 0.4:
            st.success(f"🚀 AI CHOSEN FIELD OVERTAKER\n\n**{top_charger['driver']}**\n\n*Starting P{int(top_charger['grid'])} → Finishing P{top_charger['ML Predicted Finish']:.1f}*")
        else:
            st.info("🔒 COMBAT LOCK PREDICTED\n\nMl metrics indicate linear track profiles with low overtake frequency.")

    st.markdown("---")

    st.subheader("🏁 Live Computed Simulation Standings")
    render_table = df[['grid', 'driver', 'team', 'ML Predicted Finish', 'Net Positions Change']].copy()
    render_table.columns = ['Grid Start', 'Driver Lineup', 'Constructor / Team', 'ML Predicted Finish Index', 'Projected Position Net Delta']
    
    st.dataframe(
        render_table.style.background_gradient(cmap="coolwarm", subset=['ML Predicted Finish Index'])
        .format({"ML Predicted Finish Index": "{:.1f}", "Projected Position Net Delta": "{:+.1f}", "Grid Start": "{:d}"}),
        hide_index=True,
        use_container_width=True
    )
    
except Exception as e:
    st.error(f"Execution Error: {str(e)}")
