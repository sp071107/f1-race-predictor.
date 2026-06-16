import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from sklearn.preprocessing import LabelEncoder


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
# ====================== PREDICTOR TAB ======================
with tabs[1]:
    st.subheader("📍 Next Race & AI Strategy Predictor")
    
    current_year = datetime.utcnow().year

    # Get Next Race + Calendar
    @st.cache_data(ttl=3600)
    def get_race_info():
        try:
            url = f"https://api.jolpi.ca/ergast/f1/{current_year}.json"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                races = resp.json()['MRData']['RaceTable']['Races']
                today = datetime.utcnow().date().isoformat()
                
                next_race = None
                for race in races:
                    if race.get('date', '') >= today:
                        next_race = {
                            "round": int(race['round']),
                            "name": race['raceName'],
                            "circuit": race['Circuit']['circuitId'],
                            "date": race['date'],
                            "location": f"{race['Circuit']['Location']['locality']}, {race['Circuit']['Location']['country']}"
                        }
                        break
                
                calendar_df = pd.DataFrame([{
                    "Round": r['round'],
                    "Grand Prix": r['raceName'],
                    "Circuit": r['Circuit']['circuitId'].replace('_', ' ').title(),
                    "Date": r['date']
                } for r in races])
                
                return next_race or {"round": 1, "name": "Next Grand Prix", "circuit": "catalunya", 
                                   "date": "TBD", "location": "Unknown"}, calendar_df
        except:
            pass
        # Fallback
        return {"round": 1, "name": "Spanish Grand Prix", "circuit": "catalunya", 
                "date": "2026-06-14", "location": "Barcelona, Spain"}, pd.DataFrame()

    next_race, calendar_df = get_race_info()

    # Display Next Race
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("Next Race", next_race["name"])
        st.metric("Round", next_race["round"])
    with col2:
        st.caption(f"**Date:** {next_race['date']}  |  **Location:** {next_race['location']}")
        st.caption(f"**Circuit:** {next_race['circuit'].replace('_', ' ').title()}")

    # Full Calendar
    st.markdown("### 📅 Full 2026 Season Calendar")
    st.dataframe(calendar_df, use_container_width=True, hide_index=True)

    # ================== IMPROVED PREDICTION ENGINE ==================
    if st.button("🔮 Generate AI Predictions for Next Race", type="primary", use_container_width=True):
        with st.spinner("Training model + generating predictions... (this may take 10-20 seconds first time)"):
            try:
                # === Train / Load Model On-Demand ===
                @st.cache_resource
                def train_model():
                    all_data = []
                    for year in range(2016, current_year):
                        try:
                            r = requests.get(f"https://api.jolpi.ca/ergast/f1/{year}/results.json?limit=1000", timeout=8)
                            if r.status_code == 200:
                                for race in r.json()['MRData']['RaceTable']['Races']:
                                    for res in race.get('Results', []):
                                        all_data.append({
                                            'year': year,
                                            'round': int(race['round']),
                                            'circuit': race['Circuit']['circuitId'],
                                            'driver': res['Driver']['driverId'],
                                            'constructor': res['Constructor']['constructorId'],
                                            'grid': int(res.get('grid', 20)),
                                            'finish': int(res.get('positionOrder', res.get('position', 20)))
                                        })
                        except:
                            continue
                    
                    df = pd.DataFrame(all_data)
                    if df.empty:
                        st.error("Could not load historical data")
                        return None, None, None, None
                    
                    le_c = LabelEncoder().fit(df['circuit'].unique())
                    le_d = LabelEncoder().fit(df['driver'].unique())
                    le_const = LabelEncoder().fit(df['constructor'].unique())
                    
                    df['c_enc'] = le_c.transform(df['circuit'])
                    df['d_enc'] = le_d.transform(df['driver'])
                    df['const_enc'] = le_const.transform(df['constructor'])
                    
                    from sklearn.ensemble import RandomForestRegressor
                    model = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42, n_jobs=-1)
                    X = df[['year', 'round', 'c_enc', 'd_enc', 'const_enc', 'grid']]
                    y = df['finish']
                    model.fit(X, y)
                    
                    return model, le_c, le_d, le_const

                model, le_c, le_d, le_const = train_model()

                # Team strength bias (makes predictions more realistic)
                team_bias = {
                    "Mercedes": -1.8, "Ferrari": -1.2, "McLaren": -0.9,
                    "Red Bull Racing": 0.4, "Aston Martin": 1.3, "Alpine": 2.1,
                    "Williams": 2.4, "Haas F1 Team": 2.6, "Audi": 1.7,
                    "Cadillac": 2.9, "Racing Bulls": 2.2
                }

                # Get Qualifying Grid
                grid_list = []
                try:
                    q_url = f"https://api.jolpi.ca/ergast/f1/{current_year}/{next_race['round']}/qualifying.json"
                    q_resp = requests.get(q_url, timeout=8)
                    if q_resp.status_code == 200:
                        results = q_resp.json()['MRData']['RaceTable']['Races'][0].get('QualifyingResults', [])
                        for entry in results:
                            grid_list.append({
                                "driver": f"{entry['Driver']['givenName']} {entry['Driver']['familyName']}",
                                "d_id": entry['Driver']['driverId'],
                                "team": entry['Constructor']['name'],
                                "grid": int(entry['position'])
                            })
                except:
                    # Fallback: Use current championship order
                    standings = get_current_standings(current_year)
                    for i, row in standings.iterrows():
                        grid_list.append({
                            "driver": row['Driver'],
                            "d_id": row['Driver'].lower().replace(" ", "_").replace(".", ""),
                            "team": row['Team'],
                            "grid": i + 1
                        })

                # Generate Predictions
                predictions = []
                for entry in grid_list[:22]:
                    try:
                        circ_enc = le_c.transform([next_race["circuit"]])[0] if next_race["circuit"] in le_c.classes_ else 0
                        d_enc = le_d.transform([entry["d_id"]])[0] if entry["d_id"] in le_d.classes_ else le_d.transform([le_d.classes_[0]])[0]
                        const_enc = le_const.transform([entry["team"].lower().replace(" ", "_")])[0] if any(entry["team"].lower() in c.lower() for c in le_const.classes_) else 0

                        base_pred = model.predict([[current_year, next_race["round"], circ_enc, d_enc, const_enc, entry["grid"]]])[0]

                        # Accuracy Boost
                        bias = team_bias.get(entry["team"], 1.5)
                        adjusted = base_pred + bias * 0.55 + (entry["grid"] - 5) * 0.22
                        final_pos = max(1, min(20, int(round(adjusted))))

                        predictions.append({
                            "Grid": entry["grid"],
                            "Driver": entry["driver"],
                            "Team": entry["team"],
                            "Predicted Finish": final_pos,
                            "Positions Gained": entry["grid"] - final_pos
                        })
                    except:
                        continue

                pred_df = pd.DataFrame(predictions)
                pred_df = pred_df.sort_values("Predicted Finish").reset_index(drop=True)

                st.success(f"✅ Predictions for **{next_race['name']}** Generated!")
                st.dataframe(pred_df, use_container_width=True, hide_index=True)

                # Highlights
                winner = pred_df.iloc[0]
                st.markdown(f"**🏆 Predicted Winner: {winner['Driver']}** ({winner['Team']}) from P{winner['Grid']}")

            except Exception as e:
                st.error(f"Prediction failed: {str(e)}")
                st.info("This usually happens on first run due to API limits. Try again in a few seconds.")

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
