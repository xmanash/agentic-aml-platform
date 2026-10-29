import io

from .ids import stable_id
from ..llm import extract_kyc_fields


def _regex_name(text: str):
    import re

    match = re.search(r"Name[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)", text or "")
    return match.group(1) if match else None


def _read_text(content: bytes, filename: str) -> str:
    name = (filename or "").lower()
    if name.endswith(".txt") or name.endswith(".csv"):
        return content.decode("utf-8", errors="ignore")
    try:
        if name.endswith(".pdf"):
            import pdfplumber

            text = ""
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages[:3]:
                    text += page.extract_text() or ""
            return text
        from PIL import Image
        import pytesseract

        image = Image.open(io.BytesIO(content))
        return pytesseract.image_to_string(image)
    except Exception as exc:
        return f"OCR failed: {exc}. Using raw bytes length {len(content)}"


def extract_kyc_text(text: str, filename: str = "kyc.txt") -> dict:
    doc_type = "passport" if "passport" in (filename or "").lower() else "utility_bill"
    fields = extract_kyc_fields(text) or {}
    name = fields.get("name") or _regex_name(text)
    extracted = {
        "name": name,
        "doc_type": fields.get("doc_type") or doc_type,
        "document_number": fields.get("document_number"),
        "address": fields.get("address"),
    }
    result = {"text": (text or "")[:2000], "doc_type": extracted["doc_type"], "extracted_fields": extracted}
    _persist(filename, result)
    return result


def extract_kyc_bytes(content: bytes, filename: str) -> dict:
    text = _read_text(content, filename)
    return extract_kyc_text(text, filename)


def _persist(filename: str, result: dict) -> None:
    try:
        from .supabase_client import save_kyc_document
        from .vector_store import vector_store

        save_kyc_document(filename, result["doc_type"], result["text"], result["extracted_fields"])
        name = (result["extracted_fields"] or {}).get("name") or filename
        vector_store.upsert(
            stable_id(name),
            result["text"] or name,
            {"name": name, "filename": filename, "summary": (result["text"] or "")[:240]},
            namespace="documents",
        )
    except Exception:
        return
