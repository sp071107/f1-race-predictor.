import streamlit as st
import json
import pandas as pd

st.set_page_config(page_title="F1 AI Race Predictor Pro", page_icon="🏎️", layout="wide")

# --- CORE CIRCUIT INTELLIGENCE DATABASE ---
CIRCUIT_DB = {
    "catalunya": {
        "name": "Circuit de Barcelona-Catalunya", "turns": 14, "drs_zones": 2, 
        "sc_prob": "35%", "tyre_wear": "High (Lateral)", "bias": "Aero-Heavy"
    },
    "monaco": {
        "name": "Circuit de Monaco", "turns": 19, "drs_zones": 1, 
        "sc_prob": "80%", "tyre_wear": "Very Low", "bias": "Mechanical-Grip"
    },
    "baku": {
        "name": "Baku City Circuit", "turns": 20, "drs_zones": 2, 
        "sc_prob": "90%", "tyre_wear": "Medium", "bias": "Top-Speed"
    },
    "default": {
        "name": "Grand Prix Premium Circuit", "turns": 18, "drs_zones": 2, 
        "sc_prob": "45%", "tyre_wear": "Medium", "bias": "Balanced"
    }
}

# --- APPLICATION HEADER ---
st.title("🏎️ Formula 1 Race Principal Simulation Console")
st.caption("Advanced multi-variable regression architecture tracking live environmental mutations and machine learning weight variations.")
st.markdown("---")

# --- SIDEBAR CONTROL CENTER ---
st.sidebar.header("🕹️ Strategy Control Unit")

# 1. Environmental Controls
st.sidebar.subheader("🌦️ Race Climate Engine")
weather_state = st.sidebar.selectbox("Track Surface Condition", ["Dry Baseline", "Damp / Greasy", "Heavy Monsoon Wet"])
track_temp = st.sidebar.slider("Track Temperature (°C)", 15, 60, 35)

# 2. Dynamic Team Upgrade Modifiers
st.sidebar.subheader("🛠️ Constructor Development Pace")
st.sidebar.caption("Adjust mid-season upgrade performance indexes:")
mclaren_mod = st.sidebar.slider("McLaren Chassis Dev", -1.5, 1.5, -0.4, step=0.1, help="Negative values lower the finishing position (faster pace).")
ferrari_mod = st.sidebar.slider("Ferrari Power Unit Dev", -1.5, 1.5, -0.2, step=0.1)
mercedes_mod = st.sidebar.slider("Mercedes Aero Package", -1.5, 1.5, -0.5, step=0.1)
redbull_mod = st.sidebar.slider("Red Bull Suspension Dev", -1.5, 1.5, 0.3, step=0.1)

# 3. Individual Driver Momentum Filters
st.sidebar.subheader("👤 Driver Form Adjustments")
kimi_form = st.sidebar.slider("Kimi Antonelli Hot Streak Index", 0.5, 3.0, 1.0, step=0.1, help="Lower multipliers reward high-frequency peak driver performance.")
leclerc_form = st.sidebar.slider("Charles Leclerc Quali Trim", 0.5, 3.0, 1.0, step=0.1)

# --- ENGINE LOGIC & SIMULATION DATA RUNNER ---
try:
    with open("predictions.json", "r") as f:
        raw_data = json.load(f)
        
    df = pd.DataFrame(raw_data)
    
    # Identify circuit parameters
    target_circuit = raw_data[0].get("circuit", "catalunya") if raw_data else "catalunya"
    track = CIRCUIT_DB.get(target_circuit, CIRCUIT_DB["default"])
    
    # --- LIVE MATHEMATICAL MUTATION MATRIX ---
    def execute_what_if_simulation(row):
        pred = row['predicted_finish']
        team = row['team'].upper()
        driver = row['driver']
        
        # Apply Team Upgrade Deltas
        if "MCLAREN" in team: pred += mclaren_mod
        elif "FERRARI" in team: pred += ferrari_mod
        elif "MERCEDES" in team: pred += mercedes_mod
        elif "RED BULL" in team: pred += redbull_mod
        
        # Apply Driver Momentum Values
        if "Kimi Antonelli" in driver: pred *= kimi_form
        elif "Leclerc" in driver: pred *= leclerc_form
        
        # Apply Weather Volatility Math
        if weather_state == "Damp / Greasy":
            # Veteran drivers gain a minor positioning bump in slick conditions
            if driver in ["Lewis Hamilton", "Max Verstappen", "Fernando Alonso"]:
                pred -= 0.6
        elif weather_state == "Heavy Monsoon Wet":
            if driver in ["Lewis Hamilton", "Max Verstappen"]:
                pred -= 1.2
            # High-downforce biased cars excel in heavy water logs
            if track["bias"] == "Aero-Heavy":
                pred -= 0.4
                
        # Enforce physical racing boundaries (Can't finish better than P1 or worse than P20)
        return max(1.0, min(20.0, pred))

    # Re-compute data table on the fly based on user state changes
    df['ML Predicted Finish'] = df.apply(execute_what_if_simulation, axis=1)
    df = df.sort_values(by="ML Predicted Finish").reset_index(drop=True)
    
    # Calculate Live Visual Statistics
    df['Net Positions Change'] = df['grid'] - df['ML Predicted Finish']
    winner = df.iloc[0]
    podium = df.iloc[1:3]
    top_charger = df.sort_values(by="Net Positions Change", ascending=False).iloc[0]

    # --- UI COMPONENT 1: CIRCUIT PROFILE EXPANDER ---
    with st.expander(f"🏟️ LIVE TRACK INTELLIGENCE PROFILE: {track['name'].upper()}", expanded=True):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Track Focus Bias", track["bias"])
        m2.metric("Safety Car Probability", track["sc_prob"])
        m3.metric("Tire Wear Degradation", track["tyre_wear"])
        m4.metric("Current Track Surface Temp", f"{track_temp}°C")

    # --- UI COMPONENT 2: DYNAMIC EXECUTIVE HIGHLIGHT CARDS ---
    st.subheader("📊 Live Predictive Strategy Insights")
    h1, h2, h3 = st.columns(3)
    
    with h1:
        st.error(f"🏆 PROJECTED WINNER\n\n**{winner['driver']}**\n\n*Team: {winner['team']} | Index: P{winner['ML Predicted Finish']:.1f}*")
    with h2:
        st.warning(f"🥈 / 🥉 TARGETED PODIUM LOCKS\n\n" + "\n\n".join([f"• **{r['driver']}** ({r['team']}) - P{r['ML Predicted Finish']:.1f}" for _, r in podium.iterrows()]))
    with h3:
        if top_charger['Net Positions Change'] > 0.4:
            st.success(f"🚀 AI CHOSEN FIELD OVERTAKER\n\n**{top_charger['driver']}**\n\n*Starting P{int(top_charger['grid'])} → Finishing P{top_charger['ML Predicted Finish']:.1f}*")
        else:
            st.info("🔒 COMBAT LOCK PREDICTED\n\nTrack layout variables indicate minimal overtakes will succeed across the grid margins.")

    st.markdown("---")

    # --- UI COMPONENT 3: INTERACTIVE STANDINGS MATRIX ---
    st.subheader("🏁 Live Computed Simulation Standings")
    
    render_table = df[['grid', 'driver', 'team', 'ML Predicted Finish', 'Net Positions Change']].copy()
    render_table.columns = ['Grid Start', 'Driver Lineup', 'Constructor / Team', 'ML Predicted Finish Index', 'Projected Position Net Delta']
    
    # Style and render beautifully to eliminate raw table boring textures
    st.dataframe(
        render_table.style.background_gradient(cmap="coolwarm", subset=['ML Predicted Finish Index'])
        .format({"ML Predicted Finish Index": "{:.1f}", "Projected Position Net Delta": "{:+.1f}", "Grid Start": "{:d}"}),
        hide_index=True,
        use_container_width=True
    )
    
except FileNotFoundError:
    st.error("Simulation architecture halted. Run the analytical model baseline to compile data states.")
