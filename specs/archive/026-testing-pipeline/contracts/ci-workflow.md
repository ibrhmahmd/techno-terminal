# CI Workflow Contract

## Trigger

```yaml
on: [push, pull_request]
```

## Jobs

### Job 1: Backend Tests

| Property | Value |
|----------|-------|
| **Runner** | `ubuntu-latest` |
| **Service** | PostgreSQL 15 with health check (`pg_isready`) |
| **Python** | 3.10 |
| **Steps** | 1. Checkout<br>2. Setup Python 3.10<br>3. `pip install -e .`<br>4. `pip install pytest pytest-cov`<br>5. Apply schema: `psql "$DATABASE_URL" -f db/schema.sql`<br>6. Run tests: `pytest tests/ -v --cov=app --cov-report=term-missing` |
| **Env vars** | `DATABASE_URL: postgresql://postgres:postgres@localhost:5432/techno_test`<br>`SUPABASE_URL: https://test.supabase.co`<br>`SUPABASE_ANON_KEY: test-key`<br>`SUPABASE_SERVICE_ROLE_KEY: test-key`<br>`TWILIO_ACCOUNT_SID: test-sid`<br>`TWILIO_AUTH_TOKEN: test-token`<br>`TWILIO_WHATSAPP_FROM: whatsapp:+00000000000`<br>`GMAIL_SENDER_ADDRESS: test@test.com`<br>`GMAIL_APP_PASSWORD: test-password` |

### Job 2: Frontend Build

| Property | Value |
|----------|-------|
| **Runner** | `ubuntu-latest` |
| **Node** | 18 |
| **Steps** | 1. Checkout frontend repo<br>2. Setup Node 18<br>3. `npm ci`<br>4. `npm run build` |

## Failure Behavior

- If **Job 1** fails: The workflow run shows a red X. Test output and traceback are visible in the GitHub Actions log.
- If **Job 2** fails: The workflow run shows a red X. Build errors (TypeScript compilation failures, missing modules) are visible in the log.
- Both jobs run independently (not blocking each other) for faster feedback.

## Security

- No production credentials are stored in the workflow file
- External service credentials in the CI are test-only dummy values
- The CI runner is ephemeral — destroyed after job completion
- No secrets are passed from GitHub Secrets (all services mocked)
