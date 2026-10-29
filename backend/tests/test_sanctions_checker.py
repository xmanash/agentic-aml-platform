from datetime import datetime, timezone

from backend.app.agents.sanctions_agent import sanctions_agent
from backend.app.models.schemas import Transaction
from backend.app.tools.sanctions_lookup import check_sanction


def test_ofac_hit_detection():
    result = check_sanction("Payment to Bad Actor LLC")
    assert result["hits"]
    assert result["hits"][0]["name"] == "Bad Actor LLC"


def test_clean_name_has_no_hit():
    assert check_sanction("Local Store")["hits"] == []


def test_agent_sets_hit_and_escalation_evidence():
    txs = [
        Transaction(
            transaction_id="s1",
            account_id="ACC-9",
            customer_id="CUST-9",
            amount=100,
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            counterparty="Bad Actor LLC",
        )
    ]
    result = sanctions_agent.run({"transactions": txs, "entities": []})
    assert result["hit"] is True
    assert len(result["evidence"]) >= 2
    assert len(result["reason_codes"]) >= 3
