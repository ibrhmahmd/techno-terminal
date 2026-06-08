# Feature Specification: Single-Step Student Creation

**Feature Branch**: `025-description-single-step`  
**Created**: 2026-06-08  
**Status**: Draft  
**Input**: User description: "plan for the back end to do not assign a default status and it must get the studnet status from the studnet creation endpint in single step"

## Clarifications

### Session 2026-06-08
- Q: What should the default value of `waiting_priority` be upon single-step student creation with status "Waiting"? → A: Leave as `null` (unassigned) by default.
- Q: Should we deprecate the redundant `student_status_history` table/repository methods and unify status tracking solely under the `student_activity_log` table? → A: Yes, unify under `student_activity_log` and deprecate/remove the redundant `student_status_history` table and associated repository methods.
- Q: How should the system handle duplicate student checks? → A: Reject with `409 ConflictError` if a student with the same full name (case-insensitive) and same date_of_birth already exists in the database. If date_of_birth is not provided, skip the duplicate check.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Student with Waiting Status (Priority: P1)

An administrator registers a new student and sets their status to "Waiting" in the creation form. The student is created directly with the "Waiting" status, and the waiting list timestamp is immediately recorded in a single atomic action.

**Why this priority**: High value. Eliminates inconsistent temporary state and extra network roundtrips during new registration.

**Independent Test**: Register a new student with status set to "Waiting" in a single action, and verify they appear immediately on the waiting list directory with the current date/time registered as their wait time.

**Acceptance Scenarios**:

1. **Given** an admin is on the student creation form,  
   **When** they fill in the details, select "Waiting" as the status, and submit,  
   **Then** the student is successfully created and registered with the "Waiting" status.
2. **Given** a student is successfully created with "Waiting" status,  
   **When** viewing the student's details,  
   **Then** the registration date matches the current time and their waiting priority is ready to be set.

---

### User Story 2 - Create Student with Active Status (Priority: P2)

An administrator registers a new student and sets their status to "Active" in the creation form. The student is created directly with the "Active" status, and no waiting list metadata is populated.

**Why this priority**: Medium value. Handles the standard registration flow when students enroll immediately.

**Independent Test**: Register a new student with status set to "Active", and verify they appear in the active student directory without any waiting list entry.

**Acceptance Scenarios**:

1. **Given** an admin is on the student creation form,  
   **When** they fill in details, select "Active" as the status, and submit,  
   **Then** the student is created as "Active" and has no waitlist timestamp.

---

### User Story 3 - Create Student with Inactive Status (Priority: P3)

An administrator registers a new student and sets their status to "Inactive" in the creation form. The student is created directly with the "Inactive" status.

**Why this priority**: Low value. Handles edge cases where a student is registered but not starting immediately.

**Independent Test**: Register a new student with status set to "Inactive" and verify they are created with "Inactive" status.

**Acceptance Scenarios**:

1. **Given** an admin is on the student creation form,  
   **When** they fill in details, select "Inactive" as the status, and submit,  
   **Then** the student is created as "Inactive".

---

### Edge Cases

- **Trigger Behavior on Insertion**: The database auto-timestamp for the waiting list must execute correctly on insertion (first-time save) as well as update.
- **Empty Status Payload**: If status is omitted in the creation payload, the system must assign a consistent default status of "Waiting" to ensure data integrity.
- **Duplicate Student Checks**: If a student is registered with a name and date of birth that matches an existing student record, the operation must fail with a 409 Conflict.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The student creation endpoint MUST accept student status as an explicit field.
- **FR-002**: If no status is specified during student creation, the system MUST default the status to "Waiting".
- **FR-003**: The system MUST record the exact date and time the student entered the "Waiting" status immediately upon creation.
- **FR-004**: The system MUST NOT record any waiting list timestamp if the student is created as "Active" or "Inactive".
- **FR-005**: All student details (name, date of birth, phone, and status) MUST be processed and persisted atomically in a single operation.
- **FR-006**: The `waiting_priority` attribute MUST be set to `null` (unassigned) by default when a student is registered with status 'Waiting'.
- **FR-007**: Redundant status tracking tables and repository methods (specifically the `student_status_history` table and `StudentRepository.log_status_change`) MUST be deprecated and removed. All student status logs MUST be recorded exclusively under `student_activity_log`.
- **FR-008**: The student registration endpoint MUST validate that no student with the same full name (case-insensitive) and date of birth exists before creation. If found, it MUST raise a 409 ConflictError. This check is bypassed if the date of birth is not provided.

### Key Entities

- **Student**: Represents a student registered in the CRM. Attributes include full name, birth date, phone, notes, status, and waiting metadata.
- **Parent**: Represents the parent/primary contact for the student.
- **StudentActivityLog**: Central activity and audit logging table that tracks status transitions, registrations, and other milestones.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Administrators can register students with any status (Active, Waiting, Inactive) in a single submission, eliminating the secondary status update step.
- **SC-002**: 100% of students created with "Waiting" status have their "Waiting Since" timestamp set immediately to the creation timestamp.
- **SC-003**: No "Waiting Since" timestamp is populated for students created as "Active" or "Inactive".
- **SC-004**: All student status changes (including initial setup on creation) are logged to `student_activity_log` with no dependency on the deprecated `student_status_history` table.
- **SC-005**: Duplicate registrations (matching name and date of birth) are successfully blocked with a clear 409 error message.

## Assumptions

- **Existing Status Types**: The existing status types ("active", "waiting", "inactive") are sufficient and do not require modification.
- **Parent Relationship**: Parent mapping/linking is a separate link transaction and may continue to execute after/during creation.
