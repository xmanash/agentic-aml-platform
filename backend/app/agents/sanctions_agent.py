from typing import Any, Dict

from ..tools.access import field
from ..tools.rules import load_rules
from ..tools.sanctions_lookup import adverse_media_search, check_sanction


class SanctionsAgent:
    def run(self, state: Dict[str, Any]):
        evidence = []
        reason_codes = []
        seen = set()
        names = []
        for entity in state.get("entities") or []:
            name = field(entity, "name")
            if name:
                names.append(str(name))
        for tx in state.get("transactions") or []:
            name = field(tx, "counterparty")
            if name:
                names.append(str(name))

        hit = False
        for name in names:
            for match in check_sanction(name)["hits"]:
                key = match["name"].lower()
                if key in seen:
                    continue
                seen.add(key)
                hit = True
                evidence.append(
                    {
                        "source": "sanctions",
                        "description": f"Sanctions hit: {name} matches {match['name']} ({match.get('list')})",
                        "risk_weight": 50,
                        "data": {"sdn": match},
                    }
                )
        if hit:
            evidence.append(
                {
                    "source": "sanctions",
                    "description": "Sanctions hit cannot be auto-closed and requires analyst escalation",
                    "risk_weight": 50,
                    "data": {"policy": "no_auto_close"},
                }
            )
            reason_codes.extend(["SANCTIONS_HIT", "MUST_ESCALATE", "WATCHLIST_REVIEW"])

        media = adverse_media_search(" ".join(names))
        if media["articles"]:
            evidence.append(
                {
                    "source": "adverse_media",
                    "description": media["articles"][0]["title"],
                    "risk_weight": 20,
                    "data": {"articles": media["articles"]},
                }
            )
            reason_codes.append("ADVERSE_MEDIA")

        return {
            "evidence": evidence,
            "hit": hit,
            "reason_codes": reason_codes,
            "min_score": load_rules()["sanctions"]["min_score_on_hit"],
        }


sanctions_agent = SanctionsAgent()
