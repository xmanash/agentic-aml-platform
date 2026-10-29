
from backend.app.agents.pattern_agent import pattern_agent
from backend.app.models.schemas import Transaction
from datetime import datetime, timezone
def test_structuring():
    txs = [Transaction(transaction_id=str(i), account_id="ACC-1", amount=9500, currency="USD", timestamp=datetime.now(timezone.utc), counterparty="Test", type="transfer") for i in range(5)]
    res = pattern_agent.run({"transactions": txs})
    assert res["risk_score"] >= 40
