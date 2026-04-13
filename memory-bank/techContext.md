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

### Table Inventory (30 Tables - Verified via Supabase)

| # | Table | Columns | Purpose | Category |
|---|-------|---------|---------|----------|
| 1 | **attendance** | 7 | Session attendance tracking | Core |
| 2 | **competition_categories** | 4 | Competition divisions | Core |
| 3 | **competitions** | 8 | Competition events | Core |
| 4 | **courses** | 10 | Course catalog | Core |
| 5 | **employees** | 17 | Staff directory | Core |
| 6 | **enrollments** | 14 | Student-group registrations | Core |
| 7 | **groups** | 15 | Course sections/cohorts | Core |
| 8 | **parents** | 9 | Parent/guardian directory | Core |
| 9 | **payments** | 11 | Financial transactions | Core |
| 10 | **receipts** | 14 | Payment receipts | Core |
| 11 | **sessions** | 14 | Individual class meetings | Core |
| 12 | **student_parents** | 5 | Junction: students ↔ parents | Core |
| 13 | **students** | 16 | Student profiles | Core |
| 14 | **team_members** | 5 | Students in teams | Core |
| 15 | **teams** | 11 | Competition teams | Core |
| 16 | **users** | 8 | System accounts (Supabase) | Core |
| 17 | **enrollment_balance_history** | 10 | Historical balance changes | History |
| 18 | **enrollment_level_history** | 10 | Level progression tracking | History |
| 19 | **generated_receipts** | 11 | Generated receipt records | History |
| 20 | **group_competition_participation** | 12 | Group-competition linkage | History |
| 21 | **group_course_history** | 9 | Course assignment history | History |
| 22 | **group_levels** | 14 | Group level progression | History |
| 23 | **payment_allocations** | 10 | Payment distribution | History |
| 24 | **receipt_templates** | 13 | Configurable templates | History |
| 25 | **student_activity_log** | 10 | Audit trail of actions | History |
| 26 | **student_balances** | 7 | Current balance snapshot | History |
| 27 | **student_competition_history** | 14 | Competition participation | History |
| 28 | **student_credits** | 10 | Credit balance tracking | History |
| 29 | **student_enrollment_history** | 15 | Enrollment lifecycle | History |
| 30 | **student_payment_history** | 20 | Payment transaction history | History |

### View Inventory (12 Views)

| # | View | Columns | Purpose |
|---|------|---------|---------|
| 1 | **v_students** | 13 | Student details with aggregated info |
| 2 | **v_enrollment_balance** | 9 | Real-time balance per enrollment |
| 3 | **v_enrollment_attendance** | 3 | Attendance stats per enrollment |
| 4 | **v_siblings** | 5 | Sibling relationships for families |
| 5 | **v_group_session_count** | 5 | Session counts per group |
| 6 | **v_course_stats** | 6 | Course-level statistics |
| 7 | **v_daily_collections** | 7 | Daily payment collections summary |
| 8 | **v_payment_allocations_detailed** | 17 | Detailed payment allocation view |
| 9 | **v_student_activity_timeline** | 13 | Chronological student activity |
| 10 | **v_student_financial_summary** | 13 | Student financial overview |
| 11 | **v_student_payment_history** | 26 | Payment history with details |
| 12 | **v_unpaid_enrollments** | 16 | Unpaid enrollment listing |

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
