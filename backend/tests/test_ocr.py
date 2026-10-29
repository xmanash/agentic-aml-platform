from pathlib import Path

from backend.app.tools.kyc import extract_kyc_bytes


def test_text_kyc_fixture():
    path = Path("data/eval/kyc_docs/passport_john.txt")
    result = extract_kyc_bytes(path.read_bytes(), path.name)
    assert result["extracted_fields"]["name"] == "John Smith"
    assert result["doc_type"] == "passport"
