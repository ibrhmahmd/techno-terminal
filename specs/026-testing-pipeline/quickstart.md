# Quickstart: Testing Pipeline

## Prerequisites

- PostgreSQL 15 installed locally (or Docker with `postgres:15`)
- Python 3.10+ with `.venv` activated
- Node.js 18+ (for frontend)
- Git

## Local Test Database Setup

### Option A: Native PostgreSQL

```powershell
# Create the test database
psql -U postgres -c "CREATE DATABASE techno;"

# Apply schema
psql -U postgres -d techno -f db/schema.sql

# Apply migrations (chronological order)
foreach ($f in (Get-ChildItem db/migrations/*.sql | Sort-Object Name)) {
    psql -U postgres -d techno -f $f.FullName
}
```

### Option B: Docker

```powershell
docker run -d --name techno-test-db `
  -e POSTGRES_DB=techno `
  -e POSTGRES_PASSWORD=postgres `
  -p 5432:5432 `
  postgres:15

# ... then same psql commands as above
```

## Running Backend Tests

```powershell
# .env.test is loaded automatically by config.py when pytest is detected
pytest tests/ -v

# Run specific test file
pytest tests/test_crm.py -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

## Running Frontend Validation

```powershell
cd ../techno_terminal_UI
npm install
npm run build
```

## CI Pipeline (GitHub Actions)

The CI pipeline runs automatically on every push and pull request. It:

1. Spins up a PostgreSQL 15 service container
2. Applies `db/schema.sql`
3. Runs `pytest tests/ -v`
4. Builds the frontend with `npm run build`

View workflow runs at: `https://github.com/[owner]/[repo]/actions`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `psql: could not connect to server` | Ensure PostgreSQL service is running (`pg_isready`) |
| `relation "students" does not exist` | Run `db/schema.sql` to create tables |
| Tests hit production DB | Check `.env` is not overriding `.env.test` — run with `TESTING=true` |
| `student_credits does not exist` | Your schema may be out of sync — re-apply `db/schema.sql` |
| CI fails on migration order | Some migration prefixes are duplicated (008, 020, 021, etc.) — apply chronologically |
