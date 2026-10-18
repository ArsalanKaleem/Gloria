"""APIKey model — stores only the hashed key, never the plaintext."""

from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean, Integer

from app.database import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True)               # public prefix, e.g. "gl_pub_ab12cd34"
    hashed_key = Column(String, nullable=False)         # bcrypt hash of the FULL key
    application = Column(String, nullable=False)        # "sau-portal", "lms", ...
    active = Column(Boolean, default=True, nullable=False)
    daily_limit = Column(Integer, default=1000, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
