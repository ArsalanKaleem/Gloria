"""Split fine-tuning/all.jsonl into train.jsonl / validation.jsonl (90/10)."""

import json
import random
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    src = root / "all.jsonl"
    train = root / "train.jsonl"
    val = root / "validation.jsonl"

    if not src.exists():
        print(f"No {src}. Create it first (one JSON object per line).")
        return

    records = []
    with src.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  ! line {i} is not valid JSON: {e}")

    if not records:
        print("all.jsonl is empty.")
        return

    random.seed(42)
    random.shuffle(records)
    split_at = max(1, int(len(records) * 0.9))

    with train.open("w", encoding="utf-8") as f:
        for r in records[:split_at]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with val.open("w", encoding="utf-8") as f:
        for r in records[split_at:]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Total   : {len(records)}")
    print(f"Train   : {split_at} -> {train}")
    print(f"Validate: {len(records) - split_at} -> {val}")


if __name__ == "__main__":
    main()
