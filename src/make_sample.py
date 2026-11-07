"""Genere un petit fichier au format USGS (synthetique) avec des erreurs volontaires."""
import json, random
random.seed(42)
ZONES = [(38, 143, 3), (-30, -72, 3), (-5, 105, 3), (55, -160, 3), (-20, -175, 2)]
feats = []
for i in range(400):
    lat0, lon0, s = random.choice(ZONES)
    feats.append({"type": "Feature", "id": f"us{i:06d}",
        "properties": {"mag": round(random.uniform(6.0, 8.8), 1), "magType": random.choice(["mww", "mw", "mb"]),
                       "time": random.randint(631152000000, 1767225600000),
                       "place": "zone synthetique", "tsunami": random.choice([0, 0, 1]), "status": "reviewed"},
        "geometry": {"type": "Point", "coordinates": [lon0 + random.uniform(-s, s) * 2,
                     lat0 + random.uniform(-s, s), round(random.choice([10, 15, 30, 60, 120, 300]) * random.random() + 5, 1)]}})
clone = lambda f: json.loads(json.dumps(f))
bad = [clone(feats[k]) for k in range(3)]  # doublons
for k in range(5):  # magnitude manquante
    f = clone(feats[10 + k]); f["id"] = f"bad_mag{k}"; f["properties"]["mag"] = None; bad.append(f)
for k in range(3):  # profondeur impossible
    f = clone(feats[20 + k]); f["id"] = f"bad_depth{k}"; f["geometry"]["coordinates"][2] = 9999; bad.append(f)
for k in range(2):  # id vide
    f = clone(feats[30 + k]); f["id"] = ""; bad.append(f)
for k in range(2):  # latitude impossible
    f = clone(feats[40 + k]); f["id"] = f"bad_lat{k}"; f["geometry"]["coordinates"][1] = 123; bad.append(f)
json.dump({"type": "FeatureCollection", "features": feats + bad}, open("data/raw/sample_source.json", "w"))
print("sample_source.json cree :", len(feats + bad), "lignes")
