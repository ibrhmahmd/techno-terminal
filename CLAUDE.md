# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Where AGENTS.md is out of date (checked 2026-09-25)

These override the matching lines in AGENTS.md until that file is fixed:

- **Python**: `pyproject.toml` requires `>=3.11,<3.13`. `.python-version` pins 3.11.9. It is not "3.10+".
- **Migrations**: `db/migrations/` has 90 files, not 87.
- **CI**: `.github/` does not exist, so no CI workflow runs. You must run the tests yourself.
- **Lifespan tasks**: `app/api/main.py` lifespan starts the tasks scheduler (`app/modules/tasks/scheduler.py`) and the Logfire metrics collector (`app/observability/scheduler.py`). The in-process notifications report scheduler is being replaced by external-cron trigger endpoints (`app/api/routers/notifications/internal_scheduler_router.py`, `/internal/reports/*`, guarded by the `X-Internal-Trigger-Secret` header ↔ `settings.internal_trigger_secret`). Look at the working tree for the current state.

## Other pointers

- OpenAPI docs are served at `/api/v1/docs` (Swagger), `/api/v1/redoc` and `/api/v1/openapi.json`.
- Observability uses Logfire and OpenTelemetry. It is set up in `create_app()` (`configure_logfire`, `instrument_fastapi_app`), and business metrics live in `app/observability/`.
- The task tracker is `ISSUES.md` at the repo root. Feature specs live in `specs/NNN-*/` (Speckit).
