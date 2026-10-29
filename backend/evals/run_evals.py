import json

from backend.app import config
from backend.app.llm import generate
from backend.app.models.schemas import Transaction
from backend.app.orchestration.graph import run_investigation
from backend.app.tools import supabase_client
from backend.evals.dataset import load_cases


def rules_only_positive(transactions) -> bool:
    """Blunt amount-or-count rule used as the false-positive baseline."""
    amounts = [float(tx.amount) for tx in transactions]
    return any(amount >= 5000 for amount in amounts) or len(transactions) >= 4


def _rates(y_true, y_pred):
    tp = fp = fn = tn = 0
    for truth, pred in zip(y_true, y_pred):
        if truth and pred:
            tp += 1
        elif pred and not truth:
            fp += 1
        elif truth and not pred:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "fpr": round(fpr, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def sar_complete(draft: str) -> bool:
    if not draft:
        return False
    lowered = draft.lower()
    return "subject" in lowered and "evidence" in lowered and "human verification" in lowered


def judge_sar(draft: str) -> bool:
    if not draft:
        return False
    if not config.OPENAI_API_KEY:
        return sar_complete(draft)
    text, _tokens = generate(
        "sar",
        "Reply pass or fail. Pass only if the draft names a subject, lists evidence with sources, and requires human verification.\n\n" + draft[:4000],
        "pass" if sar_complete(draft) else "fail",
    )
    return "pass" in text.lower() and "fail" not in text.lower().split()


def compute_metrics(write: bool = True) -> dict:
    original = supabase_client.get_applied_adjustments
    supabase_client.get_applied_adjustments = lambda: {}
    try:
        return _compute(write)
    finally:
        supabase_client.get_applied_adjustments = original


def _compute(write: bool) -> dict:
    y_true = []
    agent_pred = []
    rules_pred = []
    explainability_failures = []
    sar_failures = []
    for raw in load_cases():
        transactions = [Transaction(**tx) for tx in raw["transactions"]]
        result = run_investigation(raw["case_id"], transactions, [])
        truth = raw["label"] == "fraud"
        y_true.append(truth)
        agent_pred.append(result.status != "low")
        rules_pred.append(rules_only_positive(transactions))
        if result.risk_score >= 85:
            if len(result.reason_codes) < 3 or len(result.evidence) < 2:
                explainability_failures.append(raw["case_id"])
        if result.sar_draft and not judge_sar(result.sar_draft):
            sar_failures.append(raw["case_id"])

    agent = _rates(y_true, agent_pred)
    rules = _rates(y_true, rules_pred)
    if rules["fpr"]:
        reduction = (rules["fpr"] - agent["fpr"]) / rules["fpr"]
    else:
        reduction = 0.0
    metrics = {
        "n_cases": len(y_true),
        "agent": agent,
        "rules_only": rules,
        "fpr_reduction": round(reduction, 4),
        "explainability_failures": explainability_failures,
        "sar_failures": sar_failures,
        "targets": {"precision": 0.75, "recall": 0.85, "fpr_reduction": 0.60},
    }
    if write:
        path = config.ROOT / "backend" / "evals" / "results.json"
        path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main():
    metrics = compute_metrics(write=True)
    agent = metrics["agent"]
    print(
        f"Precision: {agent['precision']}, Recall: {agent['recall']}, "
        f"FPR reduction {metrics['fpr_reduction']:.0%} vs baseline"
    )
    passed = (
        agent["precision"] >= 0.75
        and agent["recall"] >= 0.85
        and metrics["fpr_reduction"] >= 0.60
        and not metrics["explainability_failures"]
        and not metrics["sar_failures"]
    )
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
