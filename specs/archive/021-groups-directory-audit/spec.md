# Feature Specification: Groups Directory Module Audit

**Feature Branch**: `021-groups-directory-audit`
**Created**: 2026-06-03
**Status**: Draft
**Input**: Post-implementation audit of `020-groups-filter-day-order` revealing broken router endpoints, dead code, missing typed contracts, and underutilized filter capabilities.

---

## Background

During implementation of `020-groups-filter-day-order`, five legacy service methods
(`search_groups`, `get_groups_by_type`, `get_groups_by_course`,
`get_enriched_groups_by_course`, `get_enriched_groups_by_type`) were deleted from the
service and repository layers because they were fully superseded by the new `filter_groups`
engine. However, the router layer was not updated — five active HTTP endpoints still call
these deleted methods, making the backend **crash at runtime** for those routes.

This audit spec covers the complete remediation: fixing the broken routes, deleting
redundant endpoints, migrating survivors to the filter engine, removing dead DTOs, and
hardening the filter itself with additional capabilities.

---

## User Scenarios & Testing

### User Story 1 — API Consumers Get Stable, Non-Crashing Endpoints (Priority: P1)

Any caller of the Groups Directory API must receive a valid response (never a 500
AttributeError from a deleted service method). All endpoints must work after this change.

**Why this priority**: The application is currently broken in production for five endpoints.

**Independent Test**: Send `GET /academics/groups`, `GET /academics/groups/archived`,
`GET /academics/groups/search?query=a`, `GET /academics/groups/by-course/1`,
`GET /academics/groups/by-type/robotics` — all must return 200, not 500.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they call `GET /academics/groups`,
   **Then** they receive a paginated list of active, enriched groups with 200 OK.
2. **Given** an authenticated user, **When** they call any previously-broken endpoint,
   **Then** the server does not raise an AttributeError or 500.
3. **Given** a UI calling `GET /academics/groups/search?query=robot`,
   **Then** it receives the same results it would get from `GET /academics/groups/filter?q=robot`.

---

### User Story 2 — Redundant Endpoints Are Removed (Priority: P1)

Two endpoints (`/search` and `/by-type/{group_type}`) duplicate the filter endpoint with
no added value. Removing them shrinks the API surface and eliminates the confusion of
having two ways to do the same thing.

**Why this priority**: Dead API surface causes incorrect client code and maintenance burden.

**Independent Test**: `GET /academics/groups/search` returns 404 (route removed).
`GET /academics/groups/by-type/{type}` returns 404.

**Acceptance Scenarios**:

1. **Given** a client calling `/academics/groups/search`, **When** the request is sent,
   **Then** the server returns 404 (endpoint no longer exists).
2. **Given** a client calling `/academics/groups/by-type/{type}`, **When** the request
   is sent, **Then** the server returns 404.

---

### User Story 3 — Enriched List Endpoint Gets Pagination (Priority: P1)

`GET /academics/groups/enriched` currently returns all active groups with no limit.
At scale this is a performance risk. It must be paginated and powered by `filter_groups`.

**Why this priority**: Unbound queries can OOM the server on large datasets.

**Independent Test**: `GET /academics/groups/enriched?skip=0&limit=20` returns at most 20
groups. `GET /academics/groups/enriched?skip=20&limit=20` returns the next page with
correct `total` count.

**Acceptance Scenarios**:

1. **Given** 150 active groups, **When** calling `GET /academics/groups/enriched`,
   **Then** the response has at most `limit` groups and `total` reflects 150.
2. **Given** no active groups, **When** calling `GET /academics/groups/enriched`,
   **Then** the response has `data: []` and `total: 0`.

---

### User Story 4 — Dead Code and DTOs Are Removed (Priority: P2)

Unused DTOs (`GroupListItem`), orphaned repository functions (`get_all_archived_groups`),
and the untyped `list[dict]` in `GroupedItem` are removed or fixed per the dead code
discipline and typed-contracts constitution principles.

**Why this priority**: Dead code increases cognitive overhead and risks future misuse.

**Independent Test**: `grep -r "GroupListItem"` returns no results outside its definition
file. `grep -r "get_all_archived_groups"` returns no callers. `GroupedItem.groups` is
typed as `list[EnrichedGroupPublic]` (not `list[dict]`).

**Acceptance Scenarios**:

1. **Given** the codebase, **When** grepping for `GroupListItem`, **Then** no file
   imports it except its own definition — or the definition itself is gone.
2. **Given** `GroupedItem` schema, **When** inspecting `groups` field type, **Then** it
   is `list[EnrichedGroupPublic]`, not `list[dict]`.
3. **Given** the repository, **When** grepping for `get_all_archived_groups`, **Then**
   no callers remain in `app/` (definition deleted).

---

### User Story 5 — Filter Endpoint Gets Additional Filter Parameters (Priority: P2)

The `filter_groups` engine should be extended with additional practically useful filters
that the old individual endpoints supported or that are obviously missing for a groups
directory search experience.

**Why this priority**: Extends the filter's utility to cover all common query patterns
without needing new endpoints.

**Independent Test**: `GET /academics/groups/filter?max_capacity=10` returns only groups
whose `max_capacity ≤ 10`. `GET /academics/groups/filter?has_instructor=false` returns
only groups with no instructor assigned. Each new param independently returns correct
results.

**Acceptance Scenarios**:

1. **Given** groups with varying capacities, **When** filtering by `max_capacity_max=8`,
   **Then** only groups with `max_capacity ≤ 8` are returned.
2. **Given** groups some assigned to an instructor and some not, **When** filtering with
   `has_instructor=false`, **Then** only instructor-less groups are returned.
3. **Given** a group with `include_inactive=true`, **When** calling filter with
   `status=inactive`, **Then** inactive groups appear in results.

---

### User Story 6 — Loose Return Types Are Replaced with Typed DTOs (Priority: P2)

Any remaining `-> tuple`, `-> dict`, `-> list[dict]` return types in the directory slice
that appear in public Protocol interfaces are replaced with named Pydantic DTOs, aligning
with constitution §III.

**Why this priority**: Typed contracts prevent silent data shape regressions.

**Independent Test**: Grep for `-> tuple` and `-> dict` in `directory/service.py`,
`directory/repository.py`, `directory/interface.py` — zero results.

**Acceptance Scenarios**:

1. **Given** `GroupDirectoryServiceInterface`, **When** inspecting all method signatures,
   **Then** no return type is `tuple`, `dict`, or `list[dict]`.
2. **Given** any public repository function called by the service, **When** that function
   is listed in the interface Protocol, **Then** its return type is a named DTO.

---

## Requirements

### Functional Requirements

#### US1 — Fix Broken Endpoints

- **FR-001**: `GET /academics/groups` MUST return paginated enriched groups (active) by
  delegating to `filter_groups(status=["active"])`. Returns `EnrichedGroupPublic` shape.
- **FR-002**: `GET /academics/groups/archived` MUST return paginated enriched groups
  (archived) by delegating to `filter_groups(status=["archived"])`.
- **FR-003**: `GET /academics/groups/by-course/{course_id}` MUST return enriched groups
  for the given course by delegating to `filter_groups(course_ids=[course_id], ...)`.
  The `include_inactive` param translates to `status=["active", "inactive"]` when true,
  or `status=["active"]` when false.

#### US2 — Remove Redundant Endpoints

- **FR-004**: `GET /academics/groups/search` MUST be removed. Clients MUST use
  `GET /academics/groups/filter?q=...` instead.
- **FR-005**: `GET /academics/groups/by-type/{group_type}` MUST be removed. Clients MUST
  use `GET /academics/groups/filter?name=...` instead.

#### US3 — Paginate Enriched List

- **FR-006**: `GET /academics/groups/enriched` MUST accept `skip` and `limit` query
  params (default `skip=0`, `limit=50`, max `limit=200`).
- **FR-007**: `GET /academics/groups/enriched` MUST delegate to
  `filter_groups(status=["active"])` internally.
- **FR-008**: `get_all_active_groups_enriched()` service method MUST be deleted.
  The `get_all_active_groups()` service method MUST be deleted (was already deleted; this
  confirms it stays gone).

#### US4 — Dead Code Cleanup

- **FR-009**: `GroupListItem` API DTO MUST be deleted if it has no remaining callers after
  the router rewrites.
- **FR-010**: `get_all_archived_groups()` in `repository.py` MUST be deleted (orphaned,
  no callers).
- **FR-011**: `GroupedItem.groups` field type MUST change from `list[dict]` to
  `list[EnrichedGroupPublic]`.
- **FR-012**: The `GroupByField` enum in `grouped.py` MUST be confirmed as used or
  deleted if it has no callers.

#### US5 — Additional Filter Parameters

- **FR-013**: `filter_groups` MUST accept `has_instructor: bool | None` — when `false`,
  returns groups with `instructor_id IS NULL`; when `true`, returns groups where
  `instructor_id IS NOT NULL`.
- **FR-014**: `filter_groups` MUST accept `max_capacity_min: int | None` and
  `max_capacity_max: int | None` — filters by `groups.max_capacity`.
- **FR-015**: `filter_groups` MUST accept `include_inactive: bool` (default `false`) as
  a convenience alias — when `true`, status filter includes inactive groups alongside
  active (equivalent to `status=["active", "inactive"]` when no explicit status given).
- **FR-016**: `filter_groups` MUST accept `q` searches across `default_day` text as well
  (e.g. searching "Friday" returns groups scheduled on Friday).

#### US6 — Typed Contracts

- **FR-017**: All public service methods in `GroupDirectoryServiceInterface` MUST have
  return types that are named Pydantic DTOs or ORM models (no `tuple`, `dict`,
  `list[dict]`).
- **FR-018**: Any router endpoint that currently uses `PaginatedResponse` with
  `GroupListItem` MUST be updated to use `ApiResponse[GroupFilterResultDTO]` or
  `PaginatedResponse[EnrichedGroupPublic]` after the migration.

### Key Entities

- **`GroupFilterDTO`**: Input contract for all group filtering — extended with 3 new fields.
- **`GroupFilterResultDTO`**: Paginated output of `filter_groups` — becomes the canonical
  return shape for all directory list endpoints.
- **`EnrichedGroupDTO`** (service layer): Typed enriched group — replaces bare `Group`
  ORM in all directory outputs.
- **`EnrichedGroupPublic`** (API layer): Public API shape for enriched group.
- **`GroupedGroupsResult`** / **`GroupedItem`**: Container for grouped views.
- **`GroupListItem`** (to be deleted): Slim ORM-backed DTO — superseded by
  `EnrichedGroupPublic`.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: All five previously broken endpoints return HTTP 200 after this change.
- **SC-002**: Two redundant endpoints (`/search`, `/by-type`) return HTTP 404 (removed).
- **SC-003**: `GET /academics/groups/enriched?limit=20` returns at most 20 groups with
  a `total` count field.
- **SC-004**: Zero occurrences of `-> tuple`, `-> dict`, `-> list[dict]` remain in
  `directory/service.py`, `directory/repository.py`, and `directory/interface.py` public
  method signatures.
- **SC-005**: Zero occurrences of `GroupListItem` anywhere in the codebase after cleanup
  (or only in its own definition if kept for a different reason).
- **SC-006**: Each new filter parameter (`has_instructor`, `max_capacity_min`,
  `max_capacity_max`, `include_inactive`) returns correct filtered results when tested
  independently.
- **SC-007**: The entire test suite passes without errors after all changes.

---

## Assumptions

- `include_inactive` in the old `by-course` endpoint means "include active + inactive"
  (not archived). Archived groups are always excluded unless `status=["archived"]` is
  explicitly passed.
- `filter_groups` with no `status` param currently returns all statuses. After FR-015,
  it will default to `status=["active"]` if no explicit `status` is provided. The
  `include_inactive=true` flag will expand this implicit default to include inactive.
  Archived groups are strictly excluded unless explicitly requested.
- `GroupListItem` is confirmed unused after US1/US2 rewrites; the cleanup in FR-009
  proceeds on that basis. If a caller is found during implementation, it is migrated to
  `EnrichedGroupPublic` rather than keeping `GroupListItem`.
- `GroupByField` enum is likely unused (the grouped endpoint accepts a raw `str`); it
  will be deleted unless a caller is found.
- No database migrations are required — all changes are in application code only.
- The frontend API contract file (`techno_terminal_UI/groups-api.md`) may need updating
  to reflect removed endpoints and new filter params. This is in scope as documentation
  only (no UI code changes required for this spec).
