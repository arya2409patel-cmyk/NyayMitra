"""Settings + model/embedding factories (step 1 of the pipeline: LLM setup)."""
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:                      # python-dotenv is optional
    load_dotenv = lambda *a, **k: None

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

MODEL_NAME = os.getenv("MODEL_NAME", "qwen3:0.6b")
EMBEDDINGS_BACKEND = os.getenv("EMBEDDINGS_BACKEND", "auto")   # auto = hf -> ollama -> hash
MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:8001/mcp")
CONTRACTS_DIR = ROOT / "data" / "contracts"
STORE_DIR = Path(os.getenv("STORE_DIR", ROOT / "store"))
CHROMA_DIR = STORE_DIR / "chroma"
CLAUSES_JSON = STORE_DIR / "contracts.json"

DISCLAIMER = ("This is not legal advice. NyayMitra is a review aid, not a lawyer. "
              "Please have a licensed lawyer review before you sign. Free legal aid may be "
              "available through your District Legal Services Authority.")

def get_llm():
    from langchain_ollama import ChatOllama
    return ChatOllama(model=MODEL_NAME, temperature=0)

_EMB = None
_EMB_NAME = None

def _make(name):
    if name == "hf":
        from langchain_huggingface import HuggingFaceEmbeddings
        emb = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5",
                                    encode_kwargs={"normalize_embeddings": True})
    elif name == "ollama":
        from langchain_ollama import OllamaEmbeddings
        emb = OllamaEmbeddings(model="nomic-embed-text")
    elif name == "hash":
        from hash_embeddings import HashEmbeddings
        emb = HashEmbeddings()
    else:
        raise ValueError(f"unknown EMBEDDINGS_BACKEND '{name}'")
    emb.embed_query("probe")            # fail now (offline, model missing) instead of mid-demo
    return emb

def get_embeddings():
    """Embedding model, cached. 'auto' tries the HuggingFace bge model first, then Ollama's
    nomic-embed-text, then a tiny offline hash model (loud warning). An explicit backend
    in .env is used strictly and raises if it cannot load."""
    global _EMB, _EMB_NAME
    if _EMB is not None:
        return _EMB
    order = ["hf", "ollama", "hash"] if EMBEDDINGS_BACKEND == "auto" else [EMBEDDINGS_BACKEND]
    last = None
    for name in order:
        try:
            _EMB, _EMB_NAME = _make(name), name
            if name != order[0]:
                print(f"WARNING: embeddings fell back to '{name}' ({type(last).__name__}: {last})")
            return _EMB
        except Exception as e:
            last = e
    raise RuntimeError(f"No embedding backend could load. Last error: {last}")

def embeddings_name():
    get_embeddings()
    return _EMB_NAME

def llm_status() -> str:
    try:
        import ollama
        ollama.show(MODEL_NAME)
        return f"LLM `{MODEL_NAME}` is ready"
    except Exception as e:
        return f"LLM `{MODEL_NAME}` not reachable ({type(e).__name__}) - answers will use fallback mode"
