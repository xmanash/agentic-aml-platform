from typing import Any, Dict

from ..llm import generate
from ..tools.access import field
from ..tools.pii_masker import mask_pii


class SummarizerAgent:
    def run(self, state: Dict[str, Any]):
        risk = state.get("risk_score", 0)
        evidence = state.get("evidence") or []
        lines = [f"Risk score {risk}:"]
        for item in evidence:
            source = field(item, "source")
            description = field(item, "description")
            weight = field(item, "risk_weight")
            lines.append(f"- [{source}] {description} (weight {weight}) [Source: {source}]")
        if not evidence:
            lines.append("No significant patterns detected.")
        hits = state.get("memory_hits") or []
        if hits:
            refs = ", ".join(str(field(hit, "case_id")) for hit in hits[:3])
            lines.append(f"Similar prior cases: {refs}")
        fallback = "\n".join(lines)
        text, tokens = generate("narrative", fallback, fallback)
        if evidence and text.count("[Source:") < len(evidence):
            text, tokens = fallback, 0
        explanation = [mask_pii(line) for line in text.splitlines() if line.strip()]
        return {"explanation": explanation, "tokens": tokens}

    def chat(self, message: str):
        fallback = (
            f"Investigation Assistant: You asked '{message}'. "
            "I can run transaction analysis, entity linking, and sanctions checks. Use /ingest/transactions to start a case."
        )
        text, _tokens = generate("narrative", message, fallback)
        return mask_pii(text)


summarizer_agent = SummarizerAgent()
