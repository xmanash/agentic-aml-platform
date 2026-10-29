import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from backend.app.tools.sanctions_lookup import adverse_media_search as search_media
from backend.app.tools.sanctions_lookup import check_sanction as lookup_sanction

mcp = FastMCP("sanctions_api")


@mcp.tool()
def check_sanction(name: str):
    return lookup_sanction(name)


@mcp.tool()
def adverse_media_search(entity: str):
    return search_media(entity)


if __name__ == "__main__":
    mcp.run()
