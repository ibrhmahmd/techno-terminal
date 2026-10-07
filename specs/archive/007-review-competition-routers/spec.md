# Feature Specification: Review Competition Routers

**Feature Branch**: `007-review-competition-routers`  
**Created**: 2026-05-13  
**Status**: Draft  
**Input**: User description: "review the competitions router making sure all the competitions module routers are making sure the competitions related routers are reflecting the competitions module correctly"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Audit Active Competition Routers for Schema & Service Alignment (Priority: P1)

A developer needs to verify that every endpoint in the active competition routers (`competitions/competitions_router.py`, `competitions/teams_router.py`, `academics/group_competitions_router.py`, `analytics/competition.py`) correctly maps to its corresponding service method and DTO from the competitions module. Each endpoint's input schema, output schema, auth guard, and service call must be documented and validated against the module's actual interface.

**Why this priority**: This is the core audit activity — without knowing what endpoints exist and whether they match module contracts, no other review is actionable.

**Independent Test**: For each active router file, produce a coverage matrix showing every endpoint, its auth guard, its service call, its input DTO, and its output DTO. Each item must trace to an actual function in the competitions module.

**Acceptance Scenarios**:

1. **Given** the active competition routers, **When** auditing endpoint-to-service mappings, **Then** every endpoint must call an existing service method with matching parameters
2. **Given** the active competition routers, **When** auditing DTOs, **Then** every inline DTO duplicates or contradicts a module DTO must be flagged
3. **Given** the active competition routers, **When** auditing auth guards, **Then** every endpoint must use `require_any` or `require_admin` consistent with the sensitivity of its operation
4. **Given** a complete audit report, **When** reviewing findings, **Then** each finding must cite exact file paths and line numbers

---

### User Story 2 — Remove or Reconcile the Orphan Router (Priority: P1)

A 315-line standalone `app/api/routers/competitions_router.py` exists but is NOT registered in `main.py`. It contains duplicated endpoint definitions that overlap with both `competitions/competitions_router.py` and `competitions/teams_router.py`. This orphan must be either deleted (if truly dead code) or reconciled into the active router structure.

**Why this priority**: Dead/duplicate code creates confusion, increases maintenance burden, and risks inconsistent behavior if someone accidentally imports it.

**Independent Test**: After resolution, a grep for endpoint paths from the orphan file will confirm they exist in active routers or are intentionally removed.

**Acceptance Scenarios**:

1. **Given** the orphan router file, **When** checking its contents, **Then** all endpoints must be cross-referenced with active routers for duplication
2. **Given** a decision to delete, **When** removing the file, **Then** no imports from `app.api.routers.competitions_router` remain anywhere in the codebase
3. **Given** a decision to keep endpoints, **When** migrating them to active routers, **Then** each migrated endpoint must follow the existing router conventions

---

### User Story 3 — Verify Architectural Compliance (Priority: P2)

All competition routers must conform to the constitution's architectural principles: no business logic in routers, no SQL in routers, no service importing from `app.api.*`, correct session lifecycle pattern, and proper dependency injection.

**Why this priority**: Architectural violations cause maintenance debt, testing difficulty, and runtime issues (e.g., mixed session patterns).

**Independent Test**: Manual code review of each router file against constitution rules produces a compliance report.

**Acceptance Scenarios**:

1. **Given** each router file, **When** checking for business logic, **Then** no SQL queries, domain calculations, or validation rules exist in the router (only Pydantic validation is permitted)
2. **Given** each router file, **When** checking imports, **Then** no router imports from `app.modules.*.services.*` in a way that violates the architecture (services are injected via `Depends`)
3. **Given** the group competitions router, **When** checking session lifecycle, **Then** the factory pattern matches the constitution's stated pattern for its module (Academics = stateless, but `get_group_competition_service` uses UoW — either the constitution or the code must be corrected)
4. **Given** all router files, **When** checking inline DTOs, **Then** any inline DTO that duplicates a module DTO must be flagged for extraction to `app/api/schemas/`

---

### User Story 4 — Verify Cross-Module Competition Endpoints (Priority: P3)

CRM student history and Finance routers expose competition-related endpoints (`/students/{student_id}/competition-history`, `/finance/competition-fees`). These must be reviewed to ensure they correctly reference competitions module models and services.

**Why this priority**: Secondary verification — these endpoints use different module services (CRM, Finance) but reference competition data.

**Independent Test**: Review each cross-module endpoint's service call to confirm it accesses competition data correctly and returns appropriate types.

**Acceptance Scenarios**:

1. **Given** the CRM competition history endpoint, **When** verifying its implementation, **Then** it must call a service that correctly queries competition participation data
2. **Given** the Finance competition fees endpoint, **When** verifying its implementation, **Then** it must correctly reference competition fee records

---

### Edge Cases

- What happens when a service method's signature changes but the router still calls the old signature? (compile-time vs. runtime detection)
- How to verify that all service methods exposed via routers actually exist and are importable?
- What if the orphan router has endpoints that active routers don't (e.g., a different behavior for a same-named endpoint)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST produce a complete endpoint inventory for all active competition routers, documenting for each: file path, line number, HTTP method, URL path, auth guard, service class, service method, input DTO, output DTO
- **FR-002**: System MUST cross-reference every service call in competition routers against the actual service interface to verify method names, parameter counts, and return types match
- **FR-003**: System MUST identify all inline DTOs defined inside router files and flag those that duplicate or overlap with module-level DTOs
- **FR-004**: System MUST assess the orphan `app/api/routers/competitions_router.py` for dead code, duplication, and whether any of its endpoints provide functionality missing from active routers
- **FR-005**: System MUST verify that every competition router endpoint uses the correct auth guard (`require_any` for reads, `require_admin` for writes)
- **FR-006**: System MUST check that no router file contains business logic, SQL queries, or domain validation outside of Pydantic schemas
- **FR-007**: System MUST verify that no service or repository import from `app.api.*` exists in the competitions module
- **FR-008**: System MUST document the session lifecycle pattern used by each competition-related service factory and flag any inconsistency with the constitution
- **FR-009**: System MUST verify cross-module competition endpoints (CRM history, Finance fees) correctly reference competitions module data
- **FR-010**: System MUST produce a remediation plan for each finding, prioritized by impact

### Key Entities *(include if feature involves data)*

- **Endpoint Inventory**: A structured list of all competition-related API endpoints with their attributes (path, method, auth, service mapping)
- **Service Interface Map**: The set of public methods exposed by `CompetitionService`, `TeamService`, `GroupCompetitionService`, `GroupAnalyticsService`, and `CompetitionAnalyticsService`
- **DTO Registry**: All Pydantic models used for competition data at both the API schema layer and the module schema layer
- **Audit Finding**: A documented issue with its severity, location, description, and recommended remediation
- **Orphan Router Assessment**: Analysis of `app/api/routers/competitions_router.py` including endpoint count, duplication percentage, and disposition recommendation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of active competition router endpoints are documented in the endpoint inventory with all 9 attributes (file, line, method, path, auth, service class, service method, input DTO, output DTO)
- **SC-002**: All service method references in routers resolve to actual, importable methods with matching signatures
- **SC-003**: All architectural violations found (maximum 3 iterations of review-and-fix) are documented with severity, file path, and line number
- **SC-004**: The orphan router receives a disposition decision: delete, migrate, or keep with documented rationale
- **SC-005**: A remediation plan with prioritized items and effort estimates is produced and reviewed
- **SC-006**: Auth guards are verified correct on 100% of competition endpoints (no read-only endpoint requires admin; no write endpoint allows unauthenticated access)

## Assumptions

- The existing test suite (42 competition tests) will be used as a regression safety net — any change to routers must not break existing tests
- The constitution at `.specify/memory/constitution.md` is the authoritative source for architectural rules
- Inline DTOs in routers are acceptable if they do not duplicate module DTOs and are not used by services
- The orphan router is assumed to be dead code until proven otherwise — burden of proof is on keeping it
- CRM and Finance modules are out of scope for deep changes — only competition-related endpoints within those routers are reviewed
- No new service or repository code will be created during this review — only router code may change
