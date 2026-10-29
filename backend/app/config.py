import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

_HERE = Path(__file__).resolve()


def _find_root() -> Path:
    env = os.getenv("AML_ROOT")
    if env:
        return Path(env)
    for parent in _HERE.parents:
        if (parent / "PRD.md").exists() and (parent / "backend").exists():
            return parent
    return _HERE.parents[2]


if load_dotenv:
    for candidate in (Path.cwd(), _HERE.parents[1], _HERE.parents[2]):
        env_file = candidate / ".env"
        if env_file.exists():
            load_dotenv(env_file)

ROOT = _find_root()


def get_env(name: str, default: str = "") -> str:
    if name == "SUPABASE_KEY":
        return os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or default
    return os.getenv(name) or default


def data_dir() -> Path:
    override = os.getenv("AML_DATA_DIR")
    if override:
        return Path(override)
    return ROOT / "data"


def audit_dir() -> Path:
    override = os.getenv("AUDIT_DIR")
    if override:
        return Path(override)
    return data_dir() / "audit"


def local_db_dir() -> Path:
    return data_dir() / "local_db"


def vector_dir() -> Path:
    return data_dir() / "vector_store"


# Mutable aliases so tests can redirect storage without restarting the process.
DATA_DIR = data_dir()
AUDIT_DIR = audit_dir()
LOCAL_DB_DIR = local_db_dir()
VECTOR_DIR = vector_dir()

SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_KEY = get_env("SUPABASE_KEY")
PINECONE_API_KEY = get_env("PINECONE_API_KEY")
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
OPENAI_MODEL = get_env("OPENAI_MODEL", "gpt-4o-mini")
REDIS_URL = get_env("REDIS_URL")
EMBED_DIM = 1536
