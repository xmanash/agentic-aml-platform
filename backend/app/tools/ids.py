import hashlib


def stable_id(name: str) -> str:
    digest = hashlib.sha256(name.strip().lower().encode()).hexdigest()[:12]
    return f"ent-{digest}"
