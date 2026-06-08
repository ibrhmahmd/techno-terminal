# Research: Testing Pipeline — Resolved Unknowns

## Unknown 1: CI Test Credentials for Supabase

**Decision**: Use mock JWT tokens for all CI tests.
**Rationale**: The project already has `tests/utils/jwt_mocks.py` which generates HS256-signed tokens using a hardcoded `TEST_SECRET`. The `override_auth` fixture in `conftest.py` replaces `get_current_user` dependency, completely bypassing real Supabase validation. No CI test needs a real Supabase connection.
**Alternatives considered**: Creating a dedicated Supabase test project — overkill for auth bypass that already works via mocks.

## Unknown 2: Twilio/Gmail in CI

**Decision**: Create mock dispatchers and use dummy env values in CI.
**Rationale**: The notification services (`email_dispatcher.py`, `twilio_dispatcher.py`) are already called through service classes. Patching them at the dispatcher level or using environment variables with dummy values prevents external calls during CI. The `.env.test` can use placeholder values for Twilio/Gmail in CI since all notification tests will mock the dispatcher layer.
**Alternatives considered**: Using real sandbox credentials — introduces dependency on external services and potential flaky tests.

## Unknown 3: Frontend Test Scope in CI

**Decision**: CI validates `npm run build` only (TypeScript compilation + Vite production build).
**Rationale**: The frontend currently has no unit test framework configured (no vitest/jest in `package.json` devDependencies). Adding a test framework is out of scope for this pipeline. Build validation catches TypeScript errors, missing exports, and import resolution failures — which covers the most common integration-breaking issues.
**Alternatives considered**: Adding vitest + component testing — valuable but adds scope; defer to a future spec.

## Database Schema Reproduction

**Decision**: Use `db/schema.sql` (which includes all 17 modular files in dependency order) plus migrations for incremental changes.
**Rationale**: The project already has a complete schema file at `db/schema.sql` that applies all tables, enums, functions, triggers, views, and indexes. Migrations handle incremental changes. For CI, running `schema.sql` creates the full test schema in seconds. The local test DB uses the same approach.
**Note**: The CI must apply migrations that correspond to the current schema files — some migrations (042-049) are cleanup/deprecation and already reflected in the schema files.

## GitHub Actions PostgreSQL Service Container

**Decision**: Use `postgres:15` official image with health check.
**Rationale**: PostgreSQL 15 is the version used by the Supabase production project. The official Docker image supports health checks (`pg_isready`) for reliable container readiness. The service container is automatically destroyed when the CI job finishes — zero cleanup overhead.
**Alternatives considered**: Self-hosted runner with pre-installed PostgreSQL — adds maintenance burden with no benefit for this scale.
