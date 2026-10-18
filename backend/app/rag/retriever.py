"""Retrieve top-k chunks for a query: hybrid vector + keyword (BM25) search.

The two rankings are fused with Reciprocal Rank Fusion (RRF), which needs
no score calibration between the two systems. Every returned hit carries a
true cosine ``distance`` to the query (computed for keyword-only hits too),
so the pipeline's weak-retrieval threshold keeps working unchanged.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from app.rag import keyword
from app.rag.embeddings import Embedder
from app.rag.vector_store import get_collection, query as vector_query

_RRF_K = 60          # standard RRF constant
_CANDIDATES = 3      # each system contributes k * _CANDIDATES candidates


def _distances_for(ids: List[str], q_vec: List[float]) -> Dict[str, float]:
    """Cosine distance from the query to stored chunks (embeddings are normalised)."""
    if not ids:
        return {}
    got = get_collection().get(ids=ids, include=["embeddings"])
    return {
        cid: 1.0 - float(sum(a * b for a, b in zip(q_vec, emb)))
        for cid, emb in zip(got["ids"], got["embeddings"])
    }


def retrieve(query: str, k: int = 5, where: Optional[Dict] = None) -> List[dict]:
    """Top-k chunks for ``query``, best first."""
    if not query.strip():
        return []
    q_vec = Embedder.embed_query(query)
    n = k * _CANDIDATES
    vec_hits = vector_query(q_vec, k=n, where=where)
    kw_hits = keyword.search(query, k=n, where=where)

    fused: Dict[str, dict] = {}
    scores: Dict[str, float] = {}
    for ranking in (vec_hits, kw_hits):
        for rank, hit in enumerate(ranking, start=1):
            scores[hit["id"]] = scores.get(hit["id"], 0.0) + 1.0 / (_RRF_K + rank)
            fused.setdefault(hit["id"], hit)

    top = sorted(scores, key=scores.get, reverse=True)[:k]
    missing = [cid for cid in top if "distance" not in fused[cid]]
    for cid, dist in _distances_for(missing, q_vec).items():
        fused[cid]["distance"] = dist
    return [
        {"id": cid, "text": fused[cid]["text"], "metadata": fused[cid]["metadata"],
         "distance": fused[cid].get("distance", 1.0)}
        for cid in top
    ]
