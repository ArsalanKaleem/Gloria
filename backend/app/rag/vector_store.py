"""ChromaDB persistent vector store wrapper."""

from __future__ import annotations

from typing import Dict, List, Optional

import chromadb

from app.config import settings


_client = None
_collection = None


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
    return _client


def get_collection():
    """Get or create the Gloria collection."""
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add(
    ids: List[str],
    documents: List[str],
    embeddings: List[List[float]],
    metadatas: List[dict],
) -> None:
    """Upsert a batch into the collection."""
    coll = get_collection()
    coll.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def query(
    embedding: List[float],
    k: int = 5,
    where: Optional[Dict] = None,
) -> List[dict]:
    """Query the collection. Returns a list of hit dicts.

    Each hit: {"id", "text", "metadata", "distance"}
    """
    coll = get_collection()
    kwargs = {
        "query_embeddings": [embedding],
        "n_results": k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    res = coll.query(**kwargs)
    hits: List[dict] = []
    ids = (res.get("ids") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    for i in range(len(ids)):
        hits.append({
            "id": ids[i],
            "text": docs[i] if i < len(docs) else "",
            "metadata": metas[i] if i < len(metas) else {},
            "distance": float(dists[i]) if i < len(dists) else 1.0,
        })
    return hits


def count() -> int:
    return get_collection().count()


def delete_where(where: Dict) -> None:
    get_collection().delete(where=where)
