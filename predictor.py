import requests
import pandas as pd
import json
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor

print("🚀 Training improved F1 Predictor...")

# ================== DATA COLLECTION ==================
all_races_data = []
today = datetime.utcnow().date()
current_year = today.year

for year in range(2016, current_year):
    url = f"https://api.jolpi.ca/ergast/f1/{year}/results.json?limit=1000"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            races = resp.json()['MRData']['RaceTable']['Races']
            for race in races:
                for res in race.get('Results', []):
                    all_races_data.append({
                        'year': year,
                        'round': int(race['round']),
                        'circuit': race['Circuit']['circuitId'],
                        'driver': res['Driver']['driverId'],
                        'constructor': res['Constructor']['constructorId'],
                        'grid': int(res.get('grid', 20)),
                        'finish': int(res.get('positionOrder', 20))
                    })
    except:
        continue

df = pd.DataFrame(all_races_data)

# ================== LABEL ENCODERS ==================
le_circuit = LabelEncoder().fit(df['circuit'].unique())
le_driver = LabelEncoder().fit(df['driver'].unique())
le_constructor = LabelEncoder().fit(df['constructor'].unique())

df['c_enc'] = le_circuit.transform(df['circuit'])
df['d_enc'] = le_driver.transform(df['driver'])
df['const_enc'] = le_constructor.transform(df['constructor'])

# ================== TRAIN MODEL ==================
X = df[['year', 'round', 'c_enc', 'd_enc', 'const_enc', 'grid']]
y = df['finish']

model = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
model.fit(X, y)

# Save everything
artifacts = {
    "year": current_year,
    "le_circuit": le_circuit.classes_.tolist(),
    "le_driver": le_driver.classes_.tolist(),
    "le_constructor": le_constructor.classes_.tolist()
}

with open("model_artifacts.json", "w") as f:
    json.dump(artifacts, f)

print("✅ Model trained successfully.")
