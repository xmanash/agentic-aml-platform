from difflib import SequenceMatcher
from typing import Any, Dict

import networkx as nx

from ..tools.access import field
from ..tools.ids import stable_id
from ..tools.vector_store import vector_store


class EntityResolutionAgent:
    def run(self, state: Dict[str, Any]):
        txs = state.get("transactions") or []
        graph = nx.Graph()
        for tx in txs:
            account = field(tx, "account_id")
            customer = field(tx, "customer_id")
            counterparty = field(tx, "counterparty")
            if account:
                graph.add_node(account, type="account")
            if customer:
                graph.add_node(customer, type="customer")
                if account:
                    graph.add_edge(account, customer)
            if counterparty:
                graph.add_node(counterparty, type="counterparty")
                if account:
                    graph.add_edge(account, counterparty)

        for existing in state.get("entities") or []:
            name = field(existing, "name")
            if name and name != "Unknown":
                graph.add_node(name, type="customer")

        entities = []
        evidence = []
        reason_codes = []
        accounts = {field(tx, "account_id") for tx in txs if field(tx, "account_id")}
        for component in nx.connected_components(graph):
            customers = sorted(node for node in component if graph.nodes[node].get("type") == "customer")
            counterparties = sorted(node for node in component if graph.nodes[node].get("type") == "counterparty")
            linked = sorted(node for node in component if graph.nodes[node].get("type") == "account")
            name = customers[0] if customers else (counterparties[0] if counterparties else sorted(component)[0])
            entities.append(
                {
                    "entity_id": stable_id(str(name)),
                    "type": "cluster",
                    "name": str(name),
                    "linked_accounts": linked,
                    "risk_score": 10,
                }
            )

        if entities and len(entities) < len(accounts):
            evidence.append(
                {
                    "source": "entity_resolution",
                    "description": "Multiple accounts linked to the same entity",
                    "risk_weight": 15,
                    "data": {"clusters": len(entities)},
                }
            )
            reason_codes.append("MULTI_ACCOUNT")

        for entity in entities:
            self._fuzzy(entity["name"], evidence, reason_codes)

        payload = nx.node_link_data(graph)
        if "edges" in payload and "links" not in payload:
            payload["links"] = payload["edges"]
        return {"entities": entities, "graph": payload, "evidence": evidence, "reason_codes": reason_codes}

    def _fuzzy(self, name: str, evidence: list, reason_codes: list) -> None:
        if not name or name.startswith("ACC-") or name.startswith("CUST-"):
            return
        try:
            hits = vector_store.query(name, top_k=3, namespace="entities")
        except Exception:
            return
        for hit in hits:
            matched = (hit.get("metadata") or {}).get("name") or ""
            if not matched or matched.lower() == name.lower():
                continue
            ratio = SequenceMatcher(None, name.lower(), matched.lower()).ratio()
            if float(hit.get("score") or 0) >= 0.80 and ratio >= 0.86:
                evidence.append(
                    {
                        "source": "entity_resolution",
                        "description": f"Fuzzy name match {name} ~ {matched}",
                        "risk_weight": 10,
                        "data": {"query": name, "match": matched, "score": hit.get("score"), "ratio": round(ratio, 3)},
                    }
                )
                if "FUZZY_ENTITY" not in reason_codes:
                    reason_codes.append("FUZZY_ENTITY")
                break


entity_resolution_agent = EntityResolutionAgent()
