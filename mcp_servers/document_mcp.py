import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from backend.app.tools.kyc import extract_kyc_text

mcp = FastMCP("document_store")


@mcp.tool()
def upload_doc(filename: str, content_text: str):
    folder = ROOT / "data" / "uploads"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / Path(filename).name
    path.write_text(content_text or "", encoding="utf-8")
    extracted = extract_kyc_text(content_text or "", path.name)
    return {"path": str(path), "extracted": extracted}


@mcp.tool()
def extract_kyc(filename: str, content_text: str = ""):
    return extract_kyc_text(content_text or "", filename)


if __name__ == "__main__":
    mcp.run()
