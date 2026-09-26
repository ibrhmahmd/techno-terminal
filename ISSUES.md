# Issues

## #1 — Scheduled daily report email does not send

**Status:** 🟡 IN PROGRESS: planning via wayfinder map `.scratch/reliable-report-delivery/map.md` (2026-09-25). The implementation plan below is superseded by that map.
**Type:** bug
**Lane:** refactor
**Created:** 2026-09-19

### Description
The scheduled daily business report email never arrives. Other notification
emails (payment, enrollment) work fine, so the email dispatch mechanism itself
is not the issue — the problem is scoped to the daily report path specifically.

### Diagnosis (Phase 2)
Traced `app/modules/notifications/services/report_scheduler.py` →
`report_notifications.py::send_daily_report()`.

Found two silent-skip points with no error/log escalation:
1. `daily_report` template missing or `is_active=False` → logs a warning, returns.
2. `_resolve_notification_recipients("daily_report")` returns an empty list →
   the send loop has nothing to iterate, so nothing is sent, no error raised.

The recipient query (`base_notification_service.py::_resolve_notification_recipients`)
requires a row in `admin_notification_settings` with
`notification_type = 'daily_report' AND is_enabled = true` for at least one admin.

**Leading hypothesis:** no admin has `daily_report` enabled in
`admin_notification_settings`, so recipients resolve to `[]` and the report is
silently skipped every day. Payment/enrollment notifications use a different
`notification_type` value that presumably *is* enabled, which is why those work.

There is also an existing watchdog (`report_watchdog.py`) built specifically to
catch this failure mode by checking `notification_logs` for a `SENT` row after
the send window — worth checking whether the watchdog itself is also silently
failing, or whether it has been alerting and was missed.

### Root Cause (confirmed against production DB)
Recipients and template are correctly configured (ruled out original hypothesis).
Actual cause: **architectural** — `start_report_scheduler()` and
`start_report_watchdog()` are both in-process `while True: await asyncio.sleep(60)`
loops that only fire if the process is alive at the exact scheduled clock minute
(currently 01:31 Cairo time, a dead-traffic hour). Hosted on **FastAPI Cloud**,
which — per the project's own history — can suspend idle containers. The Aug 31
commit `c9ca5fa` ("make scheduled report failures visible... masking the
post-FastAPI-Cloud report outage") confirms this exact failure already happened
once before on this host. Last successful `daily_report` send: **2026-09-04**
(15 days ago), zero log rows since (not even FAILED — the loop never gets CPU
time at the trigger minute, so it never even starts the send).

### Bug #2 (discovered during diagnosis, scoped in with #1 per user decision)
Gmail SMTP auth is currently failing (`535 Bad Credentials`) for
`payment_receipt` and `enrollment_confirmation` as of 2026-09-18 — a live,
ongoing outage affecting all outgoing email, not just reports.

### Implementation Plan (Phase 3 — agreed with user)

**Bug #1 — Scheduler reliability:**
1. Add authenticated internal HTTP trigger endpoints:
   - `POST /internal/notifications/trigger-daily-report`
   - `POST /internal/notifications/trigger-weekly-report`
   - `POST /internal/notifications/trigger-monthly-report`
   - Protected by a shared-secret header (`X-Internal-Trigger-Secret` vs. new
     `INTERNAL_TRIGGER_SECRET` env var)
2. Idempotency guard: before sending, query `notification_logs` for an
   existing `SENT` row for that template + date (replaces the unreliable
   in-memory `last_daily` guard — DB-backed survives restarts and works
   correctly even with 2 gunicorn workers, which currently double-fire).
3. Remove the in-process `while True` scheduler + watchdog loops (they cannot
   work reliably on this host) — replaced by external cron calling the new
   endpoints daily.
4. Regression test for the new endpoints + idempotency guard.
5. **Operational step (human-only, not code):** wire an external cron
   (FastAPI Cloud's own scheduled-job feature if available, else an external
   cron service) to call the daily/weekly/monthly endpoints. Handled via a
   `$wizard` walkthrough, not delegated to OpenCode.

**Bug #2 — SMTP auth failure:**
1. Code fix: make SMTP auth failures escalate loudly (e.g., a distinct
   logfire error event on auth failure specifically, separate from generic
   send failures) so this can't go unnoticed in `notification_logs` again.
2. **Operational step (human-only, not code):** rotate the Gmail App
   Password (revoked/stale) and update `GMAIL_APP_PASSWORD` in FastAPI
   Cloud's environment. Handled via a `$wizard` walkthrough.

### Lane
`refactor` → delegated to OpenCode for the code portions (1-4, and SMTP
code fix). Operational/credential steps handled directly with the user via
`$wizard`, not delegated.

### Closes
_(will be filled in on merge: `closes #1`)_

## #2 — Production DB password exposed in public repo

**Status:** 🔴 OPEN
**Type:** bug (security)
**Created:** 2026-09-25

### Description
`scratch/apply_074.py`, `apply_075.py` and `apply_076.py` (added in `63ae7ad`, 2026-07-10, removed in `f3f34dc`) hardcoded the production Supabase connection string, including its password. The GitHub repo is public. The testing project uses the same password. `archieve/` (student attendance spreadsheets) is also in public history.

### Actions (operational, user-only)
1. Change the database password on both Supabase projects (production `srbppkcvrgioneitktdj` and testing `qugffjtucavdseczbata`). Update `.env`, `.env.test` and the FastAPI Cloud env.
2. Decide: make the repo private, rewrite history (`git filter-repo`), or both.

## #3 — Attendance/group-progression 500s: datetime fields backed by DATE columns

**Status:** 🟢 FIXED (commit `c678197`, pending push/deploy)
**Type:** bug
**Created:** 2026-09-26

### Description
Clients hit 500s on `POST /api/v1/attendance/session/{id}/mark` and `POST /api/v1/academics/groups/{id}/progress-level` starting 2026-09-26, after working fine the day before. Confirmed via Logfire: `AttributeError: 'datetime.date' object has no attribute 'utcoffset'` in `sqlmodel/sql/sqltypes.py:46`, raised from `app/modules/enrollments/core/repository.py:26` (`get_active_enrollment`).

### Root Cause
`Enrollment.enrolled_at`, `Student.date_of_birth`, `Employee.hired_at`, and `Group.started_at` were typed `Optional[datetime]` while their Postgres columns are `DATE` (confirmed dormant since as far back as 2026-03-27). `pyproject.toml` pins `sqlmodel>=0.0.16` with no upper bound. Commit `cf7fb88` (2026-09-25, a `logfire` dependency-constraint bump, unrelated to this code) forced a fresh dependency resolution on the next FastAPI Cloud build, which pulled in `sqlmodel==0.0.47`. That version's `UTCDateTime.process_result_value` unconditionally calls `.utcoffset()` on every non-null value read for a `datetime`-typed field — a `date` object has no such method, so the six-month-old type mismatch became a hard crash with no code change to attendance/enrollments/HR/academics.

### Fix
Corrected the 4 ORM fields to `Optional[date]`, plus 8 mirrored `from_attributes=True` DTOs across enrollments/CRM/HR/academics-analytics that would have failed Pydantic validation the same way once the ORM fix went live. Verified via stash-and-compare against the full test suite: 14 failures are pre-existing (shared testing-DB FK/data-isolation issue, reproduces identically on unmodified code) — zero regressions from this change.

### Follow-up
Consider pinning `sqlmodel` (and `sqlalchemy`) to a known-good range in `pyproject.toml` so a routine dependency-constraint change can't silently re-resolve a breaking transitive version again.

### Closes
_(will be filled in on merge: `closes #3`)_

