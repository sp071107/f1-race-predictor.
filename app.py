import streamlit as st
import json
import pandas as pd

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
# Add special traits here if desired, but anyone missing will gracefully fallback!
DRIVER_TRAITS = {
    "Max Verstappen": {"wet_mastery": 1.2},
    "Lewis Hamilton": {"wet_mastery": 1.2},
    "Fernando Alonso": {"wet_mastery": 1.0},
    "Franco Colapinto": {"wet_mastery": 0.8},  # Solid wet weather instinct
    "Gabriel Bortoleto": {"wet_mastery": 0.8}  # Quick adaptability mapping
}

st.title("🏎️ Formula 1 Race Principal Simulation Console")
st.caption("Advanced data-driven simulation platform featuring zero driver restrictions.")
st.markdown("---")

try:
    # --- LOAD BASELINE DATA ---
    with open("predictions.json", "r") as f:
        raw_data = json.load(f)
        
    df = pd.DataFrame(raw_data)
    
    # Safely extract target circuit configurations
    target_circuit = raw_data[0].get("circuit", "catalunya") if raw_data else "catalunya"
    track = CIRCUIT_DB.get(target_circuit, CIRCUIT_DB["default"])
    
    # ─── DYNAMIC METADATA EXTRACTION ───
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

    # --- ROBUST MATHEMATICAL MUTATION ARCHITECTURE ---
    def execute_live_simulation(row):
        pred = float(row['predicted_finish'])
        team = row['team']
        driver = row['driver']
        
        # Apply extracted team delta upgrades
        if team in team_modifiers:
            pred += team_modifiers[team]
            
        # Apply extracted individual driver hot streaks
        if driver in driver_modifiers:
            pred *= driver_modifiers[driver]
            
        # DYNAMIC WEATHER PROFILE SYSTEM (No longer hardcoded!)
        # Check if driver has specific weather profiles, otherwise assign generic baseline
        driver_profile = DRIVER_TRAITS.get(driver, {"wet_mastery": 0.5})
        wet_skill = driver_profile["wet_mastery"]

        if weather_state == "Damp / Greasy":
            pred -= (0.5 * wet_skill)
        elif weather_state == "Heavy Monsoon Wet":
            pred -= (1.0 * wet_skill)
            if track["bias"] == "Aero-Heavy":
                pred -= 0.4
                
        # Clamp bounds strictly between P1 and P20
        return max(1.0, min(20.0, pred))

    # Re-compute standings matrix instantly on interactive changes
    df['ML Predicted Finish'] = df.apply(execute_live_simulation, axis=1)
    df = df.sort_values(by="ML Predicted Finish").reset_index(drop=True)
    
    # Calculate Live Visual Statistics
    df['Net Positions Change'] = df['grid'] - df['ML Predicted Finish']
    winner = df.iloc[0]
    podium = df.iloc[1:3]
    top_charger = df.sort_values(by="Net Positions Change", ascending=False).iloc[0]

    # --- UI COMPONENT 1: TRACK PROFILE ---
    with st.expander(f"🏟️ LIVE TRACK INTELLIGENCE PROFILE: {track['name'].upper()}", expanded=True):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Track Focus Bias", track["bias"])
        m2.metric("Safety Car Probability", track["sc_prob"])
        m3.metric("Tire Wear Degradation", track["tyre_wear"])
        m4.metric("Current Track Surface Temp", f"{track_temp}°C")

    # --- UI COMPONENT 2: STRATEGIC HEADLINE HIGHLIGHTS ---
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
            st.info("🔒 COMBAT LOCK PREDICTED\n\nMinimal overtaking delta expected based on current dynamic tracking weights.")

    st.markdown("---")

    # --- UI COMPONENT 3: INTERACTIVE LEADERBOARD MATRIX ---
    st.subheader("🏁 Live Computed Simulation Standings")
    
    render_table = df[['grid', 'driver', 'team', 'ML Predicted Finish', 'Net Positions Change']].copy()
    render_table.columns = ['Grid Start', 'Driver Lineup', 'Constructor / Team', 'ML Predicted Finish Index', 'Projected Position Net Delta']
    
    st.dataframe(
        render_table.style.background_gradient(cmap="coolwarm", subset=['ML Predicted Finish Index'])
        .format({"ML Predicted Finish Index": "{:.1f}", "Projected Position Net Delta": "{:+.1f}", "Grid Start": "{:d}"}),
        hide_index=True,
        use_container_width=True
    )
    
except FileNotFoundError:
    st.error("Simulation architecture halted. Ensure predictions.json file path is compiled and available.")
