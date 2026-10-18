"""Structured search over the SQL side (Postgres).

Queries like "email of HOD of computer science" are tokenised so that
words like "computer" and "science" match the department, not the whole
literal string.
"""
from __future__ import annotations

import re
from typing import List, Optional

from sqlalchemy import or_

from app.config import settings
from app.database import SessionLocal
from app.models.university import Person, Department, Program


# Words that shouldn't drive a match — they're too generic and appear
# everywhere. Keep this list tight; over-filtering makes queries miss.
_STOPWORDS = {
    # Grammar
    "a", "an", "the", "of", "for", "at", "in", "on", "to", "from", "by",
    "is", "are", "was", "were", "be", "been", "am",
    "and", "or", "but", "not",
    # Question words
    "who", "what", "which", "when", "where", "why", "how",
    # Pronouns
    "me", "my", "you", "your", "we", "our", "they", "their", "it", "its",
    # Verbs that don't help matching
    "please", "tell", "give", "show", "find", "get", "list", "want", "need",
    # Titles — noisy, most people rows already have them
    "sir", "madam", "mr", "mrs", "ms", "dr", "prof",
    # Very generic
    "university",
}
# The university's own name appears in every record, so it never helps.
_STOPWORDS |= {
    w.lower() for w in re.findall(r"[A-Za-z]+", f"{settings.UNIVERSITY_FULL_NAME} {settings.UNIVERSITY_NAME} {settings.UNIVERSITY_SHORT_NAME}")
}

# Bulk-listing signals: widens the result cap so "list all faculty"
# actually returns everyone, not just the top 10.
_BULK_RX = re.compile(
    r"\b(all|every|list|everyone|whole|full)\s+(the\s+)?"
    r"(faculty|staff|hod|hods|contact|contacts|email|emails|"
    r"phone|phones|people|admin|administration)",
    re.I,
)

_WORD_RX = re.compile(r"[a-zA-Z][a-zA-Z\-]{1,}")


def _tokenise(query: str) -> List[str]:
    """Return meaningful, lowercased words from the query."""
    words = _WORD_RX.findall(query.lower())
    tokens = [w for w in words if w not in _STOPWORDS and len(w) > 2]
    # De-duplicate while preserving order.
    seen = set()
    unique = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def _score_row(row, tokens: List[str], fields: List[str]) -> int:
    """Count how many query tokens appear across the given row fields."""
    hay = " ".join(str(getattr(row, f, "") or "") for f in fields).lower()
    return sum(1 for t in tokens if t in hay)


def search_people(query: str, department: Optional[str] = None, limit: int = 10) -> List[dict]:
    db = SessionLocal()
    try:
        q = db.query(Person)
        if department:
            q = q.filter(Person.department.ilike(f"%{department}%"))

        # Bulk-listing queries: widen the net so the LLM can enumerate.
        if _BULK_RX.search(query):
            limit = max(limit, 40)

        tokens = _tokenise(query)

        if tokens:
            # Match rows where ANY meaningful token appears in ANY searchable field.
            clauses = []
            for t in tokens:
                like = f"%{t}%"
                clauses.extend([
                    Person.name.ilike(like),
                    Person.designation.ilike(like),
                    Person.specialization.ilike(like),
                    Person.department.ilike(like),
                ])
            q = q.filter(or_(*clauses))
        else:
            # No meaningful tokens — fall back to literal match.
            like = f"%{query}%"
            q = q.filter(or_(
                Person.name.ilike(like),
                Person.designation.ilike(like),
                Person.specialization.ilike(like),
                Person.department.ilike(like),
            ))

        rows = q.limit(limit * 3).all()  # get more, then rank

        # Rank by number of tokens matched, best first.
        if tokens:
            rows = sorted(
                rows,
                key=lambda r: _score_row(r, tokens, ["name", "designation", "department", "specialization"]),
                reverse=True,
            )[:limit]

        return [{
            "id": r.id,
            "name": r.name,
            "designation": r.designation,
            "department": r.department,
            "email": r.email,
            "phone": r.phone,
            "specialization": r.specialization,
            "source": r.source or r.profile_url,
        } for r in rows]
    finally:
        db.close()


def search_department(query: str, limit: int = 10) -> List[dict]:
    db = SessionLocal()
    try:
        # Bulk-listing → widen.
        if _BULK_RX.search(query):
            limit = max(limit, 40)

        tokens = _tokenise(query)

        if tokens:
            clauses = []
            for t in tokens:
                like = f"%{t}%"
                clauses.extend([
                    Department.name.ilike(like),
                    Department.description.ilike(like),
                ])
            rows = db.query(Department).filter(or_(*clauses)).limit(limit * 3).all()
            rows = sorted(
                rows,
                key=lambda r: _score_row(r, tokens, ["name", "description"]),
                reverse=True,
            )[:limit]
        else:
            like = f"%{query}%"
            rows = db.query(Department).filter(or_(
                Department.name.ilike(like),
                Department.description.ilike(like),
            )).limit(limit).all()

        return [{
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "contact_email": r.contact_email,
            "contact_phone": r.contact_phone,
            "source": r.source,
        } for r in rows]
    finally:
        db.close()


def search_program(query: str, limit: int = 10) -> List[dict]:
    db = SessionLocal()
    try:
        # Bulk-listing → widen.
        if _BULK_RX.search(query):
            limit = max(limit, 40)

        tokens = _tokenise(query)

        if tokens:
            clauses = []
            for t in tokens:
                like = f"%{t}%"
                clauses.extend([
                    Program.name.ilike(like),
                    Program.description.ilike(like),
                    Program.department.ilike(like),
                ])
            rows = db.query(Program).filter(or_(*clauses)).limit(limit * 3).all()
            rows = sorted(
                rows,
                key=lambda r: _score_row(r, tokens, ["name", "description", "department"]),
                reverse=True,
            )[:limit]
        else:
            like = f"%{query}%"
            rows = db.query(Program).filter(or_(
                Program.name.ilike(like),
                Program.description.ilike(like),
                Program.department.ilike(like),
            )).limit(limit).all()

        return [{
            "id": r.id,
            "name": r.name,
            "department": r.department,
            "level": r.level,
            "duration": r.duration,
            "credit_hours": r.credit_hours,
            "admission_requirements": r.admission_requirements,
            "description": r.description,
            "source": r.source,
        } for r in rows]
    finally:
        db.close()