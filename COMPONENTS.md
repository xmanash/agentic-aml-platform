# Components Required — Affordable Stack

**MVP now** is the stack this repository runs. **Enterprise target** lists the extra components a bank deployment must add.

## Backend (Python)
- FastAPI, Uvicorn
- Pydantic v2
- LangChain / LangGraph (orchestration)
- python-multipart, pdfplumber, pytesseract, Pillow
- NetworkX for graph
- scikit-learn, pandas, numpy
- Supabase Python SDK when `SUPABASE_URL` is set; otherwise JSON files under `data/local_db`
- Pinecone client (optional, fallback to local FAISS)
- Redis client (optional fallback InMemory)
- MCP SDK: `mcp` package

## Frontend
- Next.js 14, TypeScript, Tailwind CSS
- Recharts for the risk chart
- Inline SVG entity graph in `frontend/app/page.tsx`

## Infra / Affordable
- **Supabase**: Free tier — Postgres + Auth + Storage for docs
- **Pinecone**: Free tier 1 index for semantic memory
- **MCP**: Local stdio servers (no cost)
- **OpenAI / Anthropic**: LLM for extraction/summarization (use gpt-4o-mini for cost)
- **Docker Compose** for local dev (`docker-compose.yml`). That file is the local development stack.

## MCP Tools
- `transaction_feed`: get_transactions, stream_transactions
- `document_store`: upload_doc, extract_kyc
- `sanctions_api`: check_sanction, adverse_media_search

## Data Sources (MVP)
- Transaction data: synthetic generator (`backend/app/tools/synthetic_generator.py`) + public anonymized sets
- KYC: Passports, utility bills — public templates + synthetic
- Sanctions: OFAC SDN CSV, UN list, commercial mock
- Public records, news, adverse media — NewsAPI stub
- Historical labeled fraud/AML cases for eval — CSV in `data/eval/labeled_cases.csv` (200 seeded cases)

## Integration Stubs
- Core banking/payment system adapter interface

## Enterprise target
A bank deployment adds these components. They are not in the current Compose stack.

- **Case queue** between the ingest API and investigation workers
- **Bank identity provider** for analyst, investigator, officer, and admin
- **Object storage** for KYC bytes (Postgres remains the system of record for case data)
- **Secret manager** for API keys and database credentials
- **LLM gateway** in front of model providers
