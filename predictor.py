import requests
import pandas as pd
import time
import json
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor

print("Starting Dynamic F1 Predictor...")

all_races_data = []
today = datetime.utcnow().date()
current_year = today.year

# Fetch historical data
for year in range(2016, current_year):
    url = f"https://api.jolpi.ca/ergast/f1/{year}/results.json?limit=1000"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            races = response.json()['MRData']['RaceTable']['Races']
            for race in races:
                for result in race.get('Results', []):
                    all_races_data.append({
                        'year': int(year),
                        'round': int(race['round']),
                        'circuit_id': race['Circuit']['circuitId'],
                        'driver_id': result['Driver']['driverId'],
                        'constructor_id': result['Constructor']['constructorId'],
                        'grid_position': int(result.get('grid', 0)),
                        'finishing_position': int(result.get('positionOrder', result.get('position', 20)))
                    })
            time.sleep(0.2)
    except:
        continue

df = pd.DataFrame(all_races_data)

# Label Encoders with future-proofing
base_circuits = list(df['circuit_id'].unique())
base_drivers = list(df['driver_id'].unique())
base_constructors = list(df['constructor_id'].unique())

custom_drivers = ['hadjar', 'lindblad', 'antonelli', 'bearman', 'lawson']
custom_teams = ['cadillac', 'audi', 'rb']

for d in custom_drivers:
    if d not in base_drivers: base_drivers.append(d)
for c in custom_teams:
    if c not in base_constructors: base_constructors.append(c)

le_circuit = LabelEncoder().fit(base_circuits)
le_driver = LabelEncoder().fit(base_drivers)
le_constructor = LabelEncoder().fit(base_constructors)

df['circuit_encoded'] = le_circuit.transform(df['circuit_id'])
df['driver_encoded'] = le_driver.transform(df['driver_id'])
df['constructor_encoded'] = le_constructor.transform(df['constructor_id'])

# Train model
X = df[['year', 'round', 'circuit_encoded', 'driver_encoded', 'constructor_encoded', 'grid_position']]
y = df['finishing_position']
ai_brain = RandomForestRegressor(n_estimators=120, random_state=42, n_jobs=-1)
ai_brain.fit(X, y)

# Save model artifacts
with open("model_artifacts.json", "w") as f:
    json.dump({
        "current_year": current_year,
        "le_circuit_classes": le_circuit.classes_.tolist(),
        "le_driver_classes": le_driver.classes_.tolist(),
        "le_constructor_classes": le_constructor.classes_.tolist()
    }, f)

print("✅ Predictor trained and saved.")
