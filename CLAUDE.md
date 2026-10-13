# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Other pointers

- OpenAPI docs are served at `/api/v1/docs` (Swagger), `/api/v1/redoc` and `/api/v1/openapi.json`.
- Observability uses Logfire and OpenTelemetry. It is set up in `create_app()` (`configure_logfire`, `instrument_fastapi_app`), and business metrics live in `app/observability/`. Test runs (pytest or `TESTING=true`) never send to Logfire (#145); a deployment names itself with the `LOGFIRE_ENVIRONMENT` env var (e.g. `production`, `staging`).
- Task trackers: GitHub Issues; the prioritised roadmap is #111 and the (finished) architecture migration epic is #9 (ADRs 0001–0012 in `docs/adr/`). `ISSUES.md` holds only the open security item that must stay off the public tracker until credentials are rotated. Feature specs live in `specs/NNN-*/` (Speckit); finished specs 001–041 are in `specs/archive/`.
- No linter/formatter is configured in `pyproject.toml`. Tests hit a real Postgres (see the environment ladder in AGENTS.md); nothing is mocked at the DB layer.
