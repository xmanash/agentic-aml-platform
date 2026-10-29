from ..tools.rules import load_rules
from ..tools.supabase_client import get_applied_adjustments, save_threshold_adjustment


class OptimizationAgent:
    """Tune rule weights from human feedback. Model weights stay frozen."""

    def learn_from_feedback(self, case_id: str, decision: str):
        limit = float(load_rules()["thresholds"].get("max_threshold_shift", 0.10))
        if decision == "false_positive":
            delta = -0.05
        elif decision == "confirmed":
            delta = 0.02
        else:
            return {"status": "ignored"}
        delta = round(float(delta), 4)
        if abs(delta) > limit:
            save_threshold_adjustment(case_id, "pattern_weight", delta, status="pending_approval")
            return {"status": "pending_approval"}
        current = float(get_applied_adjustments().get("pattern_weight", 0.0))
        projected = round(current + delta, 4)
        if abs(projected) > limit + 1e-9:
            save_threshold_adjustment(case_id, "pattern_weight", delta, status="pending_approval")
            return {"status": "pending_approval"}
        save_threshold_adjustment(case_id, "pattern_weight", delta, status="applied")
        return {"status": "applied"}


optimization_agent = OptimizationAgent()
