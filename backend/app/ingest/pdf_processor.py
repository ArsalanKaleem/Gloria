"""PDF text extraction using PyMuPDF, with an OCR fallback for scanned pages."""

from __future__ import annotations
import re as _re
from pathlib import Path as _Path

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF

from app.rag.chunker import CONTEXT_PREFIX


@dataclass
class PageText:
    page_number: int          # 1-based
    text: str
    used_ocr: bool = False


def _ocr_page(page: fitz.Page) -> str:
    """OCR fallback using pdf2image + pytesseract. Imported lazily so the
    module still imports if OCR deps are missing.
    """
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
    except ImportError:
        return ""

    # Render the single page to an image at 300 DPI.
    pdf_bytes = page.parent.tobytes()
    images = convert_from_bytes(
        pdf_bytes,
        dpi=300,
        first_page=page.number + 1,
        last_page=page.number + 1,
    )
    if not images:
        return ""
    return pytesseract.image_to_string(images[0])

def extract_markdown(md_path: str | Path) -> list:
    """Read a markdown file and split into ~one-page-equivalent 'pages'.

    Returns the same shape as extract_pdf: a list of Page objects (or dicts)
    with text and page_number. We slice markdown by top-level headings so
    each 'page' is a self-contained section for chunking downstream.
    """
    from dataclasses import dataclass

    @dataclass
    class Page:
        page_number: int
        text: str
        used_ocr: bool = False

    md_text = Path(md_path).read_text(encoding="utf-8", errors="ignore")

    # Strip HTML picture-text blocks that pandoc-style converters embed.
    md_text = _re.sub(
        r"<!--\s*Start of picture text\s*-->.*?<!--\s*End of picture text\s*-->",
        "",
        md_text,
        flags=_re.DOTALL | _re.IGNORECASE,
    )
    # Any other HTML comment is an author's note (e.g. the template's
    # instructions), never knowledge: keep it out of the index.
    md_text = _re.sub(r"<!--.*?-->", "", md_text, flags=_re.DOTALL)

    # Group lines into sections at heading boundaries, remembering the
    # heading path above each section. The path is prepended as a context
    # line so a chunk that is only a table or a list still says what it is
    # about ("<University> Knowledge Base > Fees > ... per-semester fees").
    heading_re = _re.compile(r"^\s{0,3}(#{1,6})\s+(\S.*)$")
    sections: list[list[str]] = []
    paths: list[str] = []
    current: list[str] = []
    current_path = ""
    root = ""                          # the document's opening H1 title
    stack: list[tuple[int, str]] = []  # open (level, title) headings

    for line in md_text.split("\n"):
        m = heading_re.match(line)
        if not m:
            current.append(line)
            continue
        level, title = len(m.group(1)), m.group(2).strip().strip("*").strip()
        if not root and level == 1 and not any(l.strip() for l in current):
            root = title
            continue
        if current:
            sections.append(current)
            paths.append(current_path)
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        current_path = " > ".join([root] * bool(root) + [t for _, t in stack])
        current = [line]
    if current:
        sections.append(current)
        paths.append(current_path)

    def _body_words(text: str) -> int:
        """Words that are not part of a heading line."""
        return len([
            w
            for line in text.split("\n")
            if not line.strip().startswith("#")
            for w in line.split()
            if any(ch.isalnum() for ch in w)
        ])

    # A section that is only heading text carries no information on its own.
    # Fold it FORWARD onto the next section (so the heading gives context to
    # the content that follows) rather than emitting it as its own chunk.
    MIN_BODY_WORDS = 20
    merged: list[tuple[str, str]] = []
    pending_headings: list[str] = []
    pending_path: str | None = None

    for sec, path in zip(sections, paths):
        text = "\n".join(sec).strip()
        if not text:
            continue

        if _body_words(text) < MIN_BODY_WORDS:
            # Heading-only or near-empty: hold it to prefix the next section.
            # (The next section's own path already includes these headings
            # when they are its parents.)
            if pending_path is None:
                pending_path = path
            pending_headings.append(text)
            continue

        if pending_headings:
            text = "\n\n".join(pending_headings + [text])
            pending_headings, pending_path = [], None

        merged.append((path, text))

    # Anything still pending at the end joins the last real section.
    if pending_headings:
        if merged:
            path, text = merged[-1]
            merged[-1] = (path, text + "\n\n" + "\n\n".join(pending_headings))
        else:
            merged.append((pending_path or "", "\n\n".join(pending_headings)))

    pages = [
        Page(page_number=i + 1, text=(f"{CONTEXT_PREFIX}{path}\n\n{text}" if path else text))
        for i, (path, text) in enumerate(merged)
    ]
    return pages

def extract_pdf(path: str | Path, ocr_threshold_chars: int = 20) -> List[PageText]:
    """Extract text from a PDF. If a page yields fewer than
    ``ocr_threshold_chars`` characters, fall back to OCR.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    pages: List[PageText] = []
    with fitz.open(path) as doc:
        for i, page in enumerate(doc):
            raw = page.get_text("text") or ""
            raw = _clean_text(raw)
            if len(raw.strip()) < ocr_threshold_chars:
                ocr_text = _ocr_page(page)
                pages.append(PageText(
                    page_number=i + 1,
                    text=_clean_text(ocr_text),
                    used_ocr=True,
                ))
            else:
                pages.append(PageText(page_number=i + 1, text=raw))
    return pages


def _clean_text(text: str) -> str:
    """Normalise common PDF text artifacts."""
    if not text:
        return ""
    # Common ligatures
    replacements = {
        "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl",
        "\ufb03": "ffi", "\ufb04": "ffl",
        "\u2013": "-", "\u2014": "-",
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Collapse runs of whitespace within a line, but preserve line breaks.
    lines = [" ".join(line.split()) for line in text.splitlines()]
    # Drop excess blank lines
    cleaned, prev_blank = [], False
    for line in lines:
        blank = not line.strip()
        if blank and prev_blank:
            continue
        cleaned.append(line)
        prev_blank = blank
    return "\n".join(cleaned).strip()
