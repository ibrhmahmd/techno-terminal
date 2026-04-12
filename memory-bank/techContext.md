# Tech Context — Stack & Dependencies

## Core Stack
- **Backend:** FastAPI + SQLModel + SQLAlchemy + PostgreSQL
- **Auth:** Supabase (JWT verification, user management)
- **UI (Current):** Streamlit + Pandas
- **UI (Planned):** Vite + React 18 + TypeScript + TanStack Query + Zustand

## Key Dependencies
```
streamlit, pandas          # Dashboard/Reports
sqlmodel, psycopg2-binary   # ORM & DB driver
alembic                     # Migration tracking
fastapi, uvicorn, gunicorn  # API server + production WSGI
httpx, python-jose          # HTTP client & JWT
supabase                    # Auth service
pydantic-settings           # Configuration
```

## Environment Variables
```
DATABASE_URL              # PostgreSQL connection
SUPABASE_URL             # Auth service endpoint
SUPABASE_ANON_KEY        # Client-side auth
SUPABASE_SERVICE_ROLE_KEY # Admin operations (HR user creation)
PDF_LOGO_PATH            # Optional PDF branding
```

## Database Schema
- **16 tables:** parents, employees, users, students, student_parents, courses, groups, sessions, enrollments, attendance, receipts, payments, competitions, competition_categories, teams, team_members
- **5 views:** v_students, v_enrollment_balance, v_enrollment_attendance, v_siblings, v_group_session_count
- **21 migrations:** in `db/migrations/` (002-021, sequential)
- **Recent fixes:** Migration 020 (groups status constraint), 021 (attendance status constraint)

## Development Commands
```bash
# UI
python run_ui.py

# API
python run_api.py

# Tests
pytest tests/ -v

# Database (greenfield)
psql $DATABASE_URL -f db/schema.sql
alembic stamp 001_baseline_v33
```

## Testing Infrastructure
- **Framework:** pytest with async support
- **Modules:** 20 test files in `tests/`
- **Coverage:** 94% of endpoints (161 tests, 160 passing)
- **Isolation:** Transaction rollback per test via `get_session()`
- **Fixtures:** client, admin_token, admin_headers, db_session in conftest.py
- **Mocking:** JWT mocks in `tests/utils/jwt_mocks.py`
- **Token Management:** Regenerate hourly via `scripts/get_test_jwt.py`

## Deployment Configuration

**Platform:** Leapcell

**Configuration File:** `railpack.json`
```json
{
  "_cache_bust": "v4",
  "build": {"cmd": "pip install -e ."},
  "start": {
    "cmd": "gunicorn app.api.main:app -k uvicorn.workers.UvicornWorker \\"
          "--bind 0.0.0.0:8000 --workers 2 --timeout 300 --graceful-timeout 60 \\"
          "--pid /tmp/gunicorn.pid --worker-tmp-dir /tmp"
  }
}
```

**Key Settings:**
- **Timeout:** 300s (increased from 120s for slow startup)
- **Graceful Timeout:** 60s
- **Workers:** 2 Uvicorn workers
- **Temp Directory:** `/tmp` (avoids read-only filesystem issues)
- **Health Check:** `/health` endpoint

**Live URL:** https://techno-terminal-ibrhmahmd2165-00zb1kxm.leapcell.dev
