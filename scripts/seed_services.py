"""
Step 6 Seed Script — Fault IQ: Seed Initial Services in Supabase.

Seeds the 5 initial core microservices:
- gateway
- auth
- orders
- payments
- notifications

Requirements satisfied:
1. Reusable and idempotent: re-running does not produce duplicates.
2. Uses existing database session and configuration (app.db.session.SessionLocal).
3. Zero credential leakage: credentials are never logged or printed.
4. Sensible development values matching Service model without inventing repo URLs or team names.
5. Verifies that all five services exist exactly once in Supabase.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.models.service import Service

# Initial service definitions matching the requirements and actual model
SERVICES_TO_SEED: List[Dict[str, Optional[str]]] = [
    {
        "name": "gateway",
        "description": "API Gateway and reverse proxy routing incoming external traffic.",
        "tier": "tier-1",
        "owner_team": None,
        "repo_url": None,
        "is_active": True,
    },
    {
        "name": "auth",
        "description": "Authentication and authorization service managing user identity, sessions, and tokens.",
        "tier": "tier-1",
        "owner_team": None,
        "repo_url": None,
        "is_active": True,
    },
    {
        "name": "orders",
        "description": "Order management service processing customer orders, status transitions, and lifecycle events.",
        "tier": "tier-1",
        "owner_team": None,
        "repo_url": None,
        "is_active": True,
    },
    {
        "name": "payments",
        "description": "Payment processing service handling billing, payments, refunds, and transaction logging.",
        "tier": "tier-1",
        "owner_team": None,
        "repo_url": None,
        "is_active": True,
    },
    {
        "name": "notifications",
        "description": "Notification dispatch service delivering real-time alerts, emails, SMS, and webhooks.",
        "tier": "tier-2",
        "owner_team": None,
        "repo_url": None,
        "is_active": True,
    },
]


def inspect_services_schema() -> bool:
    """Verify that the services table and unique constraint exist before seeding."""
    print("=" * 70)
    print("1. PRE-FLIGHT SCHEMA INSPECTION")
    print("=" * 70)
    insp = inspect(engine)
    public_tables = insp.get_table_names(schema="public")
    if "services" not in public_tables:
        print("[FAIL] 'services' table does not exist in Supabase 'public' schema.")
        return False

    columns = {col["name"]: col for col in insp.get_columns("services", schema="public")}
    expected_cols = {"id", "name", "description", "tier", "owner_team", "repo_url", "is_active", "created_at", "updated_at"}
    missing_cols = expected_cols - set(columns.keys())
    if missing_cols:
        print(f"[FAIL] 'services' table is missing expected columns: {missing_cols}")
        return False

    indexes = insp.get_indexes("services", schema="public")
    name_unique = any(idx.get("unique") and "name" in idx.get("column_names", []) for idx in indexes)
    if not name_unique:
        print("[WARNING] Unique index on 'name' column not found in database metadata.")
    else:
        print("[OK]   'services' table schema and unique constraint on 'name' verified.")

    print(f"[OK]   Table columns verified: {sorted(columns.keys())}")
    return True


def seed_services(db: Optional[Session] = None) -> Tuple[List[Service], List[Service]]:
    """
    Seed initial services idempotently.

    Returns:
        Tuple of (inserted_records, skipped_records)
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    inserted: List[Service] = []
    skipped: List[Service] = []

    try:
        for item in SERVICES_TO_SEED:
            service_name = item["name"]
            stmt = select(Service).where(Service.name == service_name)
            existing = db.execute(stmt).scalar_one_or_none()

            if existing is not None:
                skipped.append(existing)
            else:
                new_service = Service(
                    name=item["name"],
                    description=item["description"],
                    tier=item["tier"],
                    owner_team=item["owner_team"],
                    repo_url=item["repo_url"],
                    is_active=item["is_active"],
                )
                db.add(new_service)
                inserted.append(new_service)

        if inserted:
            db.commit()
            for record in inserted:
                db.refresh(record)

        return inserted, skipped

    except Exception:
        db.rollback()
        raise
    finally:
        if should_close:
            db.close()


def verify_services(db: Optional[Session] = None) -> bool:
    """Verify that all five service names exist exactly once in the database."""
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        print("\n" + "=" * 70)
        print("3. VERIFICATION OF SEEDED SERVICES IN SUPABASE")
        print("=" * 70)

        # Query all records in services table
        all_services = db.execute(select(Service).order_by(Service.name)).scalars().all()
        by_name: Dict[str, List[Service]] = {}
        for s in all_services:
            by_name.setdefault(s.name, []).append(s)

        expected_names = [s["name"] for s in SERVICES_TO_SEED]
        all_ok = True

        print(f"Total services currently in database: {len(all_services)}")
        print(f"{'Name':<15} {'ID':<38} {'Tier':<8} {'Active':<8} {'Owner Team':<12} {'Repo URL'}")
        print("-" * 100)

        for s in all_services:
            print(
                f"{s.name:<15} {str(s.id):<38} {str(s.tier):<8} {str(s.is_active):<8} "
                f"{str(s.owner_team):<12} {str(s.repo_url)}"
            )

        print("-" * 100)

        # Check each expected service
        for name in expected_names:
            matches = by_name.get(name, [])
            if len(matches) == 0:
                print(f"[FAIL] Expected service '{name}' was not found in database.")
                all_ok = False
            elif len(matches) > 1:
                print(f"[FAIL] Duplicate service found for '{name}': {len(matches)} occurrences.")
                all_ok = False
            else:
                print(f"[OK]   Service '{name}' exists exactly once (ID: {matches[0].id}).")

        # Check total count against expected count
        if len(all_services) != len(expected_names):
            print(f"[WARNING] Database contains {len(all_services)} services, expected {len(expected_names)}.")
        else:
            print(f"[OK]   Database contains exactly {len(expected_names)} services.")

        return all_ok

    finally:
        if should_close:
            db.close()


def main():
    # 1. Pre-flight schema inspection
    if not inspect_services_schema():
        print("[ABORT] Schema check failed. Halting without mutating database.")
        sys.exit(1)

    # 2. Seed services
    print("\n" + "=" * 70)
    print("2. SEEDING SERVICES")
    print("=" * 70)
    try:
        inserted, skipped = seed_services()
    except Exception as exc:
        err_msg = str(exc)
        # Sanitize credentials in output if present
        if "@" in err_msg:
            import re
            err_msg = re.sub(r"://[^@]+@", "://<credentials>@", err_msg)
        print(f"[FAIL] Seeding failed with error: {err_msg}")
        sys.exit(1)

    print(f"Candidate services to seed: {len(SERVICES_TO_SEED)}")
    print(f"Newly inserted records:     {len(inserted)}")
    print(f"Skipped existing records:   {len(skipped)}")

    if inserted:
        print("\nInserted Records:")
        for s in inserted:
            print(f"  + [NEW]  name='{s.name}' id={s.id} tier='{s.tier}' is_active={s.is_active}")

    if skipped:
        print("\nSkipped Existing Records:")
        for s in skipped:
            print(f"  ~ [SKIP] name='{s.name}' id={s.id} tier='{s.tier}' is_active={s.is_active}")

    # 3. Verification
    verification_success = verify_services()

    # 4. Final summary
    print("\n" + "=" * 70)
    print("4. SUMMARY")
    print("=" * 70)
    if verification_success:
        print("[SUCCESS] Step 6 service seeding and verification completed successfully!")
        sys.exit(0)
    else:
        print("[FAILURE] Verification checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
