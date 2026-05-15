---

description: "Task list for fixing missing session commits across 3 service files"
---

# Tasks: Fix Missing Session Commits

**Input**: Design documents from `specs/009-fix-missing-commits/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include persistence-verification tests for each affected endpoint.

**Organization**: Tasks grouped by user story — each story is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify audit findings, confirm fix pattern, apply temporary pool increase

- [ ] T001 Review audit report at `specs/006-daily-report-fixes/audit-missing-commits.md` and confirm all 16 affected methods
- [ ] T002 Increase connection pool temporarily in `app/db/connection.py` — change `pool_size=5` to `pool_size=10` and `max_overflow=5` to `max_overflow=5` (total 15)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the fix pattern so all user stories follow the same approach

- [ ] T003 Add `session.commit()` and `session.refresh(entity)` after `repo.update_course_price()` in `app/modules/academics/course/service.py` (follow fix pattern from `add_new_course`)
- [ ] T004 Confirm existing `session.commit()` pattern in `app/modules/academics/session/service.py`, `group/core/service.py`, `group/lifecycle/service.py` as reference

**Checkpoint**: Fix pattern validated — user story implementation can begin

---

## Phase 3: User Story 1 — Enrollments Persist (Priority: P1)

**Goal**: All 5 enrollment write methods persist data to the database

**Independent Test**: Create an enrollment via POST, then GET the enrollment/enriched roster and verify the data matches.

### Implementation for User Story 1

- [ ] T005 [US1] Add `session.commit()` and `session.refresh(created)` before return in `enroll_student()` at `app/modules/enrollments/services/enrollment_service.py:81-123`
- [ ] T006 [P] [US1] Add `session.commit()` and `session.refresh(updated)` before return in `apply_sibling_discount()` at `app/modules/enrollments/services/enrollment_service.py:137-138`
- [ ] T007 [P] [US1] Add `session.commit()` and `session.refresh(created)` before return in `transfer_student()` at `app/modules/enrollments/services/enrollment_service.py:159-200`
- [ ] T008 [P] [US1] Add `session.commit()` and `session.refresh(updated)` before return in `drop_enrollment()` at `app/modules/enrollments/services/enrollment_service.py:218-243`
- [ ] T009 [P] [US1] Add `session.commit()` and `session.refresh(updated)` before return in `complete_enrollment()` at `app/modules/enrollments/services/enrollment_service.py:261-286`

### Tests for User Story 1

- [ ] T010 [US1] Add `test_enroll_student_persists` — POST enrollment, then GET roster and verify student and level_number match input
- [ ] T011 [P] [US1] Add `test_enroll_drop_persists` — create enrollment, drop it, then GET and verify status is "dropped"
- [ ] T012 [P] [US1] Add `test_enroll_transfer_persists` — create enrollment, transfer to new group, verify source is "transferred" and target exists
- [ ] T013 [P] [US1] Add `test_enroll_complete_persists` — create enrollment, complete it, verify status is "completed"

**Checkpoint**: At this point, User Story 1 should be fully functional — all enrollment data persists across requests

---

## Phase 4: User Story 2 — Competitions Persist (Priority: P1)

**Goal**: All 11 competition + team write methods persist data to the database

**Independent Test**: Create a competition via POST, then GET the competition list and verify it appears.

### Implementation for User Story 2

- [ ] T014 [P] [US2] Add `session.commit()` and `session.refresh(comp)` before return in `create_competition()` at `app/modules/competitions/services/competition_service.py:31-43`
- [ ] T015 [P] [US2] Add `session.commit()` and `session.refresh(team)` before return in `update_competition()` at `app/modules/competitions/services/competition_service.py:56-59`
- [ ] T016 [P] [US2] Add `session.commit()` before return in `delete_competition()` at `app/modules/competitions/services/competition_service.py:61-70`
- [ ] T017 [P] [US2] Add `session.commit()` before return in `restore_competition()` at `app/modules/competitions/services/competition_service.py:72-75`
- [ ] T018 [US2] Add `session.commit()` before return in `register_team()` at `app/modules/competitions/services/team_service.py:160-163`
- [ ] T019 [P] [US2] Add `session.commit()` before return in `update_team()` at `app/modules/competitions/services/team_service.py:312-314`
- [ ] T020 [P] [US2] Add `session.commit()` before return in `delete_team()` at `app/modules/competitions/services/team_service.py:318-326`
- [ ] T021 [P] [US2] Add `session.commit()` before return in `restore_team()` at `app/modules/competitions/services/team_service.py:330-331`
- [ ] T022 [US2] Add `session.commit()` and `session.refresh(team)` before return in `update_placement()` at `app/modules/competitions/services/team_service.py:350-393`
- [ ] T023 [P] [US2] Add `session.commit()` before return in `add_team_member_to_existing()` at `app/modules/competitions/services/team_service.py:405-443`
- [ ] T024 [P] [US2] Add `session.commit()` before return in `remove_team_member()` at `app/modules/competitions/services/team_service.py:446-453`
- [ ] T025 [US2] Add `session.commit()` after `mark_fee_paid()` at `app/modules/competitions/services/team_service.py:534-547`

### Tests for User Story 2

- [ ] T026 [US2] Add `test_competition_create_persists` — POST competition, then GET list and verify name/date match
- [ ] T027 [P] [US2] Add `test_team_register_persists` — create comp + register team, then GET teams and verify team name and members
- [ ] T028 [P] [US2] Add `test_team_placement_persists` — register team, set placement, GET team and verify placement_rank

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 — System Stable Under Load (Priority: P2)

**Goal**: Connection pool handles concurrent enrollment operations without exhaustion

**Independent Test**: Run 5 concurrent enrollment requests — all return 201 and data persists.

### Implementation for User Story 3

- [ ] T029 [US3] Verify pool settings in `app/db/connection.py` — confirm `pool_size=10` handles concurrent load
- [ ] T030 [US3] Add connection pool utilization logging in `app/db/connection.py` — log pool size and overflow when connections are checked out

**Checkpoint**: System handles normal concurrent usage without pool exhaustion

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and documentation

- [ ] T031 [P] Update course test `test_create_course_success` in `tests/test_academics_courses.py` — add GET verification step after POST
- [ ] T032 Run full test suite for all affected modules and verify all tests pass
- [ ] T033 Update AGENTS.md — mark task completion status

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: No dependencies — can start immediately
- **Phase 2**: Depends on Phase 1 — establishes the fix pattern
- **US1 (Phase 3)**: Depends on Phase 2 — NO dependency on US2 (independent)
- **US2 (Phase 4)**: Depends on Phase 2 — NO dependency on US1 (independent)
- **US3 (Phase 5)**: Depends on Phase 1 — NO dependency on US1/US2 (independent)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US3 (P2)**: Can start after Phase 1 — no dependencies on other stories

### Within Each User Story

- Implementation tasks before tests (fix the code, then verify)
- Tasks marked [P] within a phase can run in parallel

### Parallel Opportunities

- T005-T009 can all run in parallel (different methods in same file)
- T014-T017 can all run in parallel (competition_service.py methods)
- T019-T025 can all run in parallel (team_service.py methods)
- T010-T013 (US1 tests) can all run in parallel
- T026-T028 (US2 tests) can all run in parallel
- US1, US2, and US3 are fully independent — can be done in parallel by different developers

---

## Parallel Example: All User Stories

```bash
# US1 — Fix all 5 enrollment methods in parallel:
Task: "Fix enroll_student() in enrollment_service.py"
Task: "Fix apply_sibling_discount() in enrollment_service.py"
Task: "Fix transfer_student() in enrollment_service.py"
Task: "Fix drop_enrollment() in enrollment_service.py"
Task: "Fix complete_enrollment() in enrollment_service.py"

# US2 — Fix competition + team methods in parallel:
Task: "Fix create_competition() in competition_service.py"
Task: "Fix register_team() in team_service.py"
Task: "Fix update_placement() in team_service.py"

# US3 — Pool tuning in parallel with US1/US2:
Task: "Update pool_size in connection.py"
```

---

## Implementation Strategy

### MVP Scope (US1 only)

1. Complete Phase 1 + Phase 2 (foundation)
2. Complete Phase 3 — US1: Enrollment fixes + tests
3. **STOP and VALIDATE**: Enrollment data now persists
4. Deploy if urgent — enrollments are the highest-impact fix

### Full Delivery

1. MVP (US1) → Deploy if needed
2. Add US2 (Competitions) → Test independently → Deploy
3. Add US3 (Pool tuning) → Verify under load
4. Polish tests → Final test suite run

### Parallel Team Strategy

With multiple developers:
- Developer A: US1 (Enrollments) — 5 fixes + 4 tests
- Developer B: US2 (Competitions) — 12 fixes + 3 tests
- Developer C: US3 (Pool tuning) — 2 tasks

---

## Notes

- [P] tasks = different files or independent methods, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently completable and testable
- Fixes are 1-2 lines each — every task is a simple insert
- Commit after each user story
- No schema changes, migrations, or frontend changes required
