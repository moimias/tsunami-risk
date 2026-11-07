"""Pipeline : raw -> profilage -> validation -> curated (upsert) -> risque -> rapport."""
import argparse, json, os, time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from collect import collect
from transform import flatten, typed, enrich, risk_by_cell, BASE_COLS
from validate import validate, freshness_warning

CURATED = Path("data/curated/dataset.csv")
REJECTED = Path("data/rejected/rejected_rows.csv")
RISK = Path("data/curated/risk_by_cell.csv")
REPORTS = Path("reports")


def latest_raw() -> Path:
    files = sorted(Path("data/raw").glob("source_*.json"))
    return files[-1] if files else Path("data/raw/sample_source.json")


def atomic_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)  # ecriture atomique


def profile(df: pd.DataFrame) -> dict:
    return {"rows": len(df), "columns": df.shape[1],
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_rate": df.isna().mean().round(4).to_dict(),
            "duplicates_event_id": int(df["event_id"].duplicated().sum()),
            "magnitude_min_max": [df["magnitude"].min(), df["magnitude"].max()],
            "depth_min_max": [df["depth_km"].min(), df["depth_km"].max()],
            "top_mag_type": df["mag_type"].value_counts().head(5).to_dict()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collect", action="store_true", help="telecharger depuis USGS")
    ap.add_argument("--input", help="fichier raw a utiliser")
    args = ap.parse_args()
    t0 = time.time()
    src = collect() if args.collect else Path(args.input) if args.input else latest_raw()
    payload = json.loads(src.read_text(encoding="utf-8"))

    df = typed(flatten(payload))
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "profile.json").write_text(json.dumps(profile(df), indent=2, default=str))

    accepted, rejected, counts = validate(df)
    atomic_csv(rejected, REJECTED)

    old_rows = 0
    if CURATED.exists():  # UPSERT par cle metier -> idempotence
        old = pd.read_csv(CURATED, parse_dates=["observed_at"])[BASE_COLS]
        old["observed_at"] = pd.to_datetime(old["observed_at"], utc=True)
        old["event_id"] = old["event_id"].astype("string")
        old_rows = len(old)
        accepted = pd.concat([old, accepted]).drop_duplicates("event_id", keep="last")
    curated = enrich(accepted.sort_values("observed_at"))
    atomic_csv(curated, CURATED)
    risk = risk_by_cell(curated)
    atomic_csv(risk, RISK)

    warnings = [w for w in [freshness_warning(src.name)] if w]
    status = "FAIL" if curated.empty else (
        "PASS_WITH_WARNINGS" if warnings or len(rejected) else "PASS")
    report = {"pipeline": "tsunami-risk", "executed_at": datetime.now(timezone.utc).isoformat(),
              "source_file": src.name, "input_rows": len(df),
              "accepted_rows": len(df) - len(rejected) - counts["R6_unicite_event_id"],
              "rejected_rows": len(rejected),
              "duplicates_removed": counts["R6_unicite_event_id"],
              "rule_failures": counts, "warnings": warnings,
              "curated_total_rows": len(curated),
              "new_rows_added_to_curated": len(curated) - old_rows,
              "risk_cells": len(risk), "quality_status": status,
              "duration_seconds": round(time.time() - t0, 2)}
    (REPORTS / "run_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\nTop 5 zones a risque :\n", risk.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
