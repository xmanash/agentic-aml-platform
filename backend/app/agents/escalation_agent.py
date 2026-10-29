from typing import Any, Dict

from ..tools.access import field
from ..tools.rules import load_rules


class EscalationAgent:
    def run(self, state: Dict[str, Any]):
        rules = load_rules()["thresholds"]
        risk = float(state.get("risk_score") or 0)
        evidence = state.get("evidence") or []
        sanctions_hit = bool(state.get("sanctions_hit")) or any(field(item, "source") == "sanctions" for item in evidence)
        if sanctions_hit or risk >= float(rules["auto_escalate"]):
            status = "sar_draft"
        elif risk >= float(rules["escalate"]):
            status = "escalated"
        else:
            status = "low"
        if sanctions_hit and status == "low":
            status = "sar_draft"
        return {"status": status, "reason_codes": [f"ROUTE_{status.upper()}"]}


escalation_agent = EscalationAgent()
