# Agentic AML context

Payments transaction monitoring plus basic KYC verification. Seven investigation agents run in order inside one API request, then the Optimization Agent tunes thresholds from human feedback.

## Agents

`run_investigation` in `backend/app/orchestration/graph.py` calls:

1. Ingestion / OCR (`ingestion_agent`)
2. Entity resolution (`entity_resolution_agent`)
3. Pattern / anomaly (`pattern_agent`) — YAML rules plus IsolationForest
4. Sanctions (`sanctions_agent`) — OFAC SDN mock CSV, including UN program names
5. Summarizer (`summarizer_agent`)
6. Report generator (`report_agent`)
7. Escalation router (`escalation_agent`)

`optimization_agent` is separate. It adjusts `pattern_weight` only.

## MVP now

- Ingest calls `run_investigation` before the HTTP response returns. There is no case queue and no idempotency key.
- `backend/app/main.py` trusts the client `X-Role` header and sets CORS `allow_origins=["*"]`.
- OCR is Tesseract. LSTM, Azure Document Intelligence, and live Dow Jones are named in the architecture as target adapters only.
- Postgres is optional through Supabase. The offline store is JSON in `data/local_db`. That directory is local disk and is not shared across replicas.
- Redis key `aml:case:{case_id}` has a 1-hour TTL. Pinecone namespaces are `cases`, `entities`, and `documents`, with a FAISS fallback. Keys do not include `tenant_id`.
- `agent_traces` is defined in `supabase/migrations/002_agent_traces.sql`. The local file is `data/local_db/agent_traces.json`.
- The console is Next.js 14, TypeScript, and Tailwind, with Recharts and an inline SVG entity graph in `frontend/app/page.tsx`.
- `docker-compose.yml` runs the API, frontend, Postgres, and Redis for local development.
- MCP tools under `mcp_servers/` are local stdio servers. The same functions live in `backend/app/tools/`.
- Eval data is the seeded 200-case file `data/eval/labeled_cases.csv`. MVP targets: precision >= 0.75, recall >= 0.85, false-positive reduction >= 60%.

## Enterprise target

Specified in `PRD.md` sections 7–8 and in the Deployment and Security sections of `ARCHITECTURE.md`. A bank deployment must:

- Accept ingest in under 1 second with an idempotency key, and run investigation on a queue. High-risk cases are ready for review in under 15 minutes at p50. Queue lag shows on health.
- Take identity from the bank IdP. Roles: analyst, investigator, officer, admin. Authorize on the server.
- Isolate tenants so one tenant cannot read or tune another tenant's cases, prompts, or thresholds. Production keys and Pinecone namespaces include `tenant_id`.
- Restrict CORS to the review console, limit KYC upload size, load secrets from a secret manager, and schedule an audit-chain check.
- Pass the eval harness before promotion, including the latency SLOs.

Live core banking and model retraining stay out of scope. Per-tenant threshold tuning stays inside the 10% bound.

## Tests that exist

`backend/tests/`: `test_entity_resolution.py`, `test_sanctions_checker.py`, `test_pattern.py`, `test_ocr.py`, `test_audit_log.py`, `test_optimization.py`, `test_graph_e2e.py`, `test_mcp_tools.py`, `test_precision_recall.py`.

## Doc map

`PRD.md`, `ARCHITECTURE.md`, `GUARDRAILS.md`, `MEMORY.md`, `COMPONENTS.md`, `EVALS.md`, `TESTS.md`, `README.md`.
