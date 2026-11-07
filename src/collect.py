"""Collecteur : telecharge les seismes depuis l'API USGS et garde la reponse brute."""
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
RAW_DIR = Path("data/raw")


def collect(start="1990-01-01", end=None, min_mag=6.0, url=URL) -> Path:
    end = end or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    params = {"format": "geojson", "starttime": start, "endtime": end,
              "minmagnitude": min_mag, "orderby": "time-asc"}
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as err:
        raise SystemExit(f"Collecte impossible (source indisponible ?) : {err}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = RAW_DIR / f"source_{stamp}.json"
    output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"Raw sauvegarde : {output} ({len(payload.get('features', []))} evenements)")
    return output


if __name__ == "__main__":
    collect()
