"""BM25 keyword search over the chunks already stored in Chroma.

Embeddings are good at meaning but weak at exact tokens: person names
("Attaullah"), places ("Waikato"), codes ("CS-201"), phone numbers and
specific dates ("Spring 2026"). BM25 scores exact term overlap, so the
retriever fuses both rankings (see retriever.retrieve).

The index is built lazily from the Chroma collection on first use and is
rebuilt whenever the collection's size changes (i.e. after a reindex).
"""

from __future__ import annotations

import math
import re
import threading
from collections import Counter
from typing import Dict, List, Optional

from app.rag import vector_store

_TOKEN_RX = re.compile(r"[a-z0-9@.]+")
# Small stopword list: question words and fillers that carry no topic.
_STOPWORDS = {
    "a", "an", "the", "of", "for", "at", "in", "on", "to", "from", "by", "with",
    "is", "are", "was", "were", "be", "been", "am", "do", "does", "did", "can",
    "and", "or", "but", "not", "if", "it", "its", "this", "that", "there",
    "who", "what", "which", "when", "where", "why", "how",
    "i", "me", "my", "you", "your", "we", "our", "they", "their", "he", "his", "she", "her",
    "please", "tell", "give", "about", "any", "much", "many",
}
_K1, _B = 1.5, 0.75

_lock = threading.Lock()
_index: Optional[dict] = None


def _tokens(text: str) -> List[str]:
    out = []
    for tok in _TOKEN_RX.findall(text.lower()):
        tok = tok.strip(".")
        if tok and tok not in _STOPWORDS:
            out.append(tok)
    return out


def _build() -> dict:
    coll = vector_store.get_collection()
    got = coll.get(include=["documents", "metadatas"])
    ids, docs, metas = got["ids"], got["documents"], got["metadatas"]
    tfs = [Counter(_tokens(d or "")) for d in docs]
    lengths = [sum(tf.values()) for tf in tfs]
    df: Counter = Counter()
    for tf in tfs:
        df.update(tf.keys())
    n = len(docs)
    idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
    return {
        "count": n, "ids": ids, "docs": docs, "metas": metas, "tfs": tfs,
        "lengths": lengths, "avg_len": (sum(lengths) / n) if n else 0.0, "idf": idf,
    }


def _get_index() -> dict:
    global _index
    current = vector_store.count()
    with _lock:
        if _index is None or _index["count"] != current:
            _index = _build()
        return _index


def search(query: str, k: int = 10, where: Optional[Dict] = None) -> List[dict]:
    """Top-k chunks by BM25. ``where`` supports simple equality filters."""
    idx = _get_index()
    terms = set(_tokens(query))
    if not terms or not idx["count"]:
        return []
    scored = []
    for i, tf in enumerate(idx["tfs"]):
        if where and any(idx["metas"][i].get(key) != val for key, val in where.items()):
            continue
        score = 0.0
        norm = _K1 * (1 - _B + _B * idx["lengths"][i] / idx["avg_len"])
        for t in terms:
            f = tf.get(t)
            if f:
                score += idx["idf"][t] * f * (_K1 + 1) / (f + norm)
        if score > 0:
            scored.append((score, i))
    scored.sort(reverse=True)
    return [
        {"id": idx["ids"][i], "text": idx["docs"][i], "metadata": idx["metas"][i], "bm25": s}
        for s, i in scored[:k]
    ]
