
import re
from urllib.parse import quote, unquote

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def _build_safe_url(raw_url: str) -> str:
    """
    Reconstruct a PostgreSQL connection URL that is safe for psycopg v3.

    Problems this solves:
    1. Plain "postgresql://" maps to psycopg2; rewrite to "postgresql+psycopg://".
    2. Passwords containing special chars like "@" break naive URL parsing;
       split on the *last* "@" and percent-encode the credentials block.
    """
    # Normalise driver
    if raw_url.startswith("postgres://"):
        raw_url = "postgresql" + raw_url[len("postgres"):]

    # Switch to psycopg v3 dialect
    raw_url = re.sub(r"^postgresql(\+[^:]+)?://", "postgresql+psycopg://", raw_url)

    # Split scheme from the rest: "postgresql+psycopg://user:pass@host/db"
    scheme, rest = raw_url.split("://", 1)

    # Split on the LAST "@" so embedded "@" in the password stays in credentials
    at_pos = rest.rfind("@")
    if at_pos == -1:
        # No credentials — URL is already fine
        return f"{scheme}://{rest}"

    credentials = rest[:at_pos]        # "user:password (may contain @)"
    host_db = rest[at_pos + 1:]        # "host:port/db"

    # Separate user and password (split on the FIRST ":")
    colon_pos = credentials.find(":")
    if colon_pos == -1:
        user, password = credentials, ""
    else:
        user = credentials[:colon_pos]
        password = credentials[colon_pos + 1:]

    # Percent-encode only the password (unquote first for idempotency)
    encoded_password = quote(unquote(password), safe="")

    return f"{scheme}://{user}:{encoded_password}@{host_db}"


_db_url = _build_safe_url(settings.DATABASE_URL)

engine = create_engine(
    _db_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    """FastAPI dependency that yields a database session and closes it on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
