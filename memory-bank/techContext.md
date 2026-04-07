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
fastapi, uvicorn            # API server
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
- **15 tables:** parents, employees, users, students, student_parents, courses, groups, sessions, enrollments, attendance, receipts, payments, competitions, competition_categories, teams, team_members
- **5 views:** v_students, v_enrollment_balance, v_enrollment_attendance, v_siblings, v_group_session_count

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
- **Coverage:** 94% of endpoints (75/80)
- **Isolation:** Transaction rollback per test
- **Mocking:** JWT mocks for expired/invalid tokens
- **Token Management:** Regenerate hourly via `scripts/get_test_jwt.py`
