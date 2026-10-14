"""Tiny offline bag-of-words embeddings. ONLY for tests / emergency offline fallback
(set EMBEDDINGS_BACKEND=hash). The real pipeline uses BAAI/bge-small-en-v1.5."""
import hashlib, math, re
from langchain_core.embeddings import Embeddings

DIM = 512

class HashEmbeddings(Embeddings):
    def _vec(self, text: str):
        v = [0.0] * DIM
        for w in re.findall(r"[a-z0-9]+", text.lower()):
            h = int(hashlib.md5(w.encode()).hexdigest(), 16)
            v[h % DIM] += 1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]
    def embed_documents(self, texts): return [self._vec(t) for t in texts]
    def embed_query(self, text): return self._vec(text)
