import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from backend.app.tools.transactions import get_transactions as fetch_transactions
from backend.app.tools.transactions import stream_transactions as stream_feed

mcp = FastMCP("transaction_feed")


@mcp.tool()
def get_transactions(account_id: str, limit: int = 20):
    return fetch_transactions(account_id, limit)


@mcp.tool()
def stream_transactions():
    return stream_feed()


if __name__ == "__main__":
    mcp.run()
