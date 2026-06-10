# Feature Specification: Unified Student Listing DTO

**Feature Branch**: `031-unified-student-listing-dto`
**Created**: 2026-06-10
**Status**: Draft
**Input**: User description: "Standardize all student listing API endpoints to return a consistent StudentListingDTO shape, eliminating frontend union types and runtime field checks."

---

## Overview

Currently, the backend exposes five distinct student listing endpoints, each returning a different response shape with a different subset of fields. This forces the frontend to maintain a union type (`StudentListItem | StudentFilterItem`) and sprinkle `'field' in student` runtime property checks throughout the codebase. The goal of this sprint is to harmonize all five listing endpoints so they share a common core shape — `StudentListingDTO` — while each endpoint may still return its own context-specific extended fields as addons.

**Dropped from scope (by decision):**
- `grade` — field does not exist in the database schema; adding it is a separate product decision
- `current_enrollment_count` — not required by the frontend card UI

---

## Clarifications

### Session 2026-06-10

- Q: Is it acceptable for the `/grouped` endpoint to continue using Python-side aggregation (loading all students into memory) for grouping and pagination, or must it move to a DB-level query as part of this sprint? → A: Python-side aggregation is acceptable for current scale; noted as a known tradeoff.
- Q: Should `has_unpaid_balance` reflect only currently active enrollment debts, or any enrollment debt including past/dropped enrollments? → A: Active enrollments only — consistent with the `v_unpaid_enrollments` view definition.
- Q: For the waiting-list endpoint specifically, should `has_unpaid_balance` always be `false` (since waiting students have no active enrollments), or should it reflect any outstanding balance from their prior enrollment history? → A: Check all enrollments regardless of status for the waiting-list endpoint — a waiting student is defined as one with no current active enrollment, but they may carry unpaid balances from previous enrollments, which is financially relevant when deciding to re-enroll them.
- Q: Should the `has_unpaid_balance` filter query parameter on `/filter` be aligned to active-only, kept as all-enrollments (accepting the semantic mismatch with the response field), or renamed to eliminate ambiguity? → A: Rename to `has_any_outstanding_balance` — cleanest long-term semantics; makes it explicit that this filter searches across all enrollment history, distinct from the `has_unpaid_balance` response field which is a card display indicator.
- Q: How will the 20% performance regression threshold in SC-003 be measured? → A: Measure response time of `GET /crm/students?limit=50` before and after the change using the existing test suite — record a pre-change timing, assert post-change timing stays within threshold. No external benchmarking tool required.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Frontend Student Directory Loads with Consistent Data (Priority: P1)

A staff member opens the student directory. Every student card on the page renders correctly — showing name, status, phone, age, gender, and unpaid-balance indicator — without the frontend needing to check which shape the record came from.

**Why this priority**: This is the direct blocker. The union type currently exists because the paginated list endpoint returns an incomplete shape. Fixing it unblocks the unified card component.

**Independent Test**: Call `GET /crm/students` (paginated list) and verify the response contains `age`, `date_of_birth`, and `current_group_name` on every record. The directory page renders without errors.

**Acceptance Scenarios**:

1. **Given** a list of students in the DB, **When** `GET /crm/students` is called, **Then** every item includes `id`, `full_name`, `status`, `phone`, `date_of_birth`, `age`, `gender`, `current_group_name`, and `has_unpaid_balance`.
2. **Given** a student with no active enrollment, **When** the list is returned, **Then** `current_group_name` is `null` and `has_unpaid_balance` is `false`.
3. **Given** a student with an outstanding balance, **When** the list is returned, **Then** `has_unpaid_balance` is `true`.

---

### User Story 2 — Search Results Match the Unified Shape (Priority: P2)

A staff member types a name into the search bar. The results appear as student cards with the same fields as the full directory — no missing badge data.

**Why this priority**: The search path (`?q=`) today already returns most fields but is missing `age`. Completing it delivers a fully consistent search experience.

**Independent Test**: Call `GET /crm/students?q=ahmed` and verify the response shape matches the unified DTO including `age` (computed from `date_of_birth`).

**Acceptance Scenarios**:

1. **Given** a name search query, **When** results are returned, **Then** each item includes all `StudentListingDTO` core fields.
2. **Given** a student whose `date_of_birth` is null, **When** returned in search, **Then** `age` is `null` and `date_of_birth` is `null`.

---

### User Story 3 — Filter Results Match the Unified Shape (Priority: P3)

An admin applies advanced filters (e.g., age range, gender, balance status). The results render as student cards using the same unified type — no special-case mapping needed in the frontend.

**Why this priority**: The filter endpoint today uses its own DTO with differently-named fields. Harmonizing the field names completes the unification.

**Independent Test**: Call `GET /crm/students/filter` with any valid filter and verify the response items include `date_of_birth` and that `enrollment_count` is renamed to `current_enrollment_count` and `unpaid_balance` (float) is replaced by `has_unpaid_balance` (boolean).

**Acceptance Scenarios**:

1. **Given** a filter request, **When** results are returned, **Then** each item includes `date_of_birth` and `has_unpaid_balance` as a boolean.
2. **Given** a student with `unpaid_balance > 0`, **When** returned by the filter endpoint, **Then** `has_unpaid_balance` is `true`.

---

### User Story 4 — Grouped and Waiting-List Views Match the Unified Shape (Priority: P4)

The grouped view (status/gender/age buckets) and the waiting-list view return student records that match the same unified shape, so any component consuming those endpoints can reuse the same card component without conditional rendering.

**Why this priority**: Lower traffic endpoints. Functionally the same fix applied to different service paths.

**Independent Test**: Call `GET /crm/students/grouped` and `GET /crm/students/waiting-list`. Verify the student objects inside each response include `age`, `current_group_name`, and `has_unpaid_balance`.

**Acceptance Scenarios**:

1. **Given** a grouped request by status, **When** the response is returned, **Then** each student object within each bucket includes all unified core fields.
2. **Given** the waiting list, **When** retrieved, **Then** each student includes `age` (computed) and `has_unpaid_balance`, while retaining the existing waiting-list-specific fields (`waiting_since`, `waiting_priority`, `waiting_notes`).

---

### Edge Cases

- What happens when `date_of_birth` is `null`? → `age` must be `null` (not 0 or an error).
- What happens when a student has no active enrollments? → `current_group_name` must be `null`, `has_unpaid_balance` must be `false`.
- What happens when a student has multiple active enrollments? → Return the most recent enrollment's group name (consistent with current `DISTINCT ON` behavior in `list_all_enriched`).
- What if a student has active enrollments but all are fully paid? → `has_unpaid_balance` must be `false`.
- What about the performance of `has_unpaid_balance` on the paginated base list? → A correlated subquery against `v_unpaid_enrollments` is the preferred approach (see Implementation Notes); it is acceptable for lists of ≤ 200 students.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `GET /crm/students` (paginated list) MUST include `date_of_birth`, `age` (computed), `gender`, `current_group_name`, and `has_unpaid_balance` on every item in the response.
- **FR-002**: `GET /crm/students?q=` (search) MUST include `age` (computed from `date_of_birth`) on every result item.
- **FR-003**: `GET /crm/students/filter` MUST add `date_of_birth` to response items. The `enrollment_count` field MUST be renamed to `current_enrollment_count`. The `unpaid_balance` float field MUST be replaced with `has_unpaid_balance` (boolean).
- **FR-004**: `GET /crm/students/grouped` MUST include `age` (computed), `current_group_name`, and `has_unpaid_balance` for each student object in every bucket.
- **FR-005**: `GET /crm/students/waiting-list` MUST include `age` (computed) and `has_unpaid_balance`. For this endpoint only, `has_unpaid_balance` MUST reflect **any** outstanding balance across all enrollment history (not limited to active enrollments), because waiting students by definition have no active enrollments — their debts originate from prior enrollment periods. Existing waiting-list fields (`waiting_since`, `waiting_priority`, `waiting_notes`) MUST be preserved.
- **FR-006**: All endpoints MUST preserve existing fields — no fields may be removed from current responses (additive-only changes).
- **FR-007**: `age` MUST be computed server-side from `date_of_birth` using the same calculation already in use in the `filter_students` service (`StudentValidator.compute_age`). It MUST be `null` when `date_of_birth` is `null`.
- **FR-008**: `has_unpaid_balance` MUST be a boolean with a **two-tier definition** depending on endpoint:
  - **For all listing endpoints except waiting-list** (`GET /crm/students`, `?q=`, `/grouped`, `/filter`): `true` when the student has at least one **active** enrollment (`enrollments.status = 'active'`) with a remaining balance > 0; `false` otherwise. Computed via `v_unpaid_enrollments`.
  - **For the waiting-list endpoint** (`GET /crm/students/waiting-list`): `true` when the student has **any** enrollment (regardless of enrollment status) with a remaining balance > 0; `false` otherwise. Computed via `v_enrollment_balance`. This is necessary because waiting students are defined as having no current active enrollments, so an active-only check would always return `false` and hide legitimate outstanding debts.
- **FR-009**: The `StudentListingDTO` MUST be defined as a single Pydantic schema in `app/api/schemas/crm/student.py` and used as the response model for all five listing endpoints, replacing the existing fragmented schemas.
- **FR-010**: The `StudentFilterItemDTO` in `app/modules/crm/interfaces/dtos/` MUST be updated to reflect the field renames (`enrollment_count` → `current_enrollment_count`, `unpaid_balance` float → `has_unpaid_balance` boolean, add `date_of_birth`) to ensure the service-layer contract matches the API-layer output.
- **FR-011**: The `has_unpaid_balance` **query parameter** on `GET /crm/students/filter` MUST be renamed to `has_any_outstanding_balance`. This parameter filters students whose total outstanding balance across **all enrollments** (active, dropped, or completed) is greater than zero. The old parameter name MUST be removed. This is a **breaking change** and requires simultaneous frontend update to the filter call site. The internal filter DTO (`StudentFilterDTO`) field must be renamed accordingly.

### Key Entities

- **StudentListingDTO**: The unified API-boundary schema. Contains core identity fields (`id`, `full_name`, `status`), contact (`phone`), demographics (`date_of_birth`, `age`, `gender`), and display fields (`current_group_name`, `has_unpaid_balance`).
- **StudentFilterItemDTO**: The internal service-layer DTO used by `SearchService.filter_students()`. Must be updated to align with the unified shape.
- **StudentSummaryDTO**: The internal DTO used by grouped queries. Must be extended with `age` and `has_unpaid_balance`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The frontend team can replace the `StudentListItem | StudentFilterItem` union type with a single `StudentListingDTO` type and the build passes without TypeScript errors.
- **SC-002**: All `'field' in student` runtime property checks in the frontend can be removed — direct property access works on all five endpoint responses.
- **SC-003**: The response time of `GET /crm/students?limit=50` must not regress by more than 20% after the changes. Measured by timing the endpoint in the test suite before and after the change and asserting the post-change timing stays within threshold.
- **SC-004**: All existing API tests that cover the five student listing endpoints continue to pass after the changes.
- **SC-005**: New backend tests verify that `has_unpaid_balance` is correctly `true`/`false` based on payment data, and that `age` is correctly `null` when `date_of_birth` is absent.
- **SC-006**: The `has_any_outstanding_balance` query parameter on `GET /crm/students/filter` correctly filters students with any outstanding balance across all enrollment history. The old `has_unpaid_balance` query parameter on this endpoint is no longer accepted.

---

## Assumptions

- The `has_unpaid_balance` flag has a two-tier implementation. For paginated list, search, grouped, and filter endpoints: EXISTS subquery against `v_unpaid_enrollments` (scoped to `active` enrollments). For the waiting-list endpoint: EXISTS subquery against `v_enrollment_balance` (any enrollment status) where `amount_remaining > 0`. This distinction reflects the business reality that `waiting` students have no active enrollments by definition, and the concept of "waiting" may evolve with future business requirements.
- The paginated `GET /crm/students` list is used by admins viewing at most 200 students at a time — performance is acceptable with a subquery approach given the existing pool configuration.
- Backward compatibility is required. No field names will be removed from existing responses; only new fields added or existing fields renamed (with simultaneous frontend migration).
- The `age` field computed in `filter_students` (via `StudentValidator.compute_age`) is the canonical age calculation to be reused across all endpoints.
- `current_group_name` is the name of the group from the student's most recent active enrollment. If a student has multiple active enrollments (edge case), the one with the highest enrollment ID is used (consistent with the `DISTINCT ON (s.id) ORDER BY s.id, e.id DESC` pattern already in `list_all_enriched`).
- The `v_students` DB view (which already computes `age` via `EXTRACT(year FROM age(date_of_birth))`) is available but the Python-layer `StudentValidator.compute_age` is preferred for consistency with the filter endpoint.
- Frontend migration of the union type will happen as a coordinated follow-up once this backend sprint is merged.
- **Known tradeoff (grouped endpoint)**: The `/grouped` endpoint will continue to use Python-side grouping and pagination (loading all non-deleted students into memory). Migrating it to a fully DB-level grouped query is deferred to a future sprint. Acceptable because total student count at this center's scale is bounded (typically < 500). Adding `has_unpaid_balance` to the grouped endpoint means the EXISTS subquery will still run per-student in the SQL, but grouping/slicing remains in Python.
