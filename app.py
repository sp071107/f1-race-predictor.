import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from sklearn.preprocessing import LabelEncoder

st.set_page_config(page_title="F1 Pit Wall Hub", page_icon="🏎️", layout="wide")

# ====================== STYLING ======================
st.markdown("""
<style>
    .stApp { background-color: #0b0d12; color: #f1f5f9; }
    .main-header { font-size: 3.4rem; font-weight: 900; color: #FF1801; text-align: center; letter-spacing: -0.03em; }
    .hero-banner {
        background: linear-gradient(135deg, #161922 0%, #1f2431 100%);
        padding: 35px; border-radius: 16px; margin-bottom: 25px;
        border: 2px solid #FF1801; text-align: center;
    }
    .pitwall-card { background: #12151e; padding: 24px; border-radius: 14px; border: 1px solid #FF1801; }
</style>
""", unsafe_allow_html=True)

# ====================== HERO ======================
st.markdown("""
<div class="hero-banner">
    <h1 class="main-header">F1 PIT WALL HUB</h1>
    <p style="color:#94a3b8; font-size:1.25rem; margin-top:12px;">Real-Time AI Predictions • Strategy • 2026 Season</p>
</div>
""", unsafe_allow_html=True)

# ====================== DATA FETCHERS ======================
@st.cache_data(ttl=600)
def get_current_standings(year):
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/driverStandings.json"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
            drivers = [{"Pos": int(d['position']), "Driver": f"{d['Driver']['givenName']} {d['Driver']['familyName']}", 
                       "Team": d['Constructors'][0]['name'], "Points": int(d['points'])} for d in data]
            return pd.DataFrame(drivers)
    except:
        pass
    return pd.DataFrame([{"Pos": 1, "Driver": "K. ANTONELLI", "Team": "Mercedes", "Points": 156}])

@st.cache_data(ttl=600)
def get_constructor_standings(year):
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/constructorStandings.json"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']
            cons = [{"Pos": int(c['position']), "Team": c['Constructor']['name'], "Points": int(c['points'])} for c in data]
            return pd.DataFrame(cons)
    except:
        pass
    return pd.DataFrame([{"Pos": 1, "Team": "Mercedes", "Points": 244}])

current_year = datetime.utcnow().year
standings_df = get_current_standings(current_year)
cons_df = get_constructor_standings(current_year)

tabs = st.tabs(["🏠 HOME", "🏆 PODIUM PREDICTOR", "⚔️ DRIVER COMPARISON", "📜 HISTORY", "🎙️ RACE ENGINEER", "📈 STANDINGS"])

# ====================== HOME ======================
with tabs[0]:
    st.markdown("### 🏁 Race Control Center")
    @st.cache_data(ttl=3600)
    def get_next_race():
        try:
            url = f"https://api.jolpi.ca/ergast/f1/{current_year}.json"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                races = resp.json()['MRData']['RaceTable']['Races']
                today = datetime.utcnow().date().isoformat()
                for race in races:
                    if race.get('date', '') >= today:
                        return {"name": race['raceName'], "round": race['round'], "date": race['date'], 
                                "circuit": race['Circuit']['circuitId'].replace('_', ' ').title()}
        except:
            pass
        return {"name": "Spanish Grand Prix", "round": "TBD", "date": "Soon", "circuit": "Barcelona"}

    next_race = get_next_race()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div class="pitwall-card">
            <h2>📍 Next Race: {next_race['name']}</h2>
            <p><strong>Round {next_race['round']}</strong> • {next_race['date']}</p>
            <p><strong>Circuit:</strong> {next_race['circuit']}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.metric("🏆 Leader", standings_df.iloc[0]['Driver'] if not standings_df.empty else "N/A")

    st.markdown("### 📊 Season Snapshot")
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Driver Leader", standings_df.iloc[0]['Driver'] if not standings_df.empty else "N/A")
    with m2: st.metric("Constructors Leader", cons_df.iloc[0]['Team'] if not cons_df.empty else "N/A")
    with m3: st.metric("Races Completed", len(standings_df))
    with m4: st.metric("Active Drivers", len(standings_df))

# ====================== PODIUM PREDICTOR ======================
with tabs[1]:
    st.subheader("🏆 Advanced Podium Predictor + Simulator")
    
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
                    "Round": r['round'], "Grand Prix": r['raceName'],
                    "Circuit": r['Circuit']['circuitId'].replace('_', ' ').title(), "Date": r['date']
                } for r in races])
                return next_race or {"round":1,"name":"Next GP","circuit":"catalunya","date":"TBD","location":"Unknown"}, calendar_df
        except:
            pass
        return {"round":1,"name":"Spanish Grand Prix","circuit":"catalunya","date":"2026-06-14","location":"Barcelona, Spain"}, pd.DataFrame()

    next_race, calendar_df = get_race_info()

    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("Next Race", next_race["name"])
        st.metric("Round", next_race["round"])
    with col2:
        st.caption(f"**Date:** {next_race['date']} | **Location:** {next_race['location']}")

    st.markdown("### 📅 Full Season Calendar")
    st.dataframe(calendar_df, use_container_width=True, hide_index=True)

    st.markdown("### 🌤️ Weather Simulator")
    wcol1, wcol2 = st.columns(2)
    with wcol1:
        weather = st.selectbox("Track Conditions", ["Dry", "Light Rain", "Heavy Rain", "Hot & Dry"], index=0)
    with wcol2:
        track_temp = st.slider("Track Temperature (°C)", 20, 60, 38)

    if st.button("🔮 Generate Podium Predictions", type="primary", use_container_width=True):
        with st.spinner("Training model + generating predictions..."):
            try:
                @st.cache_resource
                def train_model():
                    all_data = []
                    for year in range(2016, current_year + 1):
                        try:
                            r = requests.get(f"https://api.jolpi.ca/ergast/f1/{year}/results.json?limit=1000", timeout=8)
                            if r.status_code == 200:
                                for race in r.json()['MRData']['RaceTable']['Races']:
                                    for res in race.get('Results', []):
                                        all_data.append({
                                            'year': year, 'round': int(race['round']),
                                            'circuit': race['Circuit']['circuitId'],
                                            'driver': res['Driver']['driverId'],
                                            'constructor': res['Constructor']['constructorId'],
                                            'grid': int(res.get('grid', 20)),
                                            'finish': int(res.get('positionOrder', res.get('position', 20)))
                                        })
                        except:
                            continue
                    
                    df = pd.DataFrame(all_data)
                    le_c = LabelEncoder().fit(df['circuit'].unique())
                    le_d = LabelEncoder().fit(df['driver'].unique())
                    le_const = LabelEncoder().fit(df['constructor'].unique())
                    
                    df['c_enc'] = le_c.transform(df['circuit'])
                    df['d_enc'] = le_d.transform(df['driver'])
                    df['const_enc'] = le_const.transform(df['constructor'])
                    
                    from sklearn.ensemble import RandomForestRegressor
                    model = RandomForestRegressor(n_estimators=250, max_depth=12, random_state=42, n_jobs=-1)
                    X = df[['year', 'round', 'c_enc', 'd_enc', 'const_enc', 'grid']]
                    y = df['finish']
                    model.fit(X, y)
                    return model, le_c, le_d, le_const

                model, le_c, le_d, le_const = train_model()

                team_bias = {"Mercedes": -2.3, "Ferrari": -1.8, "McLaren": -1.4, "Red Bull Racing": 0.4,
                            "Aston Martin": 1.5, "Alpine": 2.4, "Williams": 2.7, "Haas F1 Team": 2.9,
                            "Audi": 2.0, "Cadillac": 3.1, "Racing Bulls": 2.5, "RB F1 Team": 2.5}

                weather_factor = {"Dry": 1.0, "Light Rain": 1.15, "Heavy Rain": 1.35, "Hot & Dry": 0.9}
                temp_factor = (track_temp - 38) * 0.015

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
                    for i, row in standings_df.iterrows():
                        grid_list.append({"driver": row['Driver'], "d_id": row['Driver'].lower().replace(" ", "_"), 
                                        "team": row['Team'], "grid": i+1})

                predictions = []
                for entry in grid_list[:22]:
                    try:
                        circ_enc = le_c.transform([next_race["circuit"]])[0] if next_race["circuit"] in le_c.classes_ else 0
                        d_enc = le_d.transform([entry["d_id"]])[0] if entry["d_id"] in le_d.classes_ else 0
                        const_enc = le_const.transform([entry["team"].lower().replace(" ", "_")])[0] if any(entry["team"].lower() in c.lower() for c in le_const.classes_) else 0

                        base_pred = model.predict([[current_year, next_race["round"], circ_enc, d_enc, const_enc, entry["grid"]]])[0]

                        bias = team_bias.get(entry["team"], 2.0)
                        adjusted = base_pred + bias * 0.7 + (entry["grid"] - 3) * 0.2 + temp_factor
                        final_pos = max(1, min(20, int(round(adjusted * weather_factor[weather]))))

                        predictions.append({
                            "Grid": entry["grid"], "Driver": entry["driver"], "Team": entry["team"],
                            "Predicted Finish": final_pos, "Positions Gained": entry["grid"] - final_pos
                        })
                    except:
                        continue

                pred_df = pd.DataFrame(predictions).sort_values("Predicted Finish").reset_index(drop=True)

                st.success(f"🏆 Podium Predictions for **{next_race['name']}** ({weather} conditions)")

                podium = pred_df.head(3).copy()
                podium_scores = [1 / (p + 1) for p in podium["Predicted Finish"]]
                total = sum(podium_scores)
                podium["Win Probability"] = [round((s / total) * 100, 1) for s in podium_scores]

                cols = st.columns(3)
                for i, (_, driver) in enumerate(podium.iterrows()):
                    with cols[i]:
                        pos_emoji = ["🥇", "🥈", "🥉"][i]
                        st.markdown(f"""
                        <div style="text-align:center; padding:20px; background:#1a1e2a; border-radius:12px; border:2px solid #FF1801;">
                            <h2>{pos_emoji} P{i+1}</h2>
                            <h3>{driver['Driver']}</h3>
                            <p>{driver['Team']}</p>
                            <small>From P{driver['Grid']} • {driver['Win Probability']}% Win Prob.</small>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("### Full Grid Predictions")
                st.dataframe(pred_df, use_container_width=True, hide_index=True)

                # DOWNLOAD BUTTON
                csv = pred_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Predictions as CSV",
                    data=csv,
                    file_name=f"f1_predictions_{next_race['name'].replace(' ', '_')}.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error(f"Prediction error: {str(e)}")

# ====================== DRIVER COMPARISON ======================
with tabs[2]:
    st.subheader("⚔️ Driver Comparison Tool")
    driver_list = standings_df['Driver'].tolist() if not standings_df.empty else ["K. ANTONELLI", "L. HAMILTON"]
    colA, colB = st.columns(2)
    with colA:
        driver1 = st.selectbox("Driver 1", driver_list, index=0)
    with colB:
        driver2 = st.selectbox("Driver 2", driver_list, index=1 if len(driver_list) > 1 else 0)

    if st.button("Compare Drivers", type="primary", use_container_width=True):
        d1 = standings_df[standings_df['Driver'] == driver1].iloc[0] if not standings_df.empty else None
        d2 = standings_df[standings_df['Driver'] == driver2].iloc[0] if not standings_df.empty else None
        if d1 and d2:
            c1, c2 = st.columns(2)
            with c1:
                st.metric(driver1, f"P{d1['Pos']}", f"{d1['Points']} pts")
                st.metric("Team", d1['Team'])
            with c2:
                st.metric(driver2, f"P{d2['Pos']}", f"{d2['Points']} pts")
                st.metric("Team", d2['Team'])
            st.success(f"**{driver1 if d1['Points'] > d2['Points'] else driver2}** is performing better.")

# ====================== HISTORY ======================
with tabs[3]:
    st.subheader("📜 Recent Race Results")
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{current_year}/results.json?limit=1000"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            races = resp.json()['MRData']['RaceTable']['Races'][-5:]
            for race in reversed(races):
                st.write(f"**{race['raceName']}** (Round {race['round']})")
                df_results = pd.DataFrame([{
                    "Pos": res['position'],
                    "Driver": f"{res['Driver']['givenName']} {res['Driver']['familyName']}",
                    "Team": res['Constructor']['name']
                } for res in race.get('Results', [])[:10]])
                st.dataframe(df_results, use_container_width=True, hide_index=True)
    except:
        st.info("Historical data loading...")

# ====================== RACE ENGINEER ======================
with tabs[4]:
    st.subheader("🎙️ AI Race Engineer")
    user_input = st.text_input("Your message to the Race Engineer:", placeholder="Who is leading the championship?", key="engineer_input")
    if user_input:
        query = user_input.lower().strip()
        response = "The 2026 season is highly competitive."
        if "standings" in query or "leader" in query:
            if not standings_df.empty:
                leader = standings_df.iloc[0]
                response = f"**Current leader:** {leader['Driver']} ({leader['Team']}) with {leader['Points']} points."
        st.info(f"**Race Engineer:** {response}")

# ====================== STANDINGS ======================
with tabs[5]:
    col_d, col_c = st.columns(2)
    with col_d:
        st.subheader("Driver Standings")
        st.dataframe(standings_df, use_container_width=True, hide_index=True)
    with col_c:
        st.subheader("Constructor Standings")
        st.dataframe(cons_df, use_container_width=True, hide_index=True)

st.caption("F1 Pit Wall Hub • Completely Free • Powered by Public APIs")
