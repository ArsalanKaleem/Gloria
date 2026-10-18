"""End-to-end Gloria pipeline: route -> retrieve -> generate -> pack sources.

Flow:
1. Identity / capabilities fast-path (no retrieval; LLM answers from prompt)
2. Route the question to a structured lane
3. ALSO always run vector retrieval — bios and long-form facts often live in
   retrievable text, not the structured tables
4. Merge structured + document hits, dedupe by (title, page), rank by distance,
   cap total
5. If retrieval is genuinely weak, return the refusal template
6. Call the LLM (with one retry on transient failure) and pack sources

LLM failures are caught and returned as a friendly refusal rather than 500ing.
Set env GLORIA_DEBUG=1 to log routing and retrieval decisions.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Dict, List, Tuple

from app.config import settings
from app.rag.retriever import retrieve
from app.rag.generator import generate_answer
from app.rag.router import route
from app.tools.structured import search_people, search_department, search_program
from app.tools.documents import search_hec

log = logging.getLogger("gloria.pipeline")
DEBUG = os.getenv("GLORIA_DEBUG", "").lower() in ("1", "true", "yes")

REFUSAL = (
    "I do not have verified information about this yet. For the most accurate "
    "answer, please contact the relevant university office or check the "
    "official website."
)

LLM_ERROR_MESSAGE = (
    "I'm having trouble reaching my language model right now. Please try "
    "again in a moment. If this keeps happening, contact the university IT office."
)

# --- Identity / capabilities fast-path ---------------------------------------
# Questions matching these patterns skip retrieval entirely and go straight
# to the LLM. The system prompt's Identity + Capabilities sections handle them.
IDENTITY_RX = re.compile(
    r"\b("
    r"who\s+are\s+you|what\s+is\s+your\s+name|what'?s\s+your\s+name|"
    r"who\s+made\s+you|who\s+built\s+you|who\s+created\s+you|"
    r"who\s+is\s+your\s+(creator|maker|developer)|"
    r"are\s+you\s+(an?\s+)?(ai|bot|chatbot|assistant|human|real)|"
    r"introduce\s+yourself|about\s+yourself|"
    r"what\s+(can|do)\s+you\s+(do|help)|"                # "what can you do", "what do you help"
    r"what\s+can\s+you\s+help(\s+me)?(\s+with)?|"        # "what can you help me with"
    r"how\s+(can|do)\s+you\s+help(\s+me)?|"              # "how can you help"
    r"what\s+are\s+you\s+capable|"
    r"tell\s+me\s+(all\s+)?(that\s+)?(what\s+)?you\s+can\s+do|"
    r"what\s+(features|things|tasks)\s+can|"
    r"help\s+me\s+with\s+what"
    r")\b",
    re.I,
)

# --- Constants ---------------------------------------------------------------
MAX_TOTAL_HITS = 12        # cap after merging structured + doc hits
HEC_SUPPLEMENT_K = 2       # HEC passages added to non-HEC questions
STRUCTURED_DISTANCE = 0.0     # SQL rows treated as exact match
LLM_MAX_ATTEMPTS = 2          # one initial + one retry on transient failure


# --- Helpers -----------------------------------------------------------------

def _row_to_hit(row: dict, organization: str) -> dict:
    """Pack a structured DB row into the same shape as a retrieval hit."""
    text = "\n".join(f"{k}: {v}" for k, v in row.items() if v not in (None, ""))
    return {
        "id": f"struct:{row.get('id', '')}",   # namespace to avoid ID collisions
        "text": text,
        "metadata": {
            "title": row.get("name") or row.get("id") or "Structured record",
            "organization": organization,
            "source_url": row.get("source", ""),
            "page": None,
            "source_type": "structured",
        },
        "distance": STRUCTURED_DISTANCE,
    }


def _dedupe_key(hit: dict) -> Tuple:
    """Key for de-duplication: the chunk id.

    Not (title, page): in the markdown knowledge base a "page" is a whole
    section, and a long section is split into several chunks. Deduping by
    page silently dropped the second half of a section (e.g. the
    international-admissions rule) whenever the first half was retrieved.
    """
    return (hit.get("id") or "",)


def _merge_hits(structured: List[dict], docs: List[dict], cap: int) -> List[dict]:
    """Merge and dedupe, keeping order: exact structured records first, then
    document hits in the retriever's (hybrid-ranked) order."""
    seen = set()
    merged: List[dict] = []
    for h in structured + docs:
        key = _dedupe_key(h)
        if key in seen:
            continue
        seen.add(key)
        merged.append(h)
    return merged[:cap]


def _weakly_retrieved(hits: List[dict]) -> bool:
    """True when we should refuse rather than answer."""
    if not hits:
        return True
    best = min(h.get("distance", 1.0) for h in hits)
    return best > settings.WEAK_DISTANCE_THRESHOLD


def _pack_sources(hits: List[dict]) -> List[dict]:
    out = []
    for h in hits:
        md = h.get("metadata", {}) or {}
        out.append({
            "title": md.get("title") or "",
            "page": md.get("page"),
            "source_type": md.get("source_type") or _guess_source_type(md.get("organization")),
            "source_url": md.get("source_url"),
            "organization": md.get("organization"),
        })
    return out


def _guess_source_type(org: str | None) -> str:
    if not org:
        return "university"
    if org.strip().upper() == "HEC":
        return "hec"
    return "university"


def _safe_generate(question: str, hits: List[dict]) -> Tuple[str, bool]:
    """Call the LLM, retry once on transient failure. Returns (answer, success)."""
    last_error: Exception | None = None
    for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
        try:
            return generate_answer(question, hits), True
        except Exception as e:  # noqa: BLE001
            last_error = e
            log.warning("LLM error on attempt %d/%d: %s", attempt, LLM_MAX_ATTEMPTS, e)
    log.error("LLM failed after %d attempts: %s", LLM_MAX_ATTEMPTS, last_error)
    return LLM_ERROR_MESSAGE, False


def _debug(msg: str, **kwargs) -> None:
    if DEBUG:
        parts = [msg] + [f"{k}={v!r}" for k, v in kwargs.items()]
        log.info(" | ".join(parts))


# --- Main --------------------------------------------------------------------

def gather_hits(q: str, k: int = 10) -> List[dict]:
    """Route the question and collect the context hits the LLM will see.

    Kept separate from ask() so the retrieval-only eval can measure
    retrieval quality without spending LLM quota.
    """
    # 2. Route
    lane = route(q)
    _debug("routed", question=q, lane=lane)

    # 3. Structured lookup on the chosen lane (SQL failures caught silently)
    structured_hits: List[dict] = []
    try:
        if lane == "people":
            structured_hits = [_row_to_hit(r, settings.UNIVERSITY_NAME) for r in search_people(q)]
        elif lane == "department":
            structured_hits = [_row_to_hit(r, settings.UNIVERSITY_NAME) for r in search_department(q)]
        elif lane == "program":
            structured_hits = [_row_to_hit(r, settings.UNIVERSITY_NAME) for r in search_program(q)]
        elif lane == "hec":
            structured_hits = search_hec(q, k=k)
    except Exception as e:  # noqa: BLE001
        log.warning("structured lookup failed for lane %s: %s", lane, e)
        structured_hits = []

    # 4. Always ALSO fetch document hits (bios, policies, narrative content)
    # Questions not about HEC are about the university: search its own
    # documents first, and add only a few HEC passages. Otherwise long HEC
    # curriculum PDFs crowd out the university's answer (e.g. "How do I apply
    # for BS Computer Science?" matching HEC computing-curriculum pages).
    try:
        if lane == "hec":
            doc_hits = retrieve(q, k=k)
        else:
            doc_hits = (retrieve(q, k=k, where={"source_type": "university"})
                        + retrieve(q, k=HEC_SUPPLEMENT_K, where={"source_type": "hec"}))
    except Exception as e:  # noqa: BLE001
        log.warning("vector retrieval failed: %s", e)
        doc_hits = []

    # 5. Merge, dedupe, rank, cap
    hits = _merge_hits(structured_hits, doc_hits, cap=MAX_TOTAL_HITS)
    _debug(
        "retrieved",
        structured=len(structured_hits),
        docs=len(doc_hits),
        merged=len(hits),
        best_distance=(min((h.get("distance", 1.0) for h in hits), default=None) if hits else None),
    )
    return hits


def ask(question: str, k: int = 10) -> Dict:
    """Answer a question. Returns {'answer', 'sources'}."""
    q = (question or "").strip()
    if not q:
        return {"answer": REFUSAL, "sources": []}

    # 1. Identity / capabilities fast-path
    if IDENTITY_RX.search(q):
        _debug("identity fast-path", question=q)
        answer, _ = _safe_generate(q, hits=[])
        return {"answer": answer, "sources": []}

    hits = gather_hits(q, k=k)

    # 6. Refuse if retrieval is too weak
    if _weakly_retrieved(hits):
        return {"answer": REFUSAL, "sources": []}

    # 7. Generate — safely
    answer, ok = _safe_generate(q, hits)
    if not ok:
        # LLM failed even on retry — surface the friendly error, no sources
        # (we don't want users to think Gloria cited something she couldn't reach).
        return {"answer": answer, "sources": []}

    return {"answer": answer, "sources": _pack_sources(hits)}