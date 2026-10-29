import csv
import json
from datetime import datetime, timedelta, timezone

from backend.app import config


def _tx(case_id: str, index: int, account: str, amount: float, counterparty: str, customer: str):
    stamp = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=index)
    return {
        "transaction_id": f"{case_id}-{index}",
        "account_id": account,
        "customer_id": customer,
        "amount": float(amount),
        "currency": "USD",
        "timestamp": stamp.isoformat(),
        "counterparty": counterparty,
        "channel": "payments",
        "type": "transfer",
    }


def _transactions(case_id: str, pattern: str):
    customer = f"CUST-{case_id}"
    account = f"ACC-{case_id}"
    if pattern == "structuring":
        return [_tx(case_id, i, account, 9500, "Local Store", customer) for i in range(5)]
    if pattern == "velocity":
        return [_tx(case_id, i, account, 5000, "Northwind LLC", customer) for i in range(12)]
    if pattern == "smurfing":
        return [_tx(case_id, i, account, 2000, "City Utilities", customer) for i in range(8)]
    if pattern == "layering":
        rows = []
        for i in range(4):
            rows.append(_tx(case_id, i, f"{account}-{i}", 1000, "Alice Jones", customer))
        return rows
    if pattern == "sanctions":
        return [_tx(case_id, i, account, 100, "Bad Actor LLC", customer) for i in range(2)]
    return [
        _tx(case_id, 0, account, 6500, "Local Store", customer),
        _tx(case_id, 1, account, 200, "Alice Jones", customer),
    ]


def build_cases():
    patterns = (
        ["structuring"] * 30
        + ["velocity"] * 30
        + ["sanctions"] * 20
        + ["layering"] * 20
        + ["smurfing"] * 20
        + ["legit"] * 80
    )
    cases = []
    for index, pattern in enumerate(patterns, start=1):
        case_id = f"EV{index:04d}"
        label = "legit" if pattern == "legit" else "fraud"
        transactions = _transactions(case_id, pattern)
        cases.append(
            {
                "case_id": case_id,
                "label": label,
                "pattern": pattern,
                "amount_count": len(transactions),
                "transactions": transactions,
            }
        )
    return cases


def generate_dataset():
    cases = build_cases()
    folder = config.DATA_DIR / "eval"
    folder.mkdir(parents=True, exist_ok=True)
    csv_path = folder / "labeled_cases.csv"
    jsonl_path = folder / "cases.jsonl"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["case_id", "label", "pattern", "amount_count", "risk"])
        writer.writeheader()
        for case in cases:
            writer.writerow(
                {
                    "case_id": case["case_id"],
                    "label": case["label"],
                    "pattern": case["pattern"],
                    "amount_count": case["amount_count"],
                    "risk": 90 if case["pattern"] == "sanctions" else (10 if case["label"] == "legit" else 65),
                }
            )
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(case) + "\n")
    return {"csv": str(csv_path), "jsonl": str(jsonl_path), "count": len(cases)}


def load_cases():
    path = config.DATA_DIR / "eval" / "cases.jsonl"
    if not path.exists():
        generate_dataset()
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


if __name__ == "__main__":
    print(generate_dataset())
