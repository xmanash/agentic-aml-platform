# Agentic AML — End-to-End Investigation Platform

Multi-agent system that ingests transactions/documents, performs continuous monitoring, runs investigations (entity linking, sanctions/watchlist checks, pattern analysis), generates SAR-style reports/alerts, and routes only high-risk cases to humans.

 Transaction Monitoring + basic KYC doc verification MVP with governance, audit, and human-in-the-loop.

The commands below run the **MVP now** local stack. Bank deployment requirements are the **Enterprise target** in [PRD.md](PRD.md) (Enterprise users and scope, Enterprise requirements) and [ARCHITECTURE.md](ARCHITECTURE.md) (Deployment, Security). `docker-compose.yml` is the local development stack.

## Shared console

https://administered-congressional-breathing-editor.trycloudflare.com

That address is a Cloudflare tunnel to the local review console. The console proxies `/api` to the API on this machine, so other people can open the same URL. It stays available only while this computer and the tunnel process are running. A new tunnel start issues a new address. The demo accepts the role from the client `X-Role` header.

## Quick Start (Local)

Environment variables come from `.env.example`. Copy that file to `.env` and fill the keys you have. Unset Supabase, Pinecone, and OpenAI keys fall back to local JSON, FAISS, and template text.

```bash
# from the repo root
cp .env.example .env

# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. Frontend (in another terminal)
cd frontend
npm install
npm run dev
# open http://localhost:3000
```

With Supabase or Pinecone, set `SUPABASE_URL`, `SUPABASE_KEY`, `PINECONE_API_KEY`, and `OPENAI_API_KEY` in `.env`. Empty keys fall back to local JSON under `data/local_db` and a local vector store.

Optional cloud setup, from the repo root after `.env` is filled:

```bash
python scripts/setup_supabase.py
python scripts/setup_pinecone.py && python scripts/seed_pinecone.py
```

Apply `supabase/migrations/001_initial_schema.sql` and `supabase/migrations/002_agent_traces.sql` in the Supabase SQL editor before the Supabase script. Pinecone setup creates four 1536-dimension indexes: `aml-entities`, `aml-cases`, `aml-adverse-media`, and `aml-documents`.

## What's Inside

- **Seven investigation agents, plus the Optimization Agent**: Ingestion/OCR, Entity Resolution, Pattern/Anomaly, Sanctions/Watchlist, Investigation Summarizer, Report Generator, and Escalation Router. The Optimization Agent tunes thresholds from human feedback inside the governance bound.
- **Orchestration**: LangGraph-style state machine with shared memory/context (`backend/app/orchestration/graph.py`)
- **MCP Integration**: `mcp_servers/` exposes tools for transaction feed, document store, sanctions API
- **Memory**: Supabase (postgres) for long-term, Redis for short-term, Pinecone for semantic case memory. See [MEMORY.md](MEMORY.md) for the local fallback and the enterprise `tenant_id` keys.
- **Guardrails**: PII minimization, immutable audit log, explainability, human feedback loop. See [GUARDRAILS.md](GUARDRAILS.md) for what is implemented and for the enterprise control section.
- **UI**: Next.js 14 and Tailwind, with Recharts and an inline entity graph: live case list, risk chart, SAR draft viewer, human review
- **Evals**: Precision/recall harness on the seeded 200-case file. Enterprise release gates are in [EVALS.md](EVALS.md).

See `PRD.md`, `ARCHITECTURE.md`, `COMPONENTS.md`, `EVALS.md`, `GUARDRAILS.md`, `MEMORY.md`, `TESTS.md`
