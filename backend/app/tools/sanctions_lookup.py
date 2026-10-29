import csv

from .. import config

_CACHE = None


def _load():
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    path = config.DATA_DIR / "ofac_sdn_mock.csv"
    rows = []
    if path.exists():
        try:
            with path.open(encoding="utf-8") as handle:
                rows = [row for row in csv.DictReader(handle)]
        except Exception:
            rows = []
    if not rows:
        rows = [
            {"name": "Test Entity", "type": "individual", "program": "OFAC"},
            {"name": "Bad Actor LLC", "type": "entity", "program": "OFAC"},
            {"name": "Offshore Holdings", "type": "entity", "program": "UN"},
        ]
    _CACHE = rows
    return rows


def check_sanction(name: str) -> dict:
    hits = []
    cleaned = (name or "").strip()
    if not cleaned:
        return {"name": name, "hits": hits}
    for row in _load():
        sdn = (row.get("name") or "").strip()
        if sdn and sdn.lower() in cleaned.lower():
            hits.append({"name": sdn, "list": row.get("program") or "OFAC SDN", "type": row.get("type"), "score": 0.95})
    return {"name": cleaned, "hits": hits}


def adverse_media_search(entity: str) -> dict:
    text = entity or ""
    articles = []
    if "offshore" in text.lower():
        articles.append({"title": f"Adverse media keyword for {text}", "risk": "medium"})
    return {"entity": text, "articles": articles}
