import streamlit as st
import pandas as pd
import numpy as np
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
    @import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@400;600;700;900&family=Barlow+Condensed:wght@500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Titillium Web', 'Segoe UI', sans-serif; }
    .stApp { background-color: #0b0d12; color: #f1f5f9; font-family: 'Titillium Web', 'Segoe UI', sans-serif; }
    h1, h2, h3, .main-header, .card-title, .race-row .name, .driver-card h3 {
        font-family: 'Barlow Condensed', 'Titillium Web', sans-serif; letter-spacing: 0.01em;
    }
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

def render_data_table(rows, team_col=None):
    """
    Generic animated table for non-driver-standings data (calendar, circuit winners,
    tyre stints, pit stops, strategy comparisons) — reuses the same .race-row CSS
    so every table in the app shares one consistent look instead of falling back
    to a plain st.dataframe.
    team_col: optional column name whose value is used to colour that row's left edge.
    """
    if not rows:
        st.info("No data to display.")
        return
    columns = list(rows[0].keys())
    html = ['<div class="race-table">']
    header_cells = "".join(f'<span style="flex:1; padding-right:8px;">{c}</span>' for c in columns)
    html.append(f'<div class="race-row header-row" style="border-left:none;">{header_cells}</div>')
    for i, row in enumerate(rows):
        delay = f"{min(i * 0.03, 0.5):.2f}s"
        color = "#282e3d"
        if team_col and row.get(team_col):
            color = team_meta(row[team_col])["color"]
        cells = "".join(f'<span style="flex:1; padding-right:8px;">{row.get(c, "")}</span>' for c in columns)
        html.append(f'<div class="race-row" style="animation-delay:{delay}; border-left:4px solid {color};">{cells}</div>')
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
    """Tries the current season; if that's not loaded yet on the free API, falls back to
    last season's FINAL standings (real data, clearly flagged) rather than fabricated numbers.
    Returns an empty DataFrame only if both real attempts fail — never invented placeholder rows."""
    for y in [year, year - 1]:
        try:
            url = f"https://api.jolpi.ca/ergast/f1/{y}/driverStandings.json"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                lists = resp.json()['MRData']['StandingsTable']['StandingsLists']
                if lists:
                    data = lists[0]['DriverStandings']
                    drivers = [{
                        "Pos": int(d['position']),
                        "Driver": f"{d['Driver']['givenName']} {d['Driver']['familyName']}",
                        "Team": d['Constructors'][0]['name'],
                        "Points": int(d['points']),
                        "Wins": int(d.get('wins', 0)),
                        "Nationality": d['Driver'].get('nationality', 'Unknown'),
                        "DriverId": d['Driver'].get('driverId', '')
                    } for d in data]
                    df = pd.DataFrame(drivers)
                    df.attrs['source_year'] = y
                    df.attrs['is_current'] = (y == year)
                    return df
        except Exception:
            continue
    return pd.DataFrame()

@st.cache_data(ttl=600)
def get_constructor_standings(year):
    for y in [year, year - 1]:
        try:
            url = f"https://api.jolpi.ca/ergast/f1/{y}/constructorStandings.json"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                lists = resp.json()['MRData']['StandingsTable']['StandingsLists']
                if lists:
                    data = lists[0]['ConstructorStandings']
                    cons = [{
                        "Pos": int(c['position']),
                        "Team": c['Constructor']['name'],
                        "Points": int(c['points']),
                        "Wins": int(c.get('wins', 0))
                    } for c in data]
                    df = pd.DataFrame(cons)
                    df.attrs['source_year'] = y
                    df.attrs['is_current'] = (y == year)
                    return df
        except Exception:
            continue
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_next_race(year):
    """Tries the current season's calendar first. If the free API hasn't loaded this
    season yet (common for a brand-new year), falls back to the real final race of last
    season instead of a fabricated placeholder. Returns None only if everything fails,
    so the UI can show an honest 'unavailable' message instead of fake-looking data."""
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            races = resp.json()['MRData']['RaceTable']['Races']
            if races:
                today = datetime.utcnow().date().isoformat()
                for race in races:
                    if race.get('date', '') >= today:
                        return {
                            "name": race['raceName'], "round": race['round'], "date": race['date'],
                            "circuit": race['Circuit']['circuitId'],
                            "circuit_name": race['Circuit']['circuitId'].replace('_', ' ').title(),
                            "location": f"{race['Circuit']['Location']['locality']}, {race['Circuit']['Location']['country']}",
                            "is_current": True, "season_complete": False
                        }
                # every race this year has already happened — season's over, show the real final race
                race = races[-1]
                return {
                    "name": race['raceName'], "round": race['round'], "date": race['date'],
                    "circuit": race['Circuit']['circuitId'],
                    "circuit_name": race['Circuit']['circuitId'].replace('_', ' ').title(),
                    "location": f"{race['Circuit']['Location']['locality']}, {race['Circuit']['Location']['country']}",
                    "is_current": True, "season_complete": True
                }
    except Exception:
        pass

    # Current season calendar isn't available yet on the free API — fall back to last
    # season's real final race rather than a fabricated race name.
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year - 1}.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            races = resp.json()['MRData']['RaceTable']['Races']
            if races:
                race = races[-1]
                return {
                    "name": race['raceName'], "round": race['round'], "date": race['date'],
                    "circuit": race['Circuit']['circuitId'],
                    "circuit_name": race['Circuit']['circuitId'].replace('_', ' ').title(),
                    "location": f"{race['Circuit']['Location']['locality']}, {race['Circuit']['Location']['country']}",
                    "is_current": False, "season_complete": True
                }
    except Exception:
        pass

    return None


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

@st.cache_data(ttl=3600)
def get_remaining_rounds(year, from_round):
    """Real circuit IDs for every round from `from_round` to season end — needed by the
    Season Simulator so each remaining race uses its actual circuit, not a guess."""
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            races = resp.json()['MRData']['RaceTable']['Races']
            return [{
                "round": int(r['round']), "circuit_id": r['Circuit']['circuitId'], "race_name": r['raceName']
            } for r in races if int(r['round']) >= from_round]
    except Exception:
        pass
    return []

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

@st.cache_data(ttl=86400)
def get_all_drivers_index():
    """Full historical driver roster (1950–present), not just this season's grid.
    Free, same Ergast/Jolpi feed, cached for a day since this barely changes."""
    try:
        resp = requests.get("https://api.jolpi.ca/ergast/f1/drivers.json?limit=2000", timeout=8).json()
        drivers = resp['MRData']['DriverTable']['Drivers']
        return {f"{d.get('givenName','')} {d.get('familyName','')}".strip(): d['driverId'] for d in drivers}
    except Exception:
        return {}

@st.cache_data(ttl=86400)
def get_driver_career_results(driver_id):
    try:
        resp = requests.get(f"https://api.jolpi.ca/ergast/f1/drivers/{driver_id}/results.json?limit=1000", timeout=8).json()
        races = resp['MRData']['RaceTable']['Races']
        rows = []
        for r in races:
            res = r['Results'][0]
            rows.append({
                "season": int(r['season']),
                "round": int(r['round']),
                "race": r['raceName'],
                "grid": int(res.get('grid', 0)),
                "position": res.get('positionText', 'N/A'),
                "points": float(res.get('points', 0)),
                "constructor": res['Constructor']['name'],
                "status": res.get('status', '')
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

@st.cache_resource
def train_model_and_risk_profile(year_cutoff):
    """
    Trains the pace model AND derives the Monte Carlo risk profile (DNF rates,
    pace volatility, safety-car proxy) from the same free historical dataset.
    Shared by the Predict / Strategy Simulator / Prediction-vs-Reality sub-tabs
    so there's only one engine, not three copies of it.
    """
    all_data = []
    for year in range(2016, year_cutoff + 1):
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
                            'finish': int(res.get('positionOrder', res.get('position', 20))),
                            'status': res.get('status', '')
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

    df['finished_clean'] = df['status'].str.contains("Finished", case=False, na=False) | df['status'].str.contains(r'^\+', regex=True, na=False)
    dnf_rates = (1 - df.groupby('driver')['finished_clean'].mean()).clip(0.02, 0.40).to_dict()
    pos_std = df.groupby('driver')['finish'].std().fillna(2.5).clip(0.8, 4.5).to_dict()

    race_level = df.groupby(['year', 'round', 'circuit'])['finished_clean'].apply(lambda s: (~s).sum())
    race_level = race_level.reset_index(name='retirements')
    sc_proxy = race_level.groupby('circuit')['retirements'].apply(lambda r: (r >= 3).mean()).clip(0.05, 0.65).to_dict()

    return model, le_c, le_d, le_const, dnf_rates, pos_std, sc_proxy


def fetch_grid_for_round(year, round_num, fallback_standings_df):
    """Fetches the actual qualifying grid for a given round, with constructor_id included
    so live rolling-form bias can be looked up. Falls back to standings order if quali isn't out yet."""
    grid_list = []
    try:
        q_url = f"https://api.jolpi.ca/ergast/f1/{year}/{round_num}/qualifying.json"
        q_resp = requests.get(q_url, timeout=8)
        if q_resp.status_code == 200:
            results = q_resp.json()['MRData']['RaceTable']['Races'][0].get('QualifyingResults', [])
            for entry in results:
                grid_list.append({
                    "driver": f"{entry['Driver']['givenName']} {entry['Driver']['familyName']}",
                    "d_id": entry['Driver']['driverId'],
                    "team": entry['Constructor']['name'],
                    "c_id": entry['Constructor']['constructorId'],
                    "grid": int(entry['position'])
                })
    except Exception:
        pass

    if not grid_list:
        for i, row in fallback_standings_df.iterrows():
            grid_list.append({
                "driver": row['Driver'], "d_id": row.get('DriverId', row['Driver'].lower().replace(" ", "_")),
                "team": row['Team'], "c_id": row['Team'].lower().replace(" ", "_"), "grid": i + 1
            })
    return grid_list


def build_drivers_meta(grid_list, year, round_num, circuit_id, weather, track_temp, model, le_c, le_d, le_const,
                        dnf_rates, pos_std, constructor_bias, driver_bias, extra_stop_penalty=0.0):
    """Builds each driver's Monte Carlo pace anchor + risk params. extra_stop_penalty lets the
    Strategy Simulator nudge a driver's anchor to reflect a non-optimal number of pit stops."""
    weather_factor = {"Dry": 1.0, "Light Rain": 1.15, "Heavy Rain": 1.35, "Hot & Dry": 0.9}
    temp_factor = (track_temp - 38) * 0.015

    drivers_meta, anchor_scores = [], []
    for entry in grid_list[:22]:
        try:
            circ_enc = le_c.transform([circuit_id])[0] if circuit_id in le_c.classes_ else 0
            d_enc = le_d.transform([entry["d_id"]])[0] if entry["d_id"] in le_d.classes_ else 0
            const_enc = le_const.transform([entry["c_id"]])[0] if entry["c_id"] in le_const.classes_ else 0

            base_pred = model.predict([[year, round_num, circ_enc, d_enc, const_enc, entry["grid"]]])[0]

            # LIVE rolling-form bias — replaces the old hardcoded team_bias dict.
            # Self-updates every race, no manual maintenance ever required.
            c_bias = constructor_bias.get(entry["c_id"], 0.0)
            d_bias = driver_bias.get(entry["d_id"], 0.0)

            anchor = (base_pred + c_bias + d_bias + (entry["grid"] - 3) * 0.2 + temp_factor + extra_stop_penalty) * weather_factor[weather]

            anchor_scores.append(anchor)
            drivers_meta.append({
                "Driver": entry["driver"], "Team": entry["team"], "Grid": entry["grid"],
                "dnf_p": dnf_rates.get(entry["d_id"], 0.12),
                "sigma": pos_std.get(entry["d_id"], 2.5)
            })
        except Exception:
            continue
    return drivers_meta, anchor_scores


def run_monte_carlo(drivers_meta, anchor_scores, sc_p, weather, n_sims, seed=42):
    """The shared Monte Carlo engine. Vectorized with numpy — fast even at 10k iterations."""
    n_drivers = len(drivers_meta)
    means = np.array(anchor_scores)
    sigmas = np.array([d["sigma"] for d in drivers_meta])
    dnf_p = np.array([d["dnf_p"] for d in drivers_meta])
    rain_variance_mult = {"Dry": 1.0, "Light Rain": 1.3, "Heavy Rain": 1.7, "Hot & Dry": 1.05}.get(weather, 1.0)

    rng = np.random.default_rng(seed)
    pace_noise = rng.normal(0, 1, size=(n_sims, n_drivers)) * (sigmas[None, :] * rain_variance_mult)
    sc_draws = rng.random(n_sims) < sc_p
    sc_extra = rng.normal(0, 1, size=(n_sims, n_drivers)) * 1.6
    pace_noise = pace_noise + sc_draws[:, None] * sc_extra

    scores = means[None, :] + pace_noise
    dnf_draws = rng.random(size=(n_sims, n_drivers)) < dnf_p[None, :]
    scores = np.where(dnf_draws, 999.0 + rng.random(size=(n_sims, n_drivers)), scores)

    order = np.argsort(scores, axis=1)
    finish_rank = np.argsort(order, axis=1) + 1

    win_pct = (finish_rank == 1).mean(axis=0) * 100
    podium_pct = (finish_rank <= 3).mean(axis=0) * 100
    top5_pct = (finish_rank <= 5).mean(axis=0) * 100
    dnf_pct = dnf_draws.mean(axis=0) * 100
    avg_finish = np.where(dnf_draws, np.nan, finish_rank).astype(float)
    avg_finish = np.nanmean(avg_finish, axis=0)

    sim_df = pd.DataFrame({
        "Driver": [d["Driver"] for d in drivers_meta],
        "Team": [d["Team"] for d in drivers_meta],
        "Grid": [d["Grid"] for d in drivers_meta],
        "Win %": win_pct.round(1),
        "Podium %": podium_pct.round(1),
        "Top 5 %": top5_pct.round(1),
        "DNF %": dnf_pct.round(1),
        "Avg Finish (when classified)": avg_finish.round(2)
    }).sort_values("Win %", ascending=False).reset_index(drop=True)
    return sim_df


# ====================== TYRE DEGRADATION MODEL (pure compute — zero API cost, zero new dependency) ======================
# Compound parameters are illustrative, physically-reasonable approximations (not telemetry-derived),
# calibrated to match the commonly understood behavior: Soft = fastest but degrades quickest and hits
# a "cliff" earliest; Hard = slowest out the box but most durable. This is disclosed in the UI.
TYRE_COMPOUNDS = {
    "Soft":   {"base_rate": 0.085, "cliff_lap": 14, "cliff_severity": 0.22, "color": "#ff4d4d"},
    "Medium": {"base_rate": 0.052, "cliff_lap": 24, "cliff_severity": 0.16, "color": "#f5d142"},
    "Hard":   {"base_rate": 0.030, "cliff_lap": 36, "cliff_severity": 0.10, "color": "#e8e8e8"},
}

def tyre_degradation_curve(compound, stint_laps, track_temp):
    """Returns an array of per-lap cumulative time-loss (seconds) vs. a fresh tyre, for one stint.
    Hotter track temps accelerate wear (roughly +1.8% degradation per °C above 35°C, a reasonable
    real-world rule of thumb, not an exact telemetry constant)."""
    params = TYRE_COMPOUNDS[compound]
    temp_mult = 1.0 + max(0, (track_temp - 35)) * 0.018
    laps = np.arange(1, stint_laps + 1)
    linear_loss = params["base_rate"] * temp_mult * laps
    cliff_loss = params["cliff_severity"] * temp_mult * np.maximum(0, laps - params["cliff_lap"]) ** 1.4
    return linear_loss + cliff_loss

def estimate_strategy_time_loss(n_stops, total_laps, track_temp, pit_loss_seconds):
    """Splits the race into (n_stops + 1) stints, assigns a sensible compound rotation
    (softer early, harder late — the common real-world pattern), and sums degradation
    time-loss across all stints plus the pit lane time cost of each stop.
    Returns (total_time_loss_seconds, per_stint_breakdown)."""
    n_stints = n_stops + 1
    rotation_by_stints = {
        1: ["Hard"],
        2: ["Medium", "Hard"],
        3: ["Soft", "Medium", "Hard"],
        4: ["Soft", "Soft", "Medium", "Hard"],
    }
    compounds = rotation_by_stints.get(n_stints, ["Medium"] * n_stints)
    base_stint_len = total_laps // n_stints
    remainder = total_laps - base_stint_len * n_stints
    stint_lengths = [base_stint_len + (1 if i < remainder else 0) for i in range(n_stints)]

    total_loss = 0.0
    breakdown = []
    for compound, stint_len in zip(compounds, stint_lengths):
        if stint_len <= 0:
            continue
        curve = tyre_degradation_curve(compound, stint_len, track_temp)
        stint_loss = float(curve[-1])  # cumulative loss by end of stint
        total_loss += stint_loss
        breakdown.append({"Compound": compound, "Laps": stint_len, "Time Lost (s)": round(stint_loss, 1)})

    total_loss += n_stops * pit_loss_seconds
    return total_loss, breakdown


# ====================== SEASON-LONG CHAMPIONSHIP SIMULATOR (reuses the same engine, chained across rounds) ======================
F1_POINTS_TABLE = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]  # standard race points, P1-P10. Sprint points not modeled — disclosed in UI.

def simulate_remaining_season(per_round_meta, current_points, n_sims=3000, seed=7):
    """
    per_round_meta: list of (drivers_meta, anchor_scores, sc_p) — one tuple per remaining round,
    all sharing the same driver ordering (so index i = same driver in every round).
    current_points: array aligned to that same driver ordering — each driver's real points so far.
    Runs the whole rest of the season n_sims times, awarding real F1 points each simulated race,
    then reports each driver's championship-win % and average projected final points.
    """
    n_drivers = len(per_round_meta[0][0])
    rng = np.random.default_rng(seed)
    total_points = np.zeros((n_sims, n_drivers))

    rank_to_pts = np.zeros(n_drivers + 1)
    for pos_idx, pts in enumerate(F1_POINTS_TABLE):
        if pos_idx + 1 <= n_drivers:
            rank_to_pts[pos_idx + 1] = pts

    for drivers_meta, anchor_scores, sc_p in per_round_meta:
        means = np.array(anchor_scores)
        sigmas = np.array([d["sigma"] for d in drivers_meta])
        dnf_p = np.array([d["dnf_p"] for d in drivers_meta])

        pace_noise = rng.normal(0, 1, size=(n_sims, n_drivers)) * sigmas[None, :]
        sc_draws = rng.random(n_sims) < sc_p
        sc_extra = rng.normal(0, 1, size=(n_sims, n_drivers)) * 1.6
        pace_noise = pace_noise + sc_draws[:, None] * sc_extra

        scores = means[None, :] + pace_noise
        dnf_draws = rng.random(size=(n_sims, n_drivers)) < dnf_p[None, :]
        scores = np.where(dnf_draws, 999.0 + rng.random(size=(n_sims, n_drivers)), scores)

        order = np.argsort(scores, axis=1)
        finish_rank = np.argsort(order, axis=1) + 1
        race_points = rank_to_pts[finish_rank]
        total_points += race_points

    final_points = total_points + current_points[None, :]
    champion_idx = np.argmax(final_points, axis=1)
    win_counts = np.bincount(champion_idx, minlength=n_drivers)
    champ_pct = win_counts / n_sims * 100
    avg_final_points = final_points.mean(axis=0)
    return champ_pct, avg_final_points


# ====================== PROPRIETARY RATING SYSTEM: "Pit Wall Performance Rating" (PWR) ======================
# Pure compute on data already pulled elsewhere in this app — zero new API calls, zero cost.
# A composite 0-100 score blending: season results, live rolling form, consistency, and reliability.
# This is OUR weighting scheme, not an industry-standard metric — disclosed clearly in the UI.
PWR_WEIGHTS = {"results": 0.40, "form": 0.25, "consistency": 0.20, "reliability": 0.15}

def pwr_grade(score):
    if score >= 90: return "S"
    if score >= 75: return "A"
    if score >= 60: return "B"
    if score >= 45: return "C"
    return "D"

@st.cache_data(ttl=1800)
def compute_pwr_ratings(_standings_df, _driver_bias, _pos_std, _dnf_rates):
    """Builds the PWR score + Driver Form Index for every driver currently in the standings.
    Leading underscore args tell Streamlit's cache not to hash unhashable objects (DataFrame/dicts)
    by identity instead — fine here since this is recomputed deliberately via TTL."""
    if _standings_df.empty:
        return pd.DataFrame()

    max_points = max(_standings_df['Points'].max(), 1)
    rows = []
    for _, row in _standings_df.iterrows():
        d_id = row.get('DriverId', row['Driver'].lower().replace(" ", "_"))

        results_score = (row['Points'] / max_points) * 100

        # Form: driver_bias is centered at 0, negative = better. Convert to a 0-100 scale.
        bias = _driver_bias.get(d_id, 0.0)
        form_score = max(0, min(100, 50 - bias * 60))

        # Consistency: lower finishing-position volatility = better. pos_std typically ranges ~0.8-4.5.
        sigma = _pos_std.get(d_id, 2.5)
        consistency_score = max(0, min(100, 100 - (sigma - 0.8) / (4.5 - 0.8) * 100))

        # Reliability: inverse of historical DNF rate (clipped 2%-40% elsewhere).
        dnf_p = _dnf_rates.get(d_id, 0.12)
        reliability_score = max(0, min(100, (1 - dnf_p) * 100))

        pwr = (
            results_score * PWR_WEIGHTS["results"] +
            form_score * PWR_WEIGHTS["form"] +
            consistency_score * PWR_WEIGHTS["consistency"] +
            reliability_score * PWR_WEIGHTS["reliability"]
        )

        rows.append({
            "Driver": row['Driver'], "Team": row['Team'],
            "PWR Score": round(pwr, 1), "Grade": pwr_grade(pwr),
            "Form Index": round(form_score, 1),
            "Results": round(results_score, 1),
            "Consistency": round(consistency_score, 1),
            "Reliability": round(reliability_score, 1),
        })

    return pd.DataFrame(rows).sort_values("PWR Score", ascending=False).reset_index(drop=True)


# ====================== RACE DEBRIEF GENERATOR ======================
# IMPORTANT HONESTY NOTE: this is a deterministic, rule-based natural-language template engine —
# NOT a call to a hosted LLM/AI API. A real LLM API call costs money per request and would break
# the "permanently free" requirement at any scale, so this builds prose directly from the same
# numbers already computed elsewhere in the app (rolling form, safety-car proxy, anchor scores).
def generate_race_debrief(sim_df, drivers_meta, constructor_bias, driver_bias, sc_p, race_name, weather):
    if sim_df is None or sim_df.empty:
        return "Not enough data to generate a debrief for this race yet."

    favorite = sim_df.iloc[0]
    second = sim_df.iloc[1] if len(sim_df) > 1 else None
    margin = favorite['Win %'] - (second['Win %'] if second is not None else 0)

    d_id_lookup = {d["Driver"]: d for d in drivers_meta}
    fav_meta = d_id_lookup.get(favorite['Driver'], {})
    fav_sigma = fav_meta.get("sigma", 2.5)
    fav_dnf = fav_meta.get("dnf_p", 0.12)

    sentences = []

    if margin > 15:
        sentences.append(f"The model favors **{favorite['Driver']}** by a wide margin this weekend, giving them a {favorite['Win %']}% win probability — well clear of {second['Driver'] if second is not None else 'the field'} at {second['Win %'] if second is not None else 0}%.")
    elif margin > 5:
        sentences.append(f"**{favorite['Driver']}** comes in as a moderate favorite at {favorite['Win %']}% win probability, with {second['Driver'] if second is not None else 'the rest of the field'} not far behind at {second['Win %'] if second is not None else 0}%.")
    else:
        sentences.append(f"This looks like a tight one — **{favorite['Driver']}** edges out the field with only a {favorite['Win %']}% win probability, barely ahead of {second['Driver'] if second is not None else 'the chasing pack'} at {second['Win %'] if second is not None else 0}%.")

    if sc_p >= 0.35:
        sentences.append(f"{race_name} has a historically high safety-car rate (≈{sc_p*100:.0f}% of past races here), which adds real variance to the result — the win probabilities above should be read as a range of plausible outcomes, not a near-certainty.")
    elif sc_p <= 0.12:
        sentences.append(f"{race_name} has a historically low safety-car rate (≈{sc_p*100:.0f}%), which reduces randomness and makes the favorite's position more secure than at a chaos-prone circuit.")

    if fav_dnf >= 0.20:
        sentences.append(f"Worth flagging: {favorite['Driver']}'s historical retirement rate ({fav_dnf*100:.0f}%) is on the higher side, which is already baked into the {favorite['DNF %']}% DNF probability above.")
    if fav_sigma >= 3.5:
        sentences.append(f"{favorite['Driver']}'s results have been fairly volatile historically (high race-to-race variance), so this projection carries more uncertainty than a more consistent driver's would.")

    if "Rain" in weather:
        sentences.append(f"{weather} conditions widen the spread of outcomes across the whole field — wet weather amplifies pace variance for everyone, which is reflected in the simulation above.")

    return " ".join(sentences)


# ====================== CIRCUIT INTELLIGENCE (pure compute on existing free data) ======================
@st.cache_data(ttl=3600)
def get_circuit_intelligence(circuit_id, year_cutoff):
    """Builds a profile for one circuit from real historical results already used elsewhere
    in this app: safety-car proxy, DNF rate, and a 'shake-up index' (how much grid position
    typically changes by the finish — a free proxy for overtaking difficulty)."""
    all_rows = []
    for year in range(max(2016, year_cutoff - 9), year_cutoff + 1):
        try:
            r = requests.get(f"https://api.jolpi.ca/ergast/f1/{year}/circuits/{circuit_id}/results.json?limit=200", timeout=8)
            if r.status_code == 200:
                for race in r.json()['MRData']['RaceTable']['Races']:
                    for res in race.get('Results', []):
                        all_rows.append({
                            "grid": int(res.get('grid', 0)),
                            "finish": int(res.get('positionOrder', res.get('position', 20))),
                            "status": res.get('status', ''),
                            "winner": res.get('position') == '1',
                            "driver": f"{res['Driver']['givenName']} {res['Driver']['familyName']}",
                            "constructor": res['Constructor']['name'],
                            "season": int(race['season'])
                        })
        except Exception:
            continue

    if not all_rows:
        return None

    df = pd.DataFrame(all_rows)
    df['finished_clean'] = df['status'].str.contains("Finished", case=False, na=False) | df['status'].str.contains(r'^\+', regex=True, na=False)
    dnf_rate = round((1 - df['finished_clean'].mean()) * 100, 1)
    shake_up_index = round((df['grid'] - df['finish']).abs().mean(), 2)
    pole_to_win_rate = round((df[df['grid'] == 1]['finish'] == 1).mean() * 100, 1) if (df['grid'] == 1).any() else None
    top_winners = df[df['finish'] == 1]['driver'].value_counts().head(3)
    top_constructors = df[df['finish'] == 1]['constructor'].value_counts().head(3)

    return {
        "races_analyzed": df['season'].nunique(),
        "dnf_rate": dnf_rate,
        "shake_up_index": shake_up_index,
        "pole_to_win_rate": pole_to_win_rate,
        "top_winners": top_winners,
        "top_constructors": top_constructors
    }


# ====================== TEAM PERFORMANCE ANALYZER ======================
@st.cache_data(ttl=1800)
def get_constructor_season_trend(year):
    """Cumulative constructor points race-by-race this season, for trend charting."""
    races = get_recent_results(year)
    completed = [r for r in races if r.get('Results')]
    if not completed:
        return pd.DataFrame()

    points_map = {}
    rows = []
    for race in completed:
        round_num = int(race['round'])
        for res in race.get('Results', []):
            team = res['Constructor']['name']
            pts = float(res.get('points', 0))
            points_map[team] = points_map.get(team, 0.0) + pts
        for team, total in points_map.items():
            rows.append({"Round": round_num, "Team": team, "Cumulative Points": total})

    return pd.DataFrame(rows)


# ====================== FANTASY F1 ASSISTANT ======================
# IMPORTANT HONESTY NOTE: official F1 Fantasy pricing isn't available via any free API, so this
# builds a SYNTHETIC budget (scaled from real season points/PWR) rather than pretending to mirror
# the official game's real prices. Clearly disclosed in the UI — this is a fan-built optimizer,
# not an official F1 Fantasy companion.
def build_fantasy_budget(standings_df, pwr_df):
    if standings_df.empty:
        return pd.DataFrame()
    merged = standings_df.merge(pwr_df[['Driver', 'PWR Score']], on='Driver', how='left') if not pwr_df.empty else standings_df.copy()
    if 'PWR Score' not in merged.columns:
        merged['PWR Score'] = 50.0
    merged['PWR Score'] = merged['PWR Score'].fillna(merged['PWR Score'].mean())
    # Synthetic credit cost: scaled 4.0-30.0, weighted toward current points (most predictive of real game pricing)
    score = merged['Points'].rank(pct=True) * 0.6 + merged['PWR Score'].rank(pct=True) * 0.4
    merged['Credits'] = (4.0 + score * 26.0).round(1)
    return merged[['Driver', 'Team', 'Points', 'PWR Score', 'Credits']]

def optimize_fantasy_team(budget_df, projected_points, budget_cap=100.0, team_size=5):
    """Simple greedy-by-value optimizer (points-per-credit), respecting a credit cap.
    Not a true global optimum (that's a knapsack problem) but a fast, transparent free heuristic."""
    df = budget_df.copy()
    df['Projected Points'] = df['Driver'].map(projected_points).fillna(0.0)
    df['Value'] = df['Projected Points'] / df['Credits'].replace(0, 0.1)
    df = df.sort_values('Value', ascending=False)

    picked, spent = [], 0.0
    for _, row in df.iterrows():
        if len(picked) >= team_size:
            break
        if spent + row['Credits'] <= budget_cap:
            picked.append(row)
            spent += row['Credits']
    return pd.DataFrame(picked), spent

@st.cache_data(ttl=1800)
def get_rolling_form(year, n_races=5):
    """
    Replaces the old hardcoded team_bias dict with a LIVE, self-updating signal.
    Pulls the most recent completed races of the season (free, same Ergast feed already
    used elsewhere in this app) and computes a recency-weighted average finishing
    position per constructor and per driver. More recent races count more.
    Returns (constructor_bias, driver_bias) dicts keyed by constructorId / driverId,
    centered on 0 so they behave the same way the old hardcoded numbers did.
    """
    races = get_recent_results(year)
    completed = [r for r in races if r.get('Results')]
    if not completed and year > 2016:
        # season just started / no results yet this year -> fall back to previous year's tail end
        races_prev = get_recent_results(year - 1)
        completed = [r for r in races_prev if r.get('Results')]

    recent = completed[-n_races:]
    if not recent:
        return {}, {}

    weights = list(range(1, len(recent) + 1))  # oldest of the window=1 ... most recent=n
    c_score, c_weight, d_score, d_weight = {}, {}, {}, {}

    for race, w in zip(recent, weights):
        for res in race['Results']:
            try:
                pos = int(res.get('positionOrder', res.get('position', 20)))
            except Exception:
                continue
            cid = res['Constructor']['constructorId']
            did = res['Driver']['driverId']
            c_score[cid] = c_score.get(cid, 0) + pos * w
            c_weight[cid] = c_weight.get(cid, 0) + w
            d_score[did] = d_score.get(did, 0) + pos * w
            d_weight[did] = d_weight.get(did, 0) + w

    c_avg = {k: c_score[k] / c_weight[k] for k in c_score}
    d_avg = {k: d_score[k] / d_weight[k] for k in d_score}

    constructor_bias, driver_bias = {}, {}
    if c_avg:
        mean_c = sum(c_avg.values()) / len(c_avg)
        constructor_bias = {k: round((v - mean_c) * 0.35, 3) for k, v in c_avg.items()}
    if d_avg:
        mean_d = sum(d_avg.values()) / len(d_avg)
        driver_bias = {k: round((v - mean_d) * 0.22, 3) for k, v in d_avg.items()}

    return constructor_bias, driver_bias


current_year = datetime.utcnow().year
standings_df = get_current_standings(current_year)
cons_df = get_constructor_standings(current_year)
next_race = get_next_race(current_year)
if next_race is None:
    next_race = {"name": "Race calendar temporarily unavailable", "round": "—", "date": "—",
                 "circuit": "unknown", "circuit_name": "Unavailable", "location": "—",
                 "is_current": False, "season_complete": None}

tabs = st.tabs(["🏠 HOME", "🏆 PODIUM PREDICTOR", "🪪 DRIVER CARDS", "⚔️ DRIVER COMPARISON", "📜 HISTORY", "🎙️ RACE ENGINEER", "📈 STANDINGS", "📚 STATS VAULT", "📡 LIVE SESSION", "🎮 FANTASY ASSISTANT", "🥊 RIVAL TEAM MODE", "🏟️ CIRCUIT INTELLIGENCE", "🛠️ TEAM ANALYZER"])

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
        if next_race.get("is_current") is False:
            st.caption("⚠️ Current-season calendar isn't loaded on the free data feed yet — showing the most recent confirmed race instead.")
        elif next_race.get("season_complete"):
            st.caption("🏁 The current season has concluded — showing the final race of the season.")
    with col2:
        leader_name = standings_df.iloc[0]['Driver'] if not standings_df.empty else "N/A"
        st.metric("🏆 Championship Leader", leader_name)

    if standings_df.empty:
        st.warning("📡 Live standings are temporarily unavailable from the free data feed. Try refreshing in a few minutes.")
    elif standings_df.attrs.get('is_current') is False:
        st.caption(f"⚠️ Showing final standings from {standings_df.attrs.get('source_year', 'last season')} — current-season data isn't loaded on the free feed yet.")

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
    constructor_bias, driver_bias = get_rolling_form(current_year, n_races=5)

    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("Next Race", next_race["name"])
        st.metric("Round", next_race["round"])
    with col2:
        st.caption(f"**Date:** {next_race['date']} | **Location:** {next_race['location']}")
        if constructor_bias:
            top_form = max(constructor_bias, key=lambda k: -constructor_bias[k])
            st.caption(f"📈 Live rolling form (last 5 races) currently favors **{top_form.replace('_',' ').title()}** — this updates automatically after every race, no manual edits needed.")

    st.markdown("### 📅 Full Season Calendar")
    render_data_table(calendar_df.to_dict("records"))

    predict_tab, whatif_tab, strategy_tab, season_tab, backtest_tab = st.tabs(
        ["🎯 PREDICT NEXT RACE", "🧪 WHAT-IF SANDBOX", "📋 STRATEGY SIMULATOR", "🏆 SEASON SIMULATOR", "🕰️ PREDICTION VS REALITY"]
    )

    # ============== SUB-TAB 1: PREDICT NEXT RACE ==============
    with predict_tab:
        st.markdown("### 🌤️ Weather Simulator")
        wcol1, wcol2 = st.columns(2)
        with wcol1:
            weather = st.selectbox("Track Conditions", ["Dry", "Light Rain", "Heavy Rain", "Hot & Dry"], index=0, key="predict_weather")
        with wcol2:
            track_temp = st.slider("Track Temperature (°C)", 20, 60, 38, key="predict_temp")

        st.markdown("### 🎲 Simulation Settings")
        sim_col1, sim_col2 = st.columns(2)
        with sim_col1:
            n_sims = st.select_slider("Monte Carlo Iterations", options=[1000, 2500, 5000, 8000, 10000], value=5000, key="predict_nsims",
                                       help="How many times the race is simulated. More iterations = smoother probabilities, same speed since it's vectorized.")
        with sim_col2:
            st.caption("Each simulation samples DNF risk, safety-car disruption, and per-driver pace variance from real historical data, plus live rolling-form bias from the last 5 races — then ranks the field.")

        if st.button("🔮 Run Monte Carlo Podium Simulation", type="primary", use_container_width=True, key="predict_btn"):
            with st.spinner(f"Training model + running {n_sims:,} race simulations..."):
                try:
                    model, le_c, le_d, le_const, dnf_rates, pos_std, sc_proxy = train_model_and_risk_profile(current_year)
                    grid_list = fetch_grid_for_round(current_year, next_race['round'], standings_df)
                    drivers_meta, anchor_scores = build_drivers_meta(
                        grid_list, current_year, next_race['round'], next_race["circuit"], weather, track_temp,
                        model, le_c, le_d, le_const, dnf_rates, pos_std, constructor_bias, driver_bias
                    )

                    if not drivers_meta:
                        st.warning("Not enough live grid data to simulate this race yet.")
                    else:
                        sc_p = sc_proxy.get(next_race["circuit"], 0.20)
                        sim_df = run_monte_carlo(drivers_meta, anchor_scores, sc_p, weather, n_sims)

                        st.success(f"🏆 {n_sims:,}-Race Monte Carlo Simulation — **{next_race['name']}** ({weather} conditions, Safety Car probability ≈ {sc_p*100:.0f}%)")

                        podium = sim_df.head(3)
                        cols = st.columns(3)
                        for i, (_, driver) in enumerate(podium.iterrows()):
                            with cols[i]:
                                pos_emoji = ["🥇", "🥈", "🥉"][i]
                                dmeta = team_meta(driver['Team'])
                                delay = f"{i * 0.15:.2f}s"
                                st.markdown(f"""
                                <div class="podium-card" style="animation-delay:{delay}; text-align:center; padding:20px; background:#1a1e2a; border-radius:12px; border:2px solid {dmeta['color']};">
                                    <h2>{pos_emoji} P{i+1} Favorite</h2>
                                    <h3>{dmeta['emoji']} {driver['Driver']}</h3>
                                    <p style="color:{dmeta['color']}; font-weight:700;">{driver['Team']}</p>
                                    <small>From P{driver['Grid']} • {driver['Win %']}% Win • {driver['Podium %']}% Podium</small>
                                </div>
                                """, unsafe_allow_html=True)

                        st.markdown("### 📝 Race Debrief")
                        debrief_text = generate_race_debrief(sim_df, drivers_meta, constructor_bias, driver_bias, sc_p, next_race['name'], weather)
                        st.markdown(f'<div class="pitwall-card" style="border-left:4px solid #38bdf8;">{debrief_text}</div>', unsafe_allow_html=True)
                        st.caption("Auto-generated from the same model inputs above via rule-based templates — not a paid AI/LLM call, so this stays free forever.")

                        st.markdown("### 📊 Full Probability Distribution (Win % / Podium % / Top 5 % / DNF %)")
                        st.caption("Ranked by simulated win probability — this reflects thousands of simulated race outcomes, not one fixed guess.")
                        st.dataframe(
                            sim_df, use_container_width=True, hide_index=True,
                            column_config={
                                "Win %": st.column_config.ProgressColumn("Win %", min_value=0, max_value=max(1.0, sim_df["Win %"].max()), format="%.1f%%"),
                                "Podium %": st.column_config.ProgressColumn("Podium %", min_value=0, max_value=100, format="%.1f%%"),
                                "Top 5 %": st.column_config.ProgressColumn("Top 5 %", min_value=0, max_value=100, format="%.1f%%"),
                                "DNF %": st.column_config.ProgressColumn("DNF %", min_value=0, max_value=max(1.0, sim_df["DNF %"].max()), format="%.1f%%"),
                            }
                        )

                        with st.expander("ℹ️ How this simulation works (methodology)"):
                            st.markdown(f"""
                            - **Pace anchor**: a Random Forest trained on 10 years of real F1 results (year, round, circuit, driver, constructor, grid) sets each driver's expected pace, adjusted for weather and track temperature.
                            - **Live rolling form**: constructor and driver bias is recomputed from the last 5 real races every time you load this page — no hardcoded numbers, it self-updates race after race.
                            - **DNF probability**: each driver's historical retirement rate from real race statuses (clipped 2%–40%).
                            - **Safety car risk**: share of past races at this circuit with 3+ retirements — a free, data-driven proxy.
                            - **Pace variance**: each driver's historical finishing-position volatility, amplified by wet weather.
                            - The race is simulated **{n_sims:,} times**; the percentages above are how often each driver landed in that position across all simulated races.
                            """)

                except Exception as e:
                    st.error(f"Simulation error: {str(e)}")

    # ============== SUB-TAB: WHAT-IF SANDBOX ==============
    with whatif_tab:
        st.caption("Construct your own hypothetical scenario: override any driver's starting grid position and rerun the full Monte Carlo engine to see how win/podium odds shift. Uses the same model, risk profile, and live rolling form as the main predictor — just with a grid you control instead of the real qualifying result.")

        whatif_weather = st.selectbox("Track Conditions", ["Dry", "Light Rain", "Heavy Rain", "Hot & Dry"], index=0, key="whatif_weather")
        whatif_temp = st.slider("Track Temperature (°C)", 20, 60, 38, key="whatif_temp")
        whatif_nsims = st.select_slider("Monte Carlo Iterations", options=[1000, 2500, 5000], value=2500, key="whatif_nsims")

        base_grid_list = fetch_grid_for_round(current_year, next_race['round'], standings_df)

        st.markdown("#### 🛠️ Override Starting Grid")
        st.caption("Defaults to the real (or projected) grid. Change any value to build a hypothetical — e.g. 'what if the championship leader started P15?'")

        edited_grid = []
        edit_cols = st.columns(2)
        for i, entry in enumerate(base_grid_list[:20]):
            with edit_cols[i % 2]:
                new_pos = st.number_input(f"{entry['driver']} ({entry['team']})", min_value=1, max_value=22, value=entry['grid'], key=f"whatif_grid_{i}")
                edited_grid.append({**entry, "grid": new_pos})

        if st.button("🧪 Run What-If Simulation", type="primary", use_container_width=True, key="whatif_btn"):
            with st.spinner("Running the sandbox scenario..."):
                try:
                    model, le_c, le_d, le_const, dnf_rates, pos_std, sc_proxy = train_model_and_risk_profile(current_year)
                    drivers_meta, anchor_scores = build_drivers_meta(
                        edited_grid, current_year, next_race['round'], next_race["circuit"], whatif_weather, whatif_temp,
                        model, le_c, le_d, le_const, dnf_rates, pos_std, constructor_bias, driver_bias
                    )
                    if not drivers_meta:
                        st.warning("Not enough grid data to run this scenario.")
                    else:
                        sc_p = sc_proxy.get(next_race["circuit"], 0.20)
                        whatif_df = run_monte_carlo(drivers_meta, anchor_scores, sc_p, whatif_weather, whatif_nsims)

                        st.success("🧪 What-if scenario results")
                        st.dataframe(
                            whatif_df, use_container_width=True, hide_index=True,
                            column_config={
                                "Win %": st.column_config.ProgressColumn("Win %", min_value=0, max_value=max(1.0, whatif_df["Win %"].max()), format="%.1f%%"),
                                "Podium %": st.column_config.ProgressColumn("Podium %", min_value=0, max_value=100, format="%.1f%%"),
                            }
                        )
                        whatif_debrief = generate_race_debrief(whatif_df, drivers_meta, constructor_bias, driver_bias, sc_p, next_race['name'], whatif_weather)
                        st.markdown(f'<div class="pitwall-card" style="border-left:4px solid #a855f7;">{whatif_debrief}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"What-if simulation error: {str(e)}")

    # ============== SUB-TAB 2: STRATEGY SIMULATOR ==============
    with strategy_tab:
        st.caption("See how the win/podium probability distribution shifts if a driver runs a non-optimal number of pit stops. This uses an approximate, transparently-modeled time-to-position conversion — it's a simplification, not telemetry-grade physics, but it's free and directionally honest.")

        strat_col1, strat_col2, strat_col3, strat_col4 = st.columns(4)
        with strat_col1:
            strat_weather = st.selectbox("Track Conditions", ["Dry", "Light Rain", "Heavy Rain", "Hot & Dry"], index=0, key="strat_weather")
        with strat_col2:
            strat_temp = st.slider("Track Temperature (°C)", 20, 60, 38, key="strat_temp")
        with strat_col3:
            pit_loss_seconds = st.slider("Pit Lane Loss (s)", 15, 30, 22, key="pit_loss",
                                          help="Typical real-world time lost per stop, including pit lane speed limit. Varies by circuit; 22s is a common F1 average.")
        with strat_col4:
            total_laps = st.slider("Total Race Laps", 40, 78, 58, key="total_laps", help="Most F1 races run 50-70 laps depending on circuit length.")

        st.markdown("##### 🛞 Tyre Degradation Curves at This Track Temperature")
        st.caption("Pure physics-style modeling, not telemetry-derived — illustrative wear curves showing why Softs fade fastest and Hards last longest. Feeds directly into the strategy comparison below.")
        deg_chart_rows = []
        max_preview_laps = 40
        for compound in ["Soft", "Medium", "Hard"]:
            curve = tyre_degradation_curve(compound, max_preview_laps, strat_temp)
            for lap, loss in enumerate(curve, start=1):
                deg_chart_rows.append({"Lap": lap, "Compound": compound, "Cumulative Time Lost (s)": round(float(loss), 2)})
        deg_df = pd.DataFrame(deg_chart_rows).pivot(index="Lap", columns="Compound", values="Cumulative Time Lost (s)")
        st.line_chart(deg_df, use_container_width=True, color=["#ff4d4d", "#f5d142", "#e8e8e8"])

        strat_n_sims = st.select_slider("Monte Carlo Iterations", options=[1000, 2500, 5000, 8000], value=2500, key="strat_nsims")

        st.markdown("#### Compare Strategies Side-by-Side")
        chosen_strategies = st.multiselect("Strategies to simulate", ["1-Stop", "2-Stop", "3-Stop"], default=["1-Stop", "2-Stop", "3-Stop"], key="strat_choices")

        if st.button("📋 Run Strategy Comparison", type="primary", use_container_width=True, key="strategy_btn"):
            if not chosen_strategies:
                st.warning("Pick at least one strategy to simulate.")
            else:
                with st.spinner("Running strategy comparison simulations..."):
                    try:
                        model, le_c, le_d, le_const, dnf_rates, pos_std, sc_proxy = train_model_and_risk_profile(current_year)
                        grid_list = fetch_grid_for_round(current_year, next_race['round'], standings_df)
                        sc_p = sc_proxy.get(next_race["circuit"], 0.20)

                        # Time-loss for each strategy now comes from the tyre degradation model above
                        # (real compound wear curves + pit loss), not a flat stop-count guess.
                        # ~25s of pure time loss is treated as roughly equivalent to 1 grid position of pace
                        # at most circuits — an approximation, clearly disclosed.
                        stop_count = {"1-Stop": 1, "2-Stop": 2, "3-Stop": 3}
                        time_loss_by_strategy = {}
                        breakdown_by_strategy = {}
                        for strat, n_stops in stop_count.items():
                            loss, breakdown = estimate_strategy_time_loss(n_stops, total_laps, strat_temp, pit_loss_seconds)
                            time_loss_by_strategy[strat] = loss
                            breakdown_by_strategy[strat] = breakdown

                        baseline_loss = min(time_loss_by_strategy.values())  # the fastest strategy becomes the zero-penalty reference
                        strategy_results = {}

                        for strat in chosen_strategies:
                            n_stops = stop_count[strat]
                            extra_penalty = (time_loss_by_strategy[strat] - baseline_loss) / 25.0
                            drivers_meta, anchor_scores = build_drivers_meta(
                                grid_list, current_year, next_race['round'], next_race["circuit"], strat_weather, strat_temp,
                                model, le_c, le_d, le_const, dnf_rates, pos_std, constructor_bias, driver_bias,
                                extra_stop_penalty=extra_penalty
                            )
                            if drivers_meta:
                                strategy_results[strat] = run_monte_carlo(drivers_meta, anchor_scores, sc_p, strat_weather, strat_n_sims, seed=42)

                        if not strategy_results:
                            st.warning("Not enough live grid data to simulate this race yet.")
                        else:
                            st.success(f"📋 Strategy comparison for **{next_race['name']}** — {len(chosen_strategies)} strategies, {strat_n_sims:,} simulations each")

                            st.markdown("##### ⏱️ Estimated Total Time Lost to Tyre Wear + Pit Stops")
                            st.caption("This isolated calculation often favors fewer stops in clean air — it doesn't capture the tactical upside of fresher tyres (overtaking, undercutting, reacting to a safety car). Those tactical effects come from the win/podium % below, via the Monte Carlo engine's grid-position and safety-car modeling, not from this time-loss number alone.")
                            time_loss_rows = [{"Strategy": s, "Total Time Lost (s)": round(time_loss_by_strategy[s], 1), "Pit Stops": stop_count[s]} for s in chosen_strategies]
                            render_data_table(sorted(time_loss_rows, key=lambda r: r["Total Time Lost (s)"]))

                            strat_cols = st.columns(len(strategy_results))
                            for col, (strat, df_s) in zip(strat_cols, strategy_results.items()):
                                with col:
                                    leader = df_s.iloc[0]
                                    dmeta = team_meta(leader['Team'])
                                    st.markdown(f"""
                                    <div class="pitwall-card" style="border-left:4px solid {dmeta['color']};">
                                        <h3>{strat}</h3>
                                        <h4>{dmeta['emoji']} {leader['Driver']} favored</h4>
                                        <p style="color:{dmeta['color']};">{leader['Win %']}% Win • {leader['Podium %']}% Podium</p>
                                    </div>
                                    """, unsafe_allow_html=True)

                            st.markdown("#### How each driver's odds shift by strategy")
                            compare_rows = []
                            all_drivers = strategy_results[chosen_strategies[0]]['Driver'].tolist()
                            for d in all_drivers:
                                row = {"Driver": d}
                                for strat, df_s in strategy_results.items():
                                    match = df_s[df_s['Driver'] == d]
                                    row[f"{strat} Win %"] = match['Win %'].values[0] if not match.empty else 0.0
                                    row[f"{strat} Podium %"] = match['Podium %'].values[0] if not match.empty else 0.0
                                compare_rows.append(row)
                            compare_df = pd.DataFrame(compare_rows).sort_values(f"{chosen_strategies[0]} Win %", ascending=False).reset_index(drop=True)
                            render_data_table(compare_df.to_dict("records"))
                    except Exception as e:
                        st.error(f"Strategy simulation error: {str(e)}")

    # ============== SUB-TAB 3: SEASON SIMULATOR ==============
    with season_tab:
        st.caption("Runs the rest of the season forward thousands of times using the same Monte Carlo engine as the race predictor, awarding real F1 points per simulated race, to estimate each driver's title chances. Sprint races and bonus points (fastest lap, etc.) aren't modeled — disclosed honestly. Since future qualifying doesn't exist yet, this uses each driver's current championship position as a stand-in starting grid for every remaining round — a necessary simplification.")

        season_n_sims = st.select_slider("Season Simulations", options=[500, 1000, 2000, 3000, 5000], value=2000, key="season_nsims",
                                          help="Each one replays every remaining race of the season once. Higher = smoother title-odds estimates, a bit slower.")

        if st.button("🏆 Simulate Rest of Season", type="primary", use_container_width=True, key="season_btn"):
            with st.spinner("Projecting the remainder of the season..."):
                try:
                    if standings_df.empty:
                        st.warning("Current standings are unavailable, so the season can't be projected right now.")
                    else:
                        remaining_rounds = get_remaining_rounds(current_year, int(next_race['round']) if str(next_race['round']).isdigit() else 1)
                        if not remaining_rounds:
                            st.info("📻 No remaining rounds found — the season may already be complete, or calendar data isn't loaded yet.")
                        else:
                            model, le_c, le_d, le_const, dnf_rates, pos_std, sc_proxy = train_model_and_risk_profile(current_year)

                            # Fixed driver lineup for the whole projection = current standings order.
                            # Future qualifying doesn't exist yet, so championship position is used as
                            # a stand-in grid — a necessary simplification, disclosed above.
                            season_grid_list = []
                            for i, row in standings_df.iterrows():
                                season_grid_list.append({
                                    "driver": row['Driver'],
                                    "d_id": row.get('DriverId', row['Driver'].lower().replace(" ", "_")),
                                    "team": row['Team'],
                                    "c_id": row['Team'].lower().replace(" ", "_"),
                                    "grid": int(row['Pos'])
                                })

                            per_round_meta = []
                            for rnd in remaining_rounds[:24]:  # season-length safety cap
                                drivers_meta, anchor_scores = build_drivers_meta(
                                    season_grid_list, current_year, rnd["round"], rnd["circuit_id"], "Dry", 38,
                                    model, le_c, le_d, le_const, dnf_rates, pos_std, constructor_bias, driver_bias
                                )
                                if drivers_meta:
                                    sc_p = sc_proxy.get(rnd["circuit_id"], 0.20)
                                    per_round_meta.append((drivers_meta, anchor_scores, sc_p))

                            if not per_round_meta:
                                st.warning("Not enough data to project the remaining rounds.")
                            else:
                                current_points = standings_df.sort_values('Pos')['Points'].to_numpy(dtype=float)
                                champ_pct, avg_final_points = simulate_remaining_season(per_round_meta, current_points, n_sims=season_n_sims)

                                season_df = pd.DataFrame({
                                    "Driver": [d["Driver"] for d in per_round_meta[0][0]],
                                    "Team": [d["Team"] for d in per_round_meta[0][0]],
                                    "Current Points": current_points.round(0),
                                    "Title %": champ_pct.round(1),
                                    "Projected Final Points": avg_final_points.round(0)
                                }).sort_values("Title %", ascending=False).reset_index(drop=True)

                                st.success(f"🏆 {season_n_sims:,} simulated seasons across {len(per_round_meta)} remaining round(s)")

                                top3 = season_df.head(3)
                                cols = st.columns(3)
                                for i, (_, d) in enumerate(top3.iterrows()):
                                    with cols[i]:
                                        dmeta = team_meta(d['Team'])
                                        st.markdown(f"""
                                        <div class="podium-card" style="text-align:center; padding:20px; background:#1a1e2a; border-radius:12px; border:2px solid {dmeta['color']};">
                                            <h3>{dmeta['emoji']} {d['Driver']}</h3>
                                            <p style="color:{dmeta['color']}; font-weight:700;">{d['Team']}</p>
                                            <h2>{d['Title %']}% Title Odds</h2>
                                            <small>Projected final: {int(d['Projected Final Points'])} pts</small>
                                        </div>
                                        """, unsafe_allow_html=True)

                                st.markdown("#### Full Championship Odds")
                                st.dataframe(
                                    season_df, use_container_width=True, hide_index=True,
                                    column_config={
                                        "Title %": st.column_config.ProgressColumn("Title %", min_value=0, max_value=max(1.0, season_df["Title %"].max()), format="%.1f%%"),
                                    }
                                )
                except Exception as e:
                    st.error(f"Season simulation error: {str(e)}")

    # ============== SUB-TAB 3: PREDICTION VS REALITY ==============
    with backtest_tab:
        st.caption("A retrospective check: rerun the simulation for the most recently completed race using its actual qualifying grid, then compare against what really happened. This uses today's rolling-form numbers rather than a frozen pre-race snapshot, so treat it as a sanity-check on the model, not a strict logged forecast history.")

        if st.button("🕰️ Backtest Most Recent Race", type="primary", use_container_width=True, key="backtest_btn"):
            with st.spinner("Pulling the last completed race and rerunning the simulation..."):
                try:
                    races = get_recent_results(current_year)
                    completed = [r for r in races if r.get('Results')]
                    if not completed:
                        st.info("No completed races yet this season to backtest against.")
                    else:
                        last_race = completed[-1]
                        round_num = int(last_race['round'])
                        circuit_id = last_race['Circuit']['circuitId']

                        actual_top3 = [{
                            "Pos": int(res['position']),
                            "Driver": f"{res['Driver']['givenName']} {res['Driver']['familyName']}",
                            "Team": res['Constructor']['name']
                        } for res in last_race['Results'][:3]]

                        model, le_c, le_d, le_const, dnf_rates, pos_std, sc_proxy = train_model_and_risk_profile(current_year)
                        grid_list = fetch_grid_for_round(current_year, round_num, standings_df)
                        drivers_meta, anchor_scores = build_drivers_meta(
                            grid_list, current_year, round_num, circuit_id, "Dry", 38,
                            model, le_c, le_d, le_const, dnf_rates, pos_std, constructor_bias, driver_bias
                        )
                        sim_df = None
                        if drivers_meta:
                            sc_p = sc_proxy.get(circuit_id, 0.20)
                            sim_df = run_monte_carlo(drivers_meta, anchor_scores, sc_p, "Dry", 5000)

                        if sim_df is None or sim_df.empty:
                            st.warning("Couldn't rebuild the grid for this race to backtest.")
                        else:
                            st.success(f"🕰️ Prediction vs Reality — **{last_race['raceName']}**")

                            real_col, pred_col = st.columns(2)
                            with real_col:
                                st.markdown("#### ✅ What Actually Happened")
                                for r in actual_top3:
                                    dmeta = team_meta(r['Team'])
                                    st.markdown(f'<div class="pitwall-card" style="border-left:4px solid {dmeta["color"]}; margin-bottom:8px;"><b>P{r["Pos"]}</b> — {dmeta["emoji"]} {r["Driver"]} <span style="color:{dmeta["color"]};">({r["Team"]})</span></div>', unsafe_allow_html=True)
                            with pred_col:
                                st.markdown("#### 🔮 What The Model Said")
                                for i, (_, d) in enumerate(sim_df.head(3).iterrows()):
                                    dmeta = team_meta(d['Team'])
                                    st.markdown(f'<div class="pitwall-card" style="border-left:4px solid {dmeta["color"]}; margin-bottom:8px;"><b>P{i+1} fav.</b> — {dmeta["emoji"]} {d["Driver"]} <span style="color:{dmeta["color"]};">{d["Win %"]}% win, {d["Podium %"]}% podium</span></div>', unsafe_allow_html=True)

                            actual_winner = actual_top3[0]['Driver']
                            model_winner_row = sim_df.iloc[0]
                            model_win_pct_for_actual = sim_df[sim_df['Driver'] == actual_winner]['Win %']
                            actual_winner_pct = model_win_pct_for_actual.values[0] if not model_win_pct_for_actual.empty else 0.0
                            hit = actual_winner == model_winner_row['Driver']

                            st.markdown(
                                f'<div class="pitwall-card" style="border-left:4px solid {"#22c55e" if hit else "#ef4444"};">'
                                f'<h4>{"✅ Model correctly favored the race winner" if hit else "❌ Model did not favor the actual winner"}</h4>'
                                f'<p>The model gave <b>{actual_winner}</b> a {actual_winner_pct}% win probability '
                                f'{"as its top pick." if hit else f"— its top pick was {model_winner_row["Driver"]} at {model_winner_row["Win %"]}%."}</p>'
                                f'</div>', unsafe_allow_html=True
                            )
                except Exception as e:
                    st.error(f"Backtest error: {str(e)}")

        st.markdown("---")
        st.markdown("### 📊 Model vs. Baseline — Is This Actually Better Than a Coin Flip?")
        st.caption("The honest test: across the last several completed races, how often did the model's #1 pick actually win, vs. simply always picking the pole-sitter? Pole position is a strong, free, zero-effort baseline — beating it is the real bar, not just 'sounding confident'.")

        n_baseline_races = st.slider("Races to check", 3, 8, 5, key="baseline_n_races")

        if st.button("📊 Run Baseline Comparison", use_container_width=True, key="baseline_btn"):
            with st.spinner(f"Checking the model against the last {n_baseline_races} completed races..."):
                try:
                    races = get_recent_results(current_year)
                    completed = [r for r in races if r.get('Results')]
                    if len(completed) < 2:
                        st.info("Not enough completed races yet this season to run a meaningful baseline comparison.")
                    else:
                        recent_races = completed[-n_baseline_races:]
                        model_obj, le_c, le_d, le_const, dnf_rates, pos_std, sc_proxy = train_model_and_risk_profile(current_year)

                        rows = []
                        for race in recent_races:
                            round_num = int(race['round'])
                            circuit_id = race['Circuit']['circuitId']
                            actual_winner = f"{race['Results'][0]['Driver']['givenName']} {race['Results'][0]['Driver']['familyName']}"

                            pole_sitter = None
                            for res in race['Results']:
                                if str(res.get('grid')) == '1':
                                    pole_sitter = f"{res['Driver']['givenName']} {res['Driver']['familyName']}"
                                    break

                            grid_list = fetch_grid_for_round(current_year, round_num, standings_df)
                            d_meta, a_scores = build_drivers_meta(
                                grid_list, current_year, round_num, circuit_id, "Dry", 38,
                                model_obj, le_c, le_d, le_const, dnf_rates, pos_std, constructor_bias, driver_bias
                            )
                            if d_meta:
                                sc_p_r = sc_proxy.get(circuit_id, 0.20)
                                quick_sim = run_monte_carlo(d_meta, a_scores, sc_p_r, "Dry", 1500)
                                model_pick = quick_sim.iloc[0]['Driver']
                            else:
                                model_pick = None

                            rows.append({
                                "Race": race['raceName'],
                                "Actual Winner": actual_winner,
                                "Model Pick": model_pick or "N/A",
                                "Model Hit": "✅" if model_pick == actual_winner else "❌",
                                "Pole Sitter": pole_sitter or "N/A",
                                "Pole Hit": "✅" if pole_sitter == actual_winner else "❌"
                            })

                        results_df = pd.DataFrame(rows)
                        model_hit_rate = (results_df["Model Hit"] == "✅").mean() * 100
                        pole_hit_rate = (results_df["Pole Hit"] == "✅").mean() * 100

                        bc1, bc2 = st.columns(2)
                        with bc1:
                            color = "#22c55e" if model_hit_rate >= pole_hit_rate else "#ef4444"
                            st.markdown(f'<div class="pitwall-card" style="border-left:4px solid {color};"><h3>🤖 Model Win-Pick Accuracy</h3><h2>{model_hit_rate:.0f}%</h2><small>across {len(results_df)} races</small></div>', unsafe_allow_html=True)
                        with bc2:
                            st.markdown(f'<div class="pitwall-card" style="border-left:4px solid #94a3b8;"><h3>🏁 Always-Pick-Pole Baseline</h3><h2>{pole_hit_rate:.0f}%</h2><small>across {len(results_df)} races</small></div>', unsafe_allow_html=True)

                        if model_hit_rate > pole_hit_rate:
                            st.success(f"The model beat the naive pole-position baseline by {model_hit_rate - pole_hit_rate:.0f} percentage points over this window.")
                        elif model_hit_rate == pole_hit_rate:
                            st.info("The model matched the naive pole-position baseline over this window — no edge shown yet.")
                        else:
                            st.warning(f"The model underperformed the naive pole-position baseline by {pole_hit_rate - model_hit_rate:.0f} percentage points over this window. Small sample sizes can swing this a lot — worth re-checking after more races.")

                        render_data_table(results_df.to_dict("records"))
                        st.caption("These picks are re-simulated using today's rolling form rather than a frozen pre-race snapshot — a small lookahead-bias caveat worth knowing when reading the hit rate above.")
                except Exception as e:
                    st.error(f"Baseline comparison error: {str(e)}")

# ====================== DRIVER STAT CARDS ======================
with tabs[2]:
    st.subheader("🪪 Driver Stat Cards")

    cards_subtab, rating_subtab = st.tabs(["🪪 STAT CARDS", "⭐ PWR RATING & FORM INDEX"])

    with cards_subtab:
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

    with rating_subtab:
        st.caption("**Pit Wall Performance Rating (PWR)** — our own proprietary 0-100 score blending season results (40%), live rolling form (25%), finishing-position consistency (20%), and reliability/DNF history (15%). This is our weighting, not an official F1 metric — disclosed plainly. Computed entirely from data already pulled elsewhere in this app, zero new cost.")

        if standings_df.empty:
            st.warning("Driver data is temporarily unavailable. Try again shortly.")
        else:
            try:
                _, _, _, _, dnf_rates_pwr, pos_std_pwr, _ = train_model_and_risk_profile(current_year)
                pwr_df = compute_pwr_ratings(standings_df, driver_bias, pos_std_pwr, dnf_rates_pwr)

                if pwr_df.empty:
                    st.info("Not enough data yet to compute ratings.")
                else:
                    top3 = pwr_df.head(3)
                    cols = st.columns(3)
                    for i, (_, d) in enumerate(top3.iterrows()):
                        with cols[i]:
                            dmeta = team_meta(d['Team'])
                            st.markdown(f"""
                            <div class="podium-card" style="text-align:center; padding:20px; background:#1a1e2a; border-radius:12px; border:2px solid {dmeta['color']};">
                                <h2>{["🥇","🥈","🥉"][i]} {d['Grade']}-Tier</h2>
                                <h3>{dmeta['emoji']} {d['Driver']}</h3>
                                <p style="color:{dmeta['color']}; font-weight:700;">{d['Team']}</p>
                                <h2>{d['PWR Score']} PWR</h2>
                            </div>
                            """, unsafe_allow_html=True)

                    st.markdown("#### Full PWR Leaderboard")
                    st.dataframe(
                        pwr_df, use_container_width=True, hide_index=True,
                        column_config={
                            "PWR Score": st.column_config.ProgressColumn("PWR Score", min_value=0, max_value=100, format="%.1f"),
                            "Form Index": st.column_config.ProgressColumn("Form Index", min_value=0, max_value=100, format="%.1f"),
                            "Results": st.column_config.ProgressColumn("Results", min_value=0, max_value=100, format="%.1f"),
                            "Consistency": st.column_config.ProgressColumn("Consistency", min_value=0, max_value=100, format="%.1f"),
                            "Reliability": st.column_config.ProgressColumn("Reliability", min_value=0, max_value=100, format="%.1f"),
                        }
                    )
                    with st.expander("ℹ️ How PWR and Form Index are calculated"):
                        st.markdown("""
                        - **Results (40%)**: this season's points as a share of the championship leader's points.
                        - **Form Index (25%)**: derived from the same live rolling-form bias (last 5 races) used in the Podium Predictor — a driver trending upward scores higher here, automatically, race after race.
                        - **Consistency (20%)**: inverse of historical finishing-position volatility — a driver who reliably finishes in a tight range scores higher than one who swings between P2 and P15.
                        - **Reliability (15%)**: inverse of historical DNF rate.
                        - **Grade tiers**: S (90+), A (75+), B (60+), C (45+), D (below 45).
                        """)
            except Exception as e:
                st.error(f"Rating calculation error: {str(e)}")

# ====================== DRIVER COMPARISON ======================
with tabs[3]:
    st.subheader("⚔️ Driver Comparison Tool")
    st.caption("Compare any driver in F1 history — not just this season's grid. Current-grid drivers show this season's stats; everyone else shows full career stats, all from the same free historical feed used elsewhere in this app.")

    all_drivers_index = get_all_drivers_index()
    current_names = set(standings_df['Driver'].tolist()) if not standings_df.empty else set()

    if not all_drivers_index:
        st.warning("📡 Could not reach the driver database right now. Try again shortly.")
    else:
        # Current-grid drivers float to the top of the list for convenience, full history still searchable below
        all_names = sorted(all_drivers_index.keys())
        ordered_names = sorted(current_names) + [n for n in all_names if n not in current_names]

        colA, colB = st.columns(2)
        with colA:
            driver1 = st.selectbox("Driver 1", ordered_names, index=0, key="comp_d1")
        with colB:
            default_idx2 = 1 if len(ordered_names) > 1 else 0
            driver2 = st.selectbox("Driver 2", ordered_names, index=default_idx2, key="comp_d2")

        if st.button("Compare Drivers", type="primary", use_container_width=True):

            def get_driver_snapshot(name):
                """Season stats if they're on this year's grid, otherwise full career stats."""
                if name in current_names:
                    row = standings_df[standings_df['Driver'] == name].iloc[0]
                    return {
                        "mode": "season", "Team": row['Team'], "Points": int(row['Points']),
                        "Wins": int(row.get('Wins', 0)), "Pos": int(row['Pos'])
                    }
                else:
                    driver_id = all_drivers_index.get(name)
                    df_career = get_driver_career_results(driver_id) if driver_id else pd.DataFrame()
                    if df_career.empty:
                        return {"mode": "career", "Team": "Unknown", "Points": 0, "Wins": 0, "Races": 0, "Podiums": 0}
                    wins = int((df_career['position'] == '1').sum())
                    podiums = int(df_career['position'].isin(['1', '2', '3']).sum())
                    latest_team = df_career.sort_values(['season', 'round']).iloc[-1]['constructor']
                    return {
                        "mode": "career", "Team": latest_team, "Points": float(df_career['points'].sum()),
                        "Wins": wins, "Races": len(df_career), "Podiums": podiums
                    }

            d1 = get_driver_snapshot(driver1)
            d2 = get_driver_snapshot(driver2)

            c1, c2 = st.columns(2)
            with c1:
                m1 = team_meta(d1['Team'])
                st.markdown(f"#### {m1['emoji']} {driver1}")
                if d1['mode'] == "season":
                    st.metric("Championship Position", f"P{d1['Pos']}", f"{d1['Points']} pts")
                    st.metric("Team", d1['Team'])
                    st.metric("Wins This Season", d1['Wins'])
                else:
                    st.metric("Career Points", f"{d1['Points']:.0f}")
                    st.metric("Most Recent Team", d1['Team'])
                    st.metric("Career Wins / Podiums", f"{d1['Wins']} / {d1.get('Podiums', 0)}")
                    st.caption(f"{d1.get('Races', 0)} career races")
            with c2:
                m2 = team_meta(d2['Team'])
                st.markdown(f"#### {m2['emoji']} {driver2}")
                if d2['mode'] == "season":
                    st.metric("Championship Position", f"P{d2['Pos']}", f"{d2['Points']} pts")
                    st.metric("Team", d2['Team'])
                    st.metric("Wins This Season", d2['Wins'])
                else:
                    st.metric("Career Points", f"{d2['Points']:.0f}")
                    st.metric("Most Recent Team", d2['Team'])
                    st.metric("Career Wins / Podiums", f"{d2['Wins']} / {d2.get('Podiums', 0)}")
                    st.caption(f"{d2.get('Races', 0)} career races")

            if d1['mode'] == d2['mode'] == "season":
                better = driver1 if d1['Points'] > d2['Points'] else (driver2 if d2['Points'] > d1['Points'] else None)
                if better:
                    st.success(f"**{better}** is performing better this season on points.")
                else:
                    st.info("Both drivers are tied on points this season.")
            elif d1['mode'] == d2['mode'] == "career":
                better = driver1 if d1['Points'] > d2['Points'] else (driver2 if d2['Points'] > d1['Points'] else None)
                if better:
                    st.success(f"**{better}** has the stronger career points total.")
            else:
                st.info("Comparing a current-season driver against a career stat line — points scales differ (season vs. all-time), so treat this as informational rather than head-to-head.")

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

# ====================== STATS VAULT (NEW: head-to-head, on this day, circuit history, career trajectory) ======================
with tabs[7]:
    st.subheader("📚 Historical Stats Vault")
    st.caption("Free forever — powered by the same Jolpi/Ergast API used elsewhere in this app, no keys required.")

    vault_get_driver_index = get_all_drivers_index
    vault_get_driver_results = get_driver_career_results

    @st.cache_data(ttl=86400)
    def vault_on_this_day(month, day):
        try:
            results = []
            for year in range(1950, datetime.utcnow().year):
                resp = requests.get(f"https://api.jolpi.ca/ergast/f1/{year}.json?limit=100", timeout=5).json()
                races = resp['MRData']['RaceTable']['Races']
                for r in races:
                    d = r.get('date')
                    if d:
                        dt = datetime.strptime(d, "%Y-%m-%d")
                        if dt.month == month and dt.day == day:
                            results.append({"year": year, "race": r['raceName'], "circuit": r['Circuit']['circuitName'], "round": r['round']})
            return results
        except Exception:
            return []

    @st.cache_data(ttl=86400)
    def vault_on_this_day_winner(year, round_num):
        try:
            resp = requests.get(f"https://api.jolpi.ca/ergast/f1/{year}/{round_num}/results.json?limit=5", timeout=5).json()
            races = resp['MRData']['RaceTable']['Races']
            if races and races[0]['Results']:
                w = races[0]['Results'][0]
                return f"{w['Driver']['givenName']} {w['Driver']['familyName']} ({w['Constructor']['name']})"
            return "Unknown"
        except Exception:
            return "Unknown"

    @st.cache_data(ttl=86400)
    def vault_get_circuit_index():
        try:
            resp = requests.get("https://api.jolpi.ca/ergast/f1/circuits.json?limit=200", timeout=8).json()
            circuits = resp['MRData']['CircuitTable']['Circuits']
            return {c['circuitName']: c['circuitId'] for c in circuits}
        except Exception:
            return {}

    @st.cache_data(ttl=86400)
    def vault_get_circuit_winners(circuit_id):
        try:
            resp = requests.get(f"https://api.jolpi.ca/ergast/f1/circuits/{circuit_id}/results/1.json?limit=200", timeout=8).json()
            races = resp['MRData']['RaceTable']['Races']
            rows = []
            for r in races:
                w = r['Results'][0]
                rows.append({
                    "season": int(r['season']),
                    "race": r['raceName'],
                    "winner": f"{w['Driver']['givenName']} {w['Driver']['familyName']}",
                    "constructor": w['Constructor']['name']
                })
            return pd.DataFrame(rows).sort_values("season", ascending=False).reset_index(drop=True)
        except Exception:
            return pd.DataFrame()

    vault_tabs = st.tabs(["⚔️ HEAD-TO-HEAD", "📅 ON THIS DAY", "🏟️ CIRCUIT HISTORY", "📈 CAREER TRAJECTORY"])

    # --- HEAD-TO-HEAD COMPARISON ---
    with vault_tabs[0]:
        st.markdown("#### ⚔️ Driver Head-to-Head Career Comparison")
        driver_index = vault_get_driver_index()
        if not driver_index:
            st.warning("📡 Could not reach the historical data feed right now. Try again shortly.")
        else:
            names = sorted(driver_index.keys())
            colA, colB = st.columns(2)
            with colA:
                vault_driver_a = st.selectbox("Driver A", names, index=names.index("Lewis Hamilton") if "Lewis Hamilton" in names else 0, key="vault_h2h_a")
            with colB:
                vault_driver_b = st.selectbox("Driver B", names, index=names.index("Max Verstappen") if "Max Verstappen" in names else 1, key="vault_h2h_b")

            if st.button("🔍 Compare Careers", key="vault_h2h_btn"):
                df_a = vault_get_driver_results(driver_index[vault_driver_a])
                df_b = vault_get_driver_results(driver_index[vault_driver_b])

                def vault_summarize(df):
                    if df.empty:
                        return {"Races": 0, "Wins": 0, "Podiums": 0, "Poles (P1 starts)": 0, "Total Points": 0.0, "DNFs": 0}
                    wins = (df['position'] == '1').sum()
                    podiums = df['position'].isin(['1', '2', '3']).sum()
                    poles = (df['grid'] == 1).sum()
                    points = df['points'].sum()
                    dnfs = (~df['status'].str.contains("Finished|\\+", regex=True, na=False)).sum()
                    return {"Races": len(df), "Wins": int(wins), "Podiums": int(podiums), "Poles (P1 starts)": int(poles), "Total Points": float(points), "DNFs": int(dnfs)}

                stats_a, stats_b = vault_summarize(df_a), vault_summarize(df_b)
                compare_rows_h2h = [{"Metric": k, vault_driver_a: stats_a[k], vault_driver_b: stats_b[k]} for k in stats_a]
                render_data_table(compare_rows_h2h)

                m1, m2, m3 = st.columns(3)
                with m1:
                    st.markdown(f'<div class="pitwall-card" style="border-left:4px solid #38bdf8;"><h3>🏆 Win Edge</h3><h2>{vault_driver_a if stats_a["Wins"] >= stats_b["Wins"] else vault_driver_b}</h2><small>{stats_a["Wins"]} vs {stats_b["Wins"]} wins</small></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="pitwall-card" style="border-left:4px solid #a855f7;"><h3>🥇 Points Edge</h3><h2>{vault_driver_a if stats_a["Total Points"] >= stats_b["Total Points"] else vault_driver_b}</h2><small>{stats_a["Total Points"]:.0f} vs {stats_b["Total Points"]:.0f} pts</small></div>', unsafe_allow_html=True)
                with m3:
                    rate_a = (stats_a["Podiums"]/stats_a["Races"]*100 if stats_a["Races"] else 0)
                    rate_b = (stats_b["Podiums"]/stats_b["Races"]*100 if stats_b["Races"] else 0)
                    st.markdown(f'<div class="pitwall-card" style="border-left:4px solid #22c55e;"><h3>🎯 Podium Rate</h3><h2>{rate_a:.1f}% vs {rate_b:.1f}%</h2><small>{vault_driver_a} vs {vault_driver_b}</small></div>', unsafe_allow_html=True)

    # --- ON THIS DAY ---
    with vault_tabs[1]:
        st.markdown("#### 📅 On This Day In Formula 1")
        vault_pick_today = st.checkbox("Use today's date", value=True, key="vault_otd_today")
        if vault_pick_today:
            today_dt = datetime.utcnow()
            otd_month, otd_day = today_dt.month, today_dt.day
        else:
            vault_custom_date = st.date_input("Pick a date", value=datetime.utcnow().date(), key="vault_otd_custom")
            otd_month, otd_day = vault_custom_date.month, vault_custom_date.day

        if st.button("📡 Search Race History", key="vault_otd_btn"):
            with st.spinner("Scanning decades of race calendars..."):
                events = vault_on_this_day(otd_month, otd_day)
            if not events:
                st.info("📻 No Grands Prix were held on this calendar date in F1 history. Try another date.")
            else:
                st.success(f"Found {len(events)} race(s) held on this date across F1 history.")
                for ev in sorted(events, key=lambda x: x['year'], reverse=True):
                    winner = vault_on_this_day_winner(ev['year'], ev['round'])
                    st.markdown(
                        f'<div class="pitwall-card" style="border-left:4px solid #FF1801; margin-bottom:10px;">'
                        f'<h3>{ev["year"]} — {ev["race"]}</h3>'
                        f'<p style="font-size:1.05rem;">🏆 Winner: {winner}</p>'
                        f'<small>📍 {ev["circuit"]}</small></div>',
                        unsafe_allow_html=True
                    )

    # --- CIRCUIT HISTORY ---
    with vault_tabs[2]:
        st.markdown("#### 🏟️ Circuit History: Past Winners")
        circuit_index = vault_get_circuit_index()
        if not circuit_index:
            st.warning("📡 Could not reach the circuit data feed right now. Try again shortly.")
        else:
            circuit_names = sorted(circuit_index.keys())
            default_idx = next((i for i, c in enumerate(circuit_names) if "Catalunya" in c or "Barcelona" in c), 0)
            vault_chosen_circuit = st.selectbox("Select Circuit", circuit_names, index=default_idx, key="vault_circuit_select")
            if st.button("🏁 Load Winners List", key="vault_circuit_btn"):
                with st.spinner("Pulling circuit archives..."):
                    df_winners = vault_get_circuit_winners(circuit_index[vault_chosen_circuit])
                if df_winners.empty:
                    st.info("📻 No recorded Grand Prix winners found for this circuit.")
                else:
                    top_winner_driver = df_winners['winner'].value_counts().idxmax()
                    top_winner_count = df_winners['winner'].value_counts().max()
                    st.markdown(
                        f'<div class="pitwall-card" style="border-left:4px solid #FF8000;">'
                        f'<h3>👑 Most Successful Driver Here</h3>'
                        f'<h2>{top_winner_driver}</h2>'
                        f'<small>{top_winner_count} win(s) at this circuit</small></div>',
                        unsafe_allow_html=True
                    )
                    render_data_table(df_winners.to_dict("records"), team_col="constructor")

    # --- CAREER TRAJECTORY ---
    with vault_tabs[3]:
        st.markdown("#### 📈 Driver Career Trajectory (Points Per Season)")
        driver_index_traj = vault_get_driver_index()
        if not driver_index_traj:
            st.warning("📡 Could not reach the historical data feed right now. Try again shortly.")
        else:
            traj_names = sorted(driver_index_traj.keys())
            vault_traj_driver = st.selectbox("Select Driver", traj_names, index=traj_names.index("Fernando Alonso") if "Fernando Alonso" in traj_names else 0, key="vault_traj_select")
            if st.button("📈 Plot Career Trajectory", key="vault_traj_btn"):
                with st.spinner("Aggregating season-by-season results..."):
                    df_traj = vault_get_driver_results(driver_index_traj[vault_traj_driver])
                if df_traj.empty:
                    st.info("📻 No race results found for this driver.")
                else:
                    season_points = df_traj.groupby("season")["points"].sum().reset_index()
                    season_points.columns = ["Season", "Points"]
                    st.bar_chart(season_points, x="Season", y="Points", use_container_width=True)

                    best_season = season_points.loc[season_points['Points'].idxmax()]
                    total_career_points = season_points['Points'].sum()
                    seasons_active = season_points['Season'].nunique()

                    t1, t2, t3 = st.columns(3)
                    with t1:
                        st.markdown(f'<div class="pitwall-card" style="border-left:4px solid #22c55e;"><h3>🏆 Best Season</h3><h2>{int(best_season["Season"])}</h2><small>{best_season["Points"]:.0f} points</small></div>', unsafe_allow_html=True)
                    with t2:
                        st.markdown(f'<div class="pitwall-card" style="border-left:4px solid #38bdf8;"><h3>🧮 Career Total</h3><h2>{total_career_points:.0f} pts</h2><small>Across {seasons_active} seasons</small></div>', unsafe_allow_html=True)
                    with t3:
                        avg_pts = total_career_points / seasons_active if seasons_active else 0
                        st.markdown(f'<div class="pitwall-card" style="border-left:4px solid #a855f7;"><h3>📊 Avg Points/Season</h3><h2>{avg_pts:.1f}</h2><small>{vault_traj_driver}</small></div>', unsafe_allow_html=True)

# ====================== LIVE SESSION (NEW: OpenF1 live telemetry — free, no key) ======================
with tabs[8]:
    st.subheader("📡 Live Session Feed")
    st.caption("Powered by OpenF1 — a free, no-key live F1 telemetry API. This tab activates around real practice/qualifying/race sessions; outside of those windows it shows the most recent completed session.")

    OPENF1_BASE = "https://api.openf1.org/v1"

    @st.cache_data(ttl=30)
    def openf1_get(endpoint, params=""):
        try:
            url = f"{OPENF1_BASE}/{endpoint}?{params}"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    if st.button("🔄 Refresh Live Data", key="live_refresh"):
        st.cache_data.clear()
        st.rerun()

    session_data = openf1_get("sessions", "session_key=latest")
    if not session_data:
        st.info("📻 No session data available right now — OpenF1 only returns data around real session windows (practice, qualifying, race).")
    else:
        session = session_data[0]
        session_key = session.get("session_key")
        st.markdown(
            f'<div class="pitwall-card" style="border-left:4px solid #FF1801;">'
            f'<h3>{session.get("session_name", "Session")} — {session.get("circuit_short_name", "")}</h3>'
            f'<p>{session.get("location", "")}, {session.get("country_name", "")} • {session.get("date_start", "")[:16].replace("T", " ")} UTC</p>'
            f'</div>', unsafe_allow_html=True
        )

        live_tabs = st.tabs(["⏱️ LIVE TIMING", "🛞 TYRE STINTS", "🛠️ PIT STOPS", "📻 TEAM RADIO"])

        drivers_data = openf1_get("drivers", f"session_key={session_key}")
        driver_lookup_map = {d.get("driver_number"): d for d in drivers_data} if drivers_data else {}

        with live_tabs[0]:
            position_data = openf1_get("position", f"session_key={session_key}")
            if position_data:
                latest_by_driver = {}
                for p in position_data:
                    latest_by_driver[p["driver_number"]] = p
                rows = []
                for num, p in latest_by_driver.items():
                    meta = driver_lookup_map.get(num, {})
                    rows.append({
                        "Pos": p.get("position", 99),
                        "Driver": meta.get("broadcast_name", f"#{num}"),
                        "Team": meta.get("team_name", "Unknown")
                    })
                rows = sorted(rows, key=lambda r: r["Pos"])
                render_styled_table(rows, show_wins=False)
            else:
                st.info("📻 No live position data right now — check back once a session is running.")

        with live_tabs[1]:
            stints_data = openf1_get("stints", f"session_key={session_key}")
            if stints_data:
                stint_rows = []
                for s in stints_data[-22:]:
                    meta = driver_lookup_map.get(s.get("driver_number"), {})
                    stint_rows.append({
                        "Driver": meta.get("broadcast_name", f"#{s.get('driver_number')}"),
                        "Team": meta.get("team_name", "Unknown"),
                        "Compound": s.get("compound", "Unknown"),
                        "Stint Lap Range": f"{s.get('lap_start', '?')}–{s.get('lap_end', '?')}",
                        "Tyre Age at Start": s.get("tyre_age_at_start", "?")
                    })
                render_data_table(stint_rows, team_col="Team")
            else:
                st.info("📻 No tyre stint data available for this session yet.")

        with live_tabs[2]:
            pit_data = openf1_get("pit", f"session_key={session_key}")
            if pit_data:
                pit_rows = []
                for p in pit_data[-22:]:
                    meta = driver_lookup_map.get(p.get("driver_number"), {})
                    pit_rows.append({
                        "Driver": meta.get("broadcast_name", f"#{p.get('driver_number')}"),
                        "Team": meta.get("team_name", "Unknown"),
                        "Lap": p.get("lap_number", "?"),
                        "Pit Duration (s)": p.get("pit_duration", "?")
                    })
                render_data_table(pit_rows, team_col="Team")
            else:
                st.info("📻 No pit stop data recorded for this session yet.")

        with live_tabs[3]:
            radio_data = openf1_get("team_radio", f"session_key={session_key}")
            if radio_data:
                for r in radio_data[-10:][::-1]:
                    meta = driver_lookup_map.get(r.get("driver_number"), {})
                    audio_url = r.get("recording_url")
                    st.markdown(f"**{meta.get('broadcast_name', 'Unknown driver')}** — {r.get('date', '')[:16].replace('T',' ')} UTC")
                    if audio_url:
                        st.audio(audio_url)
            else:
                st.info("📻 No team radio clips available for this session yet.")

# ====================== FANTASY F1 ASSISTANT ======================
with tabs[9]:
    st.subheader("🎮 Fantasy F1 Assistant")
    st.caption("⚠️ Official F1 Fantasy pricing isn't available via any free API, so this uses a SYNTHETIC budget (scaled from real season points + PWR rating), not the actual game's prices. Treat this as a fan-built optimizer for thinking about value, not a companion app for the official game.")

    if standings_df.empty:
        st.warning("Driver data is temporarily unavailable. Try again shortly.")
    else:
        try:
            _, _, _, _, dnf_rates_fa, pos_std_fa, _ = train_model_and_risk_profile(current_year)
            constructor_bias_fa, driver_bias_fa = get_rolling_form(current_year, n_races=5)
            pwr_df_fa = compute_pwr_ratings(standings_df, driver_bias_fa, pos_std_fa, dnf_rates_fa)
            fantasy_budget_df = build_fantasy_budget(standings_df, pwr_df_fa)

            st.markdown("#### 💰 Synthetic Driver Credits")
            st.dataframe(fantasy_budget_df, use_container_width=True, hide_index=True)

            st.markdown("#### 🛠️ Build Your Team")
            fcol1, fcol2 = st.columns(2)
            with fcol1:
                budget_cap = st.slider("Credit Budget Cap", 50.0, 150.0, 100.0, step=5.0, key="fantasy_cap")
            with fcol2:
                team_size = st.slider("Team Size", 3, 6, 5, key="fantasy_size")

            if st.button("🎮 Optimize My Fantasy Team", type="primary", use_container_width=True, key="fantasy_btn"):
                with st.spinner("Projecting next race points and optimizing..."):
                    model, le_c, le_d, le_const, dnf_rates_fa2, pos_std_fa2, sc_proxy_fa = train_model_and_risk_profile(current_year)
                    grid_list_fa = fetch_grid_for_round(current_year, next_race['round'], standings_df)
                    drivers_meta_fa, anchor_scores_fa = build_drivers_meta(
                        grid_list_fa, current_year, next_race['round'], next_race["circuit"], "Dry", 38,
                        model, le_c, le_d, le_const, dnf_rates_fa2, pos_std_fa2, constructor_bias_fa, driver_bias_fa
                    )
                    if not drivers_meta_fa:
                        st.warning("Not enough grid data to project next race points.")
                    else:
                        sc_p_fa = sc_proxy_fa.get(next_race["circuit"], 0.20)
                        sim_fa = run_monte_carlo(drivers_meta_fa, anchor_scores_fa, sc_p_fa, "Dry", 3000)
                        f1_points_table = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
                        # Expected points = sum over positions of P(finish=pos) * points(pos) — derived from Avg Finish + DNF% as an approximation
                        projected_points = {}
                        for _, row in sim_fa.iterrows():
                            if row['Avg Finish (when classified)'] <= 10:
                                idx = max(0, min(9, int(round(row['Avg Finish (when classified)'])) - 1))
                                base_pts = f1_points_table[idx]
                            else:
                                base_pts = 0
                            projected_points[row['Driver']] = base_pts * (1 - row['DNF %'] / 100)

                        picked_team, spent = optimize_fantasy_team(fantasy_budget_df, projected_points, budget_cap, team_size)
                        if picked_team.empty:
                            st.warning("Couldn't build a team within this budget — try raising the cap.")
                        else:
                            st.success(f"🎮 Optimized team — {spent:.1f} / {budget_cap:.1f} credits used")
                            for _, d in picked_team.iterrows():
                                dmeta = team_meta(d['Team'])
                                st.markdown(f'<div class="pitwall-card" style="border-left:4px solid {dmeta["color"]}; margin-bottom:8px;"><b>{dmeta["emoji"]} {d["Driver"]}</b> ({d["Team"]}) — {d["Credits"]} credits, {d["Projected Points"]:.1f} projected pts for {next_race["name"]}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Fantasy assistant error: {str(e)}")

# ====================== RIVAL TEAM MODE ======================
with tabs[10]:
    st.subheader("🥊 Rival Team Mode")
    st.caption("Pick your team and a rival — see the current points gap, recent form comparison, and projected odds of winning the inter-team battle across the rest of the season.")

    if standings_df.empty or cons_df.empty:
        st.warning("Standings data is temporarily unavailable. Try again shortly.")
    else:
        team_options = cons_df['Team'].tolist()
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            my_team = st.selectbox("My Team", team_options, index=0, key="rival_my_team")
        with rcol2:
            rival_team = st.selectbox("Rival Team", team_options, index=1 if len(team_options) > 1 else 0, key="rival_team")

        if st.button("🥊 Compare Teams", type="primary", use_container_width=True, key="rival_btn"):
            try:
                my_pts = cons_df[cons_df['Team'] == my_team]['Points'].values[0]
                rival_pts = cons_df[cons_df['Team'] == rival_team]['Points'].values[0]
                gap = my_pts - rival_pts

                constructor_bias_rv, driver_bias_rv = get_rolling_form(current_year, n_races=5)
                my_form = constructor_bias_rv.get(my_team.lower().replace(" ", "_"), 0.0)
                rival_form = constructor_bias_rv.get(rival_team.lower().replace(" ", "_"), 0.0)

                rc1, rc2 = st.columns(2)
                with rc1:
                    mmeta = team_meta(my_team)
                    st.markdown(f'<div class="pitwall-card" style="border-left:4px solid {mmeta["color"]};"><h3>{mmeta["emoji"]} {my_team}</h3><h2>{int(my_pts)} pts</h2><small>Form bias: {my_form:+.2f} (negative = stronger)</small></div>', unsafe_allow_html=True)
                with rc2:
                    rmeta = team_meta(rival_team)
                    st.markdown(f'<div class="pitwall-card" style="border-left:4px solid {rmeta["color"]};"><h3>{rmeta["emoji"]} {rival_team}</h3><h2>{int(rival_pts)} pts</h2><small>Form bias: {rival_form:+.2f} (negative = stronger)</small></div>', unsafe_allow_html=True)

                if gap > 0:
                    st.success(f"**{my_team}** leads **{rival_team}** by {gap:.0f} points.")
                elif gap < 0:
                    st.warning(f"**{rival_team}** leads **{my_team}** by {abs(gap):.0f} points.")
                else:
                    st.info("Dead even on points right now.")

                if my_form < rival_form:
                    st.info(f"📈 **{my_team}**'s recent form (last 5 races) is trending stronger than {rival_team}'s — the points gap may widen in your favor if this holds.")
                elif my_form > rival_form:
                    st.info(f"📉 **{rival_team}**'s recent form is trending stronger than {my_team}'s right now — worth watching even if the points gap looks safe today.")
            except Exception as e:
                st.error(f"Rival comparison error: {str(e)}")

# ====================== CIRCUIT INTELLIGENCE ======================
with tabs[11]:
    st.subheader("🏟️ Circuit Intelligence")
    st.caption("A data-driven profile for any circuit — safety car tendency, DNF rate, and a 'shake-up index' (how much grid position typically changes by the finish, a free proxy for overtaking difficulty). All computed from real historical results.")

    # Build the circuit name -> circuit ID map fresh (same free Ergast endpoint used in Stats Vault)
    try:
        circuit_resp = requests.get("https://api.jolpi.ca/ergast/f1/circuits.json?limit=200", timeout=8).json()
        circuit_map_ci = {c['circuitName']: c['circuitId'] for c in circuit_resp['MRData']['CircuitTable']['Circuits']}
    except Exception:
        circuit_map_ci = {}

    if not circuit_map_ci:
        st.warning("📡 Could not reach the circuit database right now. Try again shortly.")
    else:
        circuit_names_ci = sorted(circuit_map_ci.keys())
        default_idx_ci = next((i for i, c in enumerate(circuit_names_ci) if next_race["circuit"] in circuit_map_ci.get(c, "")), 0)
        chosen_circuit_ci = st.selectbox("Select Circuit", circuit_names_ci, index=default_idx_ci, key="ci_circuit_select")

        if st.button("🏟️ Analyze Circuit", type="primary", use_container_width=True, key="ci_btn"):
            with st.spinner("Pulling circuit history..."):
                intel = get_circuit_intelligence(circuit_map_ci[chosen_circuit_ci], current_year)
            if intel is None:
                st.info("📻 Not enough historical data found for this circuit.")
            else:
                ic1, ic2, ic3 = st.columns(3)
                with ic1:
                    st.markdown(f'<div class="pitwall-card" style="border-left:4px solid #ef4444;"><h3>💥 DNF Rate</h3><h2>{intel["dnf_rate"]}%</h2><small>across {intel["races_analyzed"]} season(s)</small></div>', unsafe_allow_html=True)
                with ic2:
                    st.markdown(f'<div class="pitwall-card" style="border-left:4px solid #f5d142;"><h3>🔀 Shake-Up Index</h3><h2>{intel["shake_up_index"]}</h2><small>avg |grid-finish| change</small></div>', unsafe_allow_html=True)
                with ic3:
                    pole_txt = f'{intel["pole_to_win_rate"]}%' if intel["pole_to_win_rate"] is not None else "N/A"
                    st.markdown(f'<div class="pitwall-card" style="border-left:4px solid #38bdf8;"><h3>🥇 Pole→Win Rate</h3><h2>{pole_txt}</h2><small>how often pole sitter wins here</small></div>', unsafe_allow_html=True)

                st.markdown("#### 🏆 Most Successful Drivers Here")
                st.dataframe(intel["top_winners"].reset_index().rename(columns={"index": "Driver", "driver": "Wins"}), use_container_width=True, hide_index=True)
                st.markdown("#### 🛠️ Most Successful Constructors Here")
                st.dataframe(intel["top_constructors"].reset_index().rename(columns={"index": "Team", "constructor": "Wins"}), use_container_width=True, hide_index=True)

# ====================== TEAM PERFORMANCE ANALYZER ======================
with tabs[12]:
    st.subheader("🛠️ Team Performance Analyzer")
    st.caption("Cumulative constructor points across the season, race by race — see momentum shifts, not just a static final table.")

    if st.button("🛠️ Load Season Trend", type="primary", use_container_width=True, key="team_analyzer_btn"):
        with st.spinner("Building the season trend..."):
            trend_df = get_constructor_season_trend(current_year)
        if trend_df.empty:
            st.info("No completed races yet this season to chart.")
        else:
            pivot_df = trend_df.pivot(index="Round", columns="Team", values="Cumulative Points").ffill()
            st.line_chart(pivot_df, use_container_width=True)

            st.markdown("#### Compare Two Teams Directly")
            teams_in_trend = sorted(trend_df['Team'].unique())
            tcol1, tcol2 = st.columns(2)
            with tcol1:
                team_a = st.selectbox("Team A", teams_in_trend, index=0, key="ta_select")
            with tcol2:
                team_b = st.selectbox("Team B", teams_in_trend, index=1 if len(teams_in_trend) > 1 else 0, key="tb_select")

            sub_df = pivot_df[[c for c in [team_a, team_b] if c in pivot_df.columns]]
            st.line_chart(sub_df, use_container_width=True)

st.caption("F1 Pit Wall Hub • Completely Free • Powered by Public APIs (Jolpi/Ergast + OpenF1) • No API Keys Required")
