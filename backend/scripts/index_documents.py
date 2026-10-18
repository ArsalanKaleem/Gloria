"""Index processed documents into ChromaDB.

Reads ``data/processed/*.json`` (produced by ingest_pdfs.py), chunks the
text, embeds it, and upserts into the vector collection.

Idempotent: chunk IDs are deterministic ``<sha1>::<page>::<n>`` so re-runs
overwrite existing chunks rather than duplicating.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from app.config import settings
from app.ingest.pdf_processor import PageText
from app.rag.chunker import chunk_pages
from app.rag.embeddings import Embedder
from app.rag import vector_store


BATCH = 64


def _load_processed(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _pages_from(record: dict) -> List[PageText]:
    return [
        PageText(
            page_number=p["page_number"],
            text=p.get("text") or "",
            used_ocr=bool(p.get("used_ocr")),
        )
        for p in record.get("pages", [])
    ]


def _index_record(record: dict) -> int:
    sha1 = record["sha1"]
    meta = record.get("metadata", {}) or {}
    base_metadata = {
        "sha1": sha1,
        "title": meta.get("title", ""),
        "organization": meta.get("organization", ""),
        "source_url": meta.get("source_url", ""),
        "published": meta.get("published", ""),
        "source_type": "hec" if str(meta.get("organization", "")).upper() == "HEC" else "university",
    }

    chunks = chunk_pages(_pages_from(record), base_metadata)
    if not chunks:
        return 0

    # Assign deterministic IDs and index in batches.
    ids, docs, metas = [], [], []
    per_page_counter: dict[int, int] = {}
    for c in chunks:
        page = c.metadata.get("page") or 0
        per_page_counter[page] = per_page_counter.get(page, 0) + 1
        cid = f"{sha1}::{page}::{per_page_counter[page]}"
        ids.append(cid)
        docs.append(c.text)
        metas.append(c.metadata)

    total = 0
    for i in range(0, len(ids), BATCH):
        s = slice(i, i + BATCH)
        embeddings = Embedder.embed(docs[s])
        vector_store.add(ids=ids[s], documents=docs[s], embeddings=embeddings, metadatas=metas[s])
        total += len(ids[s])
    return total


def main() -> None:
    processed_dir = Path(settings.PROCESSED_DIR)
    if not processed_dir.exists():
        print(f"No processed dir at {processed_dir}. Run ingest_pdfs.py first.")
        return

    grand = 0
    for path in sorted(processed_dir.glob("*.json")):
        record = _load_processed(path)
        n = _index_record(record)
        title = record.get("metadata", {}).get("title", path.stem)
        print(f"- {title}: {n} chunks")
        grand += n
    print(f"\nDone. Indexed {grand} chunks. Collection now has {vector_store.count()}.")


if __name__ == "__main__":
    main()
