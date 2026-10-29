import re

PRIVILEGED_ROLES = {"officer", "admin"}

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CARD = re.compile(r"\b\d{16}\b")
_ACC = re.compile(r"\bACC-\d+\b")
_LONG_NUM = re.compile(r"\b\d{9,}\b")


def is_privileged(role: str | None) -> bool:
    return (role or "").strip().lower() in PRIVILEGED_ROLES


def mask_pii(text: str) -> str:
    if text is None:
        return text
    text = str(text)
    text = _SSN.sub("***-**-****", text)
    text = _CARD.sub("**** **** **** ****", text)
    text = _EMAIL.sub("[email]", text)
    text = _ACC.sub("ACC-****", text)
    text = _LONG_NUM.sub("****", text)
    return text


def mask_name(name: str) -> str:
    parts = str(name).split()
    masked = []
    for part in parts:
        if len(part) <= 1:
            masked.append("*")
        else:
            masked.append(part[0] + ("*" * (len(part) - 1)))
    return " ".join(masked)


def mask_account(value: str) -> str:
    value = str(value)
    match = re.fullmatch(r"ACC-(\d+)", value)
    if match:
        return f"ACC-****{match.group(1)[-2:]}"
    if re.fullmatch(r"\d{9,}", value):
        return "****" + value[-2:]
    return value


def mask_customer(value: str) -> str:
    value = str(value)
    if value.startswith("CUST-"):
        return "CUST-****" + value[-2:]
    return mask_name(value)


def mask_obj(obj, key: str = ""):
    if isinstance(obj, dict):
        return {k: mask_obj(v, str(k)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [mask_obj(v, key) for v in obj]
    if isinstance(obj, str):
        if "dob" in key.lower() or "date_of_birth" in key.lower():
            return "****-**-**"
        return mask_pii(obj)
    if isinstance(obj, (int, float, bool)) or obj is None:
        return obj
    return mask_pii(str(obj))


def redact_public_case(data: dict, role: str | None) -> dict:
    if is_privileged(role):
        return data
    replacements = {}

    def remember(raw, masked):
        if raw and raw != masked:
            replacements[str(raw)] = masked

    for entity in data.get("entities") or []:
        if not isinstance(entity, dict):
            continue
        remember(entity.get("name"), mask_name(entity.get("name") or ""))
        for account in entity.get("linked_accounts") or []:
            remember(account, mask_account(account))
    for tx in data.get("transactions") or []:
        if not isinstance(tx, dict):
            continue
        if tx.get("account_id"):
            remember(tx["account_id"], mask_account(tx["account_id"]))
        if tx.get("customer_id"):
            remember(tx["customer_id"], mask_customer(tx["customer_id"]))
        if tx.get("counterparty"):
            remember(tx["counterparty"], mask_name(tx["counterparty"]))

    ordered = sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True)

    def apply(text: str) -> str:
        updated = str(text)
        for src, dst in ordered:
            updated = updated.replace(src, dst)
        return mask_pii(updated)

    def walk(value):
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, str):
            return apply(value)
        return value

    redacted = walk(data)
    for entity in redacted.get("entities") or []:
        if isinstance(entity, dict) and entity.get("name"):
            entity["name"] = mask_name(entity["name"]) if "*" not in entity["name"] else entity["name"]
    graph = redacted.get("graph") or {}
    id_map = {}
    for node in graph.get("nodes") or []:
        if isinstance(node, dict) and "id" in node:
            original = str(node["id"])
            masked = apply(original)
            id_map[original] = masked
            node["id"] = masked
    for link in (graph.get("links") or []) + (graph.get("edges") or []):
        if not isinstance(link, dict):
            continue
        for end in ("source", "target"):
            if end in link:
                link[end] = id_map.get(str(link[end]), apply(str(link[end])))
    return redacted
