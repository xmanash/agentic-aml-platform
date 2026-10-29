import uuid
from typing import Optional

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agents.ingestion_agent import ingestion_agent
from .agents.optimization_agent import optimization_agent
from .agents.summarizer_agent import summarizer_agent
from .models.schemas import CaseResponse, FeedbackIn, TransactionBatch
from .orchestration.graph import run_investigation
from .tools.audit import get_audit_logs, verify_chain
from .tools.pii_masker import redact_public_case
from .tools.supabase_client import get_case as fetch_case
from .tools.supabase_client import list_cases as fetch_cases
from .tools.supabase_client import save_feedback
from .tools.synthetic_generator import generate_transactions

app = FastAPI(title="Agentic AML Platform", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _public(result: CaseResponse, role: Optional[str]):
    return redact_public_case(result.model_dump(mode="json"), role)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Agentic AML Platform",
        "health": "/health",
        "docs": "/docs",
        "cases": "/cases",
        "console": "http://127.0.0.1:3000",
    }


@app.get("/health")
def health():
    return {"status": "ok", "agents": 8}


@app.post("/ingest/transactions")
def ingest_transactions(batch: TransactionBatch, x_role: Optional[str] = Header(default=None, alias="X-Role")):
    case_id = str(uuid.uuid4())
    result = run_investigation(case_id=case_id, transactions=batch.transactions, kyc_docs=batch.kyc_docs or [])
    return _public(result, x_role)


@app.post("/ingest/upload-kyc")
async def upload_kyc(file: UploadFile = File(...)):
    content = await file.read()
    extracted = ingestion_agent.extract_kyc(content, file.filename or "upload")
    return {"filename": file.filename, "extracted": extracted}


@app.get("/cases/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, x_role: Optional[str] = Header(default=None, alias="X-Role")):
    row = fetch_case(case_id)
    if not row:
        raise HTTPException(status_code=404, detail="case not found")
    return redact_public_case(row, x_role)


@app.get("/cases")
def list_cases(x_role: Optional[str] = Header(default=None, alias="X-Role")):
    return [redact_public_case(row, x_role) for row in fetch_cases()]


@app.post("/cases/{case_id}/feedback")
def feedback(case_id: str, body: FeedbackIn, x_role: Optional[str] = Header(default=None, alias="X-Role")):
    save_feedback(case_id, body.decision, body.notes, reviewer=x_role or "analyst")
    tuning = optimization_agent.learn_from_feedback(case_id, body.decision)
    return {"ok": True, "tuning": tuning}


@app.get("/synthetic/transactions")
def synthetic(n: int = 100):
    return generate_transactions(n)


@app.get("/audit/logs")
def audit_logs(case_id: str = None):
    return get_audit_logs(case_id)


@app.get("/audit/verify")
def audit_verify():
    return verify_chain()


class ChatReq(BaseModel):
    message: str


@app.post("/chat/investigate")
def chat_investigate(req: ChatReq):
    return {"response": summarizer_agent.chat(req.message)}
