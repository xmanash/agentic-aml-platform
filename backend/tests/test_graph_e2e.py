from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.schemas import Transaction
from backend.app.orchestration.graph import run_investigation


def _tx(i, amount, counterparty, account="ACC-E2E", customer="CUST-E2E"):
    return Transaction(
        transaction_id=f"e2e-{i}",
        account_id=account,
        customer_id=customer,
        amount=amount,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        counterparty=counterparty,
    )


def test_structuring_case_escalates():
    txs = [_tx(i, 9500, "Local Store") for i in range(5)]
    result = run_investigation("e2e-struct", txs, [])
    assert result.risk_score >= 60
    assert result.status in {"escalated", "sar_draft"}
    assert len(result.audit_hash) == 64
    assert "STRUCTURING" in result.reason_codes


def test_sanctions_cannot_auto_close():
    txs = [_tx(i, 100, "Bad Actor LLC", account="ACC-SAN", customer="CUST-SAN") for i in range(2)]
    result = run_investigation("e2e-sanctions", txs, [])
    assert result.sanctions_hit is True
    assert result.status != "low"
    assert result.status == "sar_draft"
    assert len(result.reason_codes) >= 3
    assert len(result.evidence) >= 2
    assert result.sar_draft
    assert "human verification" in result.sar_draft.lower()


def test_feedback_accepts_json_body(monkeypatch, tmp_path):
    monkeypatch.setattr("backend.app.config.LOCAL_DB_DIR", tmp_path)
    client = TestClient(app)
    payload = {
        "transactions": [
            {
                "transaction_id": "fb-1",
                "account_id": "ACC-FB",
                "customer_id": "CUST-FB",
                "amount": 9500,
                "currency": "USD",
                "timestamp": "2026-01-01T00:00:00Z",
                "counterparty": "Local Store",
                "channel": "payments",
                "type": "transfer",
            }
        ]
    }
    created = client.post("/ingest/transactions", json=payload)
    assert created.status_code == 200, created.text
    case_id = created.json()["case_id"]
    response = client.post(
        f"/cases/{case_id}/feedback",
        json={"decision": "false_positive", "notes": "analyst review"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["ok"] is True
