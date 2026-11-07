import json
from pathlib import Path

src = sorted(Path("data/raw").glob("source_*.json"))[-1]
data = json.loads(src.read_text(encoding="utf-8"))
bad = json.loads(json.dumps(data["features"][0]))
bad["id"] = "TEST_INVALID"
bad["properties"]["mag"] = None
data["features"].append(bad)
Path("data/raw/demo_invalid.json").write_text(json.dumps(data), encoding="utf-8")
print("demo_invalid.json cree")
