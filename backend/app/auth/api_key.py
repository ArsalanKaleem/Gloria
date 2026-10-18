"""API key generation and verification."""

import secrets
from datetime import datetime
from typing import Tuple

from fastapi import Depends, Header, HTTPException, status
from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.api_key import APIKey


PREFIX_TAG = "gl_pub_"


def generate_api_key() -> Tuple[str, str, str]:
    """Return (full_key, public_prefix, bcrypt_hash).

    Full key format:   gl_pub_<prefix>.<secret>
    Only the prefix is stored as the primary key; only the bcrypt hash of
    the FULL key is stored for verification.
    """
    prefix = PREFIX_TAG + secrets.token_hex(4)      # non-secret identifier
    secret = secrets.token_urlsafe(32)              # actual secret
    full = f"{prefix}.{secret}"
    return full, prefix, bcrypt.hash(full)


def require_api_key(
    authorization: str = Header(default=None),
    db: Session = Depends(get_db),
) -> APIKey:
    """FastAPI dependency: verify a Bearer API key against the DB."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    token = authorization[len("Bearer "):].strip()
    if "." not in token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Malformed API key")

    prefix = token.split(".", 1)[0]
    record = (
        db.query(APIKey)
        .filter(APIKey.id == prefix, APIKey.active == True)  # noqa: E712
        .first()
    )
    if not record or not bcrypt.verify(token, record.hashed_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")

    record.last_used_at = datetime.utcnow()
    db.commit()
    return record
