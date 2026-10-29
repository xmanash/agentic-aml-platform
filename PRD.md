# PRD — Agentic AML Investigation Platform

Sections 1–6 are **MVP now**: what this repository runs. Sections 7–8 are the **Enterprise target**: what a bank deployment must meet. Those requirements are a deployment bar, and this repository does not implement them yet.

## 1. Core Concept
Agentic Compliance, KYC/AML & Transaction Monitoring Platform
Regulatory scrutiny is intensifying as agentic systems proliferate (cyber risk, herding, model drift, accountability). Banks and fintechs need agents that autonomously triage, investigate, document, and escalate while maintaining full auditability.
Multi-agent system that ingests transactions/documents, performs continuous monitoring, runs investigations (linking entities, checking sanctions/watchlists, analyzing patterns), generates SAR-style reports or alerts, and routes only high-risk cases to humans.

## 2. Problem
- Analysts drown in alerts (95%+ false positives)
- Siloed data: transactions, KYC docs, adverse media, sanctions
- No audit trail, weak regulatory defensibility

## 3. Users
- Compliance Analyst (primary)
- BSA Officer / MLRO
- Investigator
- Engineering / Ops

## 4. MVP Scope (per req doc)
Focus: Transaction monitoring + basic KYC doc verification for payments product.
- Ingest sample transaction streams + document uploads (passport, utility bill)
- Build 7 agents:
  1. Ingestion/OCR Agent
  2. Entity Resolution Agent
  3. Pattern/Anomaly Detection Agent
  4. Sanctions/Watchlist Checker Agent
  5. Investigation Summarizer Agent
  6. Report Generator Agent
  7. Escalation Router Agent
- Connect to policy rules + human review queue + full audit logs
- Evaluate precision/recall, false-positive reduction, time-to-resolution
- Add basic adaptive learning from human feedback (within governance bounds)

## 5. User Stories
- As analyst, I see only high-risk cases with explainable evidence graph
- As BSA officer, I can export SAR draft with immutable audit log
- As system, I auto-close low-risk, auto-escalate >85 risk score

## 6. Success Metrics
- Alert precision > 0.75 (MVP), recall > 0.85
- False positive reduction 60%+ vs rules-only
- Time-to-resolution < 15 min p50
- 100% audit log coverage, PII masked

## 7. Enterprise users and scope
**Enterprise target.**

The same analyst, investigator, and BSA Officer / MLRO, plus security and platform operations. The product monitors payments for more than one tenant. Live core-banking integration stays out of scope. Full model retraining stays out of scope. Per-tenant threshold tuning stays inside the existing 10 percent governance bound.

## 8. Enterprise requirements
**Enterprise target.** A bank deployment must meet all of the following.

- Ingest returns immediately with an idempotency key. The investigation runs on a queue.
- One tenant cannot read or tune another tenant’s cases, prompts, or thresholds.
- Identity comes from the bank identity provider. Roles are analyst, investigator, officer, and admin.
- Sanctions hits cannot auto-close. SAR drafts with fewer than two evidence citations stay non-filing.
- SLOs: ingest is accepted in under 1 second. A high-risk case is ready for review in under 15 minutes at p50. Queue lag is visible on health.
- Release gate: the eval harness must pass before promotion.

## 9. Differentiation for 2027
End-to-end agentic investigation with strong governance (not just alerts), reducing analyst workload while improving regulatory defensibility. Optimization Agent for self-tuning thresholds.
