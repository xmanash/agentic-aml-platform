import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from backend.app.tools.memory_tools import memory_search as search_memory
from backend.app.tools.memory_tools import memory_write as write_memory

mcp = FastMCP("memory")


@mcp.tool()
def memory_search(query: str, top_k: int = 5):
    return search_memory(query, top_k)


@mcp.tool()
def memory_write(case_id: str, text: str):
    return write_memory(case_id, text, {"summary": text[:240]})


if __name__ == "__main__":
    mcp.run()
