import json

from backend.app.agents.optimization_agent import optimization_agent
from backend.app.tools.supabase_client import get_applied_adjustments


def test_cumulative_shift_requires_approval(monkeypatch, tmp_path):
    monkeypatch.setattr("backend.app.config.LOCAL_DB_DIR", tmp_path)
    assert optimization_agent.learn_from_feedback("c1", "false_positive")["status"] == "applied"
    assert optimization_agent.learn_from_feedback("c2", "false_positive")["status"] == "applied"
    assert optimization_agent.learn_from_feedback("c3", "false_positive")["status"] == "pending_approval"
    assert get_applied_adjustments()["pattern_weight"] == -0.1
    rows = json.loads((tmp_path / "thresholds.json").read_text(encoding="utf-8"))
    assert sum(1 for row in rows if row["status"] == "applied") == 2
    assert any(row["status"] == "pending_approval" for row in rows)
