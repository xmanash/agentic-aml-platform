import json
from pathlib import Path

from . import config
from .tools.supabase_client import get_prompt_text

_PROMPTS = Path(__file__).resolve().parent / "prompts"


def load_prompt(name: str) -> str:
    custom = get_prompt_text(name)
    if custom:
        return custom
    path = _PROMPTS / f"{name}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Use only the facts in the user message."


def _client():
    if not config.OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI

        return OpenAI(api_key=config.OPENAI_API_KEY)
    except Exception:
        return None


def generate(agent: str, user: str, fallback: str) -> tuple[str, int]:
    client = _client()
    if client is None:
        return fallback, 0
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL or "gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": load_prompt(agent)},
                {"role": "user", "content": user},
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        tokens = 0
        if getattr(response, "usage", None) is not None:
            tokens = int(getattr(response.usage, "total_tokens", 0) or 0)
        if not text:
            return fallback, 0
        return text, tokens
    except Exception:
        return fallback, 0


def grounded(text: str, evidence: list) -> bool:
    if not text:
        return False
    cites = text.count("[Source:")
    needed = min(2, len(evidence)) if evidence else 0
    if cites < needed:
        return False
    if "human verification" not in text.lower():
        return False
    return True


def extract_kyc_fields(text: str) -> dict | None:
    client = _client()
    if client is None or not text:
        return None
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL or "gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": load_prompt("kyc_extract")},
                {"role": "user", "content": text[:4000]},
            ],
        )
        raw = (response.choices[0].message.content or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.replace("json", "", 1).strip()
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None
