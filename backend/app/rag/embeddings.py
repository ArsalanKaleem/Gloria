"""Sentence-Transformers embedder, cached as a class-level singleton.

For a hosted embedder later, swap the implementation but keep the interface:
    Embedder.embed(list[str]) -> list[list[float]]
"""

from __future__ import annotations

from typing import List

from app.config import settings


class Embedder:
    _model = None

    @classmethod
    def _get(cls):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return cls._model

    @classmethod
    def embed(cls, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = cls._get()
        vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [v.tolist() for v in vecs]

    @classmethod
    def embed_one(cls, text: str) -> List[float]:
        return cls.embed([text])[0]

    @classmethod
    def embed_query(cls, query: str) -> List[float]:
        """Embed a search query. BGE models expect an instruction prefix on
        queries (not on passages) for short-question-to-passage retrieval."""
        if "bge" in settings.EMBEDDING_MODEL.lower():
            query = _BGE_QUERY_INSTRUCTION + query
        return cls.embed_one(query)


_BGE_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
