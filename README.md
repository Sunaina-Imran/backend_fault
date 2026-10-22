# Fault IQ — Backend

Fault IQ is an AI-powered system for automated incident detection, telemetry analysis, severity prediction, root-cause analysis, and remediation recommendations.

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0 (Declarative Base)
- **Database**: PostgreSQL (Supabase) via `psycopg` (v3)
- **Migrations**: Alembic
- **Validation**: Pydantic v2 & `pydantic-settings`
- **Testing**: Pytest & HTTPX TestClient

## Project Structure

```
backend_fault/
├── alembic/              # Alembic migration environment and version scripts
│   ├── env.py
│   └── versions/         # Database migration revisions
├── app/
│   ├── api/routes/       # API endpoints (health, etc.)
│   ├── core/             # Application configuration & settings
│   ├── db/               # Database engine, session maker, and Base
│   ├── models/           # SQLAlchemy 2.0 ORM models (8 core tables)
│   ├── schemas/          # Pydantic schemas & response models
│   └── main.py           # FastAPI application entry point
├── scripts/              # Seed, audit, and verification scripts
│   ├── audit_pre_migration.py
│   ├── seed_services.py
│   ├── test_db_connection.py
│   ├── verify_step4_db.py
│   └── verify_step7_fastapi.py
├── tests/                # Automated pytest test suite
├── .env.example          # Environment variable template
├── .gitignore            # Git exclusion rules
├── alembic.ini           # Alembic configuration
└── requirements.txt      # Project dependencies
```

## Database Schema

The backend defines 8 core tables with full relationship integrity:
1. `services` — Core microservices catalogue with health & metadata
2. `incidents` — Tracked outages and system degradations
3. `telemetry` — Metrics, error counts, latency, and CPU/memory signals
4. `deployments` — Service deployment logs and commit references
5. `model_versions` — Machine learning model registry
6. `predictions` — AI incident predictions and risk scores
7. `root_causes` — Identified primary root causes with confidence ratings
8. `resolutions` — Action plans and remediation runbooks

## Setup & Running Locally

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase PostgreSQL credentials
   ```

4. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Start the development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Interactive Documentation**:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - Health check: `http://localhost:8000/health`

## Testing & Verification

Run the test suite:
```bash
pytest -v
```

Run verification scripts:
```bash
python scripts/verify_step4_db.py
python scripts/verify_step7_fastapi.py
```
