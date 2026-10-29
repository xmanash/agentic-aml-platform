from backend.evals.run_evals import compute_metrics


def test_precision_recall_targets():
    metrics = compute_metrics(write=True)
    assert metrics["agent"]["precision"] >= 0.75, metrics
    assert metrics["agent"]["recall"] >= 0.85, metrics
    assert metrics["fpr_reduction"] >= 0.60, metrics
    assert metrics["explainability_failures"] == [], metrics
    assert metrics["sar_failures"] == [], metrics
