from typing import Any, Dict

from ..tools.access import field
from ..tools.ids import stable_id
from ..tools.kyc import extract_kyc_bytes, extract_kyc_text


class IngestionAgent:
    def run(self, state: Dict[str, Any]):
        txs = state.get("transactions") or []
        docs = state.get("kyc_docs") or []
        entities = []
        seen = set()
        for doc in docs:
            text = field(doc, "content_text") or ""
            extracted = extract_kyc_text(text, f"{field(doc, 'doc_type') or 'kyc'}.txt")
            name = (extracted.get("extracted_fields") or {}).get("name")
            if name and name not in seen:
                seen.add(name)
                entities.append(
                    {
                        "entity_id": stable_id(name),
                        "type": "customer",
                        "name": name,
                        "linked_accounts": [],
                        "risk_score": 0,
                    }
                )
        return {"entities": entities, "ingested_count": len(txs), "reason_codes": ["INGESTED"], "tokens": 0}

    def extract_kyc(self, content: bytes, filename: str):
        return extract_kyc_bytes(content, filename)


ingestion_agent = IngestionAgent()
