# Fine-tuning Dataset

Gloria's *voice, structure, refusal behaviour, and citation style* live here.
Facts do **not**. Facts belong in the RAG knowledge base.

## Files

| File               | Purpose                                                    |
|--------------------|------------------------------------------------------------|
| `all.jsonl`        | The full dataset you author, one example per line.         |
| `split.py`         | Splits `all.jsonl` into `train.jsonl` + `validation.jsonl`.|
| `train.jsonl`      | Produced by `split.py` — do NOT edit by hand.              |
| `validation.jsonl` | Produced by `split.py` — held-out for honest evaluation.   |

## Example line

Each line of `all.jsonl` is a JSON object with a single `messages` field:

```json
{"messages":[
  {"role":"system","content":"You are Gloria, the AI assistant of Shaikh Ayaz University..."},
  {"role":"user","content":"Hi Gloria, who should I talk to about scholarships?"},
  {"role":"assistant","content":"For scholarships, please contact the Office of Student Financial Aid.\n\nGloria can point you to the office; the office confirms eligibility and awards.\n\nSources:\n- Student Handbook, p.22 (Shaikh Ayaz University)"}
]}
```

Use the exact system prompt from `backend/app/rag/prompts.py` so your
fine-tuned model behaves the same in production as during training.

## Composition (guidance)

Aim for a healthy mix:

- 45% answering with citations
- 15% refusing unknown questions
- 10% clarifying ambiguity
- 10% HEC vs university distinctions
-  5% conflict / outdated source
-  5% safety / prompt-injection resistance
-  5% conversational politeness (hi, thanks)
-  5% follow-up / multi-turn

## Workflow

1. Author examples in `all.jsonl` (60+ to start; quality beats quantity).
2. `python split.py` to produce `train.jsonl` + `validation.jsonl`.
3. Upload to your fine-tuning provider.
4. Copy the resulting model id into `backend/.env` as `GLORIA_MODEL_NAME`.
