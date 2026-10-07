# Tasks: Extend Employee Schemas

**Input**: Design documents from `specs/005-extend-employee-schemas/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: Test tasks are included as verification steps. Write and run after implementation.

## Format: `[ID] [P] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

All paths relative to repository root: `E:\Users\Ibrahim\Desktop\techno_data_ Copy\`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No project initialization needed — all infrastructure exists. Tasks are understanding and verification.

- [X] T001 Read the current `EmployeePublic` class in `app/api/schemas/hr/employee.py` to understand existing fields and `model_config`
- [X] T002 Read the current `EmployeeListItem` class in `app/api/schemas/hr/employee.py`
- [X] T003 Read `EmployeeReadDTO` in `app/modules/hr/schemas/employee_schemas.py` to confirm all target fields exist in the internal DTO

---

## Phase 2: User Story 1 — View Complete Employee Details (Priority: P1) 🎯 MVP

**Goal**: Admin sees academic (university, major, is_graduate) and financial (monthly_salary, contract_percentage) fields in the employee detail response.

**Independent Test**: `GET /api/v1/hr/employees/{id}` returns `university`, `major`, `is_graduate`, `monthly_salary`, `contract_percentage` in the response body for any employee.

### Implementation for User Story 1

- [X] T004 [US1] Add `university: Optional[str] = None` field to `EmployeePublic` in `app/api/schemas/hr/employee.py`
- [X] T005 [US1] Add `major: Optional[str] = None` field to `EmployeePublic` in `app/api/schemas/hr/employee.py`
- [X] T006 [US1] Add `is_graduate: Optional[bool] = None` field to `EmployeePublic` in `app/api/schemas/hr/employee.py`
- [X] T007 [US1] Add `monthly_salary: Optional[float] = None` field to `EmployeePublic` in `app/api/schemas/hr/employee.py`
- [X] T008 [US1] Add `contract_percentage: Optional[float] = None` field to `EmployeePublic` in `app/api/schemas/hr/employee.py`

### Verification for User Story 1

- [X] T009 [US1] Run tests: `pytest tests/test_hr.py::TestEmployeesRead -v` — 6 passed, including new field assertions
- [ ] T010 [US1] Manual API check: start dev server (`python run_api.py`), call `GET /api/v1/hr/employees/1` with admin auth, verify all 5 new fields present in response

**Checkpoint**: Employee detail endpoint now returns all stored fields. User Story 1 deliverable complete.

---

## Phase 3: User Story 2 — Browse Employees With Contact Info (Priority: P1)

**Goal**: Admin sees phone and email fields in the employee list card responses without opening detail dialog.

**Independent Test**: `GET /api/v1/hr/employees` returns `phone` and `email` in every list item.

### Implementation for User Story 2

- [X] T011 [P] [US2] Add `phone: Optional[str] = None` field to `EmployeeListItem` in `app/api/schemas/hr/employee.py`
- [X] T012 [P] [US2] Add `email: Optional[str] = None` field to `EmployeeListItem` in `app/api/schemas/hr/employee.py`

### Verification for User Story 2

- [X] T013 [US2] Run tests: `pytest tests/test_hr.py::TestEmployeesRead -v` — 6 passed, including phone/email assertions
- [ ] T014 [US2] Manual API check: call `GET /api/v1/hr/employees` with admin auth, verify `phone` and `email` present in every list item

**Checkpoint**: Employee list endpoint now returns contact info on cards. User Story 2 deliverable complete.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [X] T015 [P] Add assertions in `tests/test_hr.py::test_get_employee_success` to verify all 5 new detail fields are present in response
- [X] T016 [P] Add assertions in `tests/test_hr.py::test_list_employees_success` to verify `phone` and `email` are present in each list item
- [X] T017 Run HR read tests: `pytest tests/test_hr.py::TestEmployeesRead -v` — all 6 passed, no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — understanding only
- **US1 (Phase 2)**: Depends on Setup
- **US2 (Phase 3)**: Depends on Setup; independent of US1 (different fields in same file, no logical conflict)
- **Polish (Phase 4)**: Depends on both US1 and US2 completion

### User Story Dependencies

- **US1**: Can start after Setup — no dependencies on US2
- **US2**: Can start after Setup — no dependencies on US1

### Within Each User Story

- Read existing code before modifying
- Add fields in order shown
- Verify after each field addition or batch

### Parallel Opportunities

- T001, T002, T003 (Setup reading) can run in parallel
- T004–T008 (US1 detail fields) are best done sequentially in one file
- T011, T012 (US2 list fields) can run in parallel
- T015, T016 (Polish test assertions) can run in parallel

---

## Parallel Example: User Story 1

```bash
# All 5 detail fields can be added together (same file, sequential edits):
Task: "Add 5 Optional fields to EmployeePublic in app/api/schemas/hr/employee.py"
```

## Parallel Example: User Story 2

```bash
# Both list fields can be added together:
Task: "Add phone and email to EmployeeListItem in app/api/schemas/hr/employee.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (read current code)
2. Complete Phase 2: User Story 1 (5 fields on detail endpoint)
3. **STOP and VALIDATE**: `pytest tests/test_hr.py::TestEmployeesRead -v`
4. Deploy/demo if needed

### Full Delivery

1. Complete Phase 1: Setup
2. Complete Phase 2: User Story 1 (detail fields) → Verify
3. Complete Phase 3: User Story 2 (list fields) → Verify
4. Complete Phase 4: Polish (test assertions) → Full test suite

### Notes

- This is a schema-only change — no migrations, no DB changes, no new services or repositories
- All new fields are `Optional` with `None` default — backward-compatible
- File `app/api/schemas/hr/employee.py` is the only source file to modify
- Test file `tests/test_hr.py` assertions need updating but existing tests won't break
