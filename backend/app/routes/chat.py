"""/v1/chat and /v1/search — authenticated Gloria endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.chat import (
    ChatRequest, ChatResponse, Source,
    SearchRequest, SearchResponse, SearchHit,
)
from app.rag.pipeline import ask
from app.rag.retriever import retrieve
from app.auth.api_key import require_api_key

router = APIRouter(prefix="/v1", tags=["gloria"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, api_key=Depends(require_api_key)):
    try:
        result = ask(req.message)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"pipeline error: {e}")
    return ChatResponse(
        answer=result["answer"],
        conversation_id=req.conversation_id,
        sources=[Source(**s) for s in result["sources"]],
    )


@router.post("/search", response_model=SearchResponse)
def search(req: SearchRequest, api_key=Depends(require_api_key)):
    where = {"organization": req.organization} if req.organization else None
    hits = retrieve(req.query, k=req.k, where=where)
    return SearchResponse(hits=[SearchHit(**h) for h in hits])
