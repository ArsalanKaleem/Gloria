# Architecture

```
  Squiggle (Next.js widget)
     |
     v
  Server-side proxy  (frontend/src/app/api/gloria/route.ts)
     |   attaches the Gloria API key server-side
     v
  Gloria API  (FastAPI)                       <---> PostgreSQL (structured)
     |                                        <---> ChromaDB (vectors)
     v
  RAG pipeline
     |    route -> retrieve -> generate -> pack sources
     v
  LLM provider (OpenAI-compatible endpoint)
```

## The two brains

1. **Fine-tuned LLM** — teaches Gloria her *voice*, *structure*, *citation style*, and *refusal behaviour*. Never facts.
2. **RAG (retrieval-augmented generation)** — teaches Gloria the *facts*: university data + HEC documents. Updates instantly by re-indexing.

## Data flow at query time

1. User sends a message from Squiggle to `/api/gloria` on the Next.js server.
2. The Next.js server attaches `Authorization: Bearer <GLORIA_API_KEY>` and forwards to the FastAPI backend at `POST /v1/chat`.
3. FastAPI verifies the key (`app.auth.api_key`), then hands the question to `app.rag.pipeline.ask()`.
4. The router picks a lane: `people`, `department`, `program`, `hec`, or `documents`.
5. Structured lanes query Postgres; document lanes query ChromaDB.
6. If retrieval is weak (best distance above `WEAK_DISTANCE_THRESHOLD`), Gloria returns the refusal template — no LLM call.
7. Otherwise, the LLM is called with the Gloria system prompt + retrieved context, and its answer + citation-friendly source list is returned.
