"""Vector-side tools: search across indexed documents."""

from __future__ import annotations

from typing import List, Optional

from app.config import settings
from app.rag.retriever import retrieve


def search_documents(query: str, organization: Optional[str] = None, k: int = 5) -> List[dict]:
    where = {"organization": organization} if organization else None
    return retrieve(query, k=k, where=where)


def search_hec(query: str, k: int = 5) -> List[dict]:
    return search_documents(query, organization="HEC", k=k)


def search_university(query: str, k: int = 5) -> List[dict]:
    return search_documents(query, organization=settings.UNIVERSITY_NAME, k=k)
