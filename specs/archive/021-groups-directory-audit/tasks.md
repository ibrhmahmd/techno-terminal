---
description: "Task list for Groups Directory Audit"
---

# Tasks: Groups Directory Module Audit

**Input**: Design documents from `/specs/021-groups-directory-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Verify API routing structure for Academics module

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

*(No blocking foundational prerequisites for these API refactors)*

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Fix Broken Endpoints (Priority: P1) 🎯 MVP

**Goal**: Restore stability by redirecting currently broken API endpoints to the filter engine.

**Independent Test**: Send `GET /academics/groups`, `GET /academics/groups/archived`, `GET /academics/groups/by-course/1`. All must return 200 OK.

### Implementation for User Story 1

- [x] T002 [US1] Update `GET /academics/groups` endpoint to delegate to `filter_groups` in `app/api/routers/academics/group_directory_router.py`
- [x] T003 [US1] Update `GET /academics/groups/archived` endpoint to delegate to `filter_groups` in `app/api/routers/academics/group_directory_router.py`
- [x] T004 [US1] Update `GET /academics/groups/by-course/{course_id}` endpoint to delegate to `filter_groups` in `app/api/routers/academics/group_directory_router.py`

**Checkpoint**: User Story 1 endpoints are functional and stable.

---

## Phase 4: User Story 2 - Remove Redundant Endpoints (Priority: P1)

**Goal**: Delete endpoints that duplicate filter functionality.

**Independent Test**: Send `GET /academics/groups/search` and `GET /academics/groups/by-type/robotics`. Both must return 404.

### Implementation for User Story 2

- [x] T005 [P] [US2] Remove `GET /academics/groups/search` from `app/api/routers/academics/group_directory_router.py`
- [x] T006 [P] [US2] Remove `GET /academics/groups/by-type/{group_type}` from `app/api/routers/academics/group_directory_router.py`

**Checkpoint**: Redundant endpoints successfully removed.

---

## Phase 5: User Story 3 - Paginate Enriched List (Priority: P1)

**Goal**: Convert the open-ended enriched group fetch into a paginated endpoint relying on the `filter_groups` engine.

**Independent Test**: `GET /academics/groups/enriched?skip=0&limit=5` returns max 5 results with a total count.

### Implementation for User Story 3

- [x] T007 [US3] Add pagination parameters and delegate `GET /academics/groups/enriched` to `filter_groups` in `app/api/routers/academics/group_directory_router.py`

**Checkpoint**: Enriched list is safely paginated.

---

## Phase 6: User Story 4 - Dead Code and DTO Cleanup (Priority: P2)

**Goal**: Erase orphaned DTOs and repository code and enforce Typed Contracts by replacing generic dicts.

**Independent Test**: The codebase can compile and tests pass without `GroupListItem`.

### Implementation for User Story 4

- [x] T008 [P] [US4] Remove `GroupListItem` class from `app/api/schemas/academics/group.py`
- [x] T009 [P] [US4] Update `groups` field type to `list[EnrichedGroupPublic]` in `GroupedItem` in `app/api/schemas/academics/grouped.py`
- [x] T010 [P] [US4] Remove `get_all_archived_groups()` method from `app/modules/academics/group/directory/repository.py`

**Checkpoint**: Dead code successfully cleared.

---

## Phase 7: User Story 5 - Additional Filter Parameters (Priority: P2)

**Goal**: Expand the filter engine so frontend has a single robust query API.

**Independent Test**: Queries to `GET /academics/groups/filter` properly isolate by `has_instructor`, `max_capacity`, and properly default to active-only status.

### Implementation for User Story 5

- [x] T011 [US5] Add `has_instructor`, `max_capacity_min`, `max_capacity_max`, `include_inactive` parameters to `GroupFilterDTO` in `app/modules/academics/group/directory/schemas.py`
- [x] T012 [US5] Implement filtering conditions for the new schema parameters in `filter_groups_query` in `app/modules/academics/group/directory/repository.py`
- [x] T013 [US5] Implement Active-only default status behavior if none provided, in `filter_groups_query` in `app/modules/academics/group/directory/repository.py`
- [x] T014 [US5] Add support for matching against `default_day` when using the generic `q` search param in `app/modules/academics/group/directory/repository.py`

**Checkpoint**: Powerful and unified filtering engine in place.

---

## Phase 8: User Story 6 - Loose Return Types (Priority: P2)

**Goal**: Ensure all directory slice protocol interfaces strictly return typed contracts.

**Independent Test**: Validate that no dict-based typings leak through `GroupDirectoryServiceInterface`.

### Implementation for User Story 6

- [x] T015 [US6] Review and verify `GroupDirectoryServiceInterface` methods exclusively return Pydantic DTOs or explicit models in `app/modules/academics/group/directory/interface.py`

**Checkpoint**: System conforms strictly to Constitution §III Typed Contracts.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T016 Run automated tests `pytest tests/test_academics.py` to confirm no regressions.
- [x] T017 Final check against AGENTS.md Constitution parameters.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: N/A
- **User Stories (Phase 3+)**: US1, US2, US3, US4, US5, US6 can mostly proceed independently but US1/US2/US3 involve the router, while US5 involves the repository.
- **Polish (Final Phase)**: Runs at the end.

### User Story Dependencies

- **User Story 1 (P1)**: Independent.
- **User Story 2 (P1)**: Independent.
- **User Story 3 (P1)**: Independent.
- **User Story 4 (P2)**: Best to do after router updates (US1/US2/US3) to ensure DTO is truly orphaned.
- **User Story 5 (P2)**: Independent, but builds repository features supporting the router.
- **User Story 6 (P2)**: Validation step checking typed contracts.

### Parallel Opportunities

- US4 tasks can be executed in parallel (T008, T009, T010).
- US2 tasks can be executed in parallel (T005, T006).
- US1 tasks can be run sequentially or concurrently.

---

## Parallel Example: User Story 2

```bash
# Removing endpoints
Task: "Remove GET /academics/groups/search"
Task: "Remove GET /academics/groups/by-type/{group_type}"
```

---

## Implementation Strategy

### MVP First (User Story 1, 2, 3 Only)

1. Fix the router to stop sending 500s.
2. Remove the redundant paths.
3. Add pagination.
4. Validate.

### Incremental Delivery

1. Deploy Router Refactor (US1-US3)
2. Deploy Filter capabilities upgrade (US5)
3. Deploy Code Cleanup (US4, US6)
