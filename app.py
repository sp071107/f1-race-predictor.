import streamlit as st
import json
import pandas as pd

st.set_page_config(page_title="F1 AI Race Predictor Pro", page_icon="🏎️", layout="wide")

# Mock database of current form / last 3 races average to simulate up-to-date tracks
# (In a production setup, this can be read from a lightweight current_form.json file)
CURRENT_FORM_MAP = {
    "Kimi Antonelli": 1.3,  # Won most recent races, stunning form index
    "Max Verstappen": 3.0,
    "Lando Norris": 2.7,
    "Charles Leclerc": 4.1,
    "Lewis Hamilton": 5.5,
    "Oscar Piastri": 3.8,
}

st.title("🏎️ Formula 1 Race Position Predictor Pro")
st.write("Advanced predictive telemetry deck featuring real-time form-state adaptation algorithms.")

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("🔧 Telemetry Adjustments")
form_weight = st.sidebar.slider(
    "Current Form Weighting (%)", 
    min_value=0, 
    max_value=100, 
    value=50,
    help="Increase to favor recent race streaks (e.g., Kimi's wins). Decrease to rely strictly on season-long baseline data."
)

try:
    with open("predictions.json", "r") as f:
        predictions_data = json.load(f)
        
    df_display = pd.DataFrame(predictions_data)
    
    # --- LIVE DATA ADJUSTMENT MATRIX ---
    # Apply user's selected form weight dynamically to the baseline prediction
    def apply_momentum(row):
        baseline = row['predicted_finish']
        driver = row['driver']
        
        # If we have recent form data for the driver, blend it in
        if driver in CURRENT_FORM_MAP:
            recent_average = CURRENT_FORM_MAP[driver]
            weight_ratio = form_weight / 100.0
            return (baseline * (1 - weight_ratio)) + (recent_average * weight_ratio)
        return baseline

    # Recalculate predictions live based on slider state
    df_display['predicted_finish'] = df_display.apply(apply_momentum, axis=1).round(1)
    
    # --- METRIC STORYLINES ---
    st.subheader("📊 Strategic Race Headlines")
    kp1, kp2 = st.columns(2)
    
    predicted_winner = df_display.sort_values(by="predicted_finish").iloc[0]
    df_display['positions_gained'] = df_display['grid'] - df_display['predicted_finish']
    biggest_mover = df_display.sort_values(by="positions_gained", ascending=False).iloc[0]
    
    with kp1:
        st.info(f"🏅 **AI Projected Winner:** \n**{predicted_winner['driver']}** ({predicted_winner['team']})  \n*Adjusted Expected Finish: P{predicted_winner['predicted_finish']}*")
    with kp2:
        st.success(f"🚀 **Highest Field Climber:** \n**{biggest_mover['driver']}** ({biggest_mover['team']})  \n*Gaining ~{round(biggest_mover['positions_gained'], 1)} positions from grid start*")

    st.markdown("---")

    # --- LEADERBOARD DATAFRAME ---
    st.subheader("🏁 Live Predictive Field Standings")
    
    table_render = df_display[['grid', 'driver', 'team', 'predicted_finish']].sort_values(by="predicted_finish").copy()
    table_render.columns = ['Grid Start', 'Driver Lineup', 'Constructor Team', 'ML Predicted Finish']
    
    st.dataframe(
        table_render.style.background_gradient(cmap="Blues", subset=['ML Predicted Finish'])
        .format({"ML Predicted Finish": "{:.1f}", "Grid Start": "{:d}"}),
        hide_index=True,
        use_container_width=True
    )

except FileNotFoundError:
    st.error("System configuration error. Prediction pipeline files not found.")
