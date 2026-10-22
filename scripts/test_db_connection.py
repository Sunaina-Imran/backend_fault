"""
Safe Supabase connection test.
- Runs SELECT 1 to verify connectivity.
- Never prints the password or full connection string.
"""
import re
import sys
from pathlib import Path

# Ensure backend root is on sys.path so app modules can be imported
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


def mask_url(url: str) -> str:
    """Return the URL with the password replaced by ***."""
    try:
        return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", url)
    except Exception:
        return "<unparseable URL>"

def main():
    try:
        from app.core.config import settings
        from app.db.session import _build_safe_url, engine
    except ImportError as exc:
        print(f"[IMPORT ERROR] {exc}")
        sys.exit(1)

    raw_url = settings.DATABASE_URL

    # --- Static analysis (no connection yet) ---
    print("=== Static Checks ===")

    # 1. Ensure DATABASE_URL is a single line (no embedded newlines)
    if "\n" in raw_url or "\r" in raw_url:
        print("[FAIL] DATABASE_URL contains embedded newline(s). Fix the .env file.")
    else:
        print("[OK]   DATABASE_URL is on a single line.")

    # 2. Verify _build_safe_url does not double-encode
    built = _build_safe_url(raw_url)
    built_again = _build_safe_url(built)          # idempotency check

    # Extract encoded passwords from both results for comparison
    def extract_encoded_password(url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).password or ""
        except Exception:
            return ""

    pw1 = extract_encoded_password(built)
    pw2 = extract_encoded_password(built_again)

    if pw1 == pw2:
        print("[OK]   _build_safe_url() is idempotent — no double-encoding.")
    else:
        print("[WARN] _build_safe_url() is NOT idempotent — possible double-encoding.")
        print(f"       First pass encoded password length : {len(pw1)}")
        print(f"       Second pass encoded password length: {len(pw2)}")

    print(f"[INFO] Safe URL (password masked): {mask_url(built)}")

    # --- Live connection test ---
    print("\n=== Connection Test ===")
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            value = result.scalar()
            if value == 1:
                print("[OK]   SELECT 1 returned 1 — Supabase connection SUCCEEDED.")
            else:
                print(f"[WARN] SELECT 1 returned unexpected value: {value!r}")
    except Exception as exc:
        # Print error type and a sanitised message — never the full URL
        err_type = type(exc).__name__
        err_msg = str(exc)
        # Strip any credential-like substrings from the message before printing
        if "@" in err_msg:
            # Mask from "://" to the last "@"
            import re
            err_msg = re.sub(r"://[^@]+@", "://<credentials>@", err_msg)
        print(f"[FAIL] Connection FAILED.")
        print(f"       Error type   : {err_type}")
        print(f"       Safe message : {err_msg[:500]}")
        sys.exit(1)

if __name__ == "__main__":
    main()
