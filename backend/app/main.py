"""FastAPI application entrypoint for the Gloria API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
from app.routes.health import router as health_router
from app.routes.chat import router as chat_router


# Create tables on startup (fine for MVP; use Alembic for production).
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Gloria API",
    description=f"The Intelligent University Knowledge Assistant of {settings.UNIVERSITY_NAME}.",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url=None,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate limiting ---
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
def _rate_limit_handler(request, exc):  # noqa: ARG001
    return JSONResponse(status_code=429, content={"detail": "Too many requests."})


# --- Routes ---
app.include_router(health_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "name": "Gloria API",
        "version": "1.0.0",
        "docs": "/docs" if settings.APP_ENV != "production" else "disabled in production",
    }
