from .pii_masker import mask_pii
from .vector_store import vector_store


def memory_search(query: str, top_k: int = 5):
    hits = vector_store.query(mask_pii(query or ""), top_k=top_k, namespace="cases")
    return [hit for hit in hits if float(hit.get("score") or 0) >= 0.35]


def memory_write(case_id: str, text: str, metadata: dict | None = None):
    safe = mask_pii(text or "")
    meta = dict(metadata or {})
    meta["summary"] = mask_pii(str(meta.get("summary") or safe[:240]))
    vector_store.upsert(case_id, safe, meta, namespace="cases")
    return {"id": case_id, "stored": True}
