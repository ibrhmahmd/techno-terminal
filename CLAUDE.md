# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Other pointers

- OpenAPI docs are served at `/api/v1/docs` (Swagger), `/api/v1/redoc` and `/api/v1/openapi.json`.
- Observability uses Logfire and OpenTelemetry. It is set up in `create_app()` (`configure_logfire`, `instrument_fastapi_app`), and business metrics live in `app/observability/`.
- Task trackers: `ISSUES.md` at the repo root holds issues #1–#3; the architecture sprint (ADRs 0001–0008) is tracked in GitHub Issues. Feature specs live in `specs/NNN-*/` (Speckit); finished specs 001–040 are in `specs/archive/`.
- `CONTEXT.md` is the domain glossary (Scheduled Report, Report Period, Report Recipient, Delivery, Trigger). Use those terms and avoid the listed alternatives.
- No linter/formatter is configured in `pyproject.toml`. Tests hit a real Postgres (see the environment ladder in AGENTS.md); nothing is mocked at the DB layer.
