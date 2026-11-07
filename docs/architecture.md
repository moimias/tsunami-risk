```mermaid
flowchart LR
  S["Source : USGS (API FDSN)"] --> C["Collecteur (collect.py)"] --> R["Raw (data/raw)"] --> V["Validation (validate.py)"]
  V --> K["Curated (dataset.csv)"] --> A["Application : risk_by_cell.csv + rapport"]
  V --> X["Rejected (rejected_rows.csv)"]
```
Une ligne représente un séisme enregistré par l'USGS.
Champs : event_id, observed_at, magnitude, mag_type, place, tsunami_flag, status, latitude, longitude, depth_km (+ is_shallow, tsunami_candidate, cell_id calculés).
