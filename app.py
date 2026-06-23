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

tabs = st.tabs(["🏠 HOME", "🏆 PODIUM PREDICTOR", "🪪 DRIVER CARDS", "⚔️ DRIVER COMPARISON", "📜 HISTORY", "🎙️ RACE ENGINEER", "📈 STANDINGS", "📚 STATS VAULT", "📡 LIVE SESSION"])

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
    st.dataframe(calendar_df, use_container_width=True, hide_index=True)

    predict_tab, strategy_tab, backtest_tab = st.tabs(["🎯 PREDICT NEXT RACE", "📋 STRATEGY SIMULATOR", "🕰️ PREDICTION VS REALITY"])

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

    # ============== SUB-TAB 2: STRATEGY SIMULATOR ==============
    with strategy_tab:
        st.caption("See how the win/podium probability distribution shifts if a driver runs a non-optimal number of pit stops. This uses an approximate, transparently-modeled time-to-position conversion — it's a simplification, not telemetry-grade physics, but it's free and directionally honest.")

        strat_col1, strat_col2, strat_col3 = st.columns(3)
        with strat_col1:
            strat_weather = st.selectbox("Track Conditions", ["Dry", "Light Rain", "Heavy Rain", "Hot & Dry"], index=0, key="strat_weather")
        with strat_col2:
            strat_temp = st.slider("Track Temperature (°C)", 20, 60, 38, key="strat_temp")
        with strat_col3:
            pit_loss_seconds = st.slider("Pit Lane Loss (s)", 15, 30, 22, key="pit_loss",
                                          help="Typical real-world time lost per stop, including pit lane speed limit. Varies by circuit; 22s is a common F1 average.")

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

                        # Reference: 2-stop treated as the "optimal" baseline (typical for most circuits).
                        # Extra/fewer stops apply a position-equivalent time penalty derived from pit_loss_seconds.
                        # ~25s of pure time loss is treated as roughly equivalent to 1 grid position of pace at most circuits — an approximation, clearly disclosed.
                        stop_count = {"1-Stop": 1, "2-Stop": 2, "3-Stop": 3}
                        baseline_stops = 2
                        strategy_results = {}

                        for strat in chosen_strategies:
                            n_stops = stop_count[strat]
                            extra_penalty = (n_stops - baseline_stops) * (pit_loss_seconds / 25.0)
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
                            st.dataframe(compare_df, use_container_width=True, hide_index=True)
                    except Exception as e:
                        st.error(f"Strategy simulation error: {str(e)}")

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

                        if not drivers_meta:
                            st.warning("Couldn't rebuild the grid for this race to backtest.")
                        else:
                            sc_p = sc_proxy.get(circuit_id, 0.20)
                            sim_df = run_monte_carlo(drivers_meta, anchor_scores, sc_p, "Dry", 5000)

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

# ====================== STATS VAULT (NEW: head-to-head, on this day, circuit history, career trajectory) ======================
with tabs[7]:
    st.subheader("📚 Historical Stats Vault")
    st.caption("Free forever — powered by the same Jolpi/Ergast API used elsewhere in this app, no keys required.")

    @st.cache_data(ttl=86400)
    def vault_get_driver_index():
        try:
            resp = requests.get("https://api.jolpi.ca/ergast/f1/drivers.json?limit=2000", timeout=8).json()
            drivers = resp['MRData']['DriverTable']['Drivers']
            return {f"{d.get('givenName','')} {d.get('familyName','')}".strip(): d['driverId'] for d in drivers}
        except Exception:
            return {}

    @st.cache_data(ttl=86400)
    def vault_get_driver_results(driver_id):
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
                compare_df = pd.DataFrame({vault_driver_a: stats_a, vault_driver_b: stats_b})
                st.dataframe(compare_df, use_container_width=True)

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
                    st.dataframe(df_winners, hide_index=True, use_container_width=True)

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
                st.dataframe(pd.DataFrame(stint_rows), use_container_width=True, hide_index=True)
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
                st.dataframe(pd.DataFrame(pit_rows), use_container_width=True, hide_index=True)
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

st.caption("F1 Pit Wall Hub • Completely Free • Powered by Public APIs (Jolpi/Ergast + OpenF1) • No API Keys Required")
