# Tasks: Groups Day Order & Search Filter

**Input**: Design documents from `/specs/020-groups-filter-day-order/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Foundational (Shared Prerequisites)

**Purpose**: Shared constants and DTO layer that both user stories depend on. Must complete before story work begins.

- [x] T001 Add `DAY_ORDER` dict to `app/modules/academics/constants.py` — `{"Friday":0,"Saturday":1,"Sunday":2,"Monday":3,"Tuesday":4,"Wednesday":5,"Thursday":6}` with inline doc note that it does NOT replace `WEEKDAYS` (which stays Monday=0 for date math)
- [x] T002 [P] Add `DAY_ABBREV_MAP` dict to `app/modules/academics/constants.py` — `{"mon":"Monday","tue":"Tuesday","wed":"Wednesday","thu":"Thursday","thurs":"Thursday","fri":"Friday","sat":"Saturday","sun":"Sunday"}` (replicated from `students_router.py`; keeps crm router unchanged)
- [x] T003 [P] Add `GroupFilterDTO` and `GroupFilterResultDTO` to `app/modules/academics/group/directory/schemas.py` — all 27 fields per data-model.md; use `Optional` + `None` defaults throughout; import `date`, `time` from `datetime` and `Literal` from `typing`

**Checkpoint**: Constants and DTOs ready — both user stories can now proceed. ✅

---

## Phase 2: User Story 1 — Day Order Fix (Priority: P1) 🎯 MVP

**Goal**: The `GET /academics/groups/grouped?group_by=day` endpoint returns weekday buckets ordered Friday → Saturday → Sunday → Monday → Tuesday → Wednesday → Thursday → Unspecified (never alphabetically).

**Independent Test**: Call `GET /academics/groups/grouped?group_by=day`. Verify the `groups[].label` sequence is `["Friday","Saturday","Sunday","Monday","Tuesday","Wednesday","Thursday"]` (Unspecified last if any null-day groups exist). Alphabetical order (Monday first) confirms the bug is still present.

- [x] T004 [US1] Fix sort key in `app/modules/academics/group/directory/service.py` — in `get_groups_grouped()` replace `all_items.sort(key=lambda x: x.label)` with `all_items.sort(key=lambda x: DAY_ORDER.get(x.label, 99))`; add import `from app.modules.academics.constants import DAY_ORDER` at top of file alongside existing imports

**Checkpoint**: US1 complete. ✅ Verify by calling the grouped endpoint — Friday must be first.

---

## Phase 3: User Story 2 — Groups Filter Endpoint (Priority: P1)

**Goal**: `GET /academics/groups/filter` accepts multi-criteria query params and returns paginated, enriched group results. Covers FR-005 through FR-017.

**Independent Test**: Call `GET /academics/groups/filter?status=active&skip=0&limit=10`. Must return `{"success":true,"data":{"groups":[...],"total":N,"skip":0,"limit":10}}`. Test each param independently per `contracts/filter_request.md`.

### Implementation for User Story 2

- [x] T005 [US2] Add `filter_groups_query()` to `app/modules/academics/group/directory/repository.py` — dynamic WHERE clauses for all filter fields, COUNT query for total, paginated data query, EXISTS subqueries for session number/date filters, enrolled-student q search via JOIN students.
  > **Note**: `gender`, `age_min`, `age_max` omitted — not present on `groups` table. `course_not`, `instructor_has_id`, `instructor_not_id` omitted — no history tables exist in schema. `price` uses `c.price_per_level` (actual column name).

- [x] T006 [US2] Add `filter_groups()` method to `app/modules/academics/group/directory/service.py` — thin delegation to `repo.filter_groups_query()`, wraps in `GroupFilterResultDTO`

- [x] T007 [US2] Add `filter_groups()` to `app/modules/academics/group/directory/interface.py` — added to `GroupDirectoryServiceInterface` Protocol with imports

- [x] T008 [US2] Add `GET /academics/groups/filter` endpoint to `app/api/routers/academics/group_directory_router.py` — placed BEFORE `/{group_id}` routes; day normalization via `_normalize_day_names()` helper using `DAY_ABBREV_MAP`; date/time string parsing with 422 on invalid format; sort_by/sort_order validation with graceful fallback

**Checkpoint**: US2 complete. ✅ Verify each filter param independently then test combined params. Check empty-result case (no error, `total:0`).

---

## Phase 4: User Story 3 — Free-Text Search Scope (Priority: P2)

**Goal**: The `q` parameter in the filter endpoint searches across ALL searchable fields simultaneously: group name, course name, instructor name, schedule time, notes, and enrolled student names. This story is satisfied entirely by the `q` implementation inside T005 — no separate files needed.

**Independent Test**: Call `GET /academics/groups/filter?q=robot`. Groups matching in any of: name, course name, instructor name, notes should be returned. Call `GET /academics/groups/filter?q=ahmed` — all groups taught by any instructor named Ahmed should appear.

- [x] T009 [P] [US3] Verify `q` clause in `app/modules/academics/group/directory/repository.py` covers all required fields — confirmed: `g.name`, `c.name`, `e.full_name`, `g.notes`, `CAST(g.default_time_start AS TEXT)`, and enrolled-student-name subquery (JOIN students via enrollments). All present in T005.

**Checkpoint**: US3 complete. ✅ All three user stories are independently functional.

---

## Phase 5: Polish & Verification

**Purpose**: Integration smoke-test, edge-case hardening, cleanup.

- [x] T010 [P] Verify `app/modules/academics/constants.py` — confirmed `WEEKDAYS` list (Monday=0) is unchanged. `next_weekday()` in `time_helpers.py` uses `WEEKDAYS.index()` — unaffected, no regression. ✅
- [x] T011 [P] Verify `app/api/routers/academics/group_directory_router.py` — confirmed `/filter` registered at line 222 BEFORE `/{group_id}/enriched` at line 316. Route order correct. ✅
- [ ] T012 Smoke-test full endpoint set: `GET /academics/groups/grouped?group_by=day` (day order), `GET /academics/groups/filter` (no params → all groups), `GET /academics/groups/filter?q=a`, `GET /academics/groups/filter?status=active&sort_by=day&sort_order=asc` — confirm 200 responses with correct envelopes
- [ ] T013 [P] Update `specs/020-groups-filter-day-order/tasks.md` — mark all completed tasks

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies — start immediately. T001, T002, T003 can all run in parallel.
- **Phase 2 (US1)**: Depends on T001 (needs `DAY_ORDER` constant).
- **Phase 3 (US2)**: Depends on T001 (`DAY_ORDER` for sort), T002 (`DAY_ABBREV_MAP` for day normalization), T003 (`GroupFilterDTO`/`GroupFilterResultDTO`).
- **Phase 4 (US3)**: Depends on T005 — verification only, no new code.
- **Phase 5 (Polish)**: Depends on all prior phases.

### User Story Dependencies

- **US1 (P1)**: Depends on T001 only. Fastest to ship — 1 file, 1 line change.
- **US2 (P1)**: Depends on T001 + T002 + T003. Core feature work.
- **US3 (P2)**: Entirely within T005 scope — no separate implementation.

### Within Each Story

- Phase 1 tasks (T001–T003): all parallel
- US1: T004 only (single task)
- US2: T005 → T006 → T007 → T008 (sequential; each builds on the previous)
- US3: T009 (verification of T005)

### Parallel Opportunities

```bash
# Phase 1 — all three tasks in parallel:
T001: Add DAY_ORDER to constants.py
T002: Add DAY_ABBREV_MAP to constants.py
T003: Add GroupFilterDTO + GroupFilterResultDTO to schemas.py

# After Phase 1 — US1 and US2 foundational work can overlap:
T004: Day sort fix in service.py          ← US1, unblocked by T001
T005: filter_groups_query() in repo.py   ← US2, unblocked by T001+T002+T003
```

---

## Implementation Strategy

### MVP (US1 only — 3 tasks, ~5 min)

1. Complete T001 (DAY_ORDER constant)
2. Complete T004 (sort fix in service.py)
3. **STOP and VALIDATE**: Call `/academics/groups/grouped?group_by=day`, verify Friday is first
4. Ship — day ordering bug is fixed

### Full Delivery

1. T001 + T002 + T003 in parallel → Foundation complete
2. T004 → US1 done (validate)
3. T005 → T006 → T007 → T008 → US2 done (validate each param)
4. T009 → US3 done (verify q scope)
5. T010–T013 → Polish complete

---

## Notes

- `[P]` = different files, no shared state dependency — safe to implement in parallel
- T005 is the most complex task: the raw SQL builder with 20+ dynamic WHERE clauses
- Historical filters (`course_not`, `instructor_has_id`, `instructor_not_id`) **not implemented** — no history tables exist in the DB schema. These are spec aspirations; a follow-up migration + spec update is needed if this is desired.
- `gender`, `age_min`, `age_max` filters **not implemented** — columns do not exist on the `groups` table.
- Session number filtering implemented via EXISTS subquery against `sessions` table (already confirmed column `session_number` exists on `CourseSession` model).
- Day normalization happens in the **router** (T008), not in the service or repo, consistent with the student filter pattern.
