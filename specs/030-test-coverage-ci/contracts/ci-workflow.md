# Contract: CI Workflow

**Branch**: `030-test-coverage-ci`
**File**: `.github/workflows/ci.yml`

## Main CI (Every Push)

### Steps
1. Checkout repository
2. Set up Python 3.10
3. Install dependencies (`pip install -e . && pip install pytest pytest-cov`)
4. Start PostgreSQL 15 service container
5. Install PostgreSQL client (`sudo apt-get install -y postgresql-client`)
6. Apply schema (`cd db && psql "$DATABASE_URL" -f schema.sql`)
7. Run schema verification (`python scripts/verify_test_db.py`)
8. Seed database (`python -c "from tests.seed_data import seed_database; seed_database(...)"`)
9. Run non-full test suites (`pytest tests/test_academics.py tests/test_analytics.py ... -v`)
10. Run coverage report

### Test Suites (Non-Full, Every Push)
```
tests/test_academics.py
tests/test_analytics.py
tests/test_attendance.py
tests/test_auth.py
tests/test_competitions.py
tests/test_crm.py
tests/test_dashboard.py
tests/test_enrollments.py
tests/test_error_handlers.py
tests/test_finance.py
tests/test_hr.py
tests/test_notifications.py
tests/test_session_level_integrity.py
```

### Env Variables
```yaml
DATABASE_URL: postgresql://postgres:postgres@localhost:5432/techno_test
SUPABASE_URL: https://test.supabase.co
SUPABASE_ANON_KEY: test-key
SUPABASE_SERVICE_ROLE_KEY: test-key
TWILIO_ACCOUNT_SID: test-sid
TWILIO_AUTH_TOKEN: test-token
TWILIO_WHATSAPP_FROM: whatsapp:+00000000000
GMAIL_SENDER_ADDRESS: test@test.com
GMAIL_APP_PASSWORD: test-password
CI: "true"
```

## Nightly CI (Cron: Midnight UTC)

### Schedule
```yaml
on:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:  # Manual trigger
```

### Same steps as Main CI, but runs ALL test suites including `*_full.py`
```yaml
- name: Run all tests
  run: pytest tests/ -v --tb=short
  timeout-minutes: 20
```

## Expected Outcomes

| Metric | Main CI | Nightly CI |
|--------|---------|------------|
| Tests run | ~580 (non-full) | ~864 (all) |
| Timeout | 10 min | 20 min |
| Coverage target | <5 failures | <50 failures (80%+) |
| Blocks PR merge | ✅ Yes | ❌ No (info only) |
