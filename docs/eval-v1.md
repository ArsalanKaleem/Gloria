# Gloria Eval Baseline — v1

**Date:** 2026-09-05
**Overall:** 48/54 (88.9%)
**Median latency:** 17.3 s
**Model:** openai/gpt-oss-120b via Groq

## Corpus

- 19 PDFs (Prospectus, Code of University, directories, webpages)
- 8 markdown webpages (Senate, Syndicate, Scholarships, Libraries, etc.)
- 7 markdown faculty bios
- 31 structured Person records in Postgres
- Total: ~550 chunks in ChromaDB

## Category scores


| Category   | Score      | Notes                                 |
| ---------- | ---------- | ------------------------------------- |
| admissions | 7/7 (100%) | perfect                               |
| contacts   | 8/8 (100%) | perfect                               |
| faculty    | 8/8 (100%) | perfect                               |
| refusals   | 5/5 (100%) | perfect                               |
| injection  | 3/3 (100%) | perfect                               |
| rules      | 5/6 (83%)  | 1 phrasing mismatch                   |
| programs   | 6/7 (86%)  | 1 phrasing mismatch                   |
| governance | 2/3 (67%)  | Chancellor question                   |
| fees       | 3/5 (60%)  | 2 fee variants missed                 |
| identity   | 1/2 (50%)  | capabilities answer needs SAU by name |

## Known failures (v1 → next iteration)

- fees: BBA self-finance and one other fee variant
- governance-001: Chancellor identification
- ident-002: capabilities answer doesn't say "Shaikh Ayaz"
- prog-003: B.Ed program specifics
- rules-005: internship length phrasing

## Latency

Median 17.3 s per question — most likely Groq rate-limit throttling on burst
runs. Individual questions in normal use return in 1-4 s.
