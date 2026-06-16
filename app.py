import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

st.set_page_config(page_title="F1 Pit-Wall Hub", page_icon="🏎️", layout="wide")

# ──────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

/* Base */
.stApp { background-color: #080a0f; color: #e2e8f0; font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.5rem !important; max-width: 1400px; }
header[data-testid="stHeader"] { background: #080a0f; border-bottom: 1px solid #1a1f2e; }

/* Top accent bar */
.stApp::before {
    content: "";
    display: block;
    height: 3px;
    background: linear-gradient(90deg, #FF1801 0%, #ff6b35 50%, #FF1801 100%);
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
}

/* Tabs */
div[data-baseweb="tab-list"] { gap: 4px; background: #0d1017; border-bottom: 1px solid #1a1f2e; padding: 0 4px; }
div[data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    color: #64748b !important;
    border-radius: 0 !important;
    padding: 14px 20px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    transition: all 0.15s;
}
div[data-baseweb="tab"]:hover { color: #94a3b8 !important; }
div[data-baseweb="tab"][aria-selected="true"] {
    color: #ffffff !important;
    border-bottom: 3px solid #FF1801 !important;
}

/* Cards */
.card {
    background: #0d1017;
    border: 1px solid #1a1f2e;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
}
.card:hover { border-color: #2a3144; }
.card-label { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #475569; margin-bottom: 6px; }
.card-headline { font-size: 1.55rem; font-weight: 800; color: #f1f5f9; line-height: 1.15; }
.card-sub { font-size: 0.82rem; color: #64748b; margin-top: 5px; font-family: 'JetBrains Mono', monospace; }

/* Section header */
.section-header {
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #475569;
    border-bottom: 1px solid #1a1f2e;
    padding-bottom: 10px; margin: 28px 0 16px 0;
    display: flex; align-items: center; gap: 8px;
}

/* Hero banner */
.hero-banner {
    background: linear-gradient(135deg, #0d1017 0%, #111827 100%);
    border: 1px solid #1a1f2e;
    border-left: 4px solid #FF1801;
    border-radius: 10px;
    padding: 24px 28px;
    margin-bottom: 24px;
}

/* Standings table wrapper */
.standings-wrap { border-radius: 10px; overflow: hidden; border: 1px solid #1a1f2e; }

/* Chat */
.chat-bubble-user {
    background: #1e2433;
    border: 1px solid #2a3144;
    border-radius: 12px 12px 4px 12px;
    padding: 12px 16px;
    margin: 8px 0 8px 60px;
    color: #e2e8f0;
    font-size: 0.9rem;
    line-height: 1.5;
}
.chat-bubble-ai {
    background: linear-gradient(135deg, #0f1520 0%, #131b28 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px 12px 12px 4px;
    padding: 14px 18px;
    margin: 8px 60px 8px 0;
    color: #cbd5e1;
    font-size: 0.9rem;
    line-height: 1.6;
}
.chat-bubble-ai strong { color: #FF1801; }
.chat-avatar { font-size: 1.4rem; margin-bottom: 4px; }
.chat-container { max-height: 480px; overflow-y: auto; padding: 4px 0; }

/* Sliders and selects */
div[data-baseweb="slider"] > div { background-color: #FF1801 !important; }
.stSelectbox > div > div { background-color: #0d1017 !important; border-color: #1a1f2e !important; }

/* Expander */
details { background: #0d1017 !important; border: 1px solid #1a1f2e !important; border-radius: 8px !important; }
summary { color: #94a3b8 !important; font-size: 0.85rem !important; font-weight: 600 !important; }

/* Team color dot */
.team-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }

/* Data frames */
[data-testid="stDataFrame"] { border: 1px solid #1a1f2e !important; border-radius: 8px; overflow: hidden; }

/* Metric */
[data-testid="stMetric"] { background: #0d1017; border: 1px solid #1a1f2e; border-radius: 8px; padding: 14px; }
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stMetricValue"] { color: #f1f5f9 !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────
TEAM_META = {
    "Mercedes":        {"color": "#00D2BE", "base_pace_rank": 1.1},
    "Ferrari":         {"color": "#E8002D", "base_pace_rank": 1.4},
    "McLaren":         {"color": "#FF8000", "base_pace_rank": 1.5},
    "Red Bull Racing": {"color": "#3671C6", "base_pace_rank": 2.2},
    "Alpine":          {"color": "#0093CC", "base_pace_rank": 3.4},
    "Racing Bulls":    {"color": "#6692FF", "base_pace_rank": 3.8},
    "Haas F1 Team":    {"color": "#B6BABD", "base_pace_rank": 4.1},
    "Haas":            {"color": "#B6BABD", "base_pace_rank": 4.1},
    "Williams":        {"color": "#37BEDD", "base_pace_rank": 4.5},
    "Audi":            {"color": "#F50A23", "base_pace_rank": 5.2},
    "Aston Martin":    {"color": "#229971", "base_pace_rank": 5.5},
    "Cadillac":        {"color": "#C8A45A", "base_pace_rank": 5.8},
}

# Fallback standings (updated to latest known 2026 data)
FALLBACK_DRIVERS = [
    {"Pos": 1,  "Driver": "K. ANTONELLI",  "Team": "Mercedes",        "Points": 156},
    {"Pos": 2,  "Driver": "L. HAMILTON",   "Team": "Ferrari",         "Points": 90},
    {"Pos": 3,  "Driver": "G. RUSSELL",    "Team": "Mercedes",        "Points": 88},
    {"Pos": 4,  "Driver": "C. LECLERC",    "Team": "Ferrari",         "Points": 75},
    {"Pos": 5,  "Driver": "O. PIASTRI",    "Team": "McLaren",         "Points": 58},
    {"Pos": 6,  "Driver": "L. NORRIS",     "Team": "McLaren",         "Points": 58},
    {"Pos": 7,  "Driver": "M. VERSTAPPEN", "Team": "Red Bull Racing", "Points": 43},
    {"Pos": 8,  "Driver": "P. GASLY",      "Team": "Alpine",          "Points": 35},
    {"Pos": 9,  "Driver": "I. HADJAR",     "Team": "Red Bull Racing", "Points": 26},
    {"Pos": 10, "Driver": "L. LAWSON",     "Team": "Racing Bulls",    "Points": 24},
    {"Pos": 11, "Driver": "O. BEARMAN",    "Team": "Haas F1 Team",    "Points": 18},
    {"Pos": 12, "Driver": "F. COLAPINTO",  "Team": "Alpine",          "Points": 15},
    {"Pos": 13, "Driver": "A. LINDBLAD",   "Team": "Racing Bulls",    "Points": 11},
    {"Pos": 14, "Driver": "C. SAINZ",      "Team": "Williams",        "Points": 6},
    {"Pos": 15, "Driver": "A. ALBON",      "Team": "Williams",        "Points": 5},
    {"Pos": 16, "Driver": "E. OCON",       "Team": "Haas F1 Team",    "Points": 3},
    {"Pos": 17, "Driver": "G. BORTOLETO",  "Team": "Audi",            "Points": 2},
    {"Pos": 18, "Driver": "F. ALONSO",     "Team": "Aston Martin",    "Points": 1},
    {"Pos": 19, "Driver": "S. PEREZ",      "Team": "Cadillac",        "Points": 0},
    {"Pos": 20, "Driver": "N. HULKENBERG", "Team": "Audi",            "Points": 0},
    {"Pos": 21, "Driver": "V. BOTTAS",     "Team": "Cadillac",        "Points": 0},
    {"Pos": 22, "Driver": "L. STROLL",     "Team": "Aston Martin",    "Points": 0},
]

FALLBACK_CONSTRUCTORS = [
    {"Pos": 1,  "Team": "Mercedes",        "Points": 244},
    {"Pos": 2,  "Team": "Ferrari",         "Points": 165},
    {"Pos": 3,  "Team": "McLaren",         "Points": 116},
    {"Pos": 4,  "Team": "Red Bull Racing", "Points": 69},
    {"Pos": 5,  "Team": "Alpine",          "Points": 50},
    {"Pos": 6,  "Team": "Racing Bulls",    "Points": 35},
    {"Pos": 7,  "Team": "Haas F1 Team",    "Points": 21},
    {"Pos": 8,  "Team": "Williams",        "Points": 11},
    {"Pos": 9,  "Team": "Audi",            "Points": 2},
    {"Pos": 10, "Team": "Aston Martin",    "Points": 1},
    {"Pos": 11, "Team": "Cadillac",        "Points": 0},
]

# ──────────────────────────────────────────────
# DATA FETCHERS — all free, no API keys needed
# ──────────────────────────────────────────────

@st.cache_data(ttl=300)  # refresh every 5 min — picks up new race results quickly
def fetch_live_standings():
    """Fetch live 2026 standings from Ergast/Jolpi (free, no key)."""
    year = datetime.utcnow().year
    base = "https://api.jolpi.ca/ergast/f1"
    drivers, constructors = [], []
    source = "live"
    try:
        dr = requests.get(f"{base}/{year}/driverStandings.json?limit=30", timeout=6)
        cr = requests.get(f"{base}/{year}/constructorStandings.json?limit=15", timeout=6)
        if dr.status_code == 200 and cr.status_code == 200:
            d_list = dr.json()["MRData"]["StandingsTable"]["StandingsLists"]
            c_list = cr.json()["MRData"]["StandingsTable"]["StandingsLists"]
            if d_list and c_list:
                for s in d_list[0]["DriverStandings"]:
                    name = f"{s['Driver']['givenName'][0]}. {s['Driver']['familyName']}".upper()
                    team = s["Constructors"][0]["name"] if s["Constructors"] else "—"
                    drivers.append({"Pos": int(s["position"]), "Driver": name, "Team": team, "Points": int(float(s["points"]))})
                for s in c_list[0]["ConstructorStandings"]:
                    constructors.append({"Pos": int(s["position"]), "Team": s["Constructor"]["name"], "Points": int(float(s["points"]))})
                return drivers, constructors, "live"
    except Exception:
        pass
    return FALLBACK_DRIVERS, FALLBACK_CONSTRUCTORS, "cached"


@st.cache_data(ttl=1800)
def fetch_race_weekend():
    """Fetch current race weekend info from OpenF1."""
    try:
        r = requests.get("https://api.openf1.org/v1/meetings?meeting_key=latest", timeout=5)
        if r.status_code == 200 and r.json():
            m = r.json()[0]
            name = m.get("meeting_official_name") or m.get("meeting_name", "F1 Grand Prix")
            location = f"{m.get('location', '')}, {m.get('country_name', '')}"
            circuit = m.get("circuit_short_name", "Circuit")
            m_key = m["meeting_key"]

            sessions = requests.get(f"https://api.openf1.org/v1/sessions?meeting_key={m_key}", timeout=5).json()
            q_key = next((s["session_key"] for s in sessions if "Qualifying" in s.get("session_name", "")), None)

            drivers = []
            if q_key:
                results = requests.get(f"https://api.openf1.org/v1/session_result?session_key={q_key}", timeout=5).json()
                driver_map = {
                    str(d["driver_number"]): {"name": d.get("broadcast_name", ""), "team": d.get("team_name", "")}
                    for d in requests.get(f"https://api.openf1.org/v1/drivers?session_key={q_key}", timeout=5).json()
                }
                for res in results:
                    pos = res.get("position")
                    dnum = str(res.get("driver_number"))
                    if pos and dnum in driver_map:
                        meta = driver_map[dnum]
                        drivers.append({"driver_num": dnum, "driver": meta["name"], "team": meta["team"], "grid_start": int(pos)})
            return {"race_name": name, "location": location, "circuit_short": circuit, "drivers": drivers}
    except Exception:
        pass
    return {
        "race_name": "Circuit de Barcelona-Catalunya Grand Prix",
        "location": "Montmeló, Spain",
        "circuit_short": "Catalunya",
        "drivers": [
            {"driver_num": "12", "driver": "K. ANTONELLI",  "team": "Mercedes",        "grid_start": 1},
            {"driver_num": "44", "driver": "L. HAMILTON",   "team": "Ferrari",         "grid_start": 2},
            {"driver_num": "63", "driver": "G. RUSSELL",    "team": "Mercedes",        "grid_start": 3},
            {"driver_num": "16", "driver": "C. LECLERC",    "team": "Ferrari",         "grid_start": 4},
            {"driver_num": "1",  "driver": "L. NORRIS",     "team": "McLaren",         "grid_start": 5},
            {"driver_num": "81", "driver": "O. PIASTRI",    "team": "McLaren",         "grid_start": 6},
            {"driver_num": "3",  "driver": "M. VERSTAPPEN", "team": "Red Bull Racing", "grid_start": 7},
            {"driver_num": "10", "driver": "P. GASLY",      "team": "Alpine",          "grid_start": 8},
        ]
    }


# ──────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────
drivers_standings, constructors_standings, standings_source = fetch_live_standings()
weekend = fetch_race_weekend()
df_field = pd.DataFrame(weekend["drivers"])

# ──────────────────────────────────────────────
# HERO BANNER
# ──────────────────────────────────────────────
live_badge = "🟢 LIVE DATA" if standings_source == "live" else "🟡 CACHED DATA"
st.markdown(f"""
<div class="hero-banner">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
        <div>
            <div style="font-size:0.72rem; font-weight:700; letter-spacing:0.12em; color:#FF1801; text-transform:uppercase; margin-bottom:6px;">
                🏎️ F1 PIT-WALL HUB &nbsp;·&nbsp; 2026 SEASON
            </div>
            <div style="font-size:1.9rem; font-weight:900; color:#f1f5f9; letter-spacing:-0.02em; line-height:1.1;">
                {weekend['race_name'].upper()}
            </div>
            <div style="font-size:0.88rem; color:#64748b; margin-top:6px;">
                📍 {weekend['location']} &nbsp;·&nbsp; {weekend['circuit_short']}
            </div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:0.7rem; color:#64748b; font-weight:600; letter-spacing:0.08em; margin-bottom:4px;">STANDINGS</div>
            <div style="font-size:0.85rem; font-weight:700; color:#94a3b8;">{live_badge}</div>
            <div style="font-size:0.7rem; color:#334155; margin-top:4px;">Auto-refreshes every 5 min</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────
tab_home, tab_predictor, tab_chatbot = st.tabs(["🏠  HOME", "📊  STRATEGY ENGINE", "🎙️  AI RACE ENGINEER"])

# ══════════════════════════════════════════════
# TAB 1 — HOME
# ══════════════════════════════════════════════
with tab_home:
    # Summary metrics
    leader = drivers_standings[0]
    constructor_leader = constructors_standings[0]
    gap = drivers_standings[0]["Points"] - drivers_standings[1]["Points"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        lc = TEAM_META.get(leader["Team"], {"color": "#FF1801"})["color"]
        st.markdown(f"""
        <div class="card" style="border-left:3px solid {lc};">
            <div class="card-label">🏆 Championship Leader</div>
            <div class="card-headline">{leader['Driver']}</div>
            <div class="card-sub">{leader['Team']} · {leader['Points']} pts</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        cc = TEAM_META.get(constructor_leader["Team"], {"color": "#FF1801"})["color"]
        st.markdown(f"""
        <div class="card" style="border-left:3px solid {cc};">
            <div class="card-label">🛠️ Constructors Leader</div>
            <div class="card-headline">{constructor_leader['Team']}</div>
            <div class="card-sub">{constructor_leader['Points']} pts · {len(constructors_standings)} teams</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="card" style="border-left:3px solid #a855f7;">
            <div class="card-label">📍 Current Venue</div>
            <div class="card-headline" style="font-size:1.2rem;">{weekend['circuit_short']}</div>
            <div class="card-sub">{weekend['location']}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="card" style="border-left:3px solid #22c55e;">
            <div class="card-label">🔺 Points Gap (P1→P2)</div>
            <div class="card-headline">+{gap} pts</div>
            <div class="card-sub">{drivers_standings[0]['Driver']} leads {drivers_standings[1]['Driver']}</div>
        </div>""", unsafe_allow_html=True)

    # Standings tables
    st.markdown('<div class="section-header">🏆 CHAMPIONSHIP STANDINGS</div>', unsafe_allow_html=True)
    col_d, col_c = st.columns(2)

    def render_standings_df(data, team_col):
        df = pd.DataFrame(data)
        def style_rows(row):
            color = TEAM_META.get(row[team_col], {"color": "#1e293b"})["color"]
            return [f"border-left:4px solid {color}; background:#0d1017; font-family:'JetBrains Mono',monospace;"] * len(row)
        return df.style.apply(style_rows, axis=1).set_properties(**{"text-align": "center"})

    with col_d:
        st.markdown("**🏁 Driver Standings**")
        st.dataframe(
            render_standings_df(drivers_standings, "Team"),
            hide_index=True, use_container_width=True, height=520,
        )
    with col_c:
        st.markdown("**🛠️ Constructor Standings**")
        st.dataframe(
            render_standings_df(constructors_standings, "Team"),
            hide_index=True, use_container_width=True, height=400,
        )

    # Beginner guide
    st.markdown('<div class="section-header">💡 F1 BASICS — WHAT TO KNOW THIS WEEKEND</div>', unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    guides = [
        ("🏎️ Track Position", "Starting at the front is gold. Clean air = less drag = faster lap times. Every car behind battles dirty turbulent air, wearing tyres faster."),
        ("⚡ ERS — The Boost Button", "Energy Recovery Systems harvest kinetic energy under braking and release it as electric power on straights — think of it as a 160hp speed boost the driver can deploy tactically."),
        ("🌡️ Tyre Degradation", "High track temps soften rubber compounds. Push too hard and you hit the 'cliff' — a sudden, dramatic loss of grip. Tyre management is often the difference between winning and finishing fifth."),
    ]
    for col, (title, text) in zip([g1, g2, g3], guides):
        with col:
            st.markdown(f"""
            <div class="card">
                <div class="card-label">{title}</div>
                <div style="color:#94a3b8; font-size:0.88rem; line-height:1.6; margin-top:6px;">{text}</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 2 — STRATEGY PREDICTOR
# ══════════════════════════════════════════════
with tab_predictor:
    if df_field.empty:
        st.warning("No qualifying data loaded. Check the API feed or use the fallback grid.")
        st.stop()

    st.markdown('<div class="section-header">🕹️ RACE CONDITION PARAMETERS</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: weather_state = st.selectbox("Track Conditions", ["Dry", "Damp / Greasy", "Heavy Rain"])
    with c2: track_temp = st.slider("Track Temp (°C)", 15, 65, 35)
    with c3: fuel_load = st.slider("Starting Fuel (kg)", 95, 110, 100)
    with c4: ers_mode = st.selectbox("ERS Mode", ["Balanced", "Attack (Overtake)", "Conservation"])

    team_modifiers = {}
    with st.expander("⚙️ Advanced: Team Performance Offsets"):
        tc = st.columns(3)
        for idx, team in enumerate(sorted(df_field["team"].unique())):
            with tc[idx % 3]:
                team_modifiers[team] = st.slider(f"{team}", -0.8, 0.8, 0.0, step=0.05, key=f"tm_{team}")

    # Pace model
    def compute_pace(row):
        team = row["team"]
        grid = int(row["grid_start"])
        meta = TEAM_META.get(team, {"base_pace_rank": 4.0})
        score = np.log1p(meta["base_pace_rank"]) * 0.65 + team_modifiers.get(team, 0.0)
        score += (track_temp - 35) * 0.012 + (fuel_load - 100) * 0.025
        if grid > 1: score += np.power(grid - 1, 1.15) * 0.045
        if ers_mode == "Attack (Overtake)": score -= 0.08
        if "Rain" in weather_state: score += grid * 0.12
        return score

    def get_strategy(grid_pos):
        if grid_pos <= 4:
            return "Medium → Hard", "Laps 19–25", "Track Position Hold"
        elif grid_pos <= 10:
            return "Soft → Medium → Hard", "Laps 12 & 38", "Undercut Attack"
        else:
            return "Hard → Medium", "Laps 36–44", "Safety Car Gamble"

    df = df_field.copy()
    df["pace_score"] = df.apply(compute_pace, axis=1)
    df = df.sort_values("pace_score").reset_index(drop=True)
    df["Pred_Pos"] = df.index + 1
    df["Pos_Delta"] = df["grid_start"] - df["Pred_Pos"]
    strats = [get_strategy(p) for p in df["grid_start"]]
    df["Strategy"], df["Pit_Window"], df["Intent"] = zip(*strats)

    winner = df.iloc[0]
    podium = df.iloc[1:3]
    charger = df.sort_values("Pos_Delta", ascending=False).iloc[0]

    # Prediction headline cards
    st.markdown('<div class="section-header">📊 AI RACE PREDICTIONS</div>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1:
        wc = TEAM_META.get(winner["team"], {"color": "#FF1801"})["color"]
        st.markdown(f"""
        <div class="card" style="border-left:4px solid {wc}; border-top: 1px solid {wc}33;">
            <div class="card-label">🏆 Predicted Winner</div>
            <div class="card-headline">{winner['driver']}</div>
            <div class="card-sub">{winner['team']} · {winner['Strategy']}</div>
        </div>""", unsafe_allow_html=True)
    with p2:
        pod_text = " · ".join([f"P{int(r.Pred_Pos)}: {r.driver}" for _, r in podium.iterrows()])
        st.markdown(f"""
        <div class="card" style="border-left:4px solid #FF8000;">
            <div class="card-label">🥈🥉 Podium Contenders</div>
            <div class="card-headline" style="font-size:1.1rem;">{pod_text}</div>
            <div class="card-sub">Optimal strategy finish group</div>
        </div>""", unsafe_allow_html=True)
    with p3:
        delta = int(charger["Pos_Delta"])
        c_text = f"{charger['driver']} +{delta} places" if delta > 0 else "Grid order holds"
        st.markdown(f"""
        <div class="card" style="border-left:4px solid #37BEDD;">
            <div class="card-label">🚀 Biggest Mover</div>
            <div class="card-headline" style="font-size:1.2rem;">{c_text}</div>
            <div class="card-sub">P{int(charger['grid_start'])} → P{int(charger['Pred_Pos'])} projected</div>
        </div>""", unsafe_allow_html=True)

    # Results table
    sub1, sub2 = st.tabs(["🏁 Full Grid Predictions", "⏱️ Time Gap to Leader"])
    with sub1:
        render_df = df[["Pred_Pos", "grid_start", "driver", "team", "Strategy", "Pit_Window", "Intent"]].copy()
        render_df.columns = ["Pred. Finish", "Grid", "Driver", "Constructor", "Strategy", "Pit Window", "Intent"]

        def style_grid(row):
            color = TEAM_META.get(row["Constructor"], {"color": "#1e293b"})["color"]
            return [f"border-left:4px solid {color}; background:#0d1017; font-family:'JetBrains Mono',monospace;"] * len(row)

        st.dataframe(
            render_df.style.apply(style_grid, axis=1),
            hide_index=True, use_container_width=True,
        )
    with sub2:
        base_time = (80.0 + df.iloc[0]["pace_score"]) * 55
        chart_data = pd.DataFrame([{
            "Driver": r["driver"],
            "Gap to Leader (s)": round(((80.0 + r["pace_score"]) * 55) - base_time, 1),
        } for _, r in df.iterrows()])
        st.bar_chart(chart_data, x="Driver", y="Gap to Leader (s)", use_container_width=True)


