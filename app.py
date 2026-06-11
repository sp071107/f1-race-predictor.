import streamlit as st
import json
import pandas as pd
import numpy as np
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

DRIVER_TRAITS = {
    "Max Verstappen": {"wet_mastery": 1.25, "tire_management": 1.20, "traffic_combat": 1.15, "street_bias": 1.00},
    "Lewis Hamilton": {"wet_mastery": 1.20, "tire_management": 1.15, "traffic_combat": 1.10, "street_bias": 1.05},
    "Fernando Alonso": {"wet_mastery": 1.15, "tire_management": 1.25, "traffic_combat": 1.20, "street_bias": 1.15},
    "Franco Colapinto": {"wet_mastery": 0.85, "tire_management": 0.95, "traffic_combat": 1.05, "street_bias": 1.10},  
    "Gabriel Bortoleto": {"wet_mastery": 0.90, "tire_management": 1.00, "traffic_combat": 1.00, "street_bias": 1.00},
    "Kimi Antonelli": {"wet_mastery": 1.35, "tire_management": 1.20, "traffic_combat": 1.10, "street_bias": 1.10} 
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
st.caption("Exponential Field Delta Matrix & Visual Strategy Predictor Engine")
st.markdown("---")

try:
    if os.path.exists("predictions.json") and os.path.getsize("predictions.json") > 0:
        with open("predictions.json", "r") as f:
            raw_data = json.load(f)
    else:
        raw_data = DEFAULT_PREDICTIONS
        
    df = pd.DataFrame(raw_data)
    unique_teams = sorted(df['team'].unique())
    unique_drivers = sorted(df['driver'].unique())

    # Helper function to turn abstract math values into plain-English tactical labels
    def get_modifier_label(val):
        if val < -0.3: return f"{val:+.2f}s (🚀 Massive Upgrade)"
        if val < 0: return f"{val:+.2f}s (📈 Minor Advantage)"
        if val > 0.3: return f"{val:+.2f}s (🐌 Severe Penalty)"
        if val > 0: return f"{val:+.2f}s (📉 Slight Deficit)"
        return "0.00s (Baseline Standard)"

    # --- MAIN SCREEN INTERACTIVE COMMAND PIT (FORMERLY SIDEBAR) ---
    st.header("🕹️ Grand Prix Strategy & Setup Terminal")
    st.caption("Adjust environmental conditions or team packages below to recalculate race scenarios live.")

    # Main Environment Rows
    env_col1, env_col2, env_col3 = st.columns(3)
    with env_col1:
        weather_state = st.selectbox("Track Surface Condition", ["Dry Baseline", "Damp / Greasy", "Heavy Monsoon Wet"])
    with env_col2:
        track_temp = st.slider("Track Temperature (°C)", 15, 60, 35)
    with env_col3:
        fuel_load = st.slider("Initial Fuel Target (kg)", 95, 110, 100)
        
    ers_mode = st.radio("ERS Powertrain Deployment Curve", ["Balanced Harvest", "Overtake Mode Peak", "Battery Conserve"], horizontal=True)

    # Collapsible Upgrades Section to clean up page layout
    team_modifiers = {}
    driver_modifiers = {}

    with st.expander("🛠️ CONSTRUCTOR GARAGE: Develop Team Car Upgrades"):
        st.caption("Move slider left (-) to bolt on faster upgrades, or right (+) to apply performance handicaps.")
        # Render sliders inside clean 2-column configurations
        team_cols = st.columns(2)
        for idx, team in enumerate(unique_teams):
            col_target = team_cols[idx % 2]
            with col_target:
                raw_team_val = st.slider(f"{team} Performance Core Adjust", -1.0, 1.0, 0.0, step=0.05, key=f"team_{team}")
                team_modifiers[team] = raw_team_val
                st.markdown(f"**Current Delta:** `{get_modifier_label(raw_team_val)}`")

    with st.expander("👤 DRIVER COCKPIT: Form and Driver Focus Controls"):
        st.caption("Modify real-time mental focus, weekend form, or physical pace variance adjustments.")
        driver_cols = st.columns(3)
        for idx, driver in enumerate(unique_drivers):
            col_target = driver_cols[idx % 3]
            with col_target:
                raw_driver_val = st.slider(f"{driver} Form Rating", -0.5, 0.5, 0.0, step=0.05, key=f"driver_{driver}")
                driver_modifiers[driver] = raw_driver_val
                st.markdown(f"**Form Feedback:** `{get_modifier_label(raw_driver_val)}`")

    # --- SIMULATION CORE MATHEMATICS ---
    track_key = raw_data[0].get("circuit", "catalunya") if raw_data else "catalunya"
    track = CIRCUIT_DB.get(track_key, CIRCUIT_DB["default"])

    def calculate_lap_pace_delta(row):
        raw_rank_val = float(row['predicted_finish'])
        base_pace = np.log1p(raw_rank_val - 1.0) * 0.75 
        
        team = row['team']
        driver = row['driver']
        grid = int(row['grid'])
        
        traits = DRIVER_TRAITS.get(driver, {"wet_mastery": 1.0, "tire_management": 1.0, "traffic_combat": 1.0, "street_bias": 1.0})
        
        if team in team_modifiers:
            base_pace += team_modifiers[team]
        if driver in driver_modifiers:
            base_pace += driver_modifiers[driver]

        temp_delta = track_temp - 35
        if temp_delta > 0:
            base_pace += (temp_delta * track["thermal_sensitivity"]) / traits["tire_management"]
        else:
            base_pace += (abs(temp_delta) * 0.015) * (2.0 - traits["tire_management"])

        fuel_delta = fuel_load - 100
        base_pace += (fuel_delta * track["fuel_penalty_per_kg"])

        if ers_mode == "Overtake Mode Peak":
            base_pace -= 0.40 * traits["traffic_combat"]
        elif ers_mode == "Battery Conserve":
            base_pace += 0.55 * (1.5 - traits["tire_management"])

        if weather_state == "Damp / Greasy":
            base_pace += 2.5 * (1.5 - traits["wet_mastery"])
        elif weather_state == "Heavy Monsoon Wet":
            base_pace += 6.0 * (2.0 - traits["wet_mastery"])

        if grid > 1:
            traffic_penalty = (np.power(grid - 1, 1.25) * 0.09) * (track["overtake_difficulty"] / traits["traffic_combat"])
            base_pace += traffic_penalty

        return base_pace

    # Apply core math processing
    df['Lap Pace Delta (s)'] = df.apply(calculate_lap_pace_delta, axis=1)
    df = df.sort_values(by='Lap Pace Delta (s)').reset_index(drop=True)
    df['ML Predicted Finish'] = df.index + 1  
    df['Net Positions Change'] = df['grid'] - df['ML Predicted Finish']
    
    winner = df.iloc[0]
    podium = df.iloc[1:3]
    top_charger = df.sort_values(by="Net Positions Change", ascending=False).iloc[0]

    # --- OUTPUT & PRESENTATION PANEL ---
    st.markdown("---")
    with st.expander(f"🏟️ LIVE CIRCUIT DESIGN SPECS: {track['name'].upper()}", expanded=False):
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
            st.info("🔒 COMBAT LOCK PREDICTED\n\nField positions stabilizing down sector chains.")

    tab1, tab2 = st.tabs(["🏁 Simulation Standings", "📊 Visual Strategy & Race Gaps"])

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
        st.subheader("⏱️ Race Deficit to Leader (Total Grand Prix Gap)")
        st.caption("This chart displays exactly how many seconds behind the race leader each driver is projected to cross the finish line.")
        
        leader_total_time = (track['base_lap_time'] + df.iloc[0]['Lap Pace Delta (s)']) * track['base_laps']
        
        chart_data = []
        for idx, row in df.iterrows():
            driver_total_time = (track['base_lap_time'] + row['Lap Pace Delta (s)']) * track['base_laps']
            gap_to_leader = driver_total_time - leader_total_time
            
            d_profile = DRIVER_TRAITS.get(row['driver'], {"wet_mastery": 1.0, "tire_management": 1.0})
            wear_factor = 0.95 + (track_temp * 0.004) / d_profile['tire_management']
            
            if wear_factor > 1.14:
                strategy_tag = "⚠️ Extreme Wear: High 2-Pit Mandatory"
            elif wear_factor > 1.06:
                strategy_tag = "📈 Moderate Deg: 1-Pit Aggressive / 2-Pit Safe"
            else:
                strategy_tag = "✅ Optimal Curve: Comfortable 1-Pit Stop"

            chart_data.append({
                "Driver": row['driver'],
                "Gap to Leader (Seconds)": round(gap_to_leader, 2),
                "Team": row['team'],
                "Pace Classification Strategy": strategy_tag
            })
            
        chart_df = pd.DataFrame(chart_data)
        st.bar_chart(chart_df, x="Driver", y="Gap to Leader (Seconds)", color="Team", use_container_width=True)
        
        st.subheader("💡 Race Engineering Tactical Readout")
        for idx, row in chart_df.iterrows():
            if idx == 0:
                st.write(f"🥇 **{row['Driver']}** is controlling the clean air up front, managing the field baseline pace.")
            else:
                st.write(f"• **P{idx+1} | {row['Driver']}** ({row['Team']}): +{row['Gap to Leader (Seconds)']}s behind leader. Strategy Profile: `{row['Pace Classification Strategy']}`")
                
except Exception as e:
    st.error(f"Execution Error: {str(e)}")
