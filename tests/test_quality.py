import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from transform import flatten, typed
from validate import validate


def load():
    payload = json.loads(Path("data/raw/sample_source.json").read_text())
    return typed(flatten(payload))


def test_rejets_et_doublons():
    acc, rej, counts = validate(load())
    assert counts["R3_domaine_magnitude"] == 5
    assert counts["R5_domaine_profondeur"] == 3
    assert counts["R1_completude_event_id"] == 2
    assert counts["R4_domaine_coordonnees"] == 2
    assert counts["R6_unicite_event_id"] == 3
    assert acc["event_id"].is_unique
    assert "reject_reason" in rej.columns


if __name__ == "__main__":
    test_rejets_et_doublons(); print("OK")
