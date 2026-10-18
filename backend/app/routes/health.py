"""Health/liveness route — no authentication required."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}
