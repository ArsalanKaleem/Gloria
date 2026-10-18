"""Create a new API key for a given application.

Usage:
    python -m scripts.create_api_key <application-name> [daily-limit]
"""

from __future__ import annotations

import sys

from app.auth.api_key import generate_api_key
from app.database import Base, SessionLocal, engine
from app.models.api_key import APIKey


def main() -> None:
    Base.metadata.create_all(bind=engine)

    app_name = sys.argv[1] if len(sys.argv) > 1 else "default"
    try:
        daily_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    except ValueError:
        print("daily-limit must be an integer.")
        sys.exit(1)

    full, prefix, hashed = generate_api_key()

    session = SessionLocal()
    try:
        session.add(APIKey(
            id=prefix,
            hashed_key=hashed,
            application=app_name,
            daily_limit=daily_limit,
        ))
        session.commit()
    finally:
        session.close()

    print("=" * 64)
    print(f"Application  : {app_name}")
    print(f"Prefix (id)  : {prefix}")
    print(f"Daily limit  : {daily_limit}")
    print(f"FULL KEY     : {full}")
    print("Store the FULL KEY securely. It will NOT be shown again.")
    print("=" * 64)


if __name__ == "__main__":
    main()
