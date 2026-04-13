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

### Table Inventory (16 Tables)

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| **parents** | Parent/guardian directory | student_parents (M:M) |
| **students** | Student profiles | enrollments, attendance, payments |
| **student_parents** | Junction: students ↔ parents | M:M relationship with metadata |
| **employees** | Staff directory | users, groups (instructor), sessions |
| **users** | System accounts (linked to Supabase) | employees, audit fields |
| **courses** | Course catalog | groups |
| **groups** | Course sections/cohorts | course, instructor, sessions, enrollments |
| **sessions** | Individual class meetings | group, attendance |
| **enrollments** | Student-group registrations | student, group, payments |
| **attendance** | Session attendance tracking | student, session, enrollment |
| **receipts** | Payment receipts | payments |
| **payments** | Financial transactions | receipt, student, enrollment |
| **competitions** | Competition events | competition_categories |
| **competition_categories** | Competition divisions | competition, teams |
| **teams** | Competition teams | category, group, team_members |
| **team_members** | Students in teams | team, student |

### View Inventory (5 Views)

| View | Purpose |
|------|---------|
| **v_students** | Student details with aggregated info |
| **v_enrollment_balance** | Real-time balance per enrollment |
| **v_enrollment_attendance** | Attendance stats per enrollment |
| **v_siblings** | Sibling relationships for families |
| **v_group_session_count** | Session counts per group |

### Key Database Features

**Triggers (Migration 019)**
- `update_student_balance()` - Auto-recalculates balance on payment changes
- Materialized view refresh for performance

**Check Constraints (Migrations 020, 021)**
- `groups_status_check` - Validates status: active, inactive, completed, archived
- `attendance_status_check` - Validates: present, absent, cancelled

**Indexes**
- `idx_enrollments_active_unique` - Prevents duplicate active enrollments per student/group
- `receipts_paid_at_index` - Optimizes payment date range queries

### Migration History (21 Files)
Sequential migrations from 002-021 covering:
- Supabase roles, employee identity, audit timestamps
- Enrollment balance, parent-guardian rename
- Competition fees, group lifecycle, waiting status
- Balance tables, payment allocations, activity logging
- Receipt enhancements, balance triggers, history views
- Status constraint fixes (020, 021)

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
