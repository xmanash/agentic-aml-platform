# Guardrails

**MVP now** is the behavior in this repository. **Enterprise target** is section 8. A bank deployment must meet that section; the current API does not.

## 1. PII Minimization
Implemented in `backend/app/tools/pii_masker.py`.
- Mask SSN, email, card numbers, and account numbers in logs, traces, and public API responses unless the caller is a privileged role
- Privileged roles in the current masker are officer and admin
- Audit payloads and agent-trace decisions are passed through the masker before they are stored

## 2. Immutable Audit Log + Explainability
Implemented in `backend/app/tools/audit.py`.
- Append-only `audit_logs` table: case_id, agent, action, input_hash, output_hash, reason_codes, timestamp, prev_hash
- Hash chain verification endpoint `/audit/verify`

## 3. Governance Bounds for Adaptive Learning
- No direct model retraining in MVP; only threshold tuning and prompt versioning via Optimization Agent
- Human feedback requires second approver if it lowers threshold >10%
- The Optimization Agent records a shift past that bound as `pending_approval`
- All prompt changes versioned in `prompt_registry`

## 4. Hallucination Prevention
Implemented in `backend/app/agents/report_agent.py` and `run_investigation` in `backend/app/orchestration/graph.py`.
- SAR generator grounded only in retrieved evidence (RAG over case)
- Citations required; if fewer than 2 sources, the draft is withheld and confidence is `low_confidence` (non-filing)

## 5. Sanctions Safety
Implemented in `backend/app/agents/sanctions_agent.py` and `backend/app/agents/escalation_agent.py`.
- Sanctions checker never auto-closes on hit; must escalate

## 6. Access Controls
**MVP now.**
- The API reads a client-supplied `X-Role` header (`backend/app/main.py`) and uses it only to decide PII masking
- CORS allows every origin

## 7. Regulatory Defensibility
- Full lineage: transaction -> entity -> rule -> agent reasoning -> human decision
- That lineage is what the audit hash chain records for each case

## 8. Enterprise controls
**Enterprise target.** A bank deployment must meet all of the following.

- Identity comes from the bank identity provider. The API does not take the caller's role from a client header.
- Server-side authorization enforces the roles analyst, investigator, officer, and admin.
- Tenant filters apply to every read and write of cases, prompts, and thresholds. One tenant cannot read or tune another tenant's data.
- CORS is restricted to the review console origin.
- KYC uploads enforce a maximum size.
- Secrets are loaded from a secret manager.
- A scheduled job verifies the audit hash chain and alerts when the chain would fail `/audit/verify`.
