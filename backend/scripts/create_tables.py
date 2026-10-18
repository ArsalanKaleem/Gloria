"""Create all tables. Idempotent — safe to run repeatedly."""

from app.database import Base, engine
from app.models import api_key, university  # noqa: F401 (register models)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Tables created / verified.")


if __name__ == "__main__":
    main()
