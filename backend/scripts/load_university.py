"""Load the university JSON knowledge base into Postgres.

Expected layout under ``data/university/``:
    departments/*.json   -> Department rows
    people/*.json        -> Person rows
    programs/*.json      -> Program rows
    officers/*.json      -> Officer rows

Each JSON file contains ONE record (an object) matching the model schema.
IDs are used as primary keys — repeated runs upsert cleanly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models.university import Department, Program, Person, Officer


def _load_dir(subdir: str) -> Iterable[dict]:
    root = Path(settings.UNIVERSITY_DATA_DIR) / subdir
    if not root.exists():
        return []
    for path in sorted(root.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  ! skipping {path}: {e}")
            continue
        if isinstance(data, list):
            yield from data
        else:
            yield data


def _upsert(session, model, rows):
    n = 0
    for row in rows:
        if "id" not in row:
            print(f"  ! skipping row without id: {row}")
            continue
        obj = session.get(model, row["id"])
        if obj is None:
            obj = model(**row)
            session.add(obj)
        else:
            for k, v in row.items():
                setattr(obj, k, v)
        n += 1
    return n


def main() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        counts = {
            "departments": _upsert(session, Department, _load_dir("departments")),
            "programs":    _upsert(session, Program,    _load_dir("programs")),
            "people":      _upsert(session, Person,     _load_dir("people")),
            "officers":    _upsert(session, Officer,    _load_dir("officers")),
        }
        session.commit()
    finally:
        session.close()

    for k, v in counts.items():
        print(f"{k:12s} upserted: {v}")


if __name__ == "__main__":
    main()
