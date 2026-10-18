"""Chunk text into ~fixed-size overlapping windows.

For an MVP, we approximate tokens with whitespace-separated words. When you
need real token counts, swap in tiktoken.encoding_for_model(...).encode().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.config import settings


# A page may start with "Context: <heading path>" (see extract_markdown).
# That line is repeated at the top of every chunk cut from the page, so each
# chunk carries its topic even when it starts mid-table.
CONTEXT_PREFIX = "Context: "


@dataclass
class Chunk:
    text: str
    metadata: dict


def _split_words(text: str) -> List[str]:
    return text.split()


def chunk_text(
    text: str,
    metadata: dict,
    size: int | None = None,
    overlap: int | None = None,
) -> List[Chunk]:
    """Return a list of Chunk objects covering ``text`` with overlap."""
    size = size or settings.CHUNK_SIZE_TOKENS
    overlap = overlap or settings.CHUNK_OVERLAP_TOKENS
    if size <= 0:
        raise ValueError("size must be positive")
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")

    words = _split_words(text)
    if not words:
        return []

    chunks: List[Chunk] = []
    stride = size - overlap
    idx = 0
    while idx < len(words):
        piece = words[idx: idx + size]
        chunk_text_str = " ".join(piece)
        chunks.append(Chunk(text=chunk_text_str, metadata=dict(metadata)))
        if idx + size >= len(words):
            break
        idx += stride
    return chunks


def chunk_pages(pages, base_metadata: dict) -> List[Chunk]:
    """Chunk a list of PageText objects, tagging each chunk with its page."""
    chunks: List[Chunk] = []
    for page in pages:
        if not page.text.strip():
            continue
        md = dict(base_metadata)
        md["page"] = page.page_number
        md["used_ocr"] = page.used_ocr
        text, context = page.text, ""
        if text.startswith(CONTEXT_PREFIX):
            context, _, text = text.partition("\n")
        for chunk in chunk_text(text, md):
            if context:
                chunk.text = f"{context}\n{chunk.text}"
            chunks.append(chunk)
    return chunks
