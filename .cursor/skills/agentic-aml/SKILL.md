---
name: agentic-aml
description: >-
  Work on the agentic AML investigation platform. Use when editing this repo,
  its agents, orchestration, guardrails, evals, docs, or when the user mentions
  AML, SAR, sanctions, KYC, case review, or MVP versus enterprise.
---

# Agentic AML

## Read first

Read [context.md](context.md) before changing behavior, docs, or tests. Docs use two labels. Keep them separate.

- **MVP now**: what this repository runs.
- **Enterprise target**: what a bank deployment must meet. Do not implement it unless the user asks, and do not describe it as current behavior.

## Invariants already in code

- Sanctions hits cannot auto-close.
- A SAR draft with fewer than two evidence citations stays non-filing (`low_confidence`).
- Threshold shifts past 10% stay `pending_approval`. Model weights stay frozen.
- Mask PII in logs, traces, and public responses. Officer and admin are the privileged roles.
- Audit records stay an append-only hash chain.

## Where to change things

| Task | Start here |
| --- | --- |
| Investigation sequence | `backend/app/orchestration/graph.py` (`run_investigation`) |
| One agent | `backend/app/agents/` |
| API, CORS, `X-Role` | `backend/app/main.py` |
| PII | `backend/app/tools/pii_masker.py` |
| Audit chain | `backend/app/tools/audit.py` |
| Local persistence | `data/local_db` via `backend/app/config.py` |
| Review console | `frontend/app/page.tsx` |
| Evals | `backend/evals/run_evals.py`, `data/eval/labeled_cases.csv` (200 cases) |

## Checks

- `pytest backend/tests -v`
- `python backend/evals/run_evals.py` when metrics or the dataset change

Auth, tenant isolation, and queue acceptance are future enterprise tests. Do not list them as existing tests.
