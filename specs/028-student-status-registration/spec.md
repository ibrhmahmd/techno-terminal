# Feature Specification: Student Status Registration

**Feature Branch**: `028-student-status-registration`  
**Created**: 2026-06-10  
**Status**: Draft  
**Input**: User description: "there is a bug i want to investigate if it is found or nor when creating a new student the status of the student when i select a waiting status the front end displays a not found message and only accepts a active status when registring a student it should defalut to waiting or how the user wants a status to be lets investigate this"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register a Student With Waiting Status (Priority: P1)

As an administrator or staff member registering a new student, I want to choose `waiting` as the student's initial status so that students who are not yet active can be recorded without errors.

**Why this priority**: The reported bug blocks normal registration workflows when a student should begin in a waiting state. This is the primary failing behavior to investigate and correct.

**Independent Test**: Can be fully tested by registering a new student with status `waiting` and confirming the student is created successfully and displayed with that status.

**Acceptance Scenarios**:

1. **Given** a staff user is registering a new student, **When** they select `waiting` as the status and submit valid student details, **Then** the student is created successfully and shown with status `waiting`.
2. **Given** a staff user submits a new student with status `waiting`, **When** registration completes, **Then** the user does not see a misleading `not found` message.

---

### User Story 2 - Default New Students to Waiting Status (Priority: P1)

As a staff user registering a student, I want the system to default the student status to `waiting` when no explicit status is chosen so that new registrations follow the expected enrollment process.

**Why this priority**: The user stated that registering a student should default to waiting. A safe default reduces errors and matches expected business workflow.

**Independent Test**: Can be fully tested by registering a valid student without manually changing the status and confirming the created student has status `waiting`.

**Acceptance Scenarios**:

1. **Given** a staff user opens the student registration form, **When** no status has been explicitly selected, **Then** the default status is `waiting`.
2. **Given** a staff user submits valid student details without changing the default status, **When** registration completes, **Then** the created student is saved and displayed with status `waiting`.

---

### User Story 3 - Register a Student With Any Allowed Status (Priority: P2)

As a staff user registering a student, I want to choose any allowed initial student status so that the student record accurately reflects their current enrollment state.

**Why this priority**: The current behavior reportedly only accepts `active`; the corrected behavior must support all allowed registration statuses, not just the default.

**Independent Test**: Can be tested by registering students with each allowed status and confirming each selected status is preserved.

**Acceptance Scenarios**:

1. **Given** a staff user selects `active` as the student status, **When** they submit valid student details, **Then** the student is created successfully with status `active`.
2. **Given** a staff user selects any allowed student status, **When** they submit valid student details, **Then** the selected status is accepted and preserved.

---

### User Story 4 - Show Clear Errors for Invalid Status Values (Priority: P3)

As a staff user, I want clear feedback if a selected status is not allowed so that I can correct the registration without confusion.

**Why this priority**: The reported `not found` message is misleading. Even if invalid data is submitted, the user should receive a clear validation message.

**Independent Test**: Can be tested by attempting registration with an invalid status and verifying the user receives a clear status validation error and no student is created.

**Acceptance Scenarios**:

1. **Given** a registration includes an unsupported status, **When** the staff user submits the form, **Then** the system rejects the submission with a clear message that the status is invalid.
2. **Given** an invalid status submission is rejected, **When** the user corrects the status to an allowed value, **Then** registration can complete successfully.

---

### Edge Cases

- What happens when the registration form omits the status field entirely? The student should default to `waiting`.
- What happens when the status value differs only by casing or whitespace? The system MUST normalize the status to lowercase before validation (via `@field_validator` on `RegisterStudentDTO.status`).
- What happens when all other student details are valid but status is invalid? No student should be created and the error should identify the status issue.
- What happens when registration succeeds but the student list or details view refreshes immediately afterward? The newly created student should be visible with the correct status.
- What happens if `waiting` students are filtered separately from `active` students? The student should appear wherever waiting students are expected to appear and must not be treated as missing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow new student registration with status `waiting`.
- **FR-002**: The system MUST default a newly registered student's status to `waiting` when no explicit status is provided.
- **FR-003**: Users MUST be able to select any of the three allowed initial statuses (`active`, `waiting`, `inactive`) during registration.
- **FR-004**: The system MUST preserve the user-selected status on the created student record.
- **FR-005**: The system MUST NOT show a `not found` message when a valid student registration uses status `waiting`.
- **FR-006**: The system MUST show a clear validation message when registration uses an unsupported status value.
- **FR-010**: The system MUST normalize status casing to lowercase before validation on `RegisterStudentDTO.status` to handle case variation from the frontend.
- **FR-007**: The system MUST ensure successfully registered students are visible after creation, including students created with `waiting` status.
- **FR-008**: The investigation MUST identify whether the failure originates from registration, status validation, post-registration lookup, list filtering, or user-facing error handling. The failure appears on the registration form after submit, indicating the POST /crm/students endpoint returns an error when status="waiting".
- **FR-009**: The investigation MUST document the observed behavior, expected behavior, reproduction steps, and affected statuses before implementation begins.
- **FR-011**: The investigation MUST include a targeted pytest that sends POST /crm/students with status="waiting" and captures the raw response to identify the error source.

### Key Entities *(include if feature involves data)*

- **Student**: A learner being registered in the center. Relevant attributes include identity details, contact/guardian information, and enrollment status.
- **Student Status**: The student's current registration/enrollment state. All three statuses defined in `StudentStatus` enum are valid initial registration values: `active`, `waiting`, and `inactive`.
- **Registration Attempt**: A staff action to create a new student record with supplied student details and an intended initial status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of valid student registrations with status `waiting` complete successfully during acceptance testing.
- **SC-002**: 100% of valid student registrations without an explicit status create students with status `waiting`.
- **SC-003**: Staff users can register a student with an allowed status in under 2 minutes without encountering a misleading error.
- **SC-004**: 0 tested valid `waiting` registrations display a `not found` message.
- **SC-005**: All invalid status submissions tested return a clear status-related validation message and do not create a student record.
- **SC-006**: The investigation produces a reproducible finding that identifies whether the bug is present and where the failing behavior occurs.

## Clarifications

### Session 2026-06-10

- Q: Which scope does this investigation cover? → A: Backend investigation + flag frontend findings. The backend code (StudentStatus enum, service layer, API endpoints) is the primary scope. Any frontend-related issues discovered during investigation will be documented and flagged but not fixed here.
- Q: Should `inactive` be an allowed initial status during registration? → A: Yes — all three statuses (active, waiting, inactive) are valid initial registration statuses.
- Q: Where does the "not found" message appear in the UI flow? → A: On the registration form itself after submitting — the POST request to create a student with status "waiting" returns an error response.
- Q: How should the system handle status casing? → A: Normalize to lowercase — add a `@field_validator` on `RegisterStudentDTO.status` to lowercase the value before enum validation.
- Q: What reproduction approach should the investigation take? → A: Write a direct pytest that POSTs to `/crm/students` with status="waiting", captures the exact response (status code + body), and compares with status="active".

### Frontend-Facing Observations (from backend investigation)

1. **Root cause confirmed**: The backend was rejecting `status="Waiting"` (capitalized) with a 422 ValidationError because Pydantic enum validation is case-sensitive. The frontend appears to display this 422 as a "not found" message — likely due to generic error handling.
2. **Fix applied**: `@field_validator("status", mode="before")` on `RegisterStudentDTO` now lowercases the status before enum validation. The backend now accepts `"waiting"`, `"Waiting"`, `"WAITING"` — all normalize to `"waiting"`.
3. **Frontend recommendation**: The frontend may want to review its error handling for 422 responses — displaying "not found" for a validation error is misleading. The frontend could either:
   - Send status in lowercase (the most robust approach)
   - Or improve error message display to show the actual server validation error

## Assumptions

- Staff users who register students are already authorized to create student records.
- `waiting` is an allowed student status for newly registered students.
- `active` and `inactive` remain allowed statuses, but none should be the only accepted registration status.
- All three `StudentStatus` enum values (`active`, `waiting`, `inactive`) are valid for initial registration.
- The reported `not found` message appears on the registration form after submission, indicating the POST /crm/students endpoint returns an error when status="waiting". The investigation will use a targeted pytest to capture the exact response.
- **Scope boundary**: This investigation covers the backend API and services. Frontend issues (e.g., display mapping, form validation) are out of scope for fixes but any frontend-observable findings will be noted for the separate frontend repo.
