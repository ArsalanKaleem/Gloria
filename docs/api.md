# Gloria API Reference

Base URL (local): `http://localhost:8000`

All endpoints under `/v1/` except `/v1/health` require an API key.

## Authentication

Send `Authorization: Bearer <FULL_KEY>` where `<FULL_KEY>` is the string
printed by `python -m scripts.create_api_key`.

## Endpoints

### `GET /v1/health`

Liveness probe. No auth.

**Response:**
```json
{"status": "ok"}
```

### `POST /v1/chat`

Ask Gloria a question.

**Request:**
```json
{
  "message": "Who is the Head of the Computer Science Department?",
  "conversation_id": "optional-client-supplied-id"
}
```

**Response:**
```json
{
  "answer": "According to the departmental listing, the current HOD is ...\n\nSources:\n- Department of Computer Science — About, p.4 (Shaikh Ayaz University)",
  "conversation_id": "optional-client-supplied-id",
  "sources": [
    {
      "title": "Department of Computer Science — About",
      "page": 4,
      "source_type": "university",
      "source_url": "https://example.sau.edu.pk/...",
      "organization": "Shaikh Ayaz University"
    }
  ]
}
```

### `POST /v1/search`

Raw retrieval — returns top-k matching chunks without an LLM call.

**Request:**
```json
{"query": "grading policy", "k": 5, "organization": "HEC"}
```

**Response:**
```json
{
  "hits": [
    {"text": "...", "metadata": {...}, "distance": 0.12}
  ]
}
```

## Errors

| Status | Meaning                                    |
|--------|--------------------------------------------|
| 400    | Malformed request body                     |
| 401    | Missing / invalid API key                  |
| 429    | Rate limit exceeded (default 60/min/IP)    |
| 500    | Pipeline error (check backend logs)        |
| 502    | Upstream (proxy) failure                   |

## Rate limits

Default: **60 requests per minute per IP** (configured in `app/main.py`).
Adjust `Limiter(default_limits=[...])` for production traffic.
