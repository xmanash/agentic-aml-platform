from datetime import datetime, timezone

from backend.app.agents.entity_resolution_agent import entity_resolution_agent
from backend.app.models.schemas import Transaction
from backend.app.tools.ids import stable_id


def _tx(account, customer, counterparty="Local Store"):
    return Transaction(
        transaction_id=f"{account}-1",
        account_id=account,
        customer_id=customer,
        amount=100,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        counterparty=counterparty,
    )


def test_links_same_customer_across_accounts():
    txs = [_tx("ACC-1", "CUST-1", "Local Store"), _tx("ACC-2", "CUST-1", "Alice Jones")]
    result = entity_resolution_agent.run({"transactions": txs, "entities": []})
    linked = []
    for entity in result["entities"]:
        linked.extend(entity["linked_accounts"])
    assert "ACC-1" in linked
    assert "ACC-2" in linked
    assert len(result["entities"]) == 1


def test_entity_id_is_stable():
    assert stable_id("Bad Actor LLC") == stable_id("bad actor llc")
    assert stable_id("Bad Actor LLC") != stable_id("Local Store")
