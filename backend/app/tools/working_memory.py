import json

from .. import config
from .jsonutil import json_safe

_memory = {}
_redis = None
_redis_failed = False


def _client():
    global _redis, _redis_failed
    if _redis_failed or not config.REDIS_URL:
        return None
    if _redis is not None:
        return _redis
    try:
        import redis

        client = redis.Redis.from_url(config.REDIS_URL, socket_connect_timeout=0.3)
        client.ping()
        _redis = client
        return client
    except Exception:
        _redis_failed = True
        return None


def save(case_id: str, payload: dict) -> None:
    safe = json_safe(payload)
    client = _client()
    if client is not None:
        try:
            client.setex(f"aml:case:{case_id}", 3600, json.dumps(safe))
            return
        except Exception:
            pass
    _memory[case_id] = safe


def load(case_id: str):
    client = _client()
    if client is not None:
        try:
            raw = client.get(f"aml:case:{case_id}")
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    return _memory.get(case_id)
