# Tasks: Return Employee National ID

**Input**: Design documents from `specs/008-return-employee-national-id/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: Test tasks are verification steps. Run after implementation.

## Format: `[ID] [P] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1)
- Include exact file paths in descriptions

## Path Conventions

All paths relative to repository root: `E:\Users\Ibrahim\Desktop\techno_data_ Copy\`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No project initialization needed — all infrastructure exists. Tasks are understanding and verification.

- [X] T001 Read the current `EmployeePublic` class in `app/api/schemas/hr/employee.py` to confirm `national_id` is missing
- [X] T002 Read `EmployeeReadDTO` in `app/modules/hr/schemas/employee_schemas.py` to confirm `national_id: str` exists in the internal DTO

---

## Phase 2: User Story 1 — View Employee National ID (Priority: P1)

**Goal**: Admin sees `national_id` in the employee detail response.

**Independent Test**: `GET /api/v1/hr/employees/{id}` returns `national_id` as a string in the response body.

### Implementation for User Story 1

- [X] T003 [US1] Add `national_id: str` field to `EmployeePublic` in `app/api/schemas/hr/employee.py`

### Verification for User Story 1

- [X] T004 [US1] Run tests: `pytest tests/test_hr.py::TestEmployeesRead -v` — confirm `test_get_employee_success` still passes

**Checkpoint**: Employee detail endpoint now returns `national_id`. User Story 1 deliverable complete.

---

## Phase 3: Polish & Cross-Cutting Concerns

- [X] T005 Add assertion in `tests/test_hr.py::test_get_employee_success` to verify `national_id` is present in response
- [X] T006 Run full HR test suite: `pytest tests/test_hr.py::TestEmployeesRead -v` — confirm no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — understanding only
- **US1 (Phase 2)**: Depends on Setup
- **Polish (Phase 3)**: Depends on US1 completion

### Within Each User Story

- Read current code before modifying
- Implement field addition
- Verify

### Parallel Opportunities

- T001, T002 (Setup reading) can run in parallel
- T005, T006 (Polish) — T005 before T006

---

## Parallel Example

```bash
# Read both source files:
Task: "Read EmployeePublic in app/api/schemas/hr/employee.py"
Task: "Read EmployeeReadDTO in app/modules/hr/schemas/employee_schemas.py"
```

---

## Implementation Strategy

### MVP

1. Complete Phase 1: Setup (read current code)
2. Complete Phase 2: User Story 1 (add `national_id` field)
3. **STOP and VALIDATE**: `pytest tests/test_hr.py::TestEmployeesRead -v`

### Full Delivery

1. Phase 1: Setup → read current schemas
2. Phase 2: Add `national_id` to `EmployeePublic`
3. Phase 3: Add test assertion, run full suite

### Notes

- Schema-only change — no migrations, no DB changes, no new services or repositories
- Field type `str` matches `EmployeeReadDTO.national_id: str`
- `model_config = {"from_attributes": True}` already exists — `model_validate` will pick up the new field automatically
