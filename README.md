# GLORIA

**An open-source AI knowledge assistant for universities.**

Gloria answers students' questions about admissions, fees, programs, rules
and contacts from your university's own official information, and says
"I don't know" when that information doesn't cover the question. It comes
as a full-screen, ChatGPT-style chat app with chat history, and as Squiggle,
a small floating widget for embedding Gloria on any page.

Built by **Arsalan Kaleem**.

Gloria was built for **Shaikh Ayaz University, Shikarpur**. Everything a
university needs lives in **one Markdown file**, so any student can make a
Gloria for their own university: see
[Make it your university](#make-it-your-university).

## How it works

Gloria uses retrieval-augmented generation (RAG). For each question she
finds the relevant passages in the knowledge base, then asks a language
model to answer **only** from those passages, and shows the sources under
the reply.

| Layer | Technology |
| --- | --- |
| Backend API | Python, FastAPI, SQLAlchemy |
| Structured data | PostgreSQL (people, offices, contacts) |
| Vector database | ChromaDB |
| Embeddings | `BAAI/bge-base-en-v1.5` via sentence-transformers |
| Retrieval | Hybrid: vector search + BM25 keyword search, fused with Reciprocal Rank Fusion |
| Chunking | Heading-aware; every chunk carries its heading path as context |
| LLM | Any OpenAI-compatible API (Gemini, Groq, OpenAI, Ollama, ...), with automatic fallback providers |
| Document ingestion | Markdown, plus PDFs via PyMuPDF with OCR fallback |
| Frontend | Next.js 14, TypeScript, Tailwind CSS: full-screen chat app plus embeddable widget |
| Security | API key kept server-side behind a proxy; bcrypt-hashed keys; prompt-injection rules |
| Deployment | Docker Compose |
| Evaluation | Question set with retrieval-only and end-to-end evals |

---

## Make it your university

You need Docker, a free LLM API key, and your university's information.
No machine-learning experience is required.

**1. Get the code and an LLM key.**
Clone this repository. Get a free API key from
[Google AI Studio](https://aistudio.google.com/apikey) (Gemini) or
[Groq](https://console.groq.com/keys). Groq's free tier allows many more
requests per day, so it's the easier choice for testing.

**2. Write your knowledge base.** This is the real work, and it decides how
good your chatbot is.

```bash
mkdir -p data/university
cp templates/knowledge-base.md data/university/knowledge-base.md
cp templates/knowledge-base.meta.json data/university/knowledge-base.meta.json
```

Fill `data/university/knowledge-base.md` with your university's
information from the prospectus, website, fee pages and notices. The
template explains the format; the essentials:

- One topic per `###` heading, phrased as the question a student would ask.
- Full sentences that repeat the subject ("The BBA fee is Rs. 25,000 per
  semester on merit."), with a plain sentence after every table.
- Only facts from official sources. When two sources disagree, keep the
  newest one and delete the other.

In `knowledge-base.meta.json`, set `title` and set `organization` to the
same value as `UNIVERSITY_NAME` below.

**3. Configure the backend.**

```bash
cp backend/.env.example backend/.env
```

In `backend/.env`, set:

| Setting | Example |
| --- | --- |
| `UNIVERSITY_NAME` | `Shaikh Ayaz University` |
| `UNIVERSITY_FULL_NAME` | `Shaikh Ayaz University Shikarpur` |
| `UNIVERSITY_SHORT_NAME` | `SAUS` |
| `UNIVERSITY_MOTTO` | `The Revival of Educational Glory` (optional) |
| `ASSISTANT_CREATOR` | your name |
| `GLORIA_MODEL_BASE_URL` | `https://api.groq.com/openai/v1` or `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `GLORIA_MODEL_API_KEY` | your key |
| `GLORIA_MODEL_NAME` | `openai/gpt-oss-120b` (Groq) or `gemini-2.5-flash` (Gemini) |

Optional: add a second and third provider in the `GLORIA_FALLBACK_*` and
`GLORIA_FALLBACK2_*` settings. Gloria switches to them automatically when
the first one hits a rate limit.

**4. Brand the widget.** Edit `frontend/src/config.ts`: university name,
motto, colour and the example questions shown when the chat opens.

**5. Start it and index your knowledge base.** Follow the
[Quick start](#quick-start-docker) below, then build the index:

```bash
docker compose exec backend python -m scripts.ingest_pdfs
docker compose exec backend python -m scripts.index_documents
docker compose restart backend
```

(On Windows, `.\reindex.ps1` does all of this, and also clears the old index.)

**6. Test it.** Edit `tests/eval_questions.json` with questions about your
university and the phrase each answer must contain, then:

```bash
# Is the answer in what Gloria retrieves? No LLM calls, no quota used.
docker compose exec -T backend python -m scripts.eval_retrieval

# Full end-to-end test (one LLM call per question).
docker compose exec -T backend python -m scripts.run_eval
```

Fix misses by improving the knowledge base: usually a clearer heading, or
a plain sentence next to a table.

**Optional: national policy documents.** Put PDFs (for example HEC policies
in Pakistan) under `data/hec/<category>/` with a `<name>.meta.json` sidecar
whose `organization` is `HEC`. Questions that mention "HEC" search them
first.

---

## Quick start (Docker)

You need **Docker** and **docker compose**. That's it.

```bash
# 1. Clone / cd into this repo
cd gloria

# 2. Create backend .env
cp backend/.env.example backend/.env
# then edit backend/.env:
#   - GLORIA_MODEL_API_KEY   your LLM provider key (OpenAI, Groq, Together, ...)
#   - GLORIA_MODEL_NAME      the model to call (gpt-4o-mini, or your ft:... id)
#   - CORS_ORIGINS           where the frontend runs (http://localhost:3000)

# 3. Bring up the database + backend first (frontend needs an API key)
docker compose up -d db backend

# 4. Wait ~10 seconds for the backend to come up, then create an API key
docker compose exec backend python -m scripts.create_api_key sau-portal

# 5. Copy the printed FULL KEY into a root-level .env
cp .env.example .env
# edit .env and paste the key into GLORIA_API_KEY=...

# 6. Start the frontend
docker compose up -d frontend

# 7. Open http://localhost:3001  (backend is on http://localhost:8080)
```

You should see the Gloria chat app. Pick a suggested question or type your
own. (Gloria refuses everything until you load knowledge: see
[Make it your university](#make-it-your-university).)

---

## Updating knowledge

All university content lives in `data/university/knowledge-base.md`. Edit
it, then rebuild the index (clears `data/processed` and `data/chroma`,
re-ingests, re-indexes and restarts the backend):

```powershell
.\reindex.ps1
```

## Fine-tuning (Day 6)

1. Author examples in `fine-tuning/all.jsonl` (one JSON object per line).
   See `fine-tuning/README.md` for the format and composition guidance.
2. Split into train / validation:
   ```bash
   python fine-tuning/split.py
   ```
3. Upload `train.jsonl` + `validation.jsonl` to your provider.
4. Put the resulting model id in `backend/.env` as `GLORIA_MODEL_NAME`.
5. Restart the backend: `docker compose restart backend`.

---

## Repo layout

```
gloria/
├── backend/                   FastAPI + RAG pipeline
│   ├── app/
│   │   ├── main.py              FastAPI entrypoint
│   │   ├── config.py            settings from .env
│   │   ├── database.py          SQLAlchemy engine/session
│   │   ├── models/              SQL models (people, departments, programs, api keys)
│   │   ├── schemas/             Pydantic request/response
│   │   ├── routes/              /v1/health, /v1/chat, /v1/search
│   │   ├── auth/api_key.py      bcrypt key gen + verify
│   │   ├── ingest/pdf_processor PyMuPDF + OCR fallback
│   │   ├── tools/               structured (SQL) and documents (vector) search
│   │   └── rag/                 chunker, embeddings, vector store, retriever,
│   │                            prompts, generator, router, pipeline
│   ├── scripts/                 create tables, load, ingest, index, api key, eval
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                  Next.js 14 + Tailwind + TypeScript
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       page shell and metadata
│   │   │   ├── page.tsx         full-screen chat app
│   │   │   └── api/gloria/      server-side proxy that hides the API key
│   │   ├── components/Chat/     ChatGPT-style app: sidebar, history, messages
│   │   ├── components/Squiggle/ floating widget for embedding on other sites
│   │   └── config.ts        university name, colour, example questions
│   ├── Dockerfile
│   └── package.json
│
├── data/                      YOUR content lives here (git-ignored)
│   ├── university/knowledge-base.md  single SAUS knowledge base (+ .meta.json)
│   ├── hec/**/*.pdf              (+ .meta.json sidecars)
│   ├── processed/               produced by ingest_pdfs.py
│   └── chroma/                  vector DB persistence
│
├── templates/                 knowledge-base.md template for a new university
├── fine-tuning/               all.jsonl, train.jsonl, validation.jsonl, split.py
├── tests/                     eval_questions.json + conftest.py
├── docs/                      architecture, api, admin, security, eval-v1
├── docker-compose.yml
└── README.md
```

---

## Local (non-Docker) dev

If you prefer to run without Docker:

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# start a Postgres somewhere; set DATABASE_URL in .env accordingly
python -m scripts.create_tables
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
cp .env.local.example .env.local  # paste your GLORIA_API_KEY into it
npm install
npm run dev
```

---

## Useful commands

```bash
# Rebuild after editing a Dockerfile or requirements.txt
docker compose build backend
docker compose up -d backend

# Watch backend logs
docker compose logs -f backend

# Check retrieval only: is the answer in the context the LLM sees?
# No LLM calls, so it costs no API quota. Run this first after any data change.
docker compose exec -T backend python -m scripts.eval_retrieval

# Run the full evaluation set (calls the LLM once per question;
# saves after every question, --resume continues a stopped run)
docker compose exec -T backend python -m scripts.run_eval
docker compose exec -T backend python -m scripts.run_eval --resume

# Reset the vector store
rm -rf data/chroma && docker compose exec backend python -m scripts.index_documents

# Get a psql shell
docker compose exec db psql -U gloria -d gloria
```

---

## Environment variables cheat sheet

| Variable                      | Where          | Purpose                                     |
|-------------------------------|----------------|---------------------------------------------|
| `UNIVERSITY_NAME` etc.        | backend/.env   | Your university's name, short name, motto   |
| `ASSISTANT_CREATOR`           | backend/.env   | Who built this Gloria (identity answers)    |
| `GLORIA_MODEL_BASE_URL`       | backend/.env   | OpenAI-compatible endpoint                  |
| `GLORIA_MODEL_API_KEY`        | backend/.env   | LLM provider key                            |
| `GLORIA_MODEL_NAME`           | backend/.env   | Model / fine-tune id                        |
| `DATABASE_URL`                | backend/.env   | Postgres connection string                  |
| `CORS_ORIGINS`                | backend/.env   | Comma-separated origins for the frontend    |
| `WEAK_DISTANCE_THRESHOLD`     | backend/.env   | Refusal threshold on retrieval distance     |
| `GLORIA_API_URL`              | frontend .env  | Where the Next.js server reaches the API    |
| `GLORIA_API_KEY`              | frontend .env  | Gloria API key (server-side only)           |
| `GLORIA_API_KEY`              | root .env      | Same, consumed by docker-compose            |

---

## Deployment

The Docker images are cloud-agnostic. Any host that speaks Docker works:
a small VM (2 vCPU / 4-8 GB RAM is plenty for MVP traffic), Cloud Run,
ECS, or a Kubernetes cluster. Terminate TLS at a reverse proxy
(Nginx / Caddy / Cloudflare) and point at ports 3000 (frontend) and
8000 (backend, or hide it entirely and route through Next.js).

See `docs/security.md` before going live.

---

## License

MIT. See [LICENSE](LICENSE).
