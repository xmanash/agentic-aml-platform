import json
from datetime import datetime, date


def json_safe(obj):
    if hasattr(obj, "model_dump"):
        return json_safe(obj.model_dump(mode="json"))
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if hasattr(obj, "item"):
        try:
            return json_safe(obj.item())
        except Exception:
            pass
    return str(obj)


def canonical(obj) -> str:
    return json.dumps(json_safe(obj), sort_keys=True, default=str)
