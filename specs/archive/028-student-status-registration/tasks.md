---

description: "Bug investigation tasks for student status registration"
---

# Tasks: Student Status Registration Bug Investigation

**Input**: Design documents from `specs/028-student-status-registration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests ARE included because the spec explicitly requires them (FR-011: targeted pytest reproduction).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend monorepo**: `app/`, `tests/` at repository root
- Paths reflect the actual project structure

---

## Phase 1: Setup (Code Reading & Understanding)

**Purpose**: Gain full context of the existing codebase before making changes

- [X] T001 Read `app/modules/crm/models/student_models.py` — understand `StudentStatus` enum and `Student.status` field default
- [X] T002 Read `app/modules/crm/schemas/student_schemas.py` — understand `RegisterStudentDTO.status` type and `RegisterStudentCommandDTO` structure
- [X] T003 Read `app/modules/crm/services/student_crud_service.py` — understand `register_student()` status defaulting logic
- [X] T004 Read `app/api/routers/crm/students_router.py` — understand POST /crm/students endpoint wrapper
- [X] T005 Read `tests/test_crm.py` — understand existing test patterns (`TestStudentsCreate` class)

---

## Phase 2: Foundational (Reproduce the Bug)

**Purpose**: Write and run a targeted pytest that demonstrates the failing behavior. This confirms the bug exists and provides a baseline to verify the fix.

**⚠️ CRITICAL**: The bug must be reproducible before any fix is attempted.

### Reproduction Tests

- [X] T006 [P] Write reproduction test `test_create_student_with_waiting_status_lowercase` in `tests/test_crm.py` — POST with `status="waiting"` (lowercase), assert 201
- [X] T007 [P] Write reproduction test `test_create_student_with_capitalized_status` (renamed to `test_create_student_with_waiting_status_capitalized`) in `tests/test_crm.py` — POST with `status="Waiting"` (capitalized), assert it fails with 422 (before fix) or 201 (after fix)
- [X] T008 Run the reproduction tests — confirmed: lowercase `"waiting"` → 201 ✅, capitalized `"Waiting"` → 422 🐛

**Checkpoint**: Bug reproduced — the exact error response is documented.

---

## Phase 3: User Story 1 — Register Student With Waiting Status (Priority: P1) 🎯 MVP

**Goal**: Ensure that registering a new student with status `"waiting"` succeeds without error, including when the status is sent with different casing.

**Independent Test**: Register a new student with `status="waiting"` (and `status="Waiting"`) via pytest; assert 201 and `data.status == "waiting"`.

### Tests for User Story 1

- [X] T009 [P] [US1] Write test `test_create_student_with_waiting_status_lowercase` in `tests/test_crm.py` — POST with `status="waiting"`, assert 201, assert response `status == "waiting"`
- [X] T010 [P] [US1] Write test `test_create_student_with_waiting_status_capitalized` in `tests/test_crm.py` — POST with `status="Waiting"`, assert 201, assert response `status == "waiting"`
- [X] T011 [P] [US1] Write test `test_create_student_with_waiting_status_uppercase` in `tests/test_crm.py` — POST with `status="WAITING"`, assert 201, assert response `status == "waiting"`

### Implementation for User Story 1

- [X] T012 [US1] Add `@field_validator("status", mode="before")` on `RegisterStudentDTO` in `app/modules/crm/schemas/student_schemas.py` that lowercases the string value before enum validation
- [X] T013 [US1] Run the reproduction tests again — all pass with 201 for all casing variants
- [X] T014 [US1] Run existing `test_create_student_success` and `test_create_student_validation_error` — no regression

**Checkpoint**: At this point, User Story 1 is fully functional — a student can be registered with `waiting` status regardless of casing.

---

## Phase 4: User Story 2 — Default New Students to Waiting (Priority: P1)

**Goal**: Verify that omitting the status field defaults the student to `"waiting"` (this should already work — verify).

**Independent Test**: Register a student without providing a status; assert 201 and `data.status == "waiting"`.

### Tests for User Story 2

- [X] T015 [P] [US2] Write test `test_create_student_defaults_to_waiting` in `tests/test_crm.py` — POST without `status` field (or `status=null`), assert 201, assert response `status == "waiting"`
- [X] T016 [P] [US2] Write test `test_create_student_explicit_null_status` in `tests/test_crm.py` — POST with `status=null`, assert 201, assert response `status == "waiting"`

### Implementation for User Story 2

- [X] T017 [US2] Verify that `RegisterStudentDTO.status` defaults to `None` and the service defaults to `StudentStatus.WAITING` — confirmed via test pass
- [X] T018 [US2] Run all US2 tests — assert pass

**Checkpoint**: Default behavior confirmed working.

---

## Phase 5: User Story 3 — Register With Any Allowed Status (Priority: P2)

**Goal**: Ensure all three status values (`active`, `waiting`, `inactive`) are accepted as initial registration statuses.

**Independent Test**: Register students with `status="active"` and `status="inactive"`; assert both succeed with correct status preserved.

### Tests for User Story 3

- [X] T019 [P] [US3] Write test `test_create_student_with_active_status` in `tests/test_crm.py` — POST with `status="active"`, assert 201, assert response `status == "active"`
- [X] T020 [P] [US3] Write test `test_create_student_with_inactive_status` in `tests/test_crm.py` — POST with `status="inactive"`, assert 201, assert response `status == "inactive"`

### Implementation for User Story 3

- [X] T021 [US3] Verify no code change needed — the `StudentStatus` enum already includes all three values and the validator normalizes casing — confirmed via test pass
- [X] T022 [US3] Run all US3 tests — assert pass

**Checkpoint**: All three statuses accepted for registration.

---

## Phase 6: User Story 4 — Clear Errors for Invalid Status Values (Priority: P3)

**Goal**: Ensure registering with an invalid status returns a clear 422 validation error (not a misleading "not found").

**Independent Test**: Register a student with `status="invalid_value"`; assert 422 with descriptive error message.

### Tests for User Story 4

- [X] T023 [P] [US4] Write test `test_create_student_invalid_status_returns_422` in `tests/test_crm.py` — POST with `status="invalid"`, assert 422, assert error message mentions allowed values
- [X] T024 [P] [US4] Write test `test_create_student_empty_status_returns_422` in `tests/test_crm.py` — POST with `status=""`, assert 422

### Implementation for User Story 4

- [X] T025 [US4] Verify no code change needed — Pydantic's built-in enum validation already produces descriptive 422 errors via the `pydantic_validation_handler` — confirmed via test pass
- [X] T026 [US4] Run all US4 tests — assert pass

**Checkpoint**: Invalid statuses produce clear validation errors.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and documentation

- [X] T027 [P] Run the full CRM test suite: `pytest tests/test_crm.py -v` — 26 passed, no regressions
- [X] T028 [P] Run the full test suite: `pytest tests/ -v` — skipped per user request (CRM suite confirmed all 26 pass)
- [X] T029 Update `quickstart.md` with final pass/fail status of each test scenario
- [X] T030 Update `research.md` with the final root cause confirmation and fix summary
- [X] T031 Document any frontend-facing observations in the spec's clarifications section

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — pure reading
- **Phase 2 (Foundational)**: Depends on Phase 1 — must understand code before reproducing bug
- **Phase 3 (US1)**: Depends on Phase 2 — fix verified against reproduction tests
- **Phase 4 (US2)**: Can run in parallel with Phase 3 — different test file, no code change needed
- **Phase 5 (US3)**: Depends on Phase 3 fix — but tests can be written in parallel
- **Phase 6 (US4)**: Depends on Phase 3 fix — but tests can be written in parallel
- **Phase 7 (Polish)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: Core fix — `@field_validator` on `RegisterStudentDTO`
- **US2 (P1)**: Default behavior — no code change needed, pure verification
- **US3 (P2)**: Depends on US1 fix — tests verify all three statuses
- **US4 (P3)**: Depends on US1 fix — tests verify error messages

### Within Each Phase

- Tests can be written in parallel within a phase (marked [P])
- Tests MUST be written and FAIL before implementation fix is applied
- Run all tests after fix to confirm pass

### Parallel Opportunities

- T006 & T007 (reproduction tests) can be written in parallel
- T009–T011 (US1 tests) can be written in parallel
- T015–T016 (US2 tests) can be written in parallel with US1 implementation
- T019–T020 (US3 tests) can be written in parallel with US1 implementation
- T023–T024 (US4 tests) can be written in parallel with US1 implementation
- T027 & T028 (full suite runs) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Write all tests for US1 in parallel:
Task: "Write test_create_student_with_waiting_status_lowercase in tests/test_crm.py"
Task: "Write test_create_student_with_waiting_status_capitalized in tests/test_crm.py"
Task: "Write test_create_student_with_waiting_status_uppercase in tests/test_crm.py"

# After tests are written and failing, implement the fix:
Task: "Add @field_validator to RegisterStudentDTO in app/modules/crm/schemas/student_schemas.py"

# Then verify all pass:
Task: "Run pytest tests/test_crm.py::TestStudentsCreate -v"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (code reading)
2. Complete Phase 2: Foundational (reproduce bug)
3. Complete Phase 3: US1 (fix + test)
4. **STOP and VALIDATE**: Run US1 tests, confirm bug fixed
5. Deploy/demo if ready — the core bug is resolved

### Incremental Delivery

1. Complete Setup + Foundational → Bug documented
2. Add US1 (fix) → MVP! Bug fixed
3. Add US2 → Default behavior verified
4. Add US3 → All statuses confirmed working
5. Add US4 → Error handling confirmed clear
6. Run full suite → No regressions

---

## Notes

- The actual code change is **exactly one method** — a `@field_validator` on `RegisterStudentDTO.status`
- The majority of tasks are tests and verification
- The `normalize_status` validator uses `mode="before"` so it runs before Pydantic's type/field validation
- The fix does not affect `UpdateStudentDTO` or `UpdateStudentStatusDTO` — those are out of scope for this investigation
- All existing tests must continue to pass
