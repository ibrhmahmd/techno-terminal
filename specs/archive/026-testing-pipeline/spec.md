# Feature Specification: Testing Pipeline & CI/CD

**Feature Branch**: `026-testing-pipeline`  
**Created**: 2026-06-08  
**Status**: Draft  
**Input**: User description: "Set up a testing environment with local test DB and GitHub Actions CI/CD pipeline"

## User Scenarios & Testing

### User Story 1 - Local Test Database for Safe Development (Priority: P1)

As a developer, I want to run the full test suite against a local PostgreSQL database that is isolated from production, so that I can verify code changes without any risk of corrupting or polluting production data.

**Why this priority**: Without a local test database, every test run risks accidentally hitting the production database. This is the foundation for all safe testing.

**Independent Test**: A developer can run `pytest tests/ -v` locally after setting up `.env.test` and confirm all tests pass against the local DB without touching production.

**Acceptance Scenarios**:

1. **Given** the `.env.test` file is configured with a local PostgreSQL connection string, **When** a developer runs `pytest`, **Then** all tests execute against the local database and no queries reach the production database URL.
2. **Given** the test framework loads `.env.test` automatically, **When** a developer runs tests, **Then** the connection uses the test database regardless of what is in `.env`.
3. **Given** the local test database has the full schema applied, **When** a migration is run, **Then** the schema evolves correctly and tests validate the new state.

---

### User Story 2 - Automated CI/CD Pipeline with GitHub Actions (Priority: P2)

As a team lead, I want every push to GitHub to automatically trigger a CI pipeline that runs the full test suite in a clean cloud environment, so that regressions are caught before code is merged or deployed.

**Why this priority**: Local testing alone does not prevent developer environment variance or forgotten changes. An automated pipeline acts as the gatekeeper for code quality.

**Independent Test**: Push a commit to a feature branch on GitHub and observe the CI pipeline trigger, spin up a fresh PostgreSQL container, apply the schema, run all tests, and report pass/fail status.

**Acceptance Scenarios**:

1. **Given** a developer pushes code to GitHub, **When** the CI workflow triggers, **Then** it provisions a clean PostgreSQL service container, applies the schema and migrations, and runs `pytest`.
2. **Given** the CI pipeline completes successfully, **When** viewing the workflow run, **Then** the status shows a green checkmark with test output.
3. **Given** a test fails in CI, **When** viewing the workflow run, **Then** the status shows a red X with the failing test output and traceback.

---

### User Story 3 - Frontend Build & Lint Validation in CI (Priority: P3)

As a developer, I want the CI pipeline to also validate the frontend by running TypeScript compilation and linting, so that broken builds or type errors never reach production.

**Why this priority**: Backend tests alone do not catch TypeScript errors, missing exports, or lint violations in the frontend codebase.

**Independent Test**: A developer introduces a TypeScript error in a frontend file, pushes to GitHub, and observes the CI pipeline report a failure on the frontend build step.

**Acceptance Scenarios**:

1. **Given** the CI pipeline runs, **When** it reaches the frontend validation step, **Then** it runs `npm run build` (or `tsc -b`) to check TypeScript compilation.
2. **Given** a frontend lint error exists, **When** CI runs the lint step, **Then** the workflow fails with the lint violation details.
3. **Given** both backend tests and frontend build pass, **When** the pipeline completes, **Then** the overall status is green.

---

### Edge Cases

- **Expired or missing environment variables for Supabase/Twilio/Gmail**: Tests should gracefully skip or mock external service calls rather than fail with cryptic connection errors.
- **Schema drift between local test DB and production**: The local test database schema must be re-appliable from scratch to match the production state; schema files must be the single source of truth.
- **CI pipeline timeout on long-running migrations**: If migrations take more than a few minutes total, the pipeline could time out. Should be monitored and optimized.
- **Parallel test execution conflicts**: If tests are run in parallel, they must not collide on shared state (e.g., unique constraint violations from fixture data).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load a separate test environment configuration (`.env.test`) when running tests, completely isolating test execution from production environment variables.
- **FR-002**: The test database MUST be a PostgreSQL instance — SQLite in-memory is NOT acceptable due to PostgreSQL-specific features (JSONB, TIMESTAMPTZ, PL/pgSQL triggers, custom enums).
- **FR-003**: The local test database schema MUST be reproducible from the schema files (`db/schema/`) and migrations (`db/migrations/`) without connecting to production.
- **FR-004**: The GitHub Actions CI pipeline MUST automatically trigger on every `git push` to any branch and on pull requests.
- **FR-005**: The CI pipeline MUST spin up a fresh PostgreSQL service container, apply the full schema, run all migrations, then execute `pytest` in an isolated environment.
- **FR-006**: External service integrations (Supabase Auth, Twilio, Gmail) MUST be gracefully handled in tests — either mocked, skipped, or configured with test-specific credentials that carry no risk.
- **FR-007**: The CI pipeline MUST also validate the frontend by running `npm run build` to ensure TypeScript compilation succeeds.
- **FR-008**: Test results MUST be clearly reported in the GitHub Actions workflow output, showing which tests passed, failed, or were skipped.

### Key Entities

- **Test Environment Configuration** (`.env.test`): Contains `DATABASE_URL` pointing to the local/CI test database, along with test-safe values for Supabase, Twilio, and Gmail credentials.
- **CI Workflow Definition** (`.github/workflows/ci.yml`): The GitHub Actions YAML file defining the pipeline triggers, service containers, steps, and environment variables.
- **Test Database**: A PostgreSQL database instance (local or CI service container) that is created, populated with schema, and destroyed as needed for test isolation.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Developers can run the full `pytest tests/` suite against a local test database in under 5 minutes of setup time (excluding initial DB creation).
- **SC-002**: The GitHub Actions CI pipeline completes from trigger to test results in under 10 minutes.
- **SC-003**: Zero accidental test queries hit the production database — verified by monitoring or by the fact that production credentials are never loaded in test context.
- **SC-004**: The CI pipeline catches and reports failures on at least 95% of regression-introducing commits before they are merged.

## Assumptions

- A local PostgreSQL server is available (either installed natively or via Docker Desktop) for local testing.
- The production Supabase project has a separate test/project-ref for CI credentials or those services are mocked in CI.
- GitHub repository is hosted on github.com (not a self-hosted instance).
- The project already has a `.specify/extensions.yml` and speckit workflow tools available for spec pipeline automation.
- Schema files in `db/schema/` and migrations in `db/migrations/` are the canonical source of truth for the database structure.
