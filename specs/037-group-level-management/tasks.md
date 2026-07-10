# Tasks: Group Level Management

**Input**: Design documents from `/specs/037-group-level-management/`
**Prerequisites**: plan.md (required), spec.md (required)

---

## Phase 1: Setup & Code Cleanup

**Purpose**: Remove dead code per Dead Code Discipline and set up schemas.

- [ ] T001 [P] Delete dead `GroupLevelCourseAssignment` class from `app/modules/academics/models/group_level_models.py`
- [ ] T002 Update exports in `app/modules/academics/__init__.py` to remove `GroupLevelCourseAssignment`
- [ ] T003 [P] Remove `complete_group_level` route from `app/api/routers/academics/group_lifecycle_router.py`

---

## Phase 2: Foundational (Schemas & Repository Functions)

**Purpose**: Create DTOs and database query helpers needed for Feature A and B.

- [ ] T004 Create `DeleteLevelResult` schema in `app/modules/academics/group/lifecycle/schemas.py`
- [ ] T005 Create `UpdateLevelInput` schema in `app/modules/academics/group/level/schemas.py`
- [ ] T006 Remove `soft_delete_level` and implement direct hard delete query in `app/modules/academics/group/level/repository.py`
- [ ] T007 Implement helper functions in `app/modules/academics/group/level/repository.py`:
  - `get_previous_active_level(session, group_id, before_level_number)`
  - `count_payments_for_level(session, group_id, level_number)`
  - `count_attendance_for_level(session, group_id, level_number)`

---

## Phase 3: User Story 1 - Undo Level (Hard Delete with Cascade) (Priority: P1) 🎯 MVP

**Goal**: Cascading delete for the latest level to undo accidental progression.

**Independent Test**:
Call `DELETE /academics/groups/{group_id}/levels/{level_number}` on a clean migrated level, then verify:
1. Level row is gone.
2. Sessions are gone.
3. Migrated enrollments are gone, and old ones are reactivated.
4. Activity logs for `level_started` are gone.
5. Group `level_number` is rolled back.

### Tasks
- [ ] T008 [P] Add `delete_level` to protocol in `app/modules/academics/group/lifecycle/interface.py`
- [ ] T009 Implement `delete_level(group_id, level_number)` in `app/modules/academics/group/lifecycle/service.py` to handle the cascade transaction
- [ ] T010 Remove `delete_level` from details interface and service in `app/modules/academics/group/details/interface.py` and `service.py`
- [ ] T011 Update `DELETE /academics/groups/{group_id}/levels/{level_number}` endpoint in `app/api/routers/academics/group_details_router.py` to call `lifecycle_svc.delete_level`

---

## Phase 4: User Story 2 - Edit Level Info (Priority: P2)

**Goal**: Support changing course, instructor, price override, and notes on active levels.

**Independent Test**:
Call `PATCH /academics/groups/{group_id}/levels/{level_number}` and verify the level record is modified but group and sessions are unaffected.

### Tasks
- [ ] T012 [P] Add `update_level` to protocol in `app/modules/academics/group/level/interface.py`
- [ ] T013 Implement `update_level(group_id, level_number, data)` in `app/modules/academics/group/level/service.py`
- [ ] T014 Add `PATCH /academics/groups/{group_id}/levels/{level_number}` route in `app/api/routers/academics/group_lifecycle_router.py`

---

## Phase 5: User Story 3 - Bug Fixes & Syncing (Priority: P2)

**Goal**: Address cancel argument mismatch, cancel group sync, and general regressions.

**Independent Test**:
Verify `POST /academics/groups/{id}/levels/{num}/cancel` works with a reason and rolls back the group level number.

### Tasks
- [ ] T015 Fix cancel service signature in `app/modules/academics/group/level/service.py` to accept `reason: Optional[str] = None`
- [ ] T016 Implement level rollback logic inside cancel method in `app/modules/academics/group/level/service.py`
- [ ] T017 Update cancel router endpoint to match updated service call in `app/api/routers/academics/group_lifecycle_router.py`

---

## Phase 6: Polish & Verification

**Purpose**: Test implementation and verify all tests pass.

- [ ] T018 Write unit tests for Feature A (Clean delete, Cascade undo, Payment/Attendance block) in `tests/test_group_levels.py`
- [ ] T019 Write unit tests for Feature B (Edit instructor/course, active block check) in `tests/test_group_levels.py`
- [ ] T020 Run the full pytest test suite to ensure zero regressions
