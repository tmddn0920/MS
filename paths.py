import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent

DATABASE_DIR = ROOT / "database"
PRODUCTS_PATH = DATABASE_DIR / "mcm_products_v2.json"

RAG_DIR = ROOT / "rag"
RAG_DOCUMENTS_PATH = RAG_DIR / "documents.jsonl"

VECTOR_DB_DIR = ROOT / "vector_db"
VECTOR_DOCUMENTS_PATH = VECTOR_DB_DIR / "documents.json"
VECTOR_INDEX_PATH = VECTOR_DB_DIR / "index.faiss"

CONFIG_DIR = ROOT / "config"
OPENAI_CONFIG_PATH = CONFIG_DIR / "openai_config.json"


def load_products():
    with PRODUCTS_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        return data.get("products", [])

    return data
