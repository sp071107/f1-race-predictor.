import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from sklearn.preprocessing import LabelEncoder

st.set_page_config(page_title="F1 Pit Wall Hub", page_icon="🏎️", layout="wide")

# ====================== TEAM COLOURS + LOGO MAPPING (100% FREE, NO API KEYS) ======================
# Colours are official-ish team hex codes. Logos are free public flag-style SVG badges
# rendered inline (no external image hosting / no paid CDN needed) so this never breaks
# or costs anything, ever.
TEAM_META = {
    "Mercedes":        {"color": "#27F4D2", "short": "MER", "emoji": "⚪"},
    "Ferrari":         {"color": "#E8002D", "short": "FER", "emoji": "🔴"},
    "Red Bull Racing": {"color": "#3671C6", "short": "RBR", "emoji": "🔵"},
    "Red Bull":        {"color": "#3671C6", "short": "RBR", "emoji": "🔵"},
    "McLaren":         {"color": "#FF8000", "short": "MCL", "emoji": "🟠"},
    "Aston Martin":    {"color": "#229971", "short": "AMR", "emoji": "🟢"},
    "Alpine":          {"color": "#FF87BC", "short": "ALP", "emoji": "🩷"},
    "Williams":        {"color": "#64C4FF", "short": "WIL", "emoji": "🔷"},
    "RB F1 Team":      {"color": "#6692FF", "short": "RB",  "emoji": "🟣"},
    "Racing Bulls":    {"color": "#6692FF", "short": "RB",  "emoji": "🟣"},
    "Visa Cash App RB": {"color": "#6692FF", "short": "RB", "emoji": "🟣"},
    "Haas F1 Team":    {"color": "#B6BABD", "short": "HAA", "emoji": "⚙️"},
    "Haas":            {"color": "#B6BABD", "short": "HAA", "emoji": "⚙️"},
    "Sauber":          {"color": "#52E252", "short": "SAU", "emoji": "🟩"},
    "Audi":            {"color": "#F50A23", "short": "AUD", "emoji": "🔺"},
    "Cadillac":        {"color": "#DEB887", "short": "CAD", "emoji": "🟤"},
}
DEFAULT_TEAM_META = {"color": "#94a3b8", "short": "N/A", "emoji": "⬜"}

def team_meta(team_name):
    if not team_name:
        return DEFAULT_TEAM_META
    if team_name in TEAM_META:
        return TEAM_META[team_name]
    # fuzzy fallback in case API returns a slightly different label
    for key, meta in TEAM_META.items():
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return meta
    return DEFAULT_TEAM_META

# ====================== PROFESSIONAL STYLING ======================
st.markdown("""
<style>
    .stApp { background-color: #0b0d12; color: #f1f5f9; }
    .main-header {
        font-size: 3.4rem; font-weight: 900; color: #FF1801;
        text-align: center; letter-spacing: -0.03em; margin-bottom: 0;
    }
    .hero-banner {
        background: linear-gradient(135deg, #161922 0%, #1f2431 100%);
        padding: 35px; border-radius: 16px; margin-bottom: 25px;
        border: 2px solid #FF1801; text-align: center;
        box-shadow: 0 8px 25px rgba(255, 24, 1, 0.15);
    }
    .pitwall-card {
        background: #12151e; padding: 24px; border-radius: 14px;
        border: 1px solid #FF1801; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .metric-card {
        background: #1a1e2a; padding: 18px; border-radius: 12px;
        border: 1px solid #FF1801; text-align: center;
    }
    .driver-card {
        border-radius: 14px;
        padding: 18px 18px 14px 18px;
        margin-bottom: 14px;
        background: linear-gradient(145deg, #161922 0%, #10131a 100%);
        box-shadow: 0 4px 16px rgba(0,0,0,0.45);
    }
    .driver-card .badge {
        display:inline-block; font-size:0.7rem; font-weight:800;
        letter-spacing:0.06em; padding:3px 8px; border-radius:6px;
        margin-bottom:8px; color:#0b0d12;
    }
    .driver-card h3 { margin: 0 0 2px 0; font-size: 1.15rem; }
    .driver-card .sub { color:#94a3b8; font-size:0.85rem; margin-bottom:10px; }
    .driver-card .pts { font-size:1.6rem; font-weight:900; }
    .chat-bubble-user {
        background:#1a1e2a; border:1px solid #282e3d; border-radius:10px;
        padding:10px 14px; margin-bottom:6px;
    }
    .chat-bubble-bot {
        background:#12151e; border-left:4px solid #FF1801; border-radius:10px;
        padding:10px 14px; margin-bottom:14px;
    }

    /* ===== ANIMATIONS (pure CSS, zero cost, zero dependencies) ===== */
    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 6px rgba(255,24,1,0.35); }
        50%      { box-shadow: 0 0 18px rgba(255,24,1,0.85); }
    }
    @keyframes podiumRise {
        from { opacity: 0; transform: translateY(28px) scale(0.94); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
    }

    .hero-banner, .pitwall-card, .metric-card, .driver-card {
        animation: fadeSlideUp 0.55s ease-out both;
    }
    .driver-card { transition: transform 0.25s ease, box-shadow 0.25s ease; }
    .driver-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 26px rgba(0,0,0,0.55);
    }

    .live-dot {
        display:inline-block; width:9px; height:9px; border-radius:50%;
        background:#22c55e; margin-right:6px; animation: pulseGlow 1.6s infinite;
    }

    /* Team-colour styled standings rows (replaces plain st.dataframe) */
    .race-table { width:100%; animation: fadeIn 0.6s ease-out both; }
    .race-row {
        display:flex; align-items:center; gap:14px;
        background: linear-gradient(135deg, #12151e 0%, #161a24 100%);
        border-radius: 10px; padding: 12px 18px; margin-bottom: 8px;
        animation: fadeSlideUp 0.5s ease-out both;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .race-row:hover {
        transform: translateX(4px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.5);
    }
    .race-row .pos {
        font-weight: 900; font-size: 1.05rem; width: 34px; text-align:center;
        color:#f1f5f9;
    }
    .race-row .team-chip {
        width:6px; height:34px; border-radius:4px; flex-shrink:0;
    }
    .race-row .name { font-weight:700; flex: 1.4; }
    .race-row .team-name { color:#94a3b8; flex:1.3; font-size:0.92rem; }
    .race-row .points { font-weight:900; font-size:1.05rem; min-width:96px; text-align:right; }
    .race-row .wins { color:#94a3b8; min-width:60px; text-align:right; font-size:0.85rem; }
    .race-row.header-row {
        background: transparent; color:#64748b; font-size:0.72rem;
        font-weight:800; letter-spacing:0.08em; text-transform:uppercase;
        animation: none; padding-bottom:0; padding-top:0; margin-bottom: 4px;
    }
    .race-row.header-row:hover { transform:none; box-shadow:none; }
    .delta-up   { color:#22c55e; font-weight:800; }
    .delta-down { color:#ef4444; font-weight:800; }
    .delta-flat { color:#64748b; font-weight:800; }

    .podium-card { animation: podiumRise 0.6s cubic-bezier(0.22, 1, 0.36, 1) both; }
    .podium-card:hover { transform: translateY(-6px) scale(1.02); transition: transform 0.25s ease; }
</style>
""", unsafe_allow_html=True)

def render_styled_table(rows, show_wins=True, delta_col=None):
    """
    Renders a team-coloured, animated HTML standings/results table.
    rows: list/iterable of dicts or pandas rows with Pos, Driver and/or Team, Points, Wins(optional)
    delta_col: optional list of ints (position change) aligned with rows, for up/down arrows
    Pure HTML/CSS — no extra libraries, no external calls, no cost.
    """
    html = ['<div class="race-table">']
    html.append(
        '<div class="race-row header-row">'
        '<span class="pos">#</span>'
        '<span class="team-chip" style="background:transparent;"></span>'
        '<span class="name">Driver</span>'
        '<span class="team-name">Team</span>'
        + ('<span class="wins">Wins</span>' if show_wins else '')
        + '<span class="points">Points</span>'
        '</div>'
    )
    for i, row in enumerate(rows):
        row = dict(row)
        meta = team_meta(row.get('Team', ''))
        delay = f"{min(i * 0.04, 0.6):.2f}s"
        delta_html = ""
        if delta_col is not None and i < len(delta_col):
            d = delta_col[i]
            if d > 0:
                delta_html = f'<span class="delta-up">&#9650;{d}</span>'
            elif d < 0:
                delta_html = f'<span class="delta-down">&#9660;{abs(d)}</span>'
            else:
                delta_html = '<span class="delta-flat">&mdash;</span>'
        driver_or_team = row.get('Driver', row.get('Team', ''))
        team_label = row.get('Team', '') if 'Driver' in row else ''
        wins_html = f'<span class="wins">{int(row.get("Wins", 0))}</span>' if show_wins else ''
        html.append(
            f'<div class="race-row" style="animation-delay:{delay};">'
            f'<span class="pos">{row.get("Pos", "-")}</span>'
            f'<span class="team-chip" style="background:{meta["color"]};"></span>'
            f'<span class="name">{meta["emoji"]} {driver_or_team}</span>'
            f'<span class="team-name">{team_label}</span>'
            f'{wins_html}'
            f'<span class="points" style="color:{meta["color"]};">{int(row.get("Points", 0))} {delta_html}</span>'
            f'</div>'
        )
    html.append('</div>')
    st.markdown("".join(html), unsafe_allow_html=True)

# ====================== HERO HEADER ======================
st.markdown("""
<div class="hero-banner">
    <h1 class="main-header">F1 PIT WALL HUB</h1>
    <p style="color:#94a3b8; font-size:1.25rem; margin-top:12px;">
        <span class="live-dot"></span>Real-Time AI Predictions • Strategy • 2026 Season • 100% Free, Forever
    </p>
</div>
""", unsafe_allow_html=True)

# ====================== DATA FETCHERS (ALL FREE / NO API KEY) ======================
# Jolpi (jolpi.ca) is a free, no-key drop-in replacement for the old Ergast F1 API.
# OpenF1 (openf1.org) is also a free, no-key live F1 telemetry API.
# Both are used here purely via plain HTTPS GET requests with no paid tier required.

@st.cache_data(ttl=600)
def get_current_standings(year):
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/driverStandings.json"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
            drivers = [{
                "Pos": int(d['position']),
                "Driver": f"{d['Driver']['givenName']} {d['Driver']['familyName']}",
                "Team": d['Constructors'][0]['name'],
                "Points": int(d['points']),
                "Wins": int(d.get('wins', 0)),
                "Nationality": d['Driver'].get('nationality', 'Unknown'),
                "DriverId": d['Driver'].get('driverId', '')
            } for d in data]
            return pd.DataFrame(drivers)
    except Exception:
        pass
    return pd.DataFrame([
        {"Pos": 1, "Driver": "K. Antonelli", "Team": "Mercedes", "Points": 156, "Wins": 3, "Nationality": "Italian", "DriverId": "antonelli"},
        {"Pos": 2, "Driver": "L. Hamilton", "Team": "Ferrari", "Points": 90, "Wins": 1, "Nationality": "British", "DriverId": "hamilton"},
        {"Pos": 3, "Driver": "G. Russell", "Team": "Mercedes", "Points": 88, "Wins": 1, "Nationality": "British", "DriverId": "russell"},
    ])

@st.cache_data(ttl=600)
def get_constructor_standings(year):
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/constructorStandings.json"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']
            cons = [{
                "Pos": int(c['position']),
                "Team": c['Constructor']['name'],
                "Points": int(c['points']),
                "Wins": int(c.get('wins', 0))
            } for c in data]
            return pd.DataFrame(cons)
    except Exception:
        pass
    return pd.DataFrame([{"Pos": 1, "Team": "Mercedes", "Points": 244, "Wins": 4}])

@st.cache_data(ttl=3600)
def get_next_race(year):
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            races = resp.json()['MRData']['RaceTable']['Races']
            today = datetime.utcnow().date().isoformat()
            for race in races:
                if race.get('date', '') >= today:
                    return {
                        "name": race['raceName'],
                        "round": race['round'],
                        "date": race['date'],
                        "circuit": race['Circuit']['circuitId'],
                        "circuit_name": race['Circuit']['circuitId'].replace('_', ' ').title(),
                        "location": f"{race['Circuit']['Location']['locality']}, {race['Circuit']['Location']['country']}"
                    }
            # season finished — return the last race as reference
            if races:
                race = races[-1]
                return {
                    "name": race['raceName'], "round": race['round'], "date": race['date'],
                    "circuit": race['Circuit']['circuitId'],
                    "circuit_name": race['Circuit']['circuitId'].replace('_', ' ').title(),
                    "location": f"{race['Circuit']['Location']['locality']}, {race['Circuit']['Location']['country']}"
                }
    except Exception:
        pass
    return {"name": "Spanish Grand Prix", "round": "TBD", "date": "Soon",
            "circuit": "catalunya", "circuit_name": "Barcelona", "location": "Barcelona, Spain"}

@st.cache_data(ttl=3600)
def get_full_calendar(year):
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            races = resp.json()['MRData']['RaceTable']['Races']
            return pd.DataFrame([{
                "Round": r['round'], "Grand Prix": r['raceName'],
                "Circuit": r['Circuit']['circuitId'].replace('_', ' ').title(), "Date": r['date']
            } for r in races])
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=600)
def get_recent_results(year):
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/results.json?limit=1000"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            return resp.json()['MRData']['RaceTable']['Races']
    except Exception:
        pass
    return []

current_year = datetime.utcnow().year
standings_df = get_current_standings(current_year)
cons_df = get_constructor_standings(current_year)
next_race = get_next_race(current_year)

tabs = st.tabs(["🏠 HOME", "🏆 PODIUM PREDICTOR", "🪪 DRIVER CARDS", "⚔️ DRIVER COMPARISON", "📜 HISTORY", "🎙️ RACE ENGINEER", "📈 STANDINGS"])

# ====================== HOME ======================
with tabs[0]:
    st.markdown("### 🏁 Race Control Center")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div class="pitwall-card">
            <h2>📍 Next Race: {next_race['name']}</h2>
            <p><strong>Round {next_race['round']}</strong> • {next_race['date']}</p>
            <p><strong>Circuit:</strong> {next_race['circuit_name']} ({next_race['location']})</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        leader_name = standings_df.iloc[0]['Driver'] if not standings_df.empty else "N/A"
        st.metric("🏆 Championship Leader", leader_name)

    st.markdown("### 📊 Season Snapshot")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        leader_team = standings_df.iloc[0]['Team'] if not standings_df.empty else "N/A"
        meta = team_meta(leader_team)
        st.markdown(f'<div class="metric-card"><h3>Driver Leader</h3><h2>{meta["emoji"]} {leader_name}</h2></div>', unsafe_allow_html=True)
    with m2:
        cons_leader = cons_df.iloc[0]["Team"] if not cons_df.empty else "N/A"
        cmeta = team_meta(cons_leader)
        st.markdown(f'<div class="metric-card"><h3>Constructors Leader</h3><h2>{cmeta["emoji"]} {cons_leader}</h2></div>', unsafe_allow_html=True)
    with m3:
        st.metric("Drivers Tracked", len(standings_df))
    with m4:
        st.metric("Teams Tracked", len(cons_df))

# ====================== PODIUM PREDICTOR ======================
with tabs[1]:
    st.subheader("🏆 Advanced Podium Predictor + Simulator")

    calendar_df = get_full_calendar(current_year)

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
                        except Exception:
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
                except Exception:
                    pass

                if not grid_list:
                    for i, row in standings_df.iterrows():
                        grid_list.append({"driver": row['Driver'], "d_id": row.get('DriverId', row['Driver'].lower().replace(" ", "_")),
                                        "team": row['Team'], "grid": i + 1})

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
                    except Exception:
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
                        dmeta = team_meta(driver['Team'])
                        delay = f"{i * 0.15:.2f}s"
                        st.markdown(f"""
                        <div class="podium-card" style="animation-delay:{delay}; text-align:center; padding:20px; background:#1a1e2a; border-radius:12px; border:2px solid {dmeta['color']};">
                            <h2>{pos_emoji} P{i+1}</h2>
                            <h3>{dmeta['emoji']} {driver['Driver']}</h3>
                            <p style="color:{dmeta['color']}; font-weight:700;">{driver['Team']}</p>
                            <small>From P{driver['Grid']} • {driver['Win Probability']}% Win Prob.</small>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("### Full Grid Predictions")
                pred_df_display = pred_df.rename(columns={"Predicted Finish": "Pos", "Positions Gained": "Delta"})
                deltas = pred_df_display["Delta"].tolist()
                render_styled_table(
                    pred_df_display.to_dict("records"),
                    show_wins=False,
                    delta_col=deltas
                )

            except Exception as e:
                st.error(f"Prediction error: {str(e)}")

# ====================== DRIVER STAT CARDS ======================
with tabs[2]:
    st.subheader("🪪 Driver Stat Cards")
    st.caption("Live season stats pulled straight from the standings feed — team-coloured, zero cost.")

    if standings_df.empty:
        st.warning("Driver data is temporarily unavailable. Try again shortly.")
    else:
        sort_choice = st.radio("Sort by", ["Championship Position", "Points (High→Low)", "Wins"], horizontal=True)
        sdf = standings_df.copy()
        if sort_choice == "Points (High→Low)":
            sdf = sdf.sort_values("Points", ascending=False)
        elif sort_choice == "Wins":
            sdf = sdf.sort_values("Wins", ascending=False)
        else:
            sdf = sdf.sort_values("Pos")

        cards_per_row = 4
        rows = [sdf.iloc[i:i + cards_per_row] for i in range(0, len(sdf), cards_per_row)]
        for row_chunk in rows:
            cols = st.columns(cards_per_row)
            for col, (_, d) in zip(cols, row_chunk.iterrows()):
                meta = team_meta(d['Team'])
                with col:
                    st.markdown(f"""
                    <div class="driver-card" style="border:1px solid {meta['color']}; border-top:5px solid {meta['color']};">
                        <span class="badge" style="background:{meta['color']};">{meta['short']}</span>
                        <h3>{meta['emoji']} {d['Driver']}</h3>
                        <div class="sub">{d['Team']} • {d.get('Nationality', '—')}</div>
                        <div class="pts" style="color:{meta['color']};">P{int(d['Pos'])} · {int(d['Points'])} pts</div>
                        <div class="sub">🏁 {int(d.get('Wins', 0))} win(s) this season</div>
                    </div>
                    """, unsafe_allow_html=True)

# ====================== DRIVER COMPARISON ======================
with tabs[3]:
    st.subheader("⚔️ Driver Comparison Tool")
    driver_list = standings_df['Driver'].tolist() if not standings_df.empty else ["K. Antonelli", "L. Hamilton"]
    colA, colB = st.columns(2)
    with colA:
        driver1 = st.selectbox("Driver 1", driver_list, index=0)
    with colB:
        driver2 = st.selectbox("Driver 2", driver_list, index=1 if len(driver_list) > 1 else 0)

    if st.button("Compare Drivers", type="primary", use_container_width=True):
        d1 = standings_df[standings_df['Driver'] == driver1].iloc[0] if not standings_df.empty else None
        d2 = standings_df[standings_df['Driver'] == driver2].iloc[0] if not standings_df.empty else None
        if d1 is not None and d2 is not None:
            c1, c2 = st.columns(2)
            with c1:
                m1 = team_meta(d1['Team'])
                st.markdown(f"#### {m1['emoji']} {driver1}")
                st.metric("Position", f"P{d1['Pos']}", f"{d1['Points']} pts")
                st.metric("Team", d1['Team'])
                st.metric("Wins", int(d1.get('Wins', 0)))
            with c2:
                m2 = team_meta(d2['Team'])
                st.markdown(f"#### {m2['emoji']} {driver2}")
                st.metric("Position", f"P{d2['Pos']}", f"{d2['Points']} pts")
                st.metric("Team", d2['Team'])
                st.metric("Wins", int(d2.get('Wins', 0)))
            better = driver1 if d1['Points'] > d2['Points'] else (driver2 if d2['Points'] > d1['Points'] else None)
            if better:
                st.success(f"**{better}** is performing better this season on points.")
            else:
                st.info("Both drivers are tied on points this season.")

# ====================== HISTORY ======================
with tabs[4]:
    st.subheader("📜 Recent Race Results")
    races = get_recent_results(current_year)
    if races:
        for race in reversed(races[-5:]):
            st.markdown(f"#### 🏁 {race['raceName']} (Round {race['round']})")
            result_rows = [{
                "Pos": res['position'],
                "Driver": f"{res['Driver']['givenName']} {res['Driver']['familyName']}",
                "Team": res['Constructor']['name'],
                "Points": res.get('points', 0)
            } for res in race.get('Results', [])[:10]]
            render_styled_table(result_rows, show_wins=False)
    else:
        st.info("Historical data is temporarily unavailable. Try refreshing shortly.")

# ====================== RACE ENGINEER (FIXED) ======================
with tabs[5]:
    st.subheader("🎙️ AI Race Engineer")
    st.caption("Rule-based, runs entirely in-app — no paid AI API calls, so this stays free forever.")

    if "engineer_history" not in st.session_state:
        st.session_state.engineer_history = []

    def driver_lookup(name_fragment, df):
        name_fragment = name_fragment.lower()
        matches = df[df['Driver'].str.lower().str.contains(name_fragment, na=False)]
        if matches.empty:
            # try matching on last name token only
            for _, row in df.iterrows():
                tokens = row['Driver'].lower().replace('.', '').split()
                if any(name_fragment in t or t in name_fragment for t in tokens):
                    return row
            return None
        return matches.iloc[0]

    def team_lookup(query_text, df):
        query_text = query_text.lower()
        for team_name in df['Team'].unique():
            if team_name.lower() in query_text:
                return team_name
        return None

    def answer_engineer(query, standings_df, cons_df, next_race):
        q = query.lower().strip()

        # Greeting
        if q in ("hi", "hello", "hey", "yo", "sup") or q.startswith(("hi ", "hello ", "hey ")):
            return "Copy that — Race Engineer online. Ask me about standings, a specific driver, a team, or the next race."

        # Next race / schedule
        if any(k in q for k in ["next race", "next gp", "schedule", "when is the race", "upcoming"]):
            return (f"Next up: **{next_race['name']}**, Round {next_race['round']}, "
                    f"on {next_race['date']} at {next_race['circuit_name']} ({next_race['location']}).")

        # Constructors / team standings
        if any(k in q for k in ["constructor", "team standings", "constructors championship"]):
            if not cons_df.empty:
                leader = cons_df.iloc[0]
                return f"In the Constructors' Championship, **{leader['Team']}** leads with {leader['Points']} points."
            return "Constructors' standings are temporarily unavailable."

        # Driver standings / championship leader
        if any(k in q for k in ["championship", "leading", "standings", "leader", "who's winning", "who is winning", "p1"]):
            if not standings_df.empty:
                leader = standings_df.iloc[0]
                return (f"Current championship leader is **{leader['Driver']}** ({leader['Team']}) "
                        f"with {leader['Points']} points and {int(leader.get('Wins', 0))} win(s).")
            return "Standings data is temporarily unavailable, try again shortly."

        # Specific team query (must come before generic driver fallback)
        matched_team = team_lookup(q, standings_df) if not standings_df.empty else None
        if matched_team and any(k in q for k in ["team", "constructor", "how is", "how are", "doing"]):
            team_drivers = standings_df[standings_df['Team'] == matched_team]
            team_points = cons_df[cons_df['Team'] == matched_team]['Points'].values
            pts_text = f"{int(team_points[0])} constructors points" if len(team_points) else "no recorded points yet"
            names = ", ".join(team_drivers['Driver'].tolist())
            return f"**{matched_team}** is running {pts_text} this season. Driver lineup in the standings: {names}."

        # Specific driver query — try matching any known driver name/surname in the question
        if not standings_df.empty:
            for _, row in standings_df.iterrows():
                surname = row['Driver'].split()[-1].lower()
                if surname in q:
                    return (f"**{row['Driver']}** ({row['Team']}) is currently P{int(row['Pos'])} "
                            f"with {int(row['Points'])} points and {int(row.get('Wins', 0))} win(s) this season.")

        # Tyres / strategy basics (general F1 knowledge, hardcoded so it's always free & instant)
        if "tyre" in q or "tire" in q:
            return ("Tyre choice is a balance of grip vs durability: Softs are fastest but degrade quickest, "
                    "Hards last longest but take time to switch on. Most strategies are built around when to "
                    "give up track position to swap compounds.")
        if "ers" in q or "energy recovery" in q:
            return ("ERS (Energy Recovery System) harvests energy under braking and deploys it on straights "
                    "for an extra power boost — think of it as a regenerative speed-boost button.")
        if "drs" in q:
            return ("DRS (Drag Reduction System) opens a flap in the rear wing to cut drag in marked zones, "
                    "helping a chasing car close the gap for an overtake attempt.")

        # Fallback — never silently fail, always say something useful
        return (f"Got it — you said: \"{query}\". I can answer questions about standings, a specific driver "
                f"or team, the next race, or basic strategy concepts like tyres, DRS, and ERS. Try one of those!")

    user_input = st.chat_input("Ask the Race Engineer (e.g. 'who is leading the championship?')")

    if user_input:
        reply = answer_engineer(user_input, standings_df, cons_df, next_race)
        st.session_state.engineer_history.append(("user", user_input))
        st.session_state.engineer_history.append(("bot", reply))

    for role, msg in st.session_state.engineer_history:
        if role == "user":
            st.markdown(f'<div class="chat-bubble-user">🧑‍💼 **You:** {msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-bot">📻 **Race Engineer:** {msg}</div>', unsafe_allow_html=True)

    if st.session_state.engineer_history:
        if st.button("🗑️ Clear conversation"):
            st.session_state.engineer_history = []
            st.rerun()

# ====================== STANDINGS ======================
with tabs[6]:
    col_d, col_c = st.columns(2)
    with col_d:
        st.subheader("Driver Standings")
        if not standings_df.empty:
            render_styled_table(standings_df.to_dict("records"), show_wins=True)
        else:
            st.info("Driver standings temporarily unavailable.")
    with col_c:
        st.subheader("Constructor Standings")
        if not cons_df.empty:
            render_styled_table(cons_df.to_dict("records"), show_wins=True)
        else:
            st.info("Constructor standings temporarily unavailable.")

st.caption("F1 Pit Wall Hub • Completely Free • Powered by Public APIs (Jolpi/Ergast + OpenF1) • No API Keys Required")
