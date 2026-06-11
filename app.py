import streamlit as st
import json
import pandas as pd
import os

st.set_page_config(page_title="F1 AI Race Predictor Pro", page_icon="🏎️", layout="wide")

# --- HIGH-FIDELITY CIRCUIT PHYSICS ENGINE ---
CIRCUIT_DB = {
    "catalunya": {
        "name": "Circuit de Barcelona-Catalunya", "bias": "Aero-Heavy", 
        "base_laps": 66, "base_lap_time": 75.0, "overtake_difficulty": 0.7, 
        "fuel_penalty_per_kg": 0.035, "thermal_sensitivity": 0.04
    },
    "monaco": {
        "name": "Circuit de Monaco", "bias": "Mechanical-Grip", 
        "base_laps": 78, "base_lap_time": 72.0, "overtake_difficulty": 0.95, 
        "fuel_penalty_per_kg": 0.022, "thermal_sensitivity": 0.01
    },
    "baku": {
        "name": "Baku City Circuit", "bias": "Top-Speed", 
        "base_laps": 51, "base_lap_time": 103.0, "overtake_difficulty": 0.3, 
        "fuel_penalty_per_kg": 0.040, "thermal_sensitivity": 0.025
    },
    "default": {
        "name": "Grand Prix Premium Circuit", "bias": "Balanced", 
        "base_laps": 55, "base_lap_time": 90.0, "overtake_difficulty": 0.5, 
        "fuel_penalty_per_kg": 0.030, "thermal_sensitivity": 0.02
    }
}

# --- EXTENDED DRIVER SKILL VECTOR DATABASE ---
DRIVER_TRAITS = {
    "Max Verstappen": {"wet_mastery": 1.25, "tire_management": 1.20, "traffic_combat": 1.15, "street_bias": 1.00},
    "Lewis Hamilton": {"wet_mastery": 1.20, "tire_management": 1.15, "traffic_combat": 1.10, "street_bias": 1.05},
    "Fernando Alonso": {"wet_mastery": 1.15, "tire_management": 1.25, "traffic_combat": 1.20, "street_bias": 1.15},
    "Franco Colapinto": {"wet_mastery": 0.85, "tire_management": 0.95, "traffic_combat": 1.05, "street_bias": 1.10},  
    "Gabriel Bortoleto": {"wet_mastery": 0.90, "tire_management": 1.00, "traffic_combat": 1.00, "street_bias": 1.00},
    "Kimi Antonelli": {"wet_mastery": 1.30, "tire_management": 1.15, "traffic_combat": 1.10, "street_bias": 1.10} # Buffed to reflect actual race pace dominance
}

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
st.caption("Relative Pace Matrix Engine — High-Accuracy Zero-Sum Grid Resolution")
st.markdown("---")

try:
    if os.path.exists("predictions.json") and os.path.getsize("predictions.json") > 0:
        with open("predictions.json", "r") as f:
            raw_data = json.load(f)
    else:
        raw_data = DEFAULT_PREDICTIONS
        
    df = pd.DataFrame(raw_data)
    
    existing_drivers = df['driver'].tolist()
    if "Franco Colapinto" not in existing_drivers:
        df = pd.concat([df, pd.DataFrame([{"grid": 9, "driver": "Franco Colapinto", "team": "Alpine", "predicted_finish": 7.1, "circuit": "catalunya"}])], ignore_index=True)
    if "Gabriel Bortoleto" not in existing_drivers:
        df = pd.concat([df, pd.DataFrame([{"grid": 11, "driver": "Gabriel Bortoleto", "team": "Audi", "predicted_finish": 8.4, "circuit": "catalunya"}])], ignore_index=True)

    unique_teams = sorted(df['team'].unique())
    unique_drivers = sorted(df['driver'].unique())

    # --- SIDEBAR CONTROL CENTER ---
    st.sidebar.header("🕹️ Strategy Control Unit")
    
    st.sidebar.subheader("🌦️ Race Climate Engine")
    weather_state = st.sidebar.selectbox("Track Surface Condition", ["Dry Baseline", "Damp / Greasy", "Heavy Monsoon Wet"])
    track_temp = st.sidebar.slider("Track Temperature (°C)", 15, 60, 35)

    st.sidebar.subheader("🔋 Energy & Weight Architecture")
    fuel_load = st.sidebar.slider("Initial Fuel Target (kg)", 95, 110, 100)
    ers_mode = st.sidebar.selectbox("ERS Deployment Curve", ["Balanced Harvest", "Overtake Mode Peak", "Battery Conserve"])

    # UI Sliders are now explicitly labeled for performance gains (+) or losses (-)
    st.sidebar.subheader("🛠️ Constructor Performance Upgrades")
    team_modifiers = {}
    for team in unique_teams:
        team_modifiers[team] = st.sidebar.slider(f"{team} Pace Shift (s)", -1.0, 1.0, 0.0, step=0.05, help="Negative values reduce lap time (Faster)")

    st.sidebar.subheader("👤 Driver Form Adjustments")
    driver_modifiers = {}
    for driver in unique_drivers:
        driver_modifiers[driver] = st.sidebar.slider(f"{driver} Form Shift (s)", -0.5, 0.5, 0.0, step=0.05, help="Negative values reduce lap time (Faster)")

    # --- ZERO-SUM MATHEMATICAL PACE SIMULATION ---
    track_key = raw_data[0].get("circuit", "catalunya") if raw_data else "catalunya"
    track = CIRCUIT_DB.get(track_key, CIRCUIT_DB["default"])

    def calculate_lap_pace_delta(row):
        # FIX 1: Map the baseline ML position to a wider, realistic lap time gap structure
        # A predicted finish of P1.2 gives an initial pace advantage over lower grid entries
        base_pace = (float(row['predicted_finish']) - 1.0) * 0.45 
        
        team = row['team']
        driver = row['driver']
        grid = int(row['grid'])
        
        traits = DRIVER_TRAITS.get(driver, {"wet_mastery": 1.0, "tire_management": 1.0, "traffic_combat": 1.0, "street_bias": 1.0})
        
        # FIX 2: Sliders are added directly. User subtracts seconds to go faster or adds to go slower.
        if team in team_modifiers:
            base_pace += team_modifiers[team]
        if driver in driver_modifiers:
            base_pace += driver_modifiers[driver]

        # 2. Track Temperature Interactions
        temp_delta = track_temp - 35
        if temp_delta > 0:
            base_pace += (temp_delta * track["thermal_sensitivity"]) / traits["tire_management"]
        else:
            base_pace += (abs(temp_delta) * 0.015) * (2.0 - traits["tire_management"])

        # 3. Fuel Mass Dynamics
        fuel_delta = fuel_load - 100
        base_pace += (fuel_delta * track["fuel_penalty_per_kg"])

        # 4. Energy Deployment Logic (Faster drivers utilize deployment more effectively)
        if ers_mode == "Overtake Mode Peak":
            base_pace -= 0.35 * traits["traffic_combat"]
        elif ers_mode == "Battery Conserve":
            base_pace += 0.45 * (1.5 - traits["tire_management"])

        # 5. Dynamic Climate Physics
        if weather_state == "Damp / Greasy":
            base_pace += 2.0 * (1.5 - traits["wet_mastery"])
        elif weather_state == "Heavy Monsoon Wet":
            base_pace += 5.0 * (2.0 - traits["wet_mastery"])
            if track["bias"] == "Aero-Heavy":
                base_pace -= 0.3

        # 6. Non-Linear Grid Traffic Penalty
        if grid > 1:
            traffic_penalty = ((grid - 1) * 0.08) * track["overtake_difficulty"] / traits["traffic_combat"]
            base_pace += traffic_penalty

        return base_pace

    # Apply corrected calculations
    df['Lap Pace Delta (s)'] = df.apply(calculate_lap_pace_delta, axis=1)
    
    # Sort strictly by lap times (Lowest lap time delta = Fastest)
    df = df.sort_values(by='Lap Pace Delta (s)').reset_index(drop=True)
    df['ML Predicted Finish'] = df.index + 1  
    
    df['Net Positions Change'] = df['grid'] - df['ML Predicted Finish']
    
    winner = df.iloc[0]
    podium = df.iloc[1:3]
    top_charger = df.sort_values(by="Net Positions Change", ascending=False).iloc[0]

    # --- MAIN INTERACTIVE DISPLAY PANEL ---
    with st.expander(f"🏟️ LIVE CIRCUIT DESIGN SPECS: {track['name'].upper()}", expanded=True):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Track Characteristic", track["bias"])
        m2.metric("Base Benchmark Laptime", f"{track['base_lap_time']:.1f}s")
        m3.metric("Overtake Resistance Factor", f"{int(track['overtake_difficulty']*100)}%")
        m4.metric("Scheduled Distance", f"{track['base_laps']} Laps")

    st.subheader("📊 Live Predictive Strategy Insights")
    h1, h2, h3 = st.columns(3)
    with h1:
        st.error(f"🏆 PROJECTED WINNER\n\n**{winner['driver']}**\n\n*Team: {winner['team']} | Pace Offset: {winner['Lap Pace Delta (s)']:.3f}s/lap*")
    with h2:
        st.warning(f"🥈 / 🥉 TARGETED PODIUM LOCKS\n\n" + "\n\n".join([f"• **{r['driver']}** ({r['team']}) - P{int(r['ML Predicted Finish'])}" for _, r in podium.iterrows()]))
    with h3:
        if top_charger['Net Positions Change'] > 0:
            st.success(f"🚀 AI CHOSEN FIELD OVERTAKER\n\n**{top_charger['driver']}**\n\n*Starting P{int(top_charger['grid'])} → Finishing P{int(top_charger['ML Predicted Finish'])} (+{int(top_charger['Net Positions Change'])} Positions)*")
        else:
            st.info("🔒 COMBAT LOCK PREDICTED\n\nNo driver has found enough tactical delta to execute high field verticality.")

    st.markdown("---")

    # --- TABBED WORKSPACE ECOSYSTEM ---
    tab1, tab2 = st.tabs(["🏁 Simulation Standings", "📊 Advanced Telemetry Analytics"])

    with tab1:
        st.subheader("Live Computed Field Standings")
        render_table = df[['ML Predicted Finish', 'grid', 'driver', 'team', 'Lap Pace Delta (s)', 'Net Positions Change']].copy()
        render_table.columns = ['Projected Finish', 'Grid Start', 'Driver Lineup', 'Constructor / Team', 'Lap Pace Delta (s)', 'Net Delta']
        
        st.dataframe(
            render_table.style.background_gradient(cmap="coolwarm", subset=['Lap Pace Delta (s)'])
            .format({"Lap Pace Delta (s)": "{:+.3f}s", "Net Delta": "{:+d}", "Grid Start": "{:d}", "Projected Finish": "P{:d}"}),
            hide_index=True,
            use_container_width=True
        )

    with tab2:
        st.subheader("Stint Degradation & Telemetry Projections")
        
        telemetry_records = []
        for idx, row in df.iterrows():
            d_profile = DRIVER_TRAITS.get(row['driver'], {"wet_mastery": 1.0, "tire_management": 1.0})
            simulated_total_time = (track['base_lap_time'] + row['Lap Pace Delta (s)']) * track['base_laps']
            hours = int(simulated_total_time // 3600)
            minutes = int((simulated_total_time % 3600) // 60)
            seconds = round(simulated_total_time % 60, 3)
            
            telemetry_records.append({
                "Finishing Order": f"P{idx+1}",
                "Driver Lineup": row['driver'],
                "Constructor / Team": row['team'],
                "Simulated Theoretical Total Race Time": f"{hours:02d}:{minutes:02d}:{seconds:06.3f}",
                "Estimated Tire Wear/Lap": f"{round(0.95 + (track_temp * 0.004) / d_profile['tire_management'], 3)}%"
            })
            
        st.dataframe(pd.DataFrame(telemetry_records), hide_index=True, use_container_width=True)
    
except Exception as e:
    st.error(f"Execution Error: {str(e)}")
