# Feature Specification: Fix Missing Session Commits

**Feature Branch**: `009-fix-missing-commits`
**Created**: 2026-05-14
**Status**: Draft
**Input**: User description: "create a spec for this sprint"

## User Scenarios & Testing

### User Story 1 — Enrollments Persist (Priority: P1)

An admin enrolls a student in a group. The API returns 201 and the enrollment actually appears in the group roster when viewed afterward.

**Why this priority**: Enrollment is the core revenue-generating operation. Students cannot attend classes, generate fees, or track progress without a persisted enrollment. This is the highest-impact bug — all enrollment actions (create, transfer, drop, complete) silently fail.

**Independent Test**: Create an enrollment via the enroll endpoint, then immediately call the group roster endpoint. The enrolled student must appear in the roster.

**Acceptance Scenarios**:

1. **Given** a valid student and active group, **When** an admin sends a POST to the enroll endpoint, **Then** the API returns 201 and the enrollment appears in the group's roster when fetched.
2. **Given** an active enrollment, **When** an admin sends a PATCH to drop that enrollment, **Then** the API returns 200 and the enrollment status is "dropped" when fetched.
3. **Given** a waiting student, **When** an admin enrolls them in a group, **Then** the student's status changes to "active" in the system.

---

### User Story 2 — Competitions Persist (Priority: P1)

A competition manager creates a competition and registers teams. The competition and its teams are visible when viewing the competition list afterward.

**Why this priority**: Competition data represents commitments to students, parents, and external organizers. Silent data loss means teams show as registered but disappear on refresh, causing operational chaos.

**Independent Test**: Create a competition via the create endpoint, then call the competition list endpoint. The new competition must appear.

**Acceptance Scenarios**:

1. **Given** valid competition data, **When** an admin sends a POST to create a competition, **Then** the API returns 201 and the competition appears in the list.
2. **Given** a competition and valid student list, **When** an admin registers a team, **Then** the API returns 201 and the team appears in the competition's team roster.
3. **Given** a competition that has concluded, **When** an admin sets placement results, **Then** the placement persists and is visible on the team detail page.

---

### User Story 3 — System Stable Under Load (Priority: P2)

The system handles normal concurrent usage without database connection pool exhaustion or request timeouts.

**Why this priority**: The current pattern of opening 3+ sessions per request consumes pool connections rapidly. While the commit fixes are urgent, the connection efficiency issue causes production outages under load.

**Independent Test**: Run a concurrent request test simulating 5 simultaneous enrollment operations. All requests should complete successfully without pool timeout errors.

**Acceptance Scenarios**:

1. **Given** 5 concurrent enrollment requests, **When** all are sent simultaneously, **Then** all return 201 and data is persisted for all 5.
2. **Given** normal office hours traffic, **When** measuring connection pool utilization, **Then** the pool should not exceed 80% capacity during peak load.

---

### User Story 4 — Tests Verify Persistence (Priority: P2)

All affected endpoints have automated tests that verify data actually persists in the database (not just HTTP response codes).

**Why this priority**: The original bug was not caught by tests because tests only check the response body. Closing this test gap prevents regression.

**Independent Test**: Run the full test suite for affected modules. All persistence-related tests must pass.

**Acceptance Scenarios**:

1. **Given** the test suite for enrollments, **When** running `test_enroll_student_persists`, **Then** the test creates an enrollment and verifies it via a subsequent GET.
2. **Given** the test suite for competitions, **When** running competition CRUD tests, **Then** each test creates data and verifies it persists via a subsequent GET.

---

### Edge Cases

- What happens when `session.commit()` is called after a read-only operation? (No effect — idempotent.)
- How does the system handle a commit failure on a `create` operation? (The `get_session()` context manager catches the exception and rolls back — no partial writes.)
- What if a service method performs multiple writes (e.g., `register_team` creates team + members + participation) and one fails? (The entire transaction rolls back atomically — this is correct behavior.)

## Requirements

### Functional Requirements

- **FR-001**: The enrollment creation endpoint MUST persist enrollment records to the database so they survive subsequent requests.
- **FR-002**: The enrollment status update endpoints (drop, transfer, complete) MUST persist status changes.
- **FR-003**: The competition creation endpoint MUST persist competition records.
- **FR-004**: The team registration endpoint MUST persist team records, member records, and group competition participation records.
- **FR-005**: The competition placement endpoint MUST persist placement results.
- **FR-006**: All existing API contracts (request/response shapes, status codes, error formats) MUST remain unchanged.
- **FR-007**: A test must exist for each affected write endpoint that verifies data persistence by reading it back.

### Key Entities

- **Enrollment**: Links a student to a group at a specific level. Tracks payment status, discount, and lifecycle (active/transferred/dropped/completed).
- **Competition**: A competition event with dates, location, categories, and per-student fees.
- **Team**: A team registered in a competition, containing students as members, with category/subcategory and placement results.
- **TeamMember**: Links a student to a team with a fee share and payment status.
- **GroupCompetitionParticipation**: Links a group to a competition team for tracking internal group participation.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of affected write endpoints pass a persistence verification test (create → read back, update → read back).
- **SC-002**: Zero regressions — all existing 201/200 responses remain unchanged in shape and status code.
- **SC-003**: Connection pool utilization during peak simulated load (5 concurrent enrollment requests) stays under 80% of capacity.
- **SC-004**: All fix deployments can be rolled out without database migrations, schema changes, or downtime.
- **SC-005**: The fix must be completable within one working day (8 hours) across all affected services.

## Assumptions

- The `session.commit()` call is the only missing piece — the data model, repository queries, and API schemas are all correct.
- Connection pool settings may need a temporary increase and later reduction after services are refactored to the UoW pattern.
- Tests will be added to the existing test files following current conventions.
- The existing test infrastructure (TestClient, database fixtures, auth headers) is sufficient for persistence verification tests.
- No frontend changes are required — the API contract is identical, only the backend persistence behavior changes.
