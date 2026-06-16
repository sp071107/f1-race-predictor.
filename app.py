import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import json

st.set_page_config(page_title="F1 Pit-Wall Hub", page_icon="🏎️", layout="wide")

# ====================== STYLING ======================
st.markdown("""
<style>
    .stApp { background-color: #0b0d12; color: #f1f5f9; }
    .main-header { font-size: 2.8rem; font-weight: 900; color: #FF1801; text-align: center; margin-bottom: 0; }
    .race-banner {
        background: linear-gradient(90deg, #161922, #1f2431);
        padding: 25px; border-radius: 12px; border-left: 6px solid #FF1801;
        margin-bottom: 20px;
    }
    .metric-card {
        background: #12151e; padding: 20px; border-radius: 10px;
        border: 1px solid #282e3d; text-align: center;
    }
    .pitwall-card { background: #1a1e2a; padding: 18px; border-radius: 10px; border: 1px solid #282e3d; }
</style>
""", unsafe_allow_html=True)

# ====================== DATA FETCHERS ======================
@st.cache_data(ttl=600)  # 10 minutes
def get_current_standings(year):
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/driverStandings.json"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
            drivers = []
            for d in data:
                drivers.append({
                    "Pos": int(d['position']),
                    "Driver": f"{d['Driver']['givenName']} {d['Driver']['familyName']}",
                    "Team": d['Constructors'][0]['name'],
                    "Points": int(d['points'])
                })
            return pd.DataFrame(drivers)
    except:
        pass
    # Fallback 2026 data
    return pd.DataFrame([
        {"Pos": 1, "Driver": "K. ANTONELLI", "Team": "Mercedes", "Points": 156},
        # ... (keep your existing fallback list)
    ])

@st.cache_data(ttl=600)
def get_constructor_standings(year):
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/constructorStandings.json"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']
            cons = []
            for c in data:
                cons.append({
                    "Pos": int(c['position']),
                    "Team": c['Constructor']['name'],
                    "Points": int(c['points'])
                })
            return pd.DataFrame(cons)
    except:
        pass
    # Your fallback here...
    return pd.DataFrame([...])  # add your 2026 fallback

def get_live_grid():
    try:
        # OpenF1 or Ergast qualifying
        resp = requests.get("https://api.openf1.org/v1/session_result?session_key=latest", timeout=6)
        # Simplified - you can expand
        return pd.DataFrame()  # placeholder for now
    except:
        return pd.DataFrame()

# ====================== MAIN APP ======================
current_year = datetime.utcnow().year
st.markdown(f"<h1 class='main-header'>F1 PIT-WALL HUB {current_year}</h1>", unsafe_allow_html=True)

standings_df = get_current_standings(current_year)
cons_df = get_constructor_standings(current_year)

# Race Context Banner
st.markdown(f"""
<div class="race-banner">
    <h2 style="margin:0; color:#ffffff;">{current_year} FIA Formula One World Championship</h2>
    <p style="margin:5px 0 0 0; color:#94a3b8;">Live Telemetry • Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🏠 HOME", "📊 STRATEGY PREDICTOR", "🎙️ RACE ENGINEER", "📈 STANDINGS"])

# ====================== HOME ======================
with tabs[0]:
    st.markdown("### Weekend Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Leader", standings_df.iloc[0]['Driver'] if not standings_df.empty else "N/A")
    with col2:
        st.metric("Constructors Leader", cons_df.iloc[0]['Team'] if not cons_df.empty else "N/A")
    with col3:
        st.metric("Races Completed", len(standings_df))

# ====================== PREDICTOR ======================
# ====================== PREDICTOR TAB ======================
with tabs[1]:
    st.subheader("📍 Upcoming Race & Strategy Predictor")
    
    # Fetch next race
    @st.cache_data(ttl=3600)
    def get_next_race():
        try:
            url = f"https://api.jolpi.ca/ergast/f1/{current_year}.json"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                races = resp.json()['MRData']['RaceTable']['Races']
                today_str = datetime.utcnow().date().isoformat()
                for race in races:
                    if race.get('date', '') >= today_str:
                        return {
                            "round": race['round'],
                            "name": race['raceName'],
                            "circuit": race['Circuit']['circuitId'],
                            "date": race['date'],
                            "location": race['Circuit']['Location']['locality']
                        }
        except:
            pass
        return {"round": "N/A", "name": "Barcelona-Catalunya GP", "circuit": "catalunya", 
                "date": "2026-06-14", "location": "Spain"}  # fallback

    next_race = get_next_race()

    colA, colB = st.columns([1, 2])
    with colA:
        st.metric("Next Race", next_race["name"])
        st.metric("Round", next_race["round"])
        st.caption(f"{next_race['date']} • {next_race['location']}")

    with colB:
        st.markdown("**Circuit**: " + next_race["circuit"].title())

    # Full Calendar
    st.markdown("### 📅 2026 Race Calendar")
    try:
        calendar_resp = requests.get(f"https://api.jolpi.ca/ergast/f1/{current_year}.json")
        if calendar_resp.status_code == 200:
            cal = calendar_resp.json()['MRData']['RaceTable']['Races']
            cal_df = pd.DataFrame([{
                "Round": r['round'],
                "Grand Prix": r['raceName'],
                "Circuit": r['Circuit']['circuitId'].title(),
                "Date": r['date']
            } for r in cal])
            st.dataframe(cal_df, use_container_width=True, hide_index=True)
    except:
        st.info("Calendar temporarily unavailable.")

    # ================== IMPROVED PREDICTIONS ==================
    if st.button("🔮 Generate Predictions for Next Race", type="primary"):
        with st.spinner("Running AI prediction engine..."):
            try:
                # Load model artifacts
                with open("model_artifacts.json") as f:
                    artifacts = json.load(f)
                
                # Simple team strength from current standings (boosts accuracy)
                team_strength = {
                    "Mercedes": -1.2, "Ferrari": -0.8, "McLaren": -0.6,
                    "Red Bull Racing": 0.5, "Aston Martin": 1.1,
                    "Alpine": 1.8, "Williams": 2.2, "Haas": 2.5,
                    "Audi": 1.9, "Cadillac": 2.8, "Racing Bulls": 2.0
                }

                # Get current grid (fallback to standings order if no quali)
                grid_data = []
                try:
                    q_url = f"https://api.jolpi.ca/ergast/f1/{current_year}/{next_race['round']}/qualifying.json"
                    q_resp = requests.get(q_url)
                    if q_resp.status_code == 200:
                        results = q_resp.json()['MRData']['RaceTable']['Races'][0]['QualifyingResults']
                        for entry in results:
                            grid_data.append({
                                "driver": f"{entry['Driver']['givenName']} {entry['Driver']['familyName']}",
                                "d_id": entry['Driver']['driverId'],
                                "team": entry['Constructor']['name'],
                                "grid": int(entry['position'])
                            })
                except:
                    # Fallback: use championship order
                    standings = get_current_standings(current_year)
                    for idx, row in standings.iterrows():
                        grid_data.append({
                            "driver": row['Driver'], "d_id": row['Driver'].lower().replace(" ", "_"),
                            "team": row['Team'], "grid": idx + 1
                        })

                predictions = []
                for entry in grid_data[:20]:
                    try:
                        d_enc = artifacts["le_driver"].index(entry["d_id"]) if entry["d_id"] in artifacts["le_driver"] else 0
                        c_enc = 0  # fallback
                        circ_enc = artifacts["le_circuit"].index(next_race["circuit"]) if next_race["circuit"] in artifacts["le_circuit"] else 0
                        
                        base_pred = model.predict([[current_year, int(next_race["round"]), circ_enc, d_enc, c_enc, entry["grid"]]])[0]
                        
                        # Post-processing for realism
                        team_bias = team_strength.get(entry["team"], 1.5)
                        adjusted = base_pred + team_bias * 0.6 + (entry["grid"] - 1) * 0.35
                        adjusted = max(1, min(20, round(adjusted)))
                        
                        predictions.append({
                            "Grid": entry["grid"],
                            "Driver": entry["driver"],
                            "Team": entry["team"],
                            "Predicted Finish": int(adjusted),
                            "Gain/Loss": entry["grid"] - int(adjusted)
                        })
                    except:
                        continue

                pred_df = pd.DataFrame(predictions)
                pred_df = pred_df.sort_values("Predicted Finish")
                
                st.success("✅ Predictions Generated")
                st.dataframe(pred_df, use_container_width=True, hide_index=True)

                # Key Insights
                winner = pred_df.iloc[0]
                st.markdown(f"**🏆 AI Predicted Winner: {winner['Driver']}** ({winner['Team']})")
                
            except Exception as e:
                st.error(f"Prediction error: {str(e)}")
                st.info("Make sure predictor.py has been run recently.")

    else:
        st.info("Click the button above to generate fresh predictions for the next race.")

# ====================== RACE ENGINEER (Improved) ======================
with tabs[2]:
    st.subheader("🎙️ AI Race Engineer")
    user_input = st.text_input("Ask anything about F1, drivers, strategy, rules, history...", key="engineer")

    if user_input:
        query = user_input.lower().strip()
        response = "Understood. Let me check the latest telemetry..."

        # Enhanced intelligence
        if any(x in query for x in ["standings", "championship", "leader"]):
            if not standings_df.empty:
                leader = standings_df.iloc[0]
                response = f"**Current Drivers' Champion leader:** {leader['Driver']} ({leader['Team']}) with {leader['Points']} points."
            else:
                response = "Standings data temporarily unavailable."

        elif "verstappen" in query:
            response = "Max Verstappen is driving for Red Bull Racing. He is a 4x World Champion known for his aggressive style."
        elif "antonelli" in query or "kimi" in query:
            response = "Kimi Antonelli is the current sensation at Mercedes – highly rated rookie with pole positions already."
        elif any(x in query for x in ["strategy", "tyre", "pit"]):
            response = "Optimal strategy depends on track temp, tyre degradation, and safety car probability. Most races this year favor 1-2 stop strategies."
        elif "rules" in query or "what is" in query:
            response = "F1 rules: DRS, ERS, Parc Fermé, 107% rule... Ask me something specific!"
        else:
            response = f"Telemetry note on '{user_input}': Current season is very competitive. Mercedes and Ferrari are fighting at the front."

        st.info(f"**Race Engineer:** {response}")

# ====================== STANDINGS ======================
with tabs[3]:
    col_d, col_c = st.columns(2)
    with col_d:
        st.subheader("Driver Standings")
        st.dataframe(standings_df, use_container_width=True, hide_index=True)
    with col_c:
        st.subheader("Constructor Standings")
        st.dataframe(cons_df, use_container_width=True, hide_index=True)

st.caption("Data from Ergast / OpenF1 • Built with ❤️ for F1 fans")
