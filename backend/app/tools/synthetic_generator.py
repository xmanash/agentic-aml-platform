
from datetime import datetime, timedelta, timezone
import random, uuid

def generate_transactions(n=100):
    accounts = [f"ACC-{1000+i}" for i in range(5)]
    txs = []
    for i in range(n):
        # inject structuring pattern 20% of time
        if random.random() < 0.2:
            amount = random.randint(9000, 9999)
        else:
            amount = random.randint(10, 15000)
        txs.append({
            "transaction_id": str(uuid.uuid4()),
            "account_id": random.choice(accounts),
            "customer_id": f"CUST-{random.randint(1,3)}",
            "amount": float(amount),
            "currency":"USD",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=random.randint(0,720))).isoformat(),
            "counterparty": random.choice(["John Smith","Bad Actor LLC","Offshore Holdings","Alice Jones","Local Store"]),
            "channel":"payments",
            "type":"transfer"
        })
    return txs
