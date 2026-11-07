"""Regles de qualite : chaque regle a un nom, une condition, un compteur, une action."""
from datetime import datetime, timezone
import pandas as pd

# (nom, action, fonction -> masque des lignes EN ECHEC)
REJECT_RULES = [
    ("R1_completude_event_id", "rejeter", lambda d: d["event_id"].isna()),
    ("R2_validite_date", "rejeter", lambda d: d["observed_at"].isna()),
    ("R3_domaine_magnitude", "rejeter", lambda d: ~d["magnitude"].between(0, 10)),
    ("R4_domaine_coordonnees", "rejeter",
     lambda d: ~(d["latitude"].between(-90, 90) & d["longitude"].between(-180, 180))),
    ("R5_domaine_profondeur", "rejeter", lambda d: ~d["depth_km"].between(-5, 800)),
]


def validate(df: pd.DataFrame):
    counts, reasons = {}, pd.Series("", index=df.index)
    for name, _, rule in REJECT_RULES:
        failed = rule(df)
        counts[name] = int(failed.sum())
        reasons = reasons.where(~failed, reasons + name + ";")
    bad = reasons != ""
    accepted, rejected = df[~bad].copy(), df[bad].copy()
    rejected["reject_reason"] = reasons[bad].str.rstrip(";")
    # R6 unicite : dedupliquer et compter
    before = len(accepted)
    accepted = accepted.drop_duplicates(subset="event_id", keep="first")
    counts["R6_unicite_event_id"] = before - len(accepted)
    return accepted, rejected, counts


def freshness_warning(filename: str, max_days=7):
    """R7 : alerte si le fichier raw est trop ancien (date lue dans le nom)."""
    try:
        stamp = datetime.strptime(filename.split("_")[1].split(".")[0], "%Y%m%dT%H%M%SZ")
        age = (datetime.now(timezone.utc) - stamp.replace(tzinfo=timezone.utc)).days
        return f"R7_fraicheur: fichier vieux de {age} jours" if age > max_days else None
    except (IndexError, ValueError):
        return "R7_fraicheur: date du fichier inconnue (echantillon ?)"
