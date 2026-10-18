"""Extract text from PDFs and markdown docs, then write per-document JSON files.

Sources under ``data/university/`` and ``data/hec/`` are scanned recursively.
Each source file may have a sidecar ``<name>.meta.json`` with fields like:
    {
      "title": "Undergraduate Prospectus 2025",
      "organization": "Your University",
      "source_url": "https://...",
      "published": "2025-01-15"
    }

Output goes to ``data/processed/<sha1>.json``, ready for index_documents.py.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable, Optional

from app.config import settings
from app.ingest.pdf_processor import extract_pdf, extract_markdown


# File extensions we know how to ingest. Add new ones (e.g. ".html") here
# once the corresponding extractor exists in pdf_processor.py.
_SUPPORTED_SUFFIXES = {".pdf", ".md"}


def _iter_docs(root: Path) -> Iterable[Path]:
    """Yield every ingestable document under ``root`` in a stable order."""
    if not root.exists():
        return []
    files = [
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in _SUPPORTED_SUFFIXES
    ]
    return sorted(files)


def _load_sidecar(doc_path: Path) -> dict:
    """Look for ``<name>.meta.json`` next to the source file."""
    sidecar = doc_path.with_suffix(".meta.json")
    if sidecar.exists():
        try:
            with sidecar.open("r", encoding="utf-8-sig") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"  ! bad sidecar {sidecar}: {e}")
    return {}


def _default_meta(doc_path: Path, org_hint: Optional[str]) -> dict:
    return {
        "title": doc_path.stem.replace("_", " ").replace("-", " ").title(),
        "organization": org_hint or settings.UNIVERSITY_NAME,
        "source_url": "",
        "published": "",
    }


def _sha1(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract(doc_path: Path):
    """Dispatch to the right extractor based on file suffix."""
    suffix = doc_path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(doc_path)
    if suffix == ".md":
        return extract_markdown(doc_path)
    raise ValueError(f"Unsupported file type: {doc_path}")


def _process(doc_path: Path, org_hint: Optional[str], out_dir: Path) -> None:
    print(f"- {doc_path}")
    meta = {**_default_meta(doc_path, org_hint), **_load_sidecar(doc_path)}
    pages = _extract(doc_path)
    record = {
        "source_path": str(doc_path),
        "sha1": _sha1(doc_path),
        "metadata": meta,
        "pages": [
            {"page_number": p.page_number, "text": p.text, "used_ocr": p.used_ocr}
            for p in pages
        ],
    }
    out_path = out_dir / f"{record['sha1']}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    ocr_pages = sum(1 for p in pages if p.used_ocr)
    print(f"    -> {out_path.name}  ({len(pages)} pages, {ocr_pages} via OCR)")


def main() -> None:
    out_dir = Path(settings.PROCESSED_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    for doc in _iter_docs(Path(settings.UNIVERSITY_DATA_DIR)):
        _process(doc, settings.UNIVERSITY_NAME, out_dir)
    for doc in _iter_docs(Path(settings.HEC_DATA_DIR)):
        _process(doc, "HEC", out_dir)


if __name__ == "__main__":
    main()