import streamlit as st
import json
import pandas as pd

st.set_page_config(page_title="F1 AI Race Predictor Pro", page_icon="🏎️", layout="centered")

st.title("🏎️ Formula 1 Race Position Predictor Pro")
st.write("This customized machine learning engine interprets historical tracks, team strength, driver profiles, and live qualifying lineups.")

st.markdown("---")

try:
    with open("predictions.json", "r") as f:
        predictions_data = json.load(f)
        
    st.subheader("🤖 Upcoming Grand Prix Simulation Results")
    st.write("The model has mapped the active weekend entries. Here is the customized prediction:")
    
    # Format the flat JSON array neatly into a Pandas DataFrame table
    df_display = pd.DataFrame(predictions_data)
    
    # Rename the technical column formats to clean presentation titles
    df_display.columns = ['Starting Grid', 'Driver', 'Constructor / Team', 'Predicted Finishing Position']
    
    # Render the dynamic dashboard data table directly to the browser view
    st.dataframe(
        df_display.style.background_gradient(cmap="Reds", subset=['Starting Grid', 'Predicted Finishing Position']),
        hide_index=True,
        use_container_width=True
    )

    st.caption("✨ Pro-Tip: The model now differentiates between driver skills and team characteristics over a 10-year period.")

except FileNotFoundError:
    st.error("Missing prediction configuration parameters. Run your automated GitHub pipeline block.")
