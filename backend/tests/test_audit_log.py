import json

from backend.app.tools.audit import get_audit_logs, log_action, verify_chain


def test_hash_chain_and_pii(monkeypatch, tmp_path):
    monkeypatch.setattr("backend.app.config.AUDIT_DIR", tmp_path)
    first = log_action("audit-case", "pattern_agent", "score", {"note": "ssn 123-45-6789 email a@b.co"}, {"ok": True}, reason_codes=["STRUCTURING"])
    second = log_action("audit-case", "sanctions_agent", "check", {"account": "ACC-1000"}, {"hit": False}, reason_codes=["WATCHLIST_REVIEW"])
    assert len(first) == 64
    assert len(second) == 64
    logs = get_audit_logs("audit-case")
    assert logs[1]["prev_hash"] == first
    assert logs[1]["hash"] == second
    assert "123-45-6789" not in json.dumps(logs)
    assert "a@b.co" not in json.dumps(logs)
    assert "ACC-1000" not in json.dumps(logs)
    assert verify_chain()["valid"] is True

    path = tmp_path / "chain.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows[1]["reason_codes"] = ["TAMPERED"]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    broken = verify_chain()
    assert broken["valid"] is False
