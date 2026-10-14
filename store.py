"""Tiny JSON store: contract_id -> {type, clauses}. The deterministic tools read the
contract from here, so the LLM never has to copy contract text into a tool call."""
import json
import config

def load() -> dict:
    if config.CLAUSES_JSON.exists():
        return json.loads(config.CLAUSES_JSON.read_text(encoding="utf-8"))
    return {}

def save(data: dict) -> None:
    config.STORE_DIR.mkdir(parents=True, exist_ok=True)
    config.CLAUSES_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def resolve_id(name: str):
    """Exact id, else unique case-insensitive substring match, else None."""
    data = load()
    if not name:
        return None
    if name in data:
        return name
    hits = [k for k in data if name.lower().strip() in k.lower()]
    return hits[0] if len(hits) == 1 else None
