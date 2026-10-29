import hashlib
import json
import math
import re
from typing import Dict, List

from .. import config
from .ids import stable_id

_SEEDS = ["Bad Actor LLC", "Offshore Holdings", "Test Entity", "John Smith"]
_INDEX_NAMES = {
    "cases": "aml-cases",
    "entities": "aml-entities",
    "documents": "aml-documents",
    "adverse": "aml-adverse-media",
}
_cache: Dict[str, dict] = {"path": "", "data": {}}


def _embed_openai(text: str):
    if not config.OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.embeddings.create(model="text-embedding-3-small", input=text or " ")
        return list(response.data[0].embedding)
    except Exception:
        return None


def embed(text: str) -> List[float]:
    remote = _embed_openai(text)
    vector = remote if remote and len(remote) == config.EMBED_DIM else hashed_embed(text)
    return _normalize(vector)


def hashed_embed(text: str, dim: int = config.EMBED_DIM) -> List[float]:
    vector = [0.0] * dim
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    if not tokens:
        vector[0] = 1.0
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode()).digest()
        bucket = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign
    return vector


def _normalize(vector: List[float]) -> List[float]:
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _store_path():
    config.VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    return config.VECTOR_DIR / "store.json"


def _empty():
    return {"cases": [], "entities": [], "documents": [], "adverse": []}


def _load() -> dict:
    path = _store_path()
    key = str(path)
    if _cache["path"] == key and _cache["data"]:
        return _cache["data"]
    data = _empty()
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                for name in data:
                    data[name] = loaded.get(name) or []
        except Exception:
            data = _empty()
    _cache["path"] = key
    _cache["data"] = data
    _ensure_seeds(data)
    return data


def _save(data: dict) -> None:
    path = _store_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)
    _cache["path"] = str(path)
    _cache["data"] = data
    _write_faiss(data.get("cases") or [])


def _ensure_seeds(data: dict) -> None:
    if data.get("entities"):
        return
    for name in _SEEDS:
        data["entities"].append(
            {
                "id": stable_id(name),
                "vector": embed(name),
                "metadata": {"name": name, "kind": "entity", "summary": name},
            }
        )
    _save(data)


def _write_faiss(rows: List[dict]) -> None:
    if not rows:
        return
    try:
        import faiss
        import numpy as np

        matrix = np.array([row["vector"] for row in rows], dtype="float32")
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        config.VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(config.VECTOR_DIR / "cases.faiss"))
    except Exception:
        return


def _search_vectors(vector: List[float], rows: List[dict], top_k: int) -> List[dict]:
    if not rows:
        return []
    try:
        import faiss
        import numpy as np

        matrix = np.array([row["vector"] for row in rows], dtype="float32")
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        scores, indices = index.search(np.array([vector], dtype="float32"), min(top_k, len(rows)))
        hits = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            row = rows[int(idx)]
            hits.append({"id": row["id"], "score": float(score), "metadata": row.get("metadata") or {}})
        return hits
    except Exception:
        scored = []
        for row in rows:
            other = row.get("vector") or []
            if len(other) != len(vector):
                continue
            score = sum(a * b for a, b in zip(vector, other))
            scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {"id": row["id"], "score": float(score), "metadata": row.get("metadata") or {}}
            for score, row in scored[:top_k]
        ]


def _pinecone_index(namespace: str):
    if not config.PINECONE_API_KEY:
        return None
    try:
        from pinecone import Pinecone

        client = Pinecone(api_key=config.PINECONE_API_KEY)
        return client.Index(_INDEX_NAMES.get(namespace, "aml-cases"))
    except Exception:
        return None


class VectorStore:
    def upsert(self, id: str, text: str, metadata: dict, namespace: str = "cases"):
        vector = embed(text)
        meta = dict(metadata or {})
        meta.setdefault("summary", (text or "")[:240])
        data = _load()
        bucket = data.setdefault(namespace, [])
        bucket[:] = [row for row in bucket if row.get("id") != id]
        bucket.append({"id": id, "vector": vector, "metadata": meta})
        _save(data)
        index = _pinecone_index(namespace)
        if index is not None:
            try:
                index.upsert(vectors=[{"id": id, "values": vector, "metadata": {k: v for k, v in meta.items() if isinstance(v, (str, int, float, bool))}}])
            except Exception:
                return

    def query(self, text: str, top_k: int = 5, namespace: str = "cases") -> List[dict]:
        vector = embed(text)
        index = _pinecone_index(namespace)
        if index is not None:
            try:
                response = index.query(vector=vector, top_k=top_k, include_metadata=True)
                matches = getattr(response, "matches", None) or response.get("matches", [])
                hits = []
                for match in matches:
                    meta = getattr(match, "metadata", None) or match.get("metadata") or {}
                    score = getattr(match, "score", None)
                    if score is None:
                        score = match.get("score", 0)
                    mid = getattr(match, "id", None) or match.get("id")
                    hits.append({"id": mid, "score": float(score), "metadata": dict(meta)})
                if hits:
                    return hits
            except Exception:
                pass
        data = _load()
        return _search_vectors(vector, data.get(namespace) or [], top_k)


vector_store = VectorStore()
