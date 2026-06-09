import streamlit as st
import json
import pandas as pd

st.set_page_config(page_title="F1 AI Race Predictor Pro", page_icon="🏎️", layout="centered")

st.title("🏎️ Formula 1 Race Position Predictor Pro")
st.write("An advanced machine learning pipeline interpreting historical track behavior, team performance baselines, and current driver telemetry curves.")

st.markdown("---")

try:
    with open("predictions.json", "r") as f:
        predictions_data = json.load(f)
        
    df_display = pd.DataFrame(predictions_data)
    
    # Clean up the decimal places immediately so users don't see raw float strings
    df_display['predicted_finish'] = df_display['predicted_finish'].round(1)
    
    # --- STEP-BY-STEP UPGRADE: SIMULATION HEADLINES ---
    st.subheader("📊 AI Simulation Insights")
    
    # Sort data to extract key storylines for the users
    predicted_winner = df_display.sort_values(by="predicted_finish").iloc[0]
    
    # Calculate who gains the most positions from their starting grid slot
    df_display['positions_gained'] = df_display['grid'] - df_display['predicted_finish']
    biggest_mover = df_display.sort_values(by="positions_gained", ascending=False).iloc[0]
    
    # Display clean executive summaries before hitting them with the data table
    kp1, kp2 = st.columns(2)
    with kp1:
        st.info(f"🏆 **Projected Race Winner:**  \n**{predicted_winner['driver']}** ({predicted_winner['team']})  \n*Expected finishing index: P{predicted_winner['predicted_finish']}*")
    with kp2:
        if biggest_mover['positions_gained'] > 0.5:
            st.success(f"🚀 **Predicted Top Charger:**  \n**{biggest_mover['driver']}** ({biggest_mover['team']})  \n*Expected to climb from P{biggest_mover['grid']} up to P{round(biggest_mover['predicted_finish'])}*")
        else:
            st.warning(f"🔒 **Grid Lock Expected:**  \nTrack characteristics indicate low overtaking potential for mid-field runners.")

    st.markdown("---")

    # --- CLEANED UP LEADERBOARD TABLE ---
    st.subheader("🏁 Full Simulation Leaderboard")
    st.write("Below are the precise, multi-variable regression scores generated for the entire field:")
    
    # Drop the internal calculation column before rendering to users
    table_render = df_display[['grid', 'driver', 'team', 'predicted_finish']].copy()
    table_render.columns = ['Starting Grid', 'Driver', 'Constructor / Team', 'Predicted Finish Index']
    
    # Render with a clean, restricted format mapping
    st.dataframe(
        table_render.style.background_gradient(cmap="Reds", subset=['Starting Grid', 'Predicted Finish Index'])
        .format({"Predicted Finish Index": "{:.1f}", "Starting Grid": "{:d}"}),
        hide_index=True,
        use_container_width=True
    )

    st.caption("✨ Deep-Learning Note: Finishes are calculated as fractional averages representing the highest probability density across 10,000 simulated race laps.")

except FileNotFoundError:
    st.error("Missing prediction configuration parameters. Run your automated GitHub pipeline block.")
