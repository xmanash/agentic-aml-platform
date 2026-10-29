from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Transaction(BaseModel):
    transaction_id: str
    account_id: str
    customer_id: Optional[str] = None
    amount: float
    currency: str = "USD"
    timestamp: datetime
    counterparty: Optional[str] = None
    channel: str = "payments"
    type: str = "transfer"


class KYCDoc(BaseModel):
    doc_type: str  # passport, utility_bill
    content_text: Optional[str] = None
    image_url: Optional[str] = None


class TransactionBatch(BaseModel):
    transactions: List[Transaction]
    kyc_docs: Optional[List[KYCDoc]] = None


class Evidence(BaseModel):
    source: str
    description: str
    risk_weight: float
    data: Dict[str, Any] = Field(default_factory=dict)


class Entity(BaseModel):
    entity_id: str
    type: str
    name: str
    linked_accounts: List[str] = Field(default_factory=list)
    risk_score: float = 0


class SimilarCase(BaseModel):
    case_id: str
    similarity: float
    summary: str = ""


class FeedbackIn(BaseModel):
    decision: str
    notes: str = ""


class CaseState(BaseModel):
    case_id: str
    transactions: List[Transaction] = Field(default_factory=list)
    kyc_docs: List[KYCDoc] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    risk_score: float = 0
    reason_codes: List[str] = Field(default_factory=list)
    memory_hits: List[SimilarCase] = Field(default_factory=list)
    graph: Dict[str, Any] = Field(default_factory=dict)
    explanation: List[str] = Field(default_factory=list)
    sar_draft: Optional[str] = None
    confidence: str = "high"
    status: str = "open"
    sanctions_hit: bool = False
    audit_hash: str = ""


class CaseResponse(BaseModel):
    case_id: str
    risk_score: float
    status: str  # low, escalated, sar_draft
    entities: List[Entity]
    evidence: List[Evidence]
    sar_draft: Optional[str] = None
    explanation: List[str] = Field(default_factory=list)
    audit_hash: str
    transactions: List[Transaction] = Field(default_factory=list)
    graph: Dict[str, Any] = Field(default_factory=dict)
    memory_hits: List[SimilarCase] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    confidence: str = "high"
    sanctions_hit: bool = False
