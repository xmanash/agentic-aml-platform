# Memory Architecture

**MVP now** is the storage this repository uses. **Enterprise target** adds `tenant_id` to production keys and namespaces. Local JSON under `data/local_db` stays the offline fallback.

## Layers
1. **Short-term (Working Memory)**: In `CaseState` — current case transactions, entities, scores. Redis TTL 1h (`aml:case:{case_id}`), fallback InMemory dict.

2. **Long-term (Supabase Postgres)**:
   - `customers`, `accounts`, `transactions`, `entities`, `cases`, `kyc_documents`, `audit_logs`, `feedback`
   - Vector column for embeddings (pgvector) if Pinecone not used
   - Offline fallback: one JSON file per table under `data/local_db` (`backend/app/config.py`, `local_db_dir`)

3. **Semantic Memory (Pinecone)**:
   - Namespace `cases`: case embedding = summary + pattern features
   - Namespaces `entities` and `documents` for resolution and KYC text
   - Used for: similar case retrieval, entity resolution fuzzy match
   - Fallback: local FAISS in `backend/app/tools/vector_store.py`

4. **Episodic (Agent Traces)**:
   - Every agent run stored in `agent_traces` with latency, tokens, decisions
   - Table defined in `supabase/migrations/002_agent_traces.sql`: `case_id`, `agent`, `latency_ms`, `tokens`, `decision`, `created_at`
   - Offline fallback: `data/local_db/agent_traces.json`

## Shared Context Pattern
`AgentGraph` passes `CaseState`:
```python
class CaseState(BaseModel):
    case_id: str
    transactions: List[Transaction]
    entities: List[Entity]
    risk_score: float
    evidence: List[Evidence]
    memory_hits: List[SimilarCase]
```

## MCP Memory
MCP servers expose memory tools as `memory_search`, `memory_write`

## Optimization Agent Memory
Stores threshold adjustments, learns from human feedback: if analyst marks false positive, lower weight for that rule for that entity type (bounded).

## Tenant scope
**MVP now.** Redis keys and Pinecone namespaces do not include a tenant id. `data/local_db` is a directory of JSON files on the machine that runs the API. Those files are local disk. Each process that uses the fallback needs its own directory, because the files are not a shared store across replicas.

**Enterprise target.** Production Postgres keys, Redis working-memory keys, and Pinecone namespaces include `tenant_id`. Object-storage paths for KYC bytes include `tenant_id`. `data/local_db` and local FAISS remain the offline development fallback.
