# Quickstart: CI Test Coverage Verification

## Prerequisites

- GitHub repository with Actions enabled
- PostgreSQL 15 service container configured
- All dummy env vars set in CI workflow

## Running the Diagnostic

### Step 1 — Run all tests to capture failures
```bash
# From repo root — this runs the full suite (temporary)
pytest tests/ -v --tb=long 2>&1 | tee /tmp/ci_failures.txt
```

### Step 2 — Categorize failures
For each failure, identify the category:
- **Needs seed data**: "relation X not found", "FK violation", "NoneType has no attribute"
- **Needs mocking**: "connection refused", "HTTPConnectionPool", "SupabaseError"
- **Needs env var**: "KeyError: '...'", "NoneType has no attribute"
- **Real bug**: AssertionError with unexpected values

### Step 3 — Validate seed data
```bash
# Apply schema
cd db && psql "$DATABASE_URL" -f schema.sql

# Seed data (Python)
python -c "
from tests.seed_data import seed_database
from app.db.connection import get_session
with get_session() as session:
    result = seed_database(session)
    print(f'Created: {list(result.keys())}')
"
```

### Step 4 — Run specific module tests
```bash
# Test individual module after seeding
pytest tests/test_academics.py -v --tb=short
pytest tests/test_enrollments.py -v --tb=short
pytest tests/test_attendance.py -v --tb=short
```

## Expected Behavior

| Test File | Expected Status | Notes |
|-----------|----------------|-------|
| `test_finance.py` | ✅ Pass (32) | Already works without seed |
| `test_crm.py` | ✅ Pass (26) | Already works without seed |
| `test_error_handlers.py` | ✅ Pass (12) | No DB dependency |
| `test_auth.py` | ✅ Pass (36) | Uses mock tokens |
| `test_academics.py` | ⚠️ Needs seed | 24 tests |
| `test_analytics.py` | ⚠️ Needs seed | 21 tests |
| `test_attendance.py` | ⚠️ Needs seed | 27 tests |
| `test_hr.py` | ⚠️ Needs seed | 34 tests |
| `test_notifications.py` | ⚠️ Needs mocks | 16 tests |
| `test_competitions.py` | ⚠️ Needs seed | 22 tests |
| `test_enrollments.py` | ⚠️ Needs seed | 9 tests |
| `test_dashboard.py` | ⚠️ Needs seed | 10 tests |
| `test_session_level_integrity.py` | ⚠️ Needs seed | 18 tests |
| `*_full.py` (any) | ❌ May fail | Integration-heavy |
