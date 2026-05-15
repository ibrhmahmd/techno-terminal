---

description: "Task list for course creation persistence fix"
---

# Tasks: Fix Course Creation Persistence & Data Integrity

**Input**: Design documents from `specs/006-daily-report-fixes/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include test tasks to close the persistence verification gap.

**Organization**: Tasks grouped by logical phase — bug fix is a single delivery unit (no user stories).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 1: Verify Bug Fixes Applied

**Purpose**: Confirm the three code fixes are correctly in place

- [ ] T001 Verify `session.commit()` + `session.refresh()` exist after `repo.create_course()` in `app/modules/academics/course/service.py:32-33`
- [ ] T002 Verify `notes=data.notes` is passed to `Course()` constructor in `app/modules/academics/course/service.py:27`
- [ ] T003 Verify `session.commit()` + `session.refresh()` exist in `update_course_price()` in `app/modules/academics/course/service.py:43-44`

---

## Phase 2: Test Persistence Verification

**Purpose**: Close the test gap — ensure tests verify data actually persists in the database

- [ ] T004 Update `test_create_course_success` in `tests/test_academics_courses.py` — after POST, add GET to `/api/v1/academics/courses/{id}` and assert name, category, price_per_level, sessions_per_level round-trip correctly
- [ ] T005 [P] Add `test_create_course_with_notes` in `tests/test_academics_courses.py` — POST with explicit `notes` field, then GET and assert notes are returned
- [ ] T006 [P] Add `test_create_course_duplicate_name` in `tests/test_academics_courses.py` — POST same name twice, verify second returns 409 Conflict
- [ ] T007 [P] Add `test_update_course_price_persists` in `tests/test_academics_courses.py` — PATCH price, then GET and verify new price

---

## Phase 3: Cross-Cutting

**Purpose**: Tighten boundary tests and edge cases

- [ ] T008 Tighten `test_create_course_boundary_price` in `tests/test_academics_courses.py` — zero price should assert 422, not ambiguous 201/422
- [ ] T009 Run full test suite: `pytest tests/test_academics_courses.py -v` and verify all pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: Can start immediately — pure code review, no changes
- **Phase 2**: Code fixes from Phase 1 must be confirmed — tests depend on fixes being in place
- **Phase 3**: Fixes and core tests must be in place before tightening boundaries

### Within Each Phase

- Tasks marked [P] can run in parallel (different test methods in same file)
- Non-[P] tasks are sequential

### Parallel Opportunities

- All Phase 1 tasks marked [P] (they are independent reads)
- T005, T006, T007 can all run in parallel (add different test methods to the same file)

---

## Parallel Example: Phase 2

```bash
# All three new tests can be added in parallel:
Task: "Add test_create_course_with_notes to tests/test_academics_courses.py"
Task: "Add test_create_course_duplicate_name to tests/test_academics_courses.py"
Task: "Add test_update_course_price_persists to tests/test_academics_courses.py"
```

---

## Implementation Strategy

### MVP Scope (Single Delivery)

1. Complete Phase 1 — verify fixes are correct
2. Complete Phase 2 — add persistence tests
3. Run full test suite — confirm all pass
4. Complete Phase 3 — tighten boundary tests

---

## Notes

- [P] tasks = different files, no dependencies
- All tasks affect a single file: `tests/test_academics_courses.py` (except Phase 1 which reviews `service.py`)
- Each test is independently runnable via `pytest tests/test_academics_courses.py::TestName::test_method -v`
- Commit after each phase
