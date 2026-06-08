# Data Model: Testing Environment Configuration

## Environment Configuration (`.env.test`)

The `.env.test` file provides all environment variables needed to run tests against a local PostgreSQL database. It mirrors `.env` structure but points to a local/test database.

| Variable | Purpose | Production vs Test |
|----------|---------|--------------------|
| `DATABASE_URL` | PostgreSQL connection string | **Production**: Supabase cloud DB<br>**Test**: `localhost:5432/techno` |
| `SUPABASE_URL` | Supabase project URL | Same value (no real auth calls in tests — mocked) |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Same value (not used when auth is overridden) |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Same value (not used when auth is overridden) |
| `TWILIO_ACCOUNT_SID` | Twilio account identifier | Can be real sandbox or dummy value (dispatchers mocked) |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | Can be real sandbox or dummy value (dispatchers mocked) |
| `TWILIO_WHATSAPP_FROM` | Twilio WhatsApp sender | Can be real sandbox or dummy value |
| `GMAIL_SENDER_ADDRESS` | Gmail sender email | Can be real or dummy value (dispatchers mocked) |
| `GMAIL_APP_PASSWORD` | Gmail app password | Can be real or dummy value (dispatchers mocked) |
| `LOG_LEVEL` | Logging verbosity | `INFO` in both environments |

## Configuration Loading (`app/core/config.py`)

The `Settings` class auto-detects test context at import time:

```
.env (production) ← default env_file
        ↑
pytest detected? → .env.test (test env_file)
```

Detection triggers (line 106):
- `pytest` in `sys.modules`
- `PYTEST_CURRENT_TEST` in `os.environ`
- `TESTING=true` in `os.environ`

## CI Environment (GitHub Actions)

The CI workflow provides all variables through GitHub Actions `env:` or `secrets:` context. Supabase/Twilio/Gmail values are set to test-safe defaults when real credentials are not available, since all external services are mocked in tests.

## Test Database Schema

The local test database must have the same schema as production:

```text
db/schema.sql ──────────→ Applies all 17 modular files in order
    ├── 00_extensions.sql       (pgcrypto, uuid-ossp)
    ├── 01_enums.sql             (custom enum types)
    ├── 02_tables_core.sql       (users, branches, etc.)
    ├── 03_tables_crm.sql        (students, parents, etc.)
    ├── 05_tables_enrollments.sql
    ├── 06_tables_finance.sql
    ├── 07_tables_competitions.sql
    ├── 08_tables_notifications.sql
    ├── 10_tables_supabase.sql
    ├── 20_indexes.sql
    ├── 30_views.sql
    ├── 40_functions.sql
    ├── 50_triggers.sql
    ├── 60_constraints.sql
    └── 90_seed_data.sql (optional — test data)
```

Migrations in `db/migrations/` are applied on top in chronological order.
