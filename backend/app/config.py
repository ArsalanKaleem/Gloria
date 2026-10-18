"""Application settings loaded from environment / .env file."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Environment ---
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # --- Your university (used in Gloria's prompt and document metadata) ---
    UNIVERSITY_NAME: str = "Your University"          # e.g. "Shaikh Ayaz University"
    UNIVERSITY_FULL_NAME: str = "Your University"     # e.g. "Shaikh Ayaz University Shikarpur"
    UNIVERSITY_SHORT_NAME: str = ""                   # e.g. "SAUS" (abbreviations students type)
    UNIVERSITY_MOTTO: str = ""                        # optional
    ASSISTANT_CREATOR: str = "the university's students"  # "You were built by ..."

    # --- Database ---
    DATABASE_URL: str = "postgresql://gloria:change-me@localhost:5432/gloria"

    # --- Vector store ---
    CHROMA_DIR: str = "./data/chroma"
    CHROMA_COLLECTION: str = "gloria_kb"

    # --- Embeddings ---
    # Local sentence-transformers model for MVP; swap for a hosted embedder later.
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Chunking ---
    CHUNK_SIZE_TOKENS: int = 300  # words; keeps chunks under the 512-token embedder limit
    CHUNK_OVERLAP_TOKENS: int = 50

    # --- Generation (LLM provider) ---
    # OpenAI-compatible; works with OpenAI, Groq, Together, Fireworks, vLLM, etc.
    GLORIA_MODEL_BASE_URL: str = "https://api.openai.com/v1"
    GLORIA_MODEL_API_KEY: str = ""
    GLORIA_MODEL_NAME: str = "gpt-4o-mini"
    GLORIA_MAX_TOKENS: int = 800
    GLORIA_TEMPERATURE: float = 0.2
    # Reasoning effort for "thinking" models. Empty = automatic per model
    # (Gemini 2.5 Flash: none, Gemini / gpt-oss: low, others: not sent).
    # Set "off" to never send it, or low / medium / high to force a level.
    GLORIA_REASONING_EFFORT: str = ""

    # Optional second provider, used only when the primary call fails
    # (rate limit, outage). Leave GLORIA_FALLBACK_API_KEY empty to disable.
    GLORIA_FALLBACK_BASE_URL: str = ""
    GLORIA_FALLBACK_API_KEY: str = ""
    GLORIA_FALLBACK_MODEL_NAME: str = ""
    # Optional third provider, tried after the fallback.
    GLORIA_FALLBACK2_BASE_URL: str = ""
    GLORIA_FALLBACK2_API_KEY: str = ""
    GLORIA_FALLBACK2_MODEL_NAME: str = ""

    # --- Retrieval tuning ---
    WEAK_DISTANCE_THRESHOLD: float = 0.55  # above this, retrieval considered weak

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000"

    # --- Data folders ---
    UNIVERSITY_DATA_DIR: str = "./data/university"
    HEC_DATA_DIR: str = "./data/hec"
    PROCESSED_DIR: str = "./data/processed"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
