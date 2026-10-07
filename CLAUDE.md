# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Where AGENTS.md is out of date (checked 2026-10-07)

These override the matching lines in AGENTS.md until that file is fixed:

- **Python**: `pyproject.toml` requires `>=3.11,<3.13`. `.python-version` pins 3.11.9. It is not "3.10+".
- **Migrations**: `db/migrations/` has 91 files, not 87.
- **CI**: `.github/` does not exist, so no CI workflow runs. You must run the tests yourself.
- **Lifespan tasks**: `app/api/main.py` lifespan starts only the tasks scheduler (`app/modules/tasks/scheduler.py`) and the Logfire metrics collector (`app/observability/scheduler.py`). There is no in-process notifications report scheduler any more: scheduled reports are fired by external-cron trigger endpoints (`app/api/routers/notifications/internal_scheduler_router.py`, `/internal/reports/*`, guarded by the `X-Internal-Trigger-Secret` header ↔ `settings.internal_trigger_secret`; an empty secret is always rejected).

## Other pointers

- OpenAPI docs are served at `/api/v1/docs` (Swagger), `/api/v1/redoc` and `/api/v1/openapi.json`.
- Observability uses Logfire and OpenTelemetry. It is set up in `create_app()` (`configure_logfire`, `instrument_fastapi_app`), and business metrics live in `app/observability/`.
- The task tracker is `ISSUES.md` at the repo root. Feature specs live in `specs/NNN-*/` (Speckit); finished specs 001–040 are in `specs/archive/` (e.g. the business-reports spec is `specs/archive/035-business-reports-feature/spec.md`, which AGENTS.md cites at its old path).
- `CONTEXT.md` is the domain glossary (Scheduled Report, Report Period, Report Recipient, Delivery, Trigger). Use those terms and avoid the listed alternatives.
- No linter/formatter is configured in `pyproject.toml`. Tests hit a real Postgres (see the environment ladder in AGENTS.md); nothing is mocked at the DB layer.
