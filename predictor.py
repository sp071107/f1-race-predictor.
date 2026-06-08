import requests
import pandas as pd
import time
import json
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor

print("Starting 2026 FIXED Data Pipeline...")
all_races_data = []

# 1. Fetch historical data (2016-2025) to train our brain
for year in range(2016, 2026):
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

# 2. Build the exact encoders we need for conversion
le_circuit, le_driver, le_constructor = LabelEncoder(), LabelEncoder(), LabelEncoder()
df['circuit_encoded'] = le_circuit.fit_transform(df['circuit_id'])
df['driver_encoded'] = le_driver.fit_transform(df['driver_id'])
df['constructor_encoded'] = le_constructor.fit_transform(df['constructor_id'])

# 3. Train the machine learning model
X = df[['year', 'round', 'circuit_encoded', 'driver_encoded', 'constructor_encoded', 'grid_position']]
y = df['finishing_position']
ai_brain = RandomForestRegressor(n_estimators=100, random_state=42)
ai_brain.fit(X, y)
print("AI Brain trained successfully.")

# 4. Target the 2026 active schedule
current_year = 2026
schedule_url = f"https://api.jolpi.ca/ergast/f1/{current_year}.json"
sched_resp = requests.get(schedule_url)

target_round = 1
target_circuit = "catalunya" # Default fallback to next up if API is transitioning

if sched_resp.status_code == 200:
    races_sched = sched_resp.json()['MRData']['RaceTable']['Races']
    today = datetime.utcnow().date()
    for race in races_sched:
        race_date_str = race.get('date')
        if race_date_str:
            race_date = datetime.strptime(race_date_str, "%Y-%m-%d").date()
            if race_date >= today:
                target_round = int(race['round'])
                target_circuit = race['Circuit']['circuitId']
                break 

print(f"Targeting active event: Year {current_year}, Round {target_round}, Circuit: {target_circuit}")

# 5. Fetch live qualifying data if available
grid_url = f"https://api.jolpi.ca/ergast/f1/{current_year}/{target_round}/qualifying.json"
grid_resp = requests.get(grid_url)
real_grid_found = False
live_predictions = []

if grid_resp.status_code == 200:
    race_table = grid_resp.json()['MRData']['RaceTable']['Races']
    if race_table and 'QualifyingResults' in race_table[0]:
        qualifying_results = race_table[0]['QualifyingResults']
        real_grid_found = True
        print(f"Live qualifying results found for Round {target_round}!")
        
        for entry in qualifying_results:
            p_grid = int(entry['position'])
            d_id = entry['Driver']['driverId']
            c_id = entry['Constructor']['constructorId']
            d_name = f"{entry['Driver'].get('givenName', '')} {entry['Driver'].get('familyName', '')}".strip()
            c_name = entry['Constructor'].get('name', '')
            
            d_enc = le_driver.transform([d_id])[0] if d_id in le_driver.classes_ else 0
            c_enc = le_constructor.transform([c_id])[0] if c_id in le_constructor.classes_ else 0
            circ_enc = le_circuit.transform([target_circuit])[0] if target_circuit in le_circuit.classes_ else 0
            
            pred = ai_brain.predict([[current_year, target_round, circ_enc, d_enc, c_enc, p_grid]])
            live_predictions.append({
                "grid": p_grid, "driver": d_name, "team": c_name, "predicted_finish": round(pred[0], 1)
            })

# 6. TRUE 2026 MID-WEEK ROSTER FALLBACK
if not real_grid_found:
    print("Mid-week gap. Simulating baseline track matrix with true 2026 driver pairings...")
    
    # 2026 explicit driver alignments 
    roster_2026 = [
        {"driver": "George Russell", "d_id": "russell", "team": "Mercedes", "c_id": "mercedes"},
        {"driver": "Kimi Antonelli", "d_id": "antonelli", "team": "Mercedes", "c_id": "mercedes"},
        {"driver": "Lewis Hamilton", "d_id": "hamilton", "team": "Ferrari", "c_id": "ferrari"},
        {"driver": "Charles Leclerc", "d_id": "leclerc", "team": "Ferrari", "c_id": "ferrari"},
        {"driver": "Max Verstappen", "d_id": "max_verstappen", "team": "Red Bull Racing", "c_id": "red_bull"},
        {"driver": "Sergio Perez", "d_id": "perez", "team": "Red Bull Racing", "c_id": "red_bull"},
        {"driver": "Lando Norris", "d_id": "norris", "team": "McLaren", "c_id": "mclaren"},
        {"driver": "Oscar Piastri", "d_id": "piastri", "team": "McLaren", "c_id": "mclaren"},
        {"driver": "Fernando Alonso", "d_id": "alonso", "team": "Aston Martin", "c_id": "aston_martin"},
        {"driver": "Lance Stroll", "d_id": "stroll", "team": "Aston Martin", "c_id": "aston_martin"},
        {"driver": "Pierre Gasly", "d_id": "gasly", "team": "Alpine", "c_id": "alpine"},
        {"driver": "Esteban Ocon", "d_id": "ocon", "team": "Haas", "c_id": "haas"},
        {"driver": "Oliver Bearman", "d_id": "bearman", "team": "Haas", "c_id": "haas"},
        {"driver": "Alex Albon", "d_id": "albon", "team": "Williams", "c_id": "williams"},
        {"driver": "Carlos Sainz", "d_id": "sainz", "team": "Williams", "c_id": "williams"},
        {"driver": "Nico Hulkenberg", "d_id": "hulkenberg", "team": "Audi", "c_id": "audi"},
        {"driver": "Yuki Tsunoda", "d_id": "tsunoda", "team": "RB", "c_id": "rb"},
        {"driver": "Liam Lawson", "d_id": "lawson", "team": "RB", "c_id": "rb"},
        {"driver": "Valtteri Bottas", "d_id": "bottas", "team": "Sauber", "c_id": "sauber"},
        {"driver": "Zhou Guanyu", "d_id": "zhou", "team": "Sauber", "c_id": "sauber"}
    ]
    
    circ_enc = le_circuit.transform([target_circuit])[0] if target_circuit in le_circuit.classes_ else 0
    
    for pos, entry in enumerate(roster_2026, 1):
        d_id, c_id = entry["d_id"], entry["c_id"]
        
        d_enc = le_driver.transform([d_id])[0] if d_id in le_driver.classes_ else 0
        c_enc = le_constructor.transform([c_id])[0] if c_id in le_constructor.classes_ else 0
        
        pred = ai_brain.predict([[current_year, target_round, circ_enc, d_enc, c_enc, pos]])
        
        live_predictions.append({
            "grid": pos,
            "driver": entry["driver"],
            "team": entry["team"],
            "predicted_finish": round(pred[0], 1)
        })

# Save clean calculations
with open("predictions.json", "w") as f:
    json.dump(live_predictions, f, indent=4)

print("Pipeline update complete. Mid-week 2026 data arrays mapped successfully.")
