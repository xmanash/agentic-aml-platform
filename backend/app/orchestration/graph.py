import time
from typing import List

from ..agents.entity_resolution_agent import entity_resolution_agent
from ..agents.escalation_agent import escalation_agent
from ..agents.ingestion_agent import ingestion_agent
from ..agents.pattern_agent import pattern_agent
from ..agents.report_agent import report_agent
from ..agents.sanctions_agent import sanctions_agent
from ..agents.summarizer_agent import summarizer_agent
from ..models.schemas import CaseResponse, CaseState, Entity, Evidence, KYCDoc, SimilarCase, Transaction
from ..tools.audit import log_action
from ..tools.memory_tools import memory_search, memory_write
from ..tools.rules import load_rules
from ..tools.supabase_client import record_trace, save_case
from ..tools.working_memory import save as save_working


def _view(case: CaseState) -> dict:
    return {
        "case_id": case.case_id,
        "transactions": case.transactions,
        "kyc_docs": case.kyc_docs,
        "entities": [entity.model_dump() for entity in case.entities],
        "evidence": [item.model_dump() for item in case.evidence],
        "risk_score": case.risk_score,
        "reason_codes": list(case.reason_codes),
        "memory_hits": [hit.model_dump() for hit in case.memory_hits],
        "graph": case.graph,
        "explanation": list(case.explanation),
        "sar_draft": case.sar_draft,
        "confidence": case.confidence,
        "status": case.status,
        "sanctions_hit": case.sanctions_hit,
    }


def _codes(case: CaseState, codes) -> None:
    for code in codes or []:
        if code not in case.reason_codes:
            case.reason_codes.append(code)


def _as_evidence(items) -> List[Evidence]:
    parsed = []
    for item in items or []:
        if isinstance(item, Evidence):
            parsed.append(item)
            continue
        parsed.append(
            Evidence(
                source=item.get("source", "unknown"),
                description=str(item.get("description", "")),
                risk_weight=float(item.get("risk_weight") or 0),
                data=item.get("data") or {},
            )
        )
    return parsed


def _as_entities(items) -> List[Entity]:
    parsed = []
    for item in items or []:
        if isinstance(item, Entity):
            parsed.append(item)
            continue
        parsed.append(
            Entity(
                entity_id=str(item.get("entity_id") or item.get("name") or "unknown"),
                type=str(item.get("type") or "customer"),
                name=str(item.get("name") or "Unknown"),
                linked_accounts=list(item.get("linked_accounts") or []),
                risk_score=float(item.get("risk_score") or 0),
            )
        )
    return parsed


def _audit(case: CaseState, agent: str, action: str, inputs: dict, result: dict, started: float) -> None:
    elapsed = (time.perf_counter() - started) * 1000
    codes = result.get("reason_codes") if isinstance(result, dict) else []
    log_action(case.case_id, agent, action, inputs, result or {}, reason_codes=list(codes or []))
    decision = action
    if isinstance(result, dict):
        decision = str(result.get("status") or result.get("risk_score") or result.get("hit") or action)
    tokens = int(result.get("tokens") or 0) if isinstance(result, dict) else 0
    record_trace(case.case_id, agent, elapsed, decision, tokens=tokens)


def run_investigation(case_id: str, transactions: List[Transaction], kyc_docs: List[KYCDoc]) -> CaseResponse:
    case = CaseState(case_id=case_id, transactions=list(transactions or []), kyc_docs=list(kyc_docs or []))

    started = time.perf_counter()
    ingested = ingestion_agent.run(_view(case))
    case.entities = _as_entities(ingested.get("entities"))
    _codes(case, ingested.get("reason_codes"))
    _audit(case, "ingestion_agent", "ingest", {"count": len(case.transactions)}, ingested, started)

    started = time.perf_counter()
    resolved = entity_resolution_agent.run(_view(case))
    case.entities = _as_entities(resolved.get("entities")) or case.entities
    if not case.entities:
        case.entities = [Entity(entity_id="unknown", type="customer", name="Unknown")]
    case.evidence.extend(_as_evidence(resolved.get("evidence")))
    case.graph = resolved.get("graph") or {}
    _codes(case, resolved.get("reason_codes"))
    _audit(case, "entity_resolution_agent", "resolve", {"entities": len(case.entities)}, resolved, started)

    started = time.perf_counter()
    pattern = pattern_agent.run(_view(case))
    case.risk_score = float(pattern.get("risk_score") or 0)
    case.evidence.extend(_as_evidence(pattern.get("evidence")))
    _codes(case, pattern.get("reason_codes"))
    _audit(case, "pattern_agent", "score", {"transactions": len(case.transactions)}, pattern, started)

    started = time.perf_counter()
    sanctions = sanctions_agent.run(_view(case))
    case.evidence.extend(_as_evidence(sanctions.get("evidence")))
    case.sanctions_hit = bool(sanctions.get("hit"))
    if case.sanctions_hit:
        case.risk_score = max(case.risk_score, float(sanctions.get("min_score") or 90))
    _codes(case, sanctions.get("reason_codes"))
    _audit(case, "sanctions_agent", "check", {"entities": len(case.entities)}, sanctions, started)

    query = " ".join(case.reason_codes + [item.description for item in case.evidence]) or case.case_id
    for hit in memory_search(query, top_k=5):
        hit_id = str(hit.get("id") or "")
        if not hit_id or hit_id == case.case_id:
            continue
        summary = str((hit.get("metadata") or {}).get("summary") or "")
        case.memory_hits.append(SimilarCase(case_id=hit_id, similarity=float(hit.get("score") or 0), summary=summary))

    started = time.perf_counter()
    summary = summarizer_agent.run(_view(case))
    case.explanation = list(summary.get("explanation") or [])
    _audit(case, "summarizer_agent", "summarize", {"evidence": len(case.evidence)}, summary, started)

    rules = load_rules()["thresholds"]
    started = time.perf_counter()
    if case.risk_score >= float(rules["sar_draft"]) and len(case.evidence) >= 2:
        report = report_agent.run(_view(case))
        case.sar_draft = report.get("sar_draft")
        case.confidence = "high"
    else:
        report = {"sar_draft": None, "tokens": 0, "confidence": "low_confidence" if len(case.evidence) < 2 else "high"}
        case.sar_draft = None
        case.confidence = "low_confidence" if len(case.evidence) < 2 else "high"
    _audit(case, "report_agent", "draft", {"risk": case.risk_score, "evidence": len(case.evidence)}, report, started)

    started = time.perf_counter()
    routed = escalation_agent.run(_view(case))
    case.status = routed["status"]
    if case.sanctions_hit and case.status == "low":
        case.status = "sar_draft"
    _codes(case, routed.get("reason_codes"))
    case.audit_hash = log_action(
        case.case_id,
        "escalation_router",
        "route",
        {"risk": case.risk_score},
        {"status": case.status, "confidence": case.confidence},
        final=True,
        reason_codes=case.reason_codes,
    )
    record_trace(case.case_id, "escalation_router", (time.perf_counter() - started) * 1000, case.status)

    memory_write(
        case.case_id,
        " ".join(case.explanation) or query,
        {"summary": (case.explanation[0] if case.explanation else query)[:240], "status": case.status, "risk_score": case.risk_score},
    )

    response = CaseResponse(
        case_id=case.case_id,
        risk_score=case.risk_score,
        status=case.status,
        entities=case.entities,
        evidence=case.evidence,
        sar_draft=case.sar_draft,
        explanation=case.explanation,
        audit_hash=case.audit_hash,
        transactions=case.transactions,
        graph=case.graph,
        memory_hits=case.memory_hits,
        reason_codes=case.reason_codes,
        confidence=case.confidence,
        sanctions_hit=case.sanctions_hit,
    )
    save_case(response)
    save_working(case.case_id, response.model_dump(mode="json"))
    return response
