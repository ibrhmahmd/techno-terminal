# Map: Reliable scheduled report delivery

Label: wayfinder:map
Tracks: ISSUES.md #1 (Scheduled daily report email does not send)

## Destination

A spec at `.scratch/reliable-report-delivery/spec.md`, agreed and ready to hand to OpenCode, for reliable delivery of the daily, weekly and monthly reports. It covers what triggers them, what counts as delivered, how a miss is detected from outside the app, and how retry and backfill work.

## Notes

- Domain: the notifications module (`app/modules/notifications/`). Glossary in `/CONTEXT.md`.
- For grilling tickets, consult `grilling` + `domain-modeling`. Use `codebase-design` for storage and interface shape. Use `wizard` for HITL operational tasks.
- The tracker is local markdown. Tickets are `issues/NN-*.md`, with `Status:` and `Blocked by:` lines.
- Production reads are **read-only** (`SET TRANSACTION READ ONLY`), and only with the user's approval. Writes go to the testing project or localhost only.
- Findings in production as of 2026-09-25:
  - Daily reports were sent only on 8/24, 8/31, 9/03 and 9/04, and not at all after 9/04.
  - 3 duplicates were sent on 8/31.
  - Every email has failed since 9/17 with Gmail `535`.
  - There is one report recipient.

## Manual setup progress (user)

- Done 2026-09-25:
  - Gmail sender changed to `techno.terminal.notifications@gmail.com`, with its new app password, in `.env`, `.env.test` and FastAPI Cloud.
  - `pg_cron` and `pg_net` enabled on production.
  - The testing project reactivated.
  - `INTERNAL_TRIGGER_SECRET`: the local value is in `.env` and `.env.test`. A separate production value was given to the user for FastAPI Cloud and Vault.
- Pending:
  - Vault secrets on production.
  - The `pg_cron` job SQL, which runs **after** the code is deployed.
  - Deploying from a clean tree.
- **Remind the user when we reach alerting:** Logfire alerts setup (tickets 12 and 13): plan check, a notification channel that doesn't depend on Gmail, and the 4 alert rules.
- Postponed by the user: changing the database password (ISSUES.md #2).

## Decisions so far

- [Trigger mechanism](issues/01-trigger-mechanism.md): Supabase `pg_cron` + `pg_net` POSTs to an authenticated internal endpoint.
- [Miss / failure detection](issues/02-miss-detection.md): Logfire alerts only, including rules that fire when an expected event is missing.
- [Email transport for now](issues/03-email-transport.md): change the Gmail app password now and decide later whether to switch provider.
- [What counts as "delivered"](issues/04-delivery-identity.md): each Delivery is keyed on (report type, report period, recipient). Skip if SENT, retry if FAILED.
- [Measure how long a report run takes](issues/06-measure-report-duration.md): generation takes about 4–6s warm and 18s cold. SMTP adds about 3.5s per recipient, sent one after another. With 1 recipient a warm daily takes about 9s, a cold one about 22s, and a Monday run with daily + weekly about 18–30s.
- [Endpoint execution model](issues/08-endpoint-execution-model.md): the report runs inside the request; failures return 500.
- [Recording the report period](issues/09-record-report-period.md): a `report_period_start` column plus a unique claim index, behind a ledger interface.
- [Schedule shape](issues/10-schedule-shape.md): three `pg_cron` jobs at 05:00 UTC.
- [What to do with the in-progress code](issues/15-in-progress-code.md): rework it in place through OpenCode.
- [Request timeout and background-work limits](issues/07-request-timeout-limits.md): the cutoff is undocumented and could be 15–125s (Envoy behind Cloudflare). Work after the response is best-effort. `pg_net` timeouts have no practical cap. Needs the measurement in ticket 17.

## Not yet specified

- End-to-end verification before production: how to prove that a `pg_cron` call on the testing project reaches a deployed app. The FastAPI Cloud app may be production-only. This depends on the pg_cron management ticket.
- Writing the spec itself once the frontier is empty. That includes the test plan (regression tests for skip/retry, auth and period computation) and the OpenCode delegation brief.

## Out of scope

- Correctness of report contents (date ranges, soft-delete filters): covered by `specs/041-fix-scheduled-report-date-range`.
- A general job queue or worker for all background work.
- Changing the leaked database password and the public-repo exposure: a separate security issue in `ISSUES.md`.
