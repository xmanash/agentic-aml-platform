from backend.app.tools.kyc import extract_kyc_text
from backend.app.tools.memory_tools import memory_search, memory_write
from backend.app.tools.sanctions_lookup import check_sanction
from backend.app.tools.transactions import get_transactions, stream_transactions


def test_transaction_and_sanctions_tools():
    rows = get_transactions("ACC-MISSING", limit=5)
    assert isinstance(rows, list)
    assert len(rows) <= 5
    assert "status" in stream_transactions()
    assert check_sanction("Bad Actor LLC")["hits"]


def test_memory_roundtrip():
    text = "structuring pattern repeated cash deposits unique-token-aml"
    memory_write("mem-test-1", text, {"summary": text})
    hits = memory_search(text, top_k=5)
    assert any(hit["id"] == "mem-test-1" for hit in hits)


def test_kyc_text_extract():
    extracted = extract_kyc_text("Name: John Smith Passport No: X123", "passport.txt")
    assert extracted["extracted_fields"]["name"] == "John Smith"
