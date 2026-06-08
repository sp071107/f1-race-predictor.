import requests
import pandas as pd
import time
import json
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor

print("Starting Dynamic Future-Proof Data Pipeline...")
all_races_data = []

# Find out what calendar year and race circuit is active right now
today = datetime.utcnow().date()
current_year = today.year  # Dynamically detects if it's 2026, 2027, etc.

# 1. Fetch historical data to train our brain (up to the previous year)
for year in range(2016, current_year):
    url = f"https://api.jolpi.ca/ergast/f1/{year}/results.json?limit=1000"
    response = requests.get(url)
    if response.status_code == 200:
        races = response.json()['MRData']['RaceTable']['Races']
        for race in races:
            circuit_id = race['Circuit']['circuitId']
            round_num = race['round']
            for result in race['Results']:
                finishing_pos = result.get('positionOrder', result.get('position'))
                all_races_data.append({
                    'year': int(year), 'round': int(round_num), 'circuit_id': circuit_id,
                    'driver_id': result['Driver']['driverId'], 'constructor_id': result['Constructor']['constructorId'],
                    'grid_position': int(result['grid']), 'finishing_position': int(finishing_pos)
                })
    time.sleep(0.1)

df = pd.DataFrame(all_races_data)

# 2. Setup Base Label Encoders
base_circuits = list(df['circuit_id'].unique())
base_drivers = list(df['driver_id'].unique())
base_constructors = list(df['constructor_id'].unique())

# Always inject your custom 2026 entities so they are safely registered in the AI's math map
custom_identities_drivers = ['hadjar', 'lindblad', 'antonelli', 'bearman', 'lawson']
custom_identities_teams = ['cadillac', 'audi', 'rb']
for d in custom_identities_drivers:
    if d not in base_drivers: base_drivers.append(d)
for c in custom_identities_teams:
    if c not in base_constructors: base_constructors.append(c)

le_circuit = LabelEncoder().fit(base_circuits)
le_driver = LabelEncoder().fit(base_drivers)
le_constructor = LabelEncoder().fit(base_constructors)

df['circuit_encoded'] = le_circuit.transform(df['circuit_id'])
df['driver_encoded'] = le_driver.transform(df['driver_id'])
df['constructor_encoded'] = le_constructor.transform(df['constructor_id'])

# 3. Train the model
X = df[['year', 'round', 'circuit_encoded', 'driver_encoded', 'constructor_encoded', 'grid_position']]
y = df['finishing_position']
ai_brain = RandomForestRegressor(n_estimators=100, random_state=42)
ai_brain.fit(X, y)
print("AI Brain trained successfully.")

# 4. Target the active round on the current calendar schedule
schedule_url = f"https://api.jolpi.ca/ergast/f1/{current_year}.json"
sched_resp = requests.get(schedule_url)

target_round = 1
target_circuit = "catalunya"

if sched_resp.status_code == 200:
    races_sched = sched_resp.json()['MRData']['RaceTable']['Races']
    for race in races_sched:
        race_date_str = race.get('date')
        if race_date_str:
            race_date = datetime.strptime(race_date_str, "%Y-%m-%d").date()
            if race_date >= today:
                target_round = int(race['round'])
                target_circuit = race['Circuit']['circuitId']
                break

print(f"Targeting Layout: Year {current_year}, Round {target_round} at {target_circuit}")

live_predictions = []
circ_enc = le_circuit.transform([target_circuit])[0] if target_circuit in le_circuit.classes_ else 0

# 5. HYBRID LOGIC ROUTER: Check if we use custom 2026 mode or automatic future mode
if current_year == 2026:
    print("Executing locked custom 2026 grid configuration...")
    roster_2026 = [
        {"driver": "Max Verstappen", "d_id": "max_verstappen", "team": "Red Bull Racing", "c_id": "red_bull"},
        {"driver": "Isack Hadjar", "d_id": "hadjar", "team": "Red Bull Racing", "c_id": "red_bull"},
        {"driver": "Sergio Perez", "d_id": "perez", "team": "Cadillac", "c_id": "cadillac"},
        {"driver": "Valtteri Bottas", "d_id": "bottas", "team": "Cadillac", "c_id": "cadillac"},
        {"driver": "Yuki Tsunoda", "d_id": "tsunoda", "team": "Racing Bulls (RB)", "c_id": "rb"},
        {"driver": "Arvid Lindblad", "d_id": "lindblad", "team": "Racing Bulls (RB)", "c_id": "rb"},
        {"driver": "George Russell", "d_id": "russell", "team": "Mercedes", "c_id": "mercedes"},
        {"driver": "Kimi Antonelli", "d_id": "antonelli", "team": "Mercedes", "c_id": "mercedes"},
        {"driver": "Lewis Hamilton", "d_id": "hamilton", "team": "Ferrari", "c_id": "ferrari"},
        {"driver": "Charles Leclerc", "d_id": "leclerc", "team": "Ferrari", "c_id": "ferrari"},
        {"driver": "Lando Norris", "d_id": "norris", "team": "McLaren", "c_id": "mclaren"},
        {"driver": "Oscar Piastri", "d_id": "piastri", "team": "McLaren", "c_id": "mclaren"},
        {"driver": "Fernando Alonso", "d_id": "alonso", "team": "Aston Martin", "c_id": "aston_martin"},
        {"driver": "Lance Stroll", "d_id": "stroll", "team": "Aston Martin", "c_id": "aston_martin"},
        {"driver": "Pierre Gasly", "d_id": "gasly", "team": "Alpine", "c_id": "alpine"},
        {"driver": "Esteban Ocon", "d_id": "ocon", "team": "Haas", "c_id": "haas"},
        {"driver": "Oliver Bearman", "d_id": "bearman", "team": "Haas", "c_id": "haas"},
        {"driver": "Alex Albon", "d_id": "albon", "team": "Williams", "c_id": "williams"},
        {"driver": "Carlos Sainz", "d_id": "sainz", "team": "Williams", "c_id": "williams"},
        {"driver": "Nico Hulkenberg", "d_id": "hulkenberg", "team": "Audi", "c_id": "audi"}
    ]
    
    for pos, entry in enumerate(roster_2026, 1):
        d_id, c_id = entry["d_id"], entry["c_id"]
        d_enc = le_driver.transform([d_id])[0]
        c_enc = le_constructor.transform([c_id])[0]
        pred = ai_brain.predict([[current_year, target_round, circ_enc, d_enc, c_enc, pos]])
        live_predictions.append({
            "grid": pos, "driver": entry["driver"], "team": entry["team"], "predicted_finish": round(pred[0], 1)
        })

else:
    print(f"Welcome to {current_year}! Activating fully automated live API grid streaming...")
    grid_url = f"https://api.jolpi.ca/ergast/f1/{current_year}/{target_round}/qualifying.json"
    grid_resp = requests.get(grid_url)
    
    # Try to use live qualifying order first, fallback to historical drivers list if mid-week
    real_grid_found = False
    if grid_resp.status_code == 200:
        race_table = grid_resp.json()['MRData']['RaceTable']['Races']
        if race_table and 'QualifyingResults' in race_table[0]:
            real_grid_found = True
            for entry in race_table[0]['QualifyingResults']:
                p_grid = int(entry['position'])
                d_id = entry['Driver']['driverId']
                c_id = entry['Constructor']['constructorId']
                d_name = f"{entry['Driver'].get('givenName', '')} {entry['Driver'].get('familyName', '')}".strip()
                c_name = entry['Constructor'].get('name', '')
                
                # Dynamic safety encoding for future unknown drivers/teams
                if d_id not in le_driver.classes_:
                    le_driver.classes_ = pd.np.append(le_driver.classes_, d_id)
                if c_id not in le_constructor.classes_:
                    le_constructor.classes_ = pd.np.append(le_constructor.classes_, c_id)
                
                d_enc = le_driver.transform([d_id])[0]
                c_enc = le_constructor.transform([c_id])[0]
                pred = ai_brain.predict([[current_year, target_round, circ_enc, d_enc, c_enc, p_grid]])
                live_predictions.append({
                    "grid": p_grid, "driver": d_name, "team": c_name, "predicted_finish": round(pred[0], 1)
                })
                
    if not real_grid_found:
        print("Qualifying not live yet for this future event. Pulling active driver database entries...")
        # Fallback to the official driver standings roster for that active year
        drivers_url = f"https://api.jolpi.ca/ergast/f1/{current_year}/drivers.json"
        dr_resp = requests.get(drivers_url)
        if dr_resp.status_code == 200:
            d_list = dr_resp.json()['MRData']['DriverTable']['Drivers']
            for pos, d in enumerate(d_list[:20], 1):
                d_id = d['driverId']
                d_name = f"{d.get('givenName', '')} {d.get('familyName', '')}".strip()
                
                if d_id not in le_driver.classes_:
                    le_driver.classes_ = pd.np.append(le_driver.classes_, d_id)
                
                d_enc = le_driver.transform([d_id])[0]
                c_enc = 0 # Default safety mapping
                pred = ai_brain.predict([[current_year, target_round, circ_enc, d_enc, c_enc, pos]])
                live_predictions.append({
                    "grid": pos, "driver": d_name, "team": "Dynamic Entry", "predicted_finish": round(pred[0], 1)
                })

# 6. Output calculations cleanly to Streamlit interface
with open("predictions.json", "w") as f:
    json.dump(live_predictions, f, indent=4)

print(f"Data pipeline complete. Smart-router resolved for {current_year} context.")
