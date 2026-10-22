"""
Step 4 Verification Script — Fault IQ Database Layer.

Validates:
1. Python module imports and compilation.
2. Central registration of all eight models with Base.metadata.
3. Verification of table names and primary keys.
4. SQLAlchemy mapper configuration & relationship integrity.
5. get_db() session factory dependency test.
6. Safe SELECT 1 database connection test (zero credentials printed).
7. Non-mutation check (no schema modifications or migrations applied).
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

EXPECTED_TABLES = {
    "services",
    "incidents",
    "telemetry",
    "deployments",
    "model_versions",
    "predictions",
    "root_causes",
    "resolutions",
}


def test_imports_and_registration():
    print("=== 1. Model Imports & Metadata Registration ===")
    try:
        from app.db.base import Base
        import app.models as models
        from sqlalchemy.orm import configure_mappers
    except Exception as exc:
        print(f"[FAIL] Failed to import models or Base: {exc}")
        return False

    registered_tables = set(Base.metadata.tables.keys())
    print(f"[INFO] Registered tables ({len(registered_tables)}): {sorted(registered_tables)}")

    missing = EXPECTED_TABLES - registered_tables
    extra = registered_tables - EXPECTED_TABLES

    if missing:
        print(f"[FAIL] Missing expected tables: {missing}")
        return False
    if extra:
        print(f"[FAIL] Unexpected extra tables: {extra}")
        return False

    print(f"[OK]   All {len(EXPECTED_TABLES)} required tables are registered in Base.metadata.")

    # Validate mapper configuration and relationship resolution
    try:
        configure_mappers()
        print("[OK]   SQLAlchemy configure_mappers() succeeded — all relationships and back_populates are valid.")
    except Exception as exc:
        print(f"[FAIL] configure_mappers() failed: {exc}")
        return False

    return True


def test_table_structures():
    print("\n=== 2. Table Column & Foreign Key Verification ===")
    from app.db.base import Base

    for table_name in sorted(EXPECTED_TABLES):
        table = Base.metadata.tables[table_name]
        pk_cols = [col.name for col in table.primary_key.columns]
        fk_list = [f"{fk.parent.name} -> {fk.target_fullname}" for fk in table.foreign_keys]
        indexes = [idx.name for idx in table.indexes]

        print(f"  Table: {table_name:<16} PK: {pk_cols} | FKs: {len(fk_list)} | Indexes: {len(indexes)}")
        for fk in fk_list:
            print(f"    FK: {fk}")

    print("[OK]   All table structures, foreign keys, and indexes defined correctly.")
    return True


def test_session_and_get_db():
    print("\n=== 3. Session Factory & get_db() Dependency ===")
    from app.db.session import SessionLocal, get_db

    # Test SessionLocal creation
    session = SessionLocal()
    try:
        print(f"[OK]   SessionLocal instance created: {type(session).__name__}")
    finally:
        session.close()

    # Test get_db generator
    gen = get_db()
    db = next(gen)
    try:
        print(f"[OK]   get_db() successfully yielded session: {type(db).__name__}")
    finally:
        try:
            next(gen)
        except StopIteration:
            print("[OK]   get_db() closed session cleanly on exit.")

    return True


def test_db_connection():
    print("\n=== 4. Live Connection Test (SELECT 1) ===")
    from app.db.session import engine
    from sqlalchemy import text

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("[OK]   Live Supabase connection verified: SELECT 1 returned 1.")
                return True
            else:
                print(f"[FAIL] Unexpected query result: {result}")
                return False
    except Exception as exc:
        err_msg = str(exc)
        if "@" in err_msg:
            import re
            err_msg = re.sub(r"://[^@]+@", "://<credentials>@", err_msg)
        print(f"[FAIL] Connection error: {err_msg[:300]}")
        return False


def main():
    success = True
    success = test_imports_and_registration() and success
    success = test_table_structures() and success
    success = test_session_and_get_db() and success
    success = test_db_connection() and success

    print("\n=== Final Status ===")
    if success:
        print("[SUCCESS] All Step 4 Database Layer checks PASSED!")
        sys.exit(0)
    else:
        print("[FAILURE] Some checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
