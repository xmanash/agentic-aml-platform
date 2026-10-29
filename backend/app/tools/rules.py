from functools import lru_cache
from pathlib import Path

import yaml

_RULES_PATH = Path(__file__).resolve().parents[1] / "rules" / "aml_rules.yaml"

_DEFAULTS = {
    "base_score": 10,
    "structuring": {"min_amount": 9000, "max_amount": 9999, "min_count": 3, "weight": 55, "reason_code": "STRUCTURING"},
    "velocity": {"min_count": 11, "min_sum": 50000, "weight": 55, "reason_code": "HIGH_VELOCITY"},
    "smurfing": {"min_count": 8, "max_amount": 3000, "min_sum": 15000, "weight": 55, "reason_code": "SMURFING"},
    "layering": {"min_linked_accounts": 3, "weight": 55, "reason_code": "LAYERING"},
    "ml_anomaly": {"min_samples": 11, "contamination": 0.1, "weight": 10, "reason_code": "ML_ANOMALY"},
    "thresholds": {"sar_draft": 70, "escalate": 60, "auto_escalate": 85, "max_threshold_shift": 0.10},
    "sanctions": {"min_score_on_hit": 90},
}


@lru_cache(maxsize=1)
def load_rules() -> dict:
    if not _RULES_PATH.exists():
        return _DEFAULTS
    with _RULES_PATH.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    merged = dict(_DEFAULTS)
    merged.update(loaded)
    return merged
