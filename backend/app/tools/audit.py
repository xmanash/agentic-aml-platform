import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .. import config
from .jsonutil import canonical, json_safe
from .pii_masker import mask_obj

_GENESIS = "0" * 64
_chain_cache = {"path": None, "rows": None}


def _path():
    config.AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    return config.AUDIT_DIR / "chain.jsonl"


def _hash(payload: dict) -> str:
    return hashlib.sha256(canonical(payload).encode()).hexdigest()


def _signature(path):
    if not path.exists():
        return (0, 0)
    stat = path.stat()
    return (stat.st_mtime_ns, stat.st_size)


def _read_chain() -> List[dict]:
    path = _path()
    key = str(path)
    sig = _signature(path)
    if _chain_cache["path"] == key and _chain_cache.get("sig") == sig and _chain_cache["rows"] is not None:
        return _chain_cache["rows"]
    rows = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rows.append(json.loads(line))
    _chain_cache["path"] = key
    _chain_cache["sig"] = sig
    _chain_cache["rows"] = rows
    return rows


def _append(record: dict) -> None:
    path = _path()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    key = str(path)
    if _chain_cache["path"] == key and _chain_cache["rows"] is not None:
        _chain_cache["rows"].append(record)
    else:
        _chain_cache["path"] = key
        _chain_cache["rows"] = [record]
    _chain_cache["sig"] = _signature(path)


def _mirror_supabase(record: dict, inputs: dict, outputs: dict) -> None:
    try:
        from .supabase_client import insert_audit
        insert_audit(record, inputs, outputs)
    except Exception:
        return


def log_action(case_id: str, agent: str, action: str, inputs: Dict, outputs: Dict, final: bool = False, reason_codes: Optional[List[str]] = None):
    del final  # retained so existing call sites stay valid
    chain = _read_chain()
    prev_hash = chain[-1]["hash"] if chain else _GENESIS
    safe_inputs = mask_obj(json_safe(inputs))
    safe_outputs = mask_obj(json_safe(outputs))
    codes = list(reason_codes or [])
    body = {
        "case_id": case_id,
        "agent": agent,
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_hash": _hash(safe_inputs),
        "output_hash": _hash(safe_outputs),
        "prev_hash": prev_hash,
        "reason_codes": codes,
        "payload": {"inputs": safe_inputs, "outputs": safe_outputs},
    }
    body["hash"] = _hash(body)
    _append(body)
    _mirror_supabase(body, safe_inputs, safe_outputs)
    return body["hash"]


def get_audit_logs(case_id=None):
    rows = _read_chain()
    if case_id:
        return [row for row in rows if row.get("case_id") == case_id]
    return rows


def verify_chain():
    rows = _read_chain()
    prev = _GENESIS
    for index, row in enumerate(rows):
        if row.get("prev_hash") != prev:
            return {"valid": False, "broken_at": index, "reason": "prev_hash"}
        body = {key: value for key, value in row.items() if key != "hash"}
        if _hash(body) != row.get("hash"):
            return {"valid": False, "broken_at": index, "reason": "hash mismatch"}
        if len(row.get("hash") or "") != 64:
            return {"valid": False, "broken_at": index, "reason": "short hash"}
        prev = row["hash"]
    return {"valid": True, "length": len(rows)}
