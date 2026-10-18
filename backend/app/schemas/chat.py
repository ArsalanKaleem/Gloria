"""Chat API request and response schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: Optional[str] = None


class Source(BaseModel):
    title: str
    page: Optional[int] = None
    source_type: str = "university"      # "university" | "hec" | "structured"
    source_url: Optional[str] = None
    organization: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    conversation_id: Optional[str] = None
    sources: List[Source] = []


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    k: int = Field(default=5, ge=1, le=20)
    organization: Optional[str] = None


class SearchHit(BaseModel):
    text: str
    metadata: dict
    distance: float


class SearchResponse(BaseModel):
    hits: List[SearchHit]
