# Tasks: Single-Step Student Creation

**Input**: Design documents from `/specs/025-description-single-step/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are not requested as this is a production database.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema, triggers, and function updates

- [ ] T001 Update `update_waiting_since()` function to handle INSERT trigger in `db/schema/40_functions.sql`
- [ ] T002 Update `trg_update_waiting_since` trigger definition in `db/schema/50_triggers.sql`
- [ ] T003 [P] Create migration script `db/migrations/077_update_waiting_since_trigger.sql` with function and trigger updates

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repository interface methods, schema updates, and cleanups

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Add `get_by_name_and_dob` query interface to `app/modules/crm/interfaces/__init__.py`
- [ ] T005 [P] Implement `get_by_name_and_dob` in `app/modules/crm/repositories/student_repository.py`
- [ ] T006 Remove deprecated `log_status_change` repository method from `app/modules/crm/repositories/student_repository.py`
- [ ] T007 Modify `RegisterStudentDTO` to support optional status field in `app/modules/crm/schemas/student_schemas.py`
- [ ] T008 [P] Add `status` field to frontend input type `CreateStudentDTO` in `src/api/crm/students/types/inputs.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Create Student with Waiting Status (Priority: P1) 🎯 MVP

**Goal**: Support direct registration of a student with "Waiting" status in a single transaction, including duplicate check, wait timestamp, and activity logging.

**Independent Test**: Register a student with status set to "Waiting" in a single action, and verify they appear immediately on the waiting list directory with the current date/time registered as their wait time. Verify duplicate checks.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Support setting `waiting` status, duplicate checking, and activity logging inside `register_student()` service layer in `app/modules/crm/services/student_crud_service.py`
- [ ] T010 [P] [US1] Pass `status` in `createStudentMutation` payload and remove secondary patching block in `src/components/directory/hooks/useStudentActions.ts`
- [ ] T011 [US1] Pass `status` in `createStudentMutation` payload and remove secondary patching block in `src/components/dashboard/QuickActionsGrid.tsx`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Create Student with Active Status (Priority: P2)

**Goal**: Support direct registration of a student with "Active" status in a single transaction.

**Independent Test**: Register a new student with status set to "Active", and verify they appear in the active student directory without any waiting list entry.

### Implementation for User Story 2

- [ ] T012 [P] [US2] Support active status (ensure no waiting timestamps are recorded) in `app/modules/crm/services/student_crud_service.py`
- [ ] T013 [US2] Implement active status selector handling in student creation modal in `src/components/directory/hooks/useStudentActions.ts`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Create Student with Inactive Status (Priority: P3)

**Goal**: Support direct registration of a student with "Inactive" status in a single transaction.

**Independent Test**: Register a new student with status set to "Inactive" and verify they are created with "Inactive" status.

### Implementation for User Story 3

- [ ] T014 [P] [US3] Support inactive status in `app/modules/crm/services/student_crud_service.py`
- [ ] T015 [US3] Implement inactive status selector handling in student creation modal in `src/components/directory/hooks/useStudentActions.ts`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Build checks and final documentation

- [ ] T016 Run typescript compilation check using `npm run build` in the UI project directory `e:\Users\ibrahim\Desktop\techno_terminal_UI`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (P1) is our MVP.
  - User Story 2 (P2) can be worked in parallel or sequentially after US1.
  - User Story 3 (P3) can be worked in parallel or sequentially after US2.
- **Polish (Phase 6)**: Depends on all user stories being complete.

### Parallel Opportunities

- T003 can run in parallel with T001 and T002.
- T005, T008 can run in parallel with foundational schema/interface updates.
- Once Foundational completes, US1 front/backend tasks (T009, T010, T011) can run in parallel.
- US2 and US3 implementation tasks can run in parallel once US1 core is implemented.
