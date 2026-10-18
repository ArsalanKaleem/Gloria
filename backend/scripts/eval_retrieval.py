"""Retrieval-only evaluation: does the context Gloria sends to the LLM
contain the answer? Makes no LLM calls, so it costs no API quota and runs
in seconds. Use it to tune retrieval before spending quota on run_eval.

For every question with ``expected_contains``, the script builds the exact
context block the LLM would receive and checks whether any expected phrase
appears in it (same normalisation as run_eval). A miss here means the LLM
cannot answer, however good it is.

    python -m scripts.eval_retrieval            # summary + misses
    python -m scripts.eval_retrieval -v         # also show where hits were found
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from app.rag.pipeline import IDENTITY_RX, gather_hits, _weakly_retrieved
from app.rag.prompts import build_context_block

EVAL_PATH = Path("/app/tests/eval_questions.json")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9@.]", "", s.lower())


def _first_line(text: str) -> str:
    line = (text or "").strip().split("\n", 1)[0]
    return line.replace("Context: ", "")[:110]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    questions = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    found = total = 0
    per_category: dict[str, list[bool]] = {}
    misses = []

    for q in questions:
        needed = q.get("expected_contains") or []
        if q.get("expected_refusal") or not needed or IDENTITY_RX.search(q["question"]):
            continue
        hits = gather_hits(q["question"])
        context = _norm(build_context_block(hits))
        ok = (not _weakly_retrieved(hits)) and any(_norm(str(n)) in context for n in needed)
        total += 1
        found += ok
        per_category.setdefault(q.get("category", "?"), []).append(ok)
        rank = next((i for i, h in enumerate(hits, 1)
                     if any(_norm(str(n)) in _norm(h.get("text", "")) for n in needed)), None)
        if not ok:
            misses.append((q, hits))
        elif args.verbose:
            print(f"ok   {q['id']:<12} rank {rank}: {_first_line(hits[rank - 1]['text']) if rank else ''}")

    print(f"\nAnswer present in LLM context: {found}/{total} ({found / total * 100:.1f}%)\n")
    for cat, oks in sorted(per_category.items()):
        print(f"  {cat:<12} {sum(oks)}/{len(oks)}")

    if misses:
        print("\nMisses (expected phrase not in context):")
    for q, hits in misses:
        print(f"\n- {q['id']}: {q['question']}  expected {q['expected_contains']}")
        for h in hits[:4]:
            md = h.get("metadata", {}) or {}
            print(f"    {h.get('distance', 1):.3f} {md.get('title', '')[:30]:<30} | {_first_line(h.get('text', ''))}")


if __name__ == "__main__":
    main()
