"""Aplatir le GeoJSON, typer, enrichir, et calculer le risque probabiliste."""
import numpy as np
import pandas as pd

CELL = 5  # taille d'une cellule geographique en degres
BASE_COLS = ["event_id", "observed_at", "magnitude", "mag_type", "place",
             "tsunami_flag", "status", "latitude", "longitude", "depth_km"]


def flatten(payload: dict) -> pd.DataFrame:
    rows = []
    for f in payload.get("features", []):
        p = f.get("properties") or {}
        c = list((f.get("geometry") or {}).get("coordinates") or []) + [None] * 3
        rows.append({"event_id": f.get("id"), "time_ms": p.get("time"),
                     "magnitude": p.get("mag"), "mag_type": p.get("magType"),
                     "place": p.get("place"), "tsunami_flag": p.get("tsunami"),
                     "status": p.get("status"),
                     "longitude": c[0], "latitude": c[1], "depth_km": c[2]})
    return pd.DataFrame(rows)


def typed(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["observed_at"] = pd.to_datetime(pd.to_numeric(df["time_ms"], errors="coerce"),
                                       unit="ms", utc=True, errors="coerce")
    for col in ["magnitude", "latitude", "longitude", "depth_km", "tsunami_flag"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["event_id"] = df["event_id"].astype("string").str.strip().replace("", pd.NA)
    return df.drop(columns=["time_ms"])[BASE_COLS]


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["is_shallow"] = df["depth_km"] <= 70
    df["tsunami_candidate"] = (df["magnitude"] >= 6.5) & df["is_shallow"]
    lat_c = np.floor(df["latitude"] / CELL) * CELL + CELL / 2
    lon_c = np.floor(df["longitude"] / CELL) * CELL + CELL / 2
    df["cell_lat"], df["cell_lon"] = lat_c, lon_c
    df["cell_id"] = lat_c.astype(str) + "_" + lon_c.astype(str)
    return df


def risk_by_cell(df: pd.DataFrame, horizon_years=10) -> pd.DataFrame:
    """Modele de Poisson : lambda = nb evenements candidats / duree du catalogue.
    P(au moins 1 evenement en T ans) = 1 - exp(-lambda * T)."""
    years = max((df["observed_at"].max() - df["observed_at"].min()).days / 365.25, 1)
    cand = df[df["tsunami_candidate"]]
    out = (cand.groupby(["cell_id", "cell_lat", "cell_lon"]).size()
           .rename("n_events").reset_index())
    out["annual_rate"] = out["n_events"] / years
    out[f"prob_{horizon_years}y"] = 1 - np.exp(-out["annual_rate"] * horizon_years)
    return out.sort_values("annual_rate", ascending=False).reset_index(drop=True)
