import requests
import pandas as pd
import time
import json
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor

print("Starting UPGRADED F1 Data Pipeline...")
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
print("AI Brain trained successfully on historical datasets.")

# 4. Fetch the CURRENT Grand Prix to find the active weekend round
current_year = 2026
schedule_url = f"https://api.jolpi.ca/ergast/f1/{current_year}.json"
sched_resp = requests.get(schedule_url)

target_round = 1
target_circuit = df['circuit_id'].iloc[-1] 

if sched_resp.status_code == 200:
    races_sched = sched_resp.json()['MRData']['RaceTable']['Races']
    today = datetime.utcnow().date()
    
    for race in races_sched:
        race_date_str = race.get('date')
        if race_date_str:
            race_date = datetime.strptime(race_date_str, "%Y-%m-%d").date()
            target_round = int(race['round'])
            target_circuit = race['Circuit']['circuitId']
            if race_date >= today:
                break 

print(f"Targeting active event: Year {current_year}, Round {target_round}, Circuit: {target_circuit}")

# 5. Fetch the REAL qualifying/grid entries for this weekend
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
            
            # Handle rookies/unknown values safely
            d_enc = le_driver.transform([d_id])[0] if d_id in le_driver.classes_ else 0
            c_enc = le_constructor.transform([c_id])[0] if c_id in le_constructor.classes_ else 0
            circ_enc = le_circuit.transform([target_circuit])[0] if target_circuit in le_circuit.classes_ else 0
            
            pred = ai_brain.predict([[current_year, target_round, circ_enc, d_enc, c_enc, p_grid]])
            
            live_predictions.append({
                "grid": p_grid,
                "driver": d_name,
                "team": c_name,
                "predicted_finish": round(pred[0], 1)
            })

# Fallback block: If qualifying isn't live, simulate the grid using the correct active rosters
if not real_grid_found:
    print("Qualifying session data isn't live yet on the API. Simulating baseline track matrix...")
    
    # --- UPDATED GRID ROSTER MATRIX ---
    drivers_list = [
        'max_verstappen', 'perez', 'hamilton', 'leclerc', 'norris', 
        'piastri', 'russell', 'antonelli', 'alonso', 'stroll', 
        'gasly', 'ocon', 'albon', 'sainz', 'hulkenberg', 
        'bearman', 'tsunoda', 'lawson', 'bottas', 'zhou'
    ]
    constructors_list = [
        'red_bull', 'red_bull', 'ferrari', 'ferrari', 'mclaren', 
        'mclaren', 'mercedes', 'mercedes', 'aston_martin', 'aston_martin', 
        'alpine', 'haas', 'williams', 'williams', 'audi', 
        'haas', 'rb', 'rb', 'sauber', 'sauber'
    ]
    
    circ_enc = le_circuit.transform([target_circuit])[0] if target_circuit in le_circuit.classes_ else 0
    
    for pos in range(1, 21):
        d_id = drivers_list[pos-1] if pos-1 < len(drivers_list) else 'max_verstappen'
        c_id = constructors_list[pos-1] if pos-1 < len(constructors_list) else 'red_bull'
        
        d_enc = le_driver.transform([d_id])[0] if d_id in le_driver.classes_ else 0
        c_enc = le_constructor.transform([c_id])[0] if c_id in le_constructor.classes_ else 0
        
        pred = ai_brain.predict([[current_year, target_round, circ_enc, d_enc, c_enc, pos]])
        
        # Clean up text displays nicely
        display_driver = d_id.replace('_', ' ').title()
        display_team = c_id.replace('_', ' ').title()
        if d_id == 'antonelli': display_driver = "Kimi Antonelli"
        
        live_predictions.append({
            "grid": pos,
            "driver": display_driver,
            "team": display_team,
            "predicted_finish": round(pred[0], 1)
        })

# 6. Save data to predictions.json
with open("predictions.json", "w") as f:
    json.dump(live_predictions, f, indent=4)

print("Upgraded pipeline completed successfully! predictions.json completely customized.")
