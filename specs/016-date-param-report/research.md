# Research: Date-Parameterized Daily Report Endpoints

## Key Decisions
1. Single POST endpoint with two modes (PDF base64 vs email) based on presence of `email_recipients` body field
2. Separate GET `/data` endpoint for JSON-only access
3. `target_date` as optional query param (defaults to today) — most REST-friendly
4. 404 for dates with no data (sessions_held=0 AND payment_count=0 AND new_enrollments=0)
5. Email validation via regex in Pydantic validator
6. PDF generation runs in thread pool via `asyncio.to_thread` to avoid blocking the event loop
7. Email dispatch uses `asyncio.create_task` for fire-and-forget sending

## Existing Patterns
- `POST /reports/daily` already exists — extended with optional params
- Thread pool pattern used elsewhere for blocking operations
- `ApiResponse` envelope for all responses
- Auth: `require_admin` guard (same as existing)
