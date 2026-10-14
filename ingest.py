"""Pipeline steps 2-5: load PDF -> split (clause-aware + RecursiveCharacterTextSplitter)
-> embed (BAAI/bge-small-en-v1.5) -> persist to Chroma. Also saves clauses to the JSON store.
Run:  python ingest.py            (ingests every PDF in data/contracts)"""
import sys
from pathlib import Path
import config, core, store

CHUNK_SIZE, CHUNK_OVERLAP = 900, 100

def get_vectorstore():
    from langchain_chroma import Chroma
    emb = config.get_embeddings()
    path = config.CHROMA_DIR / config.embeddings_name()      # one index per embedding model
    path.mkdir(parents=True, exist_ok=True)
    return Chroma(collection_name="contracts", embedding_function=emb, persist_directory=str(path))

def get_retriever(contract_id: str = "", k: int = 3):
    kwargs = {"k": k}
    if contract_id:
        kwargs["filter"] = {"contract_id": contract_id}
    return get_vectorstore().as_retriever(search_kwargs=kwargs)

def ingest_pdf(path) -> dict:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document

    path = Path(path)
    cid = path.stem
    pages = PyPDFLoader(str(path)).load()                       # 2. document loading
    text = "\n".join(p.page_content for p in pages)
    clauses = core.parse_clauses(text)
    if not clauses:
        raise ValueError(f"No readable text found in {path.name} (scanned PDF? needs OCR).")
    ctype = core.detect_type(text)

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    docs = []                                                    # 3. text splitting
    for c in clauses:                                            # clause boundary first,
        parts = splitter.split_text(c["text"]) if len(c["text"]) > CHUNK_SIZE else [c["text"]]
        for i, part in enumerate(parts):                         # size splitter only for long clauses
            docs.append(Document(page_content=f"[{cid} | Clause {c['no']}] {part}",
                                 metadata={"contract_id": cid, "clause": c["no"], "heading": c["heading"], "part": i}))
    vs = get_vectorstore()                                       # 4. embeddings + vector store
    try:
        vs._collection.delete(where={"contract_id": cid})        # re-ingest = replace
    except Exception:
        pass
    vs.add_documents(docs)

    data = store.load()
    data[cid] = {"type": ctype, "source": path.name, "clauses": clauses}
    store.save(data)
    return {"contract_id": cid, "type": ctype, "clauses": len(clauses), "chunks": len(docs)}

def ingest_folder(folder=None) -> list:
    folder = Path(folder or config.CONTRACTS_DIR)
    return [ingest_pdf(p) for p in sorted(folder.glob("*.pdf"))]

def _chunks_for(cid: str, clauses: list) -> list:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    docs = []
    for c in clauses:
        parts = splitter.split_text(c["text"]) if len(c["text"]) > CHUNK_SIZE else [c["text"]]
        for i, part in enumerate(parts):
            docs.append(Document(page_content=f"[{cid} | Clause {c['no']}] {part}",
                                 metadata={"contract_id": cid, "clause": c["no"], "heading": c["heading"], "part": i}))
    return docs

def rebuild_from_store():
    """Re-embed every stored contract (used when the embedding model changed)."""
    vs = get_vectorstore()
    for cid, rec in store.load().items():
        vs.add_documents(_chunks_for(cid, rec["clauses"]))

def ensure_index():
    """Called at app start: build the index once if nothing is ingested yet, or rebuild
    the vector index if it is empty for the active embedding model."""
    if not store.load():
        return ingest_folder()
    if get_vectorstore()._collection.count() == 0:
        rebuild_from_store()
    return []

if __name__ == "__main__":
    for r in ingest_folder(sys.argv[1] if len(sys.argv) > 1 else None):
        print(r)
