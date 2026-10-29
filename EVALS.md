# AI Evals — Precision/Recall, False-Positive Reduction

**MVP now** is the harness in this repository. **Enterprise target** is the release gate a bank deployment must pass before promotion.

## Metrics
- Precision, Recall, F1 per alert type
- False Positive Rate reduction vs rules baseline
- Time-to-resolution
- SAR draft completeness (LLM-as-judge)

## Datasets
- `data/eval/labeled_cases.csv` — seeded 200 cases (structuring, velocity, layering, smurfing, sanctions, and legitimate activity). The harness writes this file from `backend/evals/dataset.py` and also writes `data/eval/cases.jsonl`.
- `data/eval/kyc_docs/` — sample passport and utility-bill texts. `backend/tests/test_ocr.py` reads the passport fixture.

## Harness
Run: `python backend/evals/run_evals.py`

Steps:
1. Rules-only baseline
2. Rules + ML + Agents
3. Agents + Human feedback (after 50 reviews)

Target MVP: Precision >=0.75, Recall >=0.85, FPR reduction 60%

## Adaptive Learning Eval
- Measure if feedback improves precision without catastrophic forgetting
- Guardrail: model weights frozen; only thresholds + prompts tuned (Optimization Agent)

## Explainability Eval
- Every high-risk case must have >=3 reason codes + evidence links

## Enterprise release gates
**Enterprise target.** Promotion requires the eval harness to pass, and the latency SLOs below to hold. `run_evals.py` checks precision, recall, false-positive reduction, and explainability. The latency SLOs are part of the same gate and are measured on the deployed queue, which this harness does not start.

- Precision >= 0.75
- Recall >= 0.85
- False-positive reduction >= 60% versus the rules-only baseline
- Explainability: every high-risk case has at least three reason codes and evidence links
- Latency SLOs from the PRD: ingest accepted in under 1 second; high-risk case ready for review in under 15 minutes at p50; queue lag visible on health
