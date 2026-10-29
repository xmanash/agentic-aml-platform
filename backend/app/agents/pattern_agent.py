from collections import defaultdict
from typing import Any, Dict

from ..tools.access import field
from ..tools.rules import load_rules


class PatternAgent:
    def run(self, state: Dict[str, Any]):
        from ..tools.supabase_client import get_applied_adjustments

        rules = load_rules()
        factor = 1 + float(get_applied_adjustments().get("pattern_weight", 0.0))
        txs = state.get("transactions") or []
        evidence = []
        reason_codes = []
        score = float(rules.get("base_score", 10))
        amounts = [float(field(tx, "amount") or 0) for tx in txs]

        structuring = rules["structuring"]
        structuring_count = sum(1 for amount in amounts if structuring["min_amount"] <= amount <= structuring["max_amount"])
        if structuring_count >= structuring["min_count"]:
            weight = structuring["weight"] * factor
            evidence.append(
                {
                    "source": "pattern",
                    "description": f"Structuring detected: {structuring_count} transactions in the reporting band",
                    "risk_weight": weight,
                    "data": {"count": structuring_count},
                }
            )
            reason_codes.append(structuring["reason_code"])
            score += weight

        velocity = rules["velocity"]
        grouped = defaultdict(list)
        for tx in txs:
            grouped[field(tx, "account_id")].append(tx)
        for account, rows in grouped.items():
            total = sum(float(field(tx, "amount") or 0) for tx in rows)
            if len(rows) >= velocity["min_count"] and total >= velocity["min_sum"]:
                weight = velocity["weight"] * factor
                evidence.append(
                    {
                        "source": "pattern",
                        "description": f"High velocity account {account}: {len(rows)} transactions",
                        "risk_weight": weight,
                        "data": {"account": account, "count": len(rows), "total": total},
                    }
                )
                reason_codes.append(velocity["reason_code"])
                score += weight

        smurfing = rules["smurfing"]
        small = [amount for amount in amounts if amount <= smurfing["max_amount"]]
        if len(small) >= smurfing["min_count"] and sum(small) >= smurfing["min_sum"]:
            weight = smurfing["weight"] * factor
            evidence.append(
                {
                    "source": "pattern",
                    "description": f"Smurfing pattern: {len(small)} sub-threshold payments",
                    "risk_weight": weight,
                    "data": {"count": len(small), "total": sum(small)},
                }
            )
            reason_codes.append(smurfing["reason_code"])
            score += weight

        layering = rules["layering"]
        for entity in state.get("entities") or []:
            linked = field(entity, "linked_accounts") or []
            if len(linked) >= layering["min_linked_accounts"]:
                weight = layering["weight"] * factor
                evidence.append(
                    {
                        "source": "pattern",
                        "description": f"Layering across {len(linked)} linked accounts",
                        "risk_weight": weight,
                        "data": {"accounts": linked},
                    }
                )
                reason_codes.append(layering["reason_code"])
                score += weight
                break

        ml = rules["ml_anomaly"]
        if len(amounts) >= ml["min_samples"]:
            try:
                import numpy as np
                from sklearn.ensemble import IsolationForest

                model = IsolationForest(contamination=ml["contamination"], random_state=42)
                predictions = model.fit_predict(np.array(amounts).reshape(-1, 1))
                anomalies = int((predictions == -1).sum())
                if anomalies > 0:
                    weight = ml["weight"] * factor
                    evidence.append(
                        {
                            "source": "ml_anomaly",
                            "description": f"ML detected {anomalies} anomalous amounts",
                            "risk_weight": weight,
                            "data": {"anom": anomalies},
                        }
                    )
                    reason_codes.append(ml["reason_code"])
                    score += weight
            except Exception:
                pass

        return {"risk_score": float(min(100, score)), "evidence": evidence, "reason_codes": reason_codes}


pattern_agent = PatternAgent()
