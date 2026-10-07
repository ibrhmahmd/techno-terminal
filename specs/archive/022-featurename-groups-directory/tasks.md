---
description: "Task list for Academics Groups Directory Router Cleanup"
---

# Tasks: Academics Groups Directory Router Cleanup

**Input**: Design documents from `/specs/022-featurename-groups-directory/`
**Prerequisites**: plan.md (required)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify API routing structure for Academics module and confirm targeted endpoints exist

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

*(No blocking foundational prerequisites for these API deletions)*

**Checkpoint**: Foundation ready - endpoint removal can begin

---

## Phase 3: User Story 1 - Remove Redundant Endpoints in Group Directory Router (Priority: P1)

**Goal**: Delete the identical convenience wrapper endpoints that duplicate the `filter_groups` engine functionality.

**Independent Test**: Send `GET /academics/groups`, `GET /academics/groups/enriched`, `GET /academics/groups/archived`, and `GET /academics/groups/by-course/1`. All must return 404 Not Found.

### Implementation for User Story 1

- [x] T002 [P] [US1] Remove `GET /academics/groups` endpoint from `app/api/routers/academics/group_directory_router.py`
- [x] T003 [P] [US1] Remove `GET /academics/groups/enriched` endpoint from `app/api/routers/academics/group_directory_router.py`
- [x] T004 [P] [US1] Remove `GET /academics/groups/archived` endpoint from `app/api/routers/academics/group_directory_router.py`
- [x] T005 [P] [US1] Remove `GET /academics/groups/by-course/{course_id}` endpoint from `app/api/routers/academics/group_directory_router.py`

**Checkpoint**: Redundant endpoints successfully removed from the main group directory router.

---

## Phase 4: User Story 2 - Remove Redundant Endpoints in Courses Router (Priority: P1)

**Goal**: Delete the identical convenience wrapper endpoint from the courses router that duplicates the `filter_groups` engine functionality.

**Independent Test**: Send `GET /academics/courses/1/groups`. It must return 404 Not Found.

### Implementation for User Story 2

- [x] T006 [US2] Remove `GET /academics/courses/{course_id}/groups` endpoint from `app/api/routers/academics/courses_router.py`

**Checkpoint**: Redundant endpoint successfully removed from the courses router.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T007 Run automated tests `pytest tests/test_academics.py` to confirm no routing conflicts or regressions.
- [x] T008 Final check to ensure `GET /academics/groups/filter` properly handles all capabilities previously covered by the deleted endpoints.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: N/A
- **User Stories (Phase 3+)**: US1 and US2 can proceed entirely in parallel.
- **Polish (Final Phase)**: Runs at the end.

### User Story Dependencies

- **User Story 1 (P1)**: Independent.
- **User Story 2 (P1)**: Independent.

### Parallel Opportunities

- US1 tasks (T002, T003, T004, T005) can all be executed concurrently in a single replacement block.
- US1 and US2 can be executed concurrently as they affect different router files.

---

## Implementation Strategy

### MVP First

1. Remove all 5 endpoints from their respective routers.
2. Validate that the OpenAPI `/docs` reflects the correct API surface area.
