# Tasks: Session Level Integrity & Course Validation

**Input**: [spec.md](spec.md), [plan.md](plan.md) | **Phase**: Tasks

---

## Phase 1: US1 — Group sessions show only current level content (P1)

**Goal**: Default session queries return only the current active level's sessions instead of ALL historical sessions.

- [ ] T001 [P] [US1] Add `get_group_level_id()` helper to `app/modules/academics/session/repository.py` — lookup `GroupLevel.id` by `(group_id, level_number)`
- [ ] T002 [P] [US1] Add `list_sessions_by_group_level()` to `app/modules/academics/session/repository.py` — filter `CourseSession` by `group_level_id`
- [ ] T003 [US1] Change `list_group_sessions()` in `app/modules/academics/session/service.py` to look up group's active `group_level_id` via `get_current_group_level()` when `level_number` is None, then filter by it
- [ ] T004 [US1] Update `get_levels_detailed()` in `app/modules/academics/group/details/service.py` — default to current active level instead of ALL levels when `level_number` is None

**Test**: T011-05 (default returns current level), T011-06 (explicit filter still works), T011-09 (get_levels_detailed defaults)

---

## Phase 2: US2 — Sessions linked to GroupLevel record (P1)

**Goal**: All session creation paths populate `group_level_id`.

- [ ] T005 [US2] Add `group_level_id: int | None = None` param to `create_sessions_in_session()` in `app/modules/academics/helpers/session_planning.py` — set on each created `CourseSession`
- [ ] T006 [US2] Pass `group_level_id=level.id` in `create_group_with_first_level()` at `app/modules/academics/group/lifecycle/service.py:126`
- [ ] T007 [US2] Pass `group_level_id=new_level.id` in `progress_to_next_level()` at `app/modules/academics/group/lifecycle/service.py:249`
- [ ] T008 [US2] Pass `group_level_id=level.id` in `add_level_to_existing_group()` at `app/modules/academics/group/lifecycle/service.py:375`
- [ ] T009 [US2] Look up `group_level_id` via `repo.get_group_level_id()` in `generate_level_sessions()` at `app/modules/academics/session/service.py:75` — pass to `create_sessions_in_session()`
- [ ] T010 [US2] Look up `group_level_id` via `repo.get_group_level_id()` in `add_extra_session()` at `app/modules/academics/session/service.py:93` — set on individual `CourseSession`
- [ ] T011 [US2] Look up `group_level_id` in `cancel_session()` at `app/modules/academics/session/service.py:189` — set on replacement `CourseSession`
- [ ] T012 [US2] Create migration `db/migrations/053_backfill_session_group_level_id.sql` to backfill NULL `group_level_id` by matching `(group_id, level_number)` to `group_levels`

**Test**: T011-01 (create_sessions_in_session param), T011-02 (lifecycle service calls), T011-03 (extra session), T011-04 (generate level sessions), T011-10 (backfill migration)

---

## Phase 3: US3 — Course creation limits (P2)

**Goal**: Prevent excessive levels/sessions at course creation time.

- [ ] T013 [US3] Add `MAX_SESSIONS_PER_LEVEL = 100` constant and extend validator in `AddNewCourseInput` at `app/modules/academics/course/schemas.py` — reject > 100
- [ ] T014 [US3] Add same max validation to `UpdateCourseDTO.sessions_per_level` in same file
- [ ] T015 [US3] Add `MAX_LEVELS = 100` constant and `max_levels` field validation to both schemas (optional field, validated if provided)

**Test**: T011-07 (sessions_per_level > 100 rejected), T011-08 (max_levels > 100 rejected)

---

## Dependency Graph

```
T001 ─┐
T002 ─┤
      ├──→ T003 ─→ T004    (Phase 1: US1)
      │
T005 ─┤
      ├──→ T006 ─→ T007 ─→ T008   (Phase 2: US2 bulk creation paths)
      │
T009 ─┤
      ├──→ T010 ─→ T011   (Phase 2: US2 individual creation paths)
      │
T012                  (Phase 2: US2 migration — independent, run last)
      
T013 ─→ T014 ─→ T015   (Phase 3: US3 — fully independent of US1/US2)
```

T001-T002, T005, T009, T012, T013 can run in parallel (different files, no dependencies).
