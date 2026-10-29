import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .. import config

try:
    from supabase import create_client
    _url = config.SUPABASE_URL
    _key = config.SUPABASE_KEY
    supa = create_client(_url, _key) if _url and _key else None
except Exception:
    supa = None

_CASE_COLUMNS = (
    "case_id",
    "risk_score",
    "status",
    "summary",
    "sar_draft",
    "entities",
    "evidence",
    "explanation",
    "reason_codes",
    "memory_hits",
    "graph",
    "confidence",
    "audit_hash",
)
_CASE_BASE = (
    "case_id",
    "risk_score",
    "status",
    "summary",
    "sar_draft",
    "entities",
    "evidence",
    "explanation",
)


def _path(name: str):
    config.LOCAL_DB_DIR.mkdir(parents=True, exist_ok=True)
    return config.LOCAL_DB_DIR / name


def _read_json(name: str, default):
    path = _path(name)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(name: str, data) -> None:
    path = _path(name)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)


def _case_dict(case) -> dict:
    if hasattr(case, "model_dump"):
        return case.model_dump(mode="json")
    return case


def _summary(data: dict) -> str:
    explanation = data.get("explanation") or []
    return explanation[0] if explanation else ""


def save_case(case):
    data = _case_dict(case)
    data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    rows = [row for row in _read_json("cases.json", []) if row.get("case_id") != data.get("case_id")]
    rows.append(data)
    _write_json("cases.json", rows[-500:])
    if not supa:
        return
    row = {
        "case_id": data.get("case_id"),
        "risk_score": data.get("risk_score", 0),
        "status": data.get("status", "open"),
        "summary": _summary(data),
        "sar_draft": data.get("sar_draft"),
        "entities": data.get("entities") or [],
        "evidence": data.get("evidence") or [],
        "explanation": data.get("explanation") or [],
        "reason_codes": data.get("reason_codes") or [],
        "memory_hits": data.get("memory_hits") or [],
        "graph": data.get("graph") or {},
        "confidence": data.get("confidence"),
        "audit_hash": data.get("audit_hash"),
    }
    try:
        supa.table("cases").upsert(row, on_conflict="case_id").execute()
    except Exception:
        base = {key: row[key] for key in _CASE_BASE}
        try:
            supa.table("cases").upsert(base, on_conflict="case_id").execute()
        except Exception:
            return


def get_case(case_id: str):
    for row in _read_json("cases.json", []):
        if row.get("case_id") == case_id:
            return row
    if not supa:
        return None
    try:
        res = supa.table("cases").select("*").eq("case_id", case_id).limit(1).execute()
        if res.data:
            return res.data[0]
    except Exception:
        return None
    return None


def list_cases():
    rows = _read_json("cases.json", [])
    if rows:
        return list(reversed(rows))[:100]
    if not supa:
        return []
    try:
        res = supa.table("cases").select("*").order("created_at", desc=True).limit(100).execute()
        return res.data or []
    except Exception:
        return []


def save_feedback(case_id: str, decision: str, notes: str = "", reviewer: str = "analyst"):
    row = {
        "case_id": case_id,
        "decision": decision,
        "notes": notes,
        "reviewer": reviewer,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    rows = _read_json("feedback.json", [])
    rows.append(row)
    _write_json("feedback.json", rows)
    if not supa:
        return
    try:
        supa.table("feedback").insert(
            {"case_id": case_id, "decision": decision, "notes": notes, "reviewer": reviewer}
        ).execute()
    except Exception:
        return


def save_threshold_adjustment(case_id: str, key: str, delta: float, status: str = "applied"):
    row = {
        "case_id": case_id,
        "key": key,
        "delta": delta,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    rows = _read_json("thresholds.json", [])
    rows.append(row)
    _write_json("thresholds.json", rows)
    if not supa:
        return
    try:
        supa.table("threshold_adjustments").insert(
            {"case_id": case_id, "key": key, "delta": delta, "status": status}
        ).execute()
    except Exception:
        try:
            supa.table("threshold_adjustments").insert(
                {"case_id": case_id, "key": key, "delta": delta}
            ).execute()
        except Exception:
            return


def get_applied_adjustments() -> Dict[str, float]:
    rows = _read_json("thresholds.json", [])
    if not rows and supa:
        try:
            res = supa.table("threshold_adjustments").select("*").execute()
            rows = res.data or []
        except Exception:
            rows = []
    totals: Dict[str, float] = {}
    for row in rows:
        if row.get("status", "applied") != "applied":
            continue
        key = row.get("key")
        if not key:
            continue
        totals[key] = round(totals.get(key, 0.0) + float(row.get("delta") or 0), 4)
    return totals


def save_kyc_document(filename: str, doc_type: str, extracted_text: str, extracted_fields: dict):
    row = {
        "filename": filename,
        "doc_type": doc_type,
        "extracted_text": extracted_text,
        "extracted_fields": extracted_fields,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    rows = _read_json("kyc_documents.json", [])
    rows.append(row)
    _write_json("kyc_documents.json", rows)
    if not supa:
        return row
    try:
        supa.table("kyc_documents").insert(
            {
                "filename": filename,
                "doc_type": doc_type,
                "extracted_text": extracted_text,
                "extracted_fields": extracted_fields,
            }
        ).execute()
    except Exception:
        return row
    return row


def record_trace(case_id: str, agent: str, latency_ms: float, decision: str, tokens: int = 0):
    from .pii_masker import mask_pii

    row = {
        "case_id": case_id,
        "agent": agent,
        "latency_ms": round(float(latency_ms), 3),
        "tokens": int(tokens or 0),
        "decision": mask_pii(decision or ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    rows = _read_json("agent_traces.json", [])
    rows.append(row)
    _write_json("agent_traces.json", rows[-2000:])
    if not supa:
        return row
    try:
        supa.table("agent_traces").insert(
            {
                "case_id": case_id,
                "agent": agent,
                "latency_ms": row["latency_ms"],
                "tokens": row["tokens"],
                "decision": row["decision"],
            }
        ).execute()
    except Exception:
        return row
    return row


def insert_audit(record: dict, inputs: dict, outputs: dict) -> None:
    if not supa:
        return
    payload = {"inputs": inputs, "outputs": outputs, "reason_codes": record.get("reason_codes") or []}
    supa.table("audit_logs").insert(
        {
            "case_id": record["case_id"],
            "agent": record["agent"],
            "action": record["action"],
            "input_hash": record["input_hash"],
            "output_hash": record["output_hash"],
            "prev_hash": record["prev_hash"],
            "hash": record["hash"],
            "payload": payload,
        }
    ).execute()


def get_prompt_text(agent: str) -> Optional[str]:
    if not supa:
        return None
    try:
        res = (
            supa.table("prompt_registry")
            .select("prompt_text,version")
            .eq("agent", agent)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if rows and rows[0].get("prompt_text"):
            return rows[0]["prompt_text"]
    except Exception:
        return None
    return None


def list_traces(case_id: Optional[str] = None) -> List[dict]:
    rows = _read_json("agent_traces.json", [])
    if case_id:
        rows = [row for row in rows if row.get("case_id") == case_id]
    return rows
