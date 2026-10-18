"""Run the evaluation set against the Gloria pipeline and report results.

Reads ``tests/eval_questions.json`` — see that file for the expected shape.

Free-tier LLM APIs rate-limit hard, so the script pauses between questions.
Set EVAL_DELAY_SECONDS to change the pause (default 8 s, which keeps under
Gemini Flash's 10 requests/minute free tier; use 0 for paid tiers).

Every result is appended to ``tests/eval_results.jsonl`` as soon as it is
known, so a cancelled or quota-limited run loses nothing:

    python -m scripts.run_eval                     # fresh run, all questions
    python -m scripts.run_eval --resume            # skip questions already answered
    python -m scripts.run_eval --category fees     # one category only
    python -m scripts.run_eval --limit 15          # first 15 (after filters)
    python -m scripts.run_eval --report            # just print the saved results

The run stops early once every LLM provider is rate-limited, instead of
burning through the remaining questions as failures; ``--resume`` later.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from statistics import median

from app.rag import generator
from app.rag.pipeline import ask, REFUSAL, LLM_ERROR_MESSAGE


EVAL_PATH = Path("/app/tests/eval_questions.json")
RESULTS_PATH = Path("/app/tests/eval_results.jsonl")
DELAY_SECONDS = float(os.getenv("EVAL_DELAY_SECONDS", "8"))
# Stop after this many LLM errors in a row: every provider is out of quota.
MAX_CONSECUTIVE_LLM_ERRORS = 3


def _passes(qrec: dict, answer: str) -> bool:
    if qrec.get("expected_refusal"):
        return answer.strip().startswith(REFUSAL[:40])
    needed = qrec.get("expected_contains") or []
    if not needed:
        return True
    # Normalize: lowercase, strip non-alphanumerics between them
    import re
    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9@.]", "", s.lower())
    text = norm(answer)
    # Pass if ANY expected phrase appears (OR logic, not AND)
    return any(norm(str(k)) in text for k in needed)


def _load_results() -> dict[str, dict]:
    """Saved results keyed by question id (later lines win)."""
    results: dict[str, dict] = {}
    if RESULTS_PATH.exists():
        for line in RESULTS_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                results[rec["id"]] = rec
    return results


def _report(results: dict[str, dict], total_questions: int) -> None:
    recs = list(results.values())
    if not recs:
        print("No results yet.")
        return
    passes = sum(r["result"] == "PASS" for r in recs)
    llm_errors = sum(r["result"] == "LLMERR" for r in recs)
    latencies = [r["ms"] for r in recs if r["result"] != "ERROR"]
    print("-" * 60)
    print(f"Answered: {len(recs)}/{total_questions} questions")
    print(f"Overall:  {passes}/{len(recs)} passed  ({passes / len(recs) * 100:.1f}%)")
    if llm_errors:
        print(f"LLM errors: {llm_errors} (rate limits; rerun with --resume to retry them)")
    if latencies:
        print(f"Median latency: {median(latencies):.0f} ms")
    providers: dict[str, int] = {}
    for r in recs:
        providers[r["provider"]] = providers.get(r["provider"], 0) + 1
    print("Answered by: " + ", ".join(f"{k} {v}" for k, v in sorted(providers.items())))
    print("\nBy category:")
    per_category: dict[str, list[bool]] = {}
    for r in recs:
        per_category.setdefault(r["category"], []).append(r["result"] == "PASS")
    for cat, oks in sorted(per_category.items()):
        print(f"  {cat:<20} {sum(oks)}/{len(oks)}  ({sum(oks) / len(oks) * 100:.1f}%)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--resume", action="store_true",
                        help="keep saved results; skip questions already answered")
    parser.add_argument("--category", help="only run this category")
    parser.add_argument("--limit", type=int, help="run at most N questions")
    parser.add_argument("--report", action="store_true", help="print saved results and exit")
    args = parser.parse_args()

    if not EVAL_PATH.exists():
        print(f"No eval file at {EVAL_PATH}. Author some questions first.")
        return

    with EVAL_PATH.open("r", encoding="utf-8") as f:
        questions = json.load(f)

    if not questions:
        print("Eval file is empty. Add some questions first.")
        return

    if args.report:
        _report(_load_results(), len(questions))
        return

    if args.resume:
        saved = _load_results()
    else:
        saved = {}
        RESULTS_PATH.write_text("", encoding="utf-8")

    todo = [q for q in questions
            if not (q.get("id") in saved and saved[q["id"]]["result"] != "LLMERR")]
    if args.category:
        todo = [q for q in todo if q.get("category") == args.category]
    if args.limit:
        todo = todo[: args.limit]

    print(f"{len(todo)} questions to run, {DELAY_SECONDS:g}s pause between them\n", flush=True)
    print(f"{'ID':<10} {'Category':<14} {'ms':>6}  {'Result':<7} Provider", flush=True)
    print("-" * 60, flush=True)

    consecutive_llm_errors = 0
    for i, q in enumerate(todo):
        if i and DELAY_SECONDS:
            time.sleep(DELAY_SECONDS)
        generator.last_provider = ""
        cat = q.get("category", "uncategorised")
        start = time.perf_counter()
        sources: list[str] = []
        try:
            result = ask(q["question"])
            answer = result["answer"]
            sources = [f"{s.get('title') or ''}" + (f" (section {s['page']})" if s.get("page") else "")
                       for s in result.get("sources", [])]
            if answer == LLM_ERROR_MESSAGE:
                label = "LLMERR"
            else:
                label = "PASS" if _passes(q, answer) else "FAIL"
        except Exception as e:  # noqa: BLE001
            answer, label = f"{type(e).__name__}: {e}", "ERROR"
        elapsed_ms = (time.perf_counter() - start) * 1000
        provider = generator.last_provider or "-"

        rec = {"id": q.get("id", ""), "category": cat, "result": label,
               "provider": provider, "ms": round(elapsed_ms), "answer": answer,
               "sources": sources}
        saved[rec["id"]] = rec
        with RESULTS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"{rec['id']:<10} {cat:<14} {elapsed_ms:>6.0f}  {label:<7} {provider}", flush=True)

        consecutive_llm_errors = consecutive_llm_errors + 1 if label == "LLMERR" else 0
        wait = generator.seconds_until_available()
        if label == "LLMERR" and wait > 0:
            hours, minutes = divmod(round(wait / 60), 60)
            print(f"\nStopping: every LLM provider is rate-limited (daily quota). The first "
                  f"one is free again in about {hours}h {minutes:02d}m. Rerun then with --resume, "
                  "or add another provider in backend/.env.", flush=True)
            break
        if consecutive_llm_errors >= MAX_CONSECUTIVE_LLM_ERRORS:
            print(f"\nStopping: {consecutive_llm_errors} LLM errors in a row - every "
                  "provider looks rate-limited. Rerun later with --resume.", flush=True)
            break

    _report(saved, len(questions))


if __name__ == "__main__":
    main()
