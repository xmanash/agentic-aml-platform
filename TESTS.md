# Tests

**MVP now** is the suite under `backend/tests`. **Enterprise target** tests are listed at the end and are not in this repository yet.

Run: `pytest backend/tests -v`

## Unit
- `test_entity_resolution.py` — linking the same customer across accounts
- `test_sanctions_checker.py` — OFAC hit detection
- `test_pattern.py` — structuring pattern
- `test_ocr.py` — KYC extraction
- `test_audit_log.py` — hash chain integrity and PII masking
- `test_optimization.py` — threshold tuning stays inside the governance bound

## Integration
- `test_graph_e2e.py` — full case from ingest to escalation, including the sanctions auto-close gate
- `test_mcp_tools.py` — transaction feed, sanctions lookup, KYC text extraction, and memory round-trip

## Evals as Tests
- `test_precision_recall.py` — harness stays above the MVP precision, recall, and false-positive targets, with explainability and SAR citation checks

## Enterprise tests
**Enterprise target.** These are future tests for a bank deployment. They are not current tests.

- Authentication against the bank identity provider, with server-side roles (analyst, investigator, officer, admin)
- Tenant isolation: one tenant cannot read or tune another tenant’s cases, prompts, or thresholds
- Queue acceptance: ingest returns with an idempotency key before the investigation worker finishes
