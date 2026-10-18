"""Remove near-empty chunks (headings with no body) from the vector store.

Markdown documents that open with a title followed immediately by another
heading produce chunks containing only heading text. Those chunks embed as
pure topic signal and outrank real content chunks on topical queries.

Safety: this refuses to delete more than MAX_DELETE_FRACTION of the
collection, and never touches a chunk longer than MAX_JUNK_CHARS.

Run with --dry-run first.
"""
from __future__ import annotations

import re
import sys

from app.rag.vector_store import get_collection

# Hard ceiling: a chunk longer than this is never junk, whatever the
# word count says. Protects against a broken word counter deleting real data.
MAX_JUNK_CHARS = 200

# A chunk needs at least this many non-heading words to survive.
MIN_BODY_WORDS = 10

# Refuse to run if we'd delete more than this share of the collection.
MAX_DELETE_FRACTION = 0.10


def body_word_count(text: str) -> int:
    """Words remaining after removing markdown heading markers."""
    # Remove leading heading hashes wherever they appear, including after
    # newline collapse (e.g. "# Title # Subtitle body words...").
    t = re.sub(r"#{1,6}", " ", text or "")
    # Remove markdown table rule rows
    t = re.sub(r"\|[\s\-:|]+\|", " ", t)
    # Remove pipes and emphasis markers
    t = re.sub(r"[|*_~`]", " ", t)
    words = [w for w in t.split() if any(ch.isalnum() for ch in w)]
    return len(words)


def main() -> None:
    dry = "--dry-run" in sys.argv

    col = get_collection()
    res = col.get(include=["documents", "metadatas"], limit=100000)
    ids, docs, metas = res["ids"], res["documents"], res["metadatas"]
    total = len(ids)

    candidates = []
    for cid, doc, md in zip(ids, docs, metas):
        doc = doc or ""
        if len(doc) > MAX_JUNK_CHARS:
            continue                       # too long to be heading-only
        n = body_word_count(doc)
        if n < MIN_BODY_WORDS:
            candidates.append((cid, md.get("title"), md.get("page"),
                               n, len(doc), doc.replace("\n", " ")[:110]))

    print(f"Scanned {total} chunks.")
    print(f"Candidates (< {MAX_JUNK_CHARS} chars AND < {MIN_BODY_WORDS} body words): "
          f"{len(candidates)}\n")
    for cid, title, page, n, clen, preview in candidates:
        print(f"  [{n:>2}w {clen:>3}ch] {title} p.{page}")
        print(f"       {preview}")

    if not candidates:
        print("\nNothing to prune.")
        return

    frac = len(candidates) / max(total, 1)
    if frac > MAX_DELETE_FRACTION:
        print(f"\nABORT: would delete {frac:.0%} of the collection "
              f"(limit {MAX_DELETE_FRACTION:.0%}). Something is wrong — "
              f"check the word counter before proceeding.")
        return

    if dry:
        print(f"\nDRY RUN — nothing deleted. "
              f"Would remove {len(candidates)} of {total} chunks ({frac:.1%}).")
        return

    col.delete(ids=[c[0] for c in candidates])
    print(f"\nDeleted {len(candidates)} chunks. Collection now has {col.count()}.")


if __name__ == "__main__":
    main()