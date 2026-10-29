from .synthetic_generator import generate_transactions


def get_transactions(account_id: str, limit: int = 20):
    txs = generate_transactions(limit)
    matched = [tx for tx in txs if tx.get("account_id") == account_id]
    return matched or txs[:limit]


def stream_transactions():
    return {"status": "streaming stub - connect to Kafka/Kinesis in prod"}
