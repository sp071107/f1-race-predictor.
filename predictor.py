import requests
import pandas as pd
import time
import json
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor

print("Starting F1 Data Pipeline...")
all_races_data = []

# Fetch historical data (2016-2025)
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
                    'year': year, 'round': int(round_num), 'circuit_id': circuit_id,
                    'driver_id': result['Driver']['driverId'], 'constructor_id': result['Constructor']['constructorId'],
                    'grid_position': int(result['grid']), 'finishing_position': int(finishing_pos)
                })
    time.sleep(0.2)

df = pd.DataFrame(all_races_data)

# Encode words into numbers
le_circuit, le_driver, le_constructor = LabelEncoder(), LabelEncoder(), LabelEncoder()
df['circuit_encoded'] = le_circuit.fit_transform(df['circuit_id'])
df['driver_encoded'] = le_driver.fit_transform(df['driver_id'])
df['constructor_encoded'] = le_constructor.fit_transform(df['constructor_id'])

# Train the AI Brain
X = df[['year', 'round', 'circuit_encoded', 'driver_encoded', 'constructor_encoded', 'grid_position']]
y = df['finishing_position']
ai_brain = RandomForestRegressor(n_estimators=100, random_state=42)
ai_brain.fit(X, y)

# Generate predictions for a standard mock grid grid (P1 through P20)
# This mock data simulates a basic race lineup structure
mock_predictions = []
for pos in range(1, 21):
    pred = ai_brain.predict([[2026, 5, 0, 0, 0, pos]])
    mock_predictions.append({"grid": pos, "predicted_finish": round(pred[0], 1)})

# Save the predictions to a flat file!
with open("predictions.json", "w") as f:
    json.dump(mock_predictions, f, indent=4)

print("Pipeline finished successfully! predictions.json updated.")
