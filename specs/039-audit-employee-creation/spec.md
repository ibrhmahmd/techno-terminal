# Feature Specification: Employee Creation Endpoint Audit & Fixes

**Feature Branch**: `039-audit-employee-creation`
**Created**: 2026-08-23
**Status**: Draft
**Input**: User description: "review the staff adding feature — i see many bugs in adding new employees, so we need to review the endpoints looking for any potential bugs"

## Clarifications

### Session 2026-08-23

- Q: What details must be unique/validated so two employee records count as duplicates or invalid? → A: Phone number, national ID, and email — each validated; every problem or duplicate reported back to the client.
- Q: What happens to an active login account when its employee is deactivated? → A: The account is blocked automatically along with the employee.
- Q: What credential rules govern account provisioning? → A: Explicit minimums — syntactically valid email and a password of at least 8 characters.
- Q: What severity tiers does the findings catalog use? → A: ERROR (blocks/breaks the flow), WARNING (wrong or misleading behavior), INFO (hygiene/polish).
- Q: What retry experience follows a midway provisioning failure? → A: Clean rollback plus a clear failure message; the admin retries manually.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reliable Employee Creation (Priority: P1)

An administrator adds a new staff member (e.g., a new instructor hired for the term) by submitting their details through the employee creation form. Every submission ends in exactly one of two outcomes: the employee record is fully created and immediately visible in the staff list, or the submission is rejected with a clear, specific explanation of what was wrong. There are no silent partial saves, no unexplained system errors, and no situations where the admin must guess why creation failed.

**Why this priority**: Adding employees is a daily operational task; every failure here blocks staffing of classes and erodes trust in the whole system.

**Independent Test**: Can be fully tested by submitting a series of valid and invalid employee records through the staff creation flow and verifying each outcome matches one of the two allowed results with an accurate message.

**Acceptance Scenarios**:

1. **Given** an authenticated admin, **When** they submit a complete, valid new-employee record, **Then** the employee is created and returned in full detail matching what was submitted, with no fields silently blanked or altered.
2. **Given** an authenticated admin, **When** any step of creating an employee fails partway, **Then** no half-created or orphaned data remains — the system is left exactly as it was before the attempt.
3. **Given** an authenticated admin, **When** creation fails for any reason, **Then** the failure reason is specific enough to fix on the next attempt without trial-and-error.
4. **Given** a non-admin user, **When** they attempt to create, edit, or provision accounts for employees, **Then** the request is denied consistently regardless of which endpoint they target.

---

### User Story 2 - Precise Rejection of Invalid or Conflicting Records (Priority: P2)

An administrator who submits an incomplete, malformed, or conflicting employee record (for example, a duplicate of someone already on staff, or missing required contact details) receives feedback that names each problem field and the reason it was rejected — all problems reported together, not one at a time. The admin can correct everything in a single pass instead of discovering issues one by one.

**Why this priority**: Bad data entering the staff roster corrupts schedules, payroll views, and reports downstream; prevention at entry time is far cheaper than cleanup later.

**Independent Test**: Can be tested by submitting records with known defects (missing required fields, bad formats, duplicates of existing staff, conflicting updates to an existing employee) and verifying every defect in the submission is reported back accurately in one response.

**Acceptance Scenarios**:

1. **Given** an existing employee record, **When** an admin creates or edits another record into direct conflict with it (same identity details), **Then** the conflict is blocked and named explicitly rather than saved as a near-duplicate.
2. **Given** a submission containing several invalid fields at once, **When** the admin submits it, **Then** all invalid fields are identified together in the rejection message.
3. **Given** a valid record, **When** an admin later edits it into an invalid state via the update flow, **Then** the same validation quality applies as during initial creation — editing cannot bypass checks that creating enforces.

---

### User Story 3 - Trustworthy Login-Account Provisioning (Priority: P3)

After adding an employee, an administrator provisions the employee's login account. When provisioning succeeds, the account appears immediately in the staff accounts overview with correct, complete details linked to the right employee. When provisioning fails (e.g., the email is already registered), the admin gets a precise reason, and retrying after fixing it works — leaving no duplicate, orphaned, or half-linked account behind.

**Why this priority**: Staff cannot sign in until accounts exist, so provisioning failures directly block people from working — but this only triggers after an employee record already exists, hence P3.

**Independent Test**: Can be tested by provisioning accounts for newly created employees under success, duplicate-email, weak-credential, and simulated-failure conditions, then verifying listing accuracy and absence of leftover partial state in each case.

**Acceptance Scenarios**:

1. **Given** an employee without a login account, **When** an admin provisions an account with valid unique credentials, **Then** the account is created, linked to that exact employee, and shown correctly in the staff accounts overview.
2. **Given** credentials already used by another account, **When** an admin attempts provisioning, **Then** the attempt is rejected naming the conflict, and no partial account state is left behind.
3. **Given** an employee who already has an active login account, **When** provisioning is attempted again, **Then** the system refuses with a clear "already has an account" outcome instead of creating a second account.
4. **Given** the staff accounts overview, **When** an admin reviews it after any provisioning history, **Then** every listed account shows accurate, complete information for its linked employee — no permanently blank placeholder columns.
5. **Given** an employee with an active login account, **When** an admin deactivates that employee, **Then** the linked account is blocked automatically and can no longer sign in.

---

### User Story 4 - Documented Findings Prevent Recurrence (Priority: P4)

Every defect uncovered by this review is recorded in a findings catalog with severity, evidence, reproduction steps, and resolution status. ERROR-tier defects are fixed and locked in with automated regression checks before this effort closes, so the same class of bug cannot silently return.

**Why this priority**: Without documentation and regression coverage, fixes rot and the review must be repeated; however, it delivers value only after Stories 1–3 identify real issues.

**Independent Test**: Can be tested by reviewing the findings catalog for completeness against the known bug symptoms and confirming each fixed defect has an automated check that fails when the bug is reintroduced.

**Acceptance Scenarios**:

1. **Given** the completed review, **When** the findings catalog is inspected, **Then** every discovered defect lists its severity, affected behavior, reproduction steps, and status (fixed / accepted-risk).
2. **Given** a fixed defect, **When** its automated regression check runs against the fixed system, **Then** it passes; reintroducing the original faulty behavior makes it fail.

---

### Edge Cases

- What happens when two admins create the "same" new employee at the same moment?
- When account provisioning fails midway (e.g., identity service unreachable), the system rolls back cleanly and tells the admin what happened; retrying manually after the cause clears succeeds (resolved: see FR-002).
- What happens when an employee's identity details are edited to match another employee's?
- What happens when submissions include unexpected extra fields, wrong data types, or whitespace-only values?
- When an employee is deactivated or removed while holding an active login account, the system blocks that account automatically (resolved: see FR-011).
- How does the system behave when extremely long values are submitted for name/contact fields?

## Requirements *(mandatory)*

### Functional Requirements

**Creation correctness**

- **FR-001**: System MUST fully persist every accepted employee record so that retrieved details afterward exactly match what was submitted — no silently dropped or blanked fields anywhere in the flow.
- **FR-002**: System MUST leave zero partial state when any step of employee creation or account provisioning fails midway, and MUST report a clear failure message so the admin can retry manually.
- **FR-003**: System MUST reject every unauthenticated, non-admin, or deactivated-user attempt on all staff-management operations uniformly.

**Validation & conflicts**

- **FR-004**: System MUST report ALL validation problems in a single rejected submission at once, each naming the offending field and reason.
- **FR-005**: System MUST enforce uniqueness of national ID, phone number, and email across employee records — each checked independently, with format problems and duplicate collisions reported per field back to the client.
- **FR-006**: System MUST enforce identical validation rules when updating an employee as when creating one.
- **FR-007**: System MUST validate credential inputs before attempting account creation: email must be syntactically valid, and password must be at least 8 characters; violations are rejected with a per-field reason.

**Account provisioning**

- **FR-008**: System MUST refuse to provision a second login account for an employee who already has one, with an explicit outcome message.
- **FR-009**: System MUST surface credential conflicts (already-registered email) as explicit rejections naming the conflict.
- **FR-010**: Staff accounts overview MUST display complete, accurate, up-to-date information for each account — no permanent placeholder blanks where meaningful data exists.
- **FR-011**: System MUST automatically block an employee's login account when that employee is deactivated — a deactivated employee must never retain sign-in access.

**Audit deliverables**

- **FR-012**: The review MUST produce a findings catalog covering every defect found across the staff onboarding endpoints, each with a severity tier (ERROR — blocks/breaks the flow; WARNING — wrong or misleading behavior; INFO — hygiene/polish), evidence, reproduction steps, and resolution status.
- **FR-013**: Every applied fix MUST have an automated check demonstrating the original failure mode now passes.
- **FR-014**: Defects intentionally not fixed MUST be documented with severity and accepted risk rationale rather than silently ignored.

### Key Entities *(include if feature involves data)*

- **Employee**: A staff member record — identity, contact, job title/position, employment status. National ID, phone number, and email act as unique identifiers (phone required; email may be empty but must not collide when present). Owned and edited only by admins. Referenced by enrollments-of-instructors, sessions, and payroll-related views.
- **Staff Account**: A login identity linked to exactly one employee; carries role and activation state. Duplicate links (one employee → many active accounts) must not occur.
- **Finding**: One documented defect from this audit — ERROR / WARNING / INFO severity, affected behavior, reproduction steps, resolution status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An admin completes adding a new employee with valid details in under 1 minute, first try, with no errors.
- **SC-002**: 100% of rejected submissions return a specific, actionable reason per problematic field (zero generic "something went wrong" outcomes on the staff path).
- **SC-003**: Zero staff-onboarding requests terminate in unexplained failures across a full test pass of valid, invalid, boundary, and concurrent scenarios.
- **SC-004**: Attempted duplicate/conflicting employee records are blocked 100% of the time.
- **SC-005**: After provisioning, staff accounts listings reflect the account immediately with 100% field accuracy.
- **SC-006**: 100% of ERROR-tier findings from the catalog are fixed and covered by automated regression checks before closure; remaining findings each carry a documented accepted-risk rationale.
- **SC-007**: Re-running the full staff-path verification suite produces zero failures.

## Assumptions

- Only administrators perform staff management today; this effort changes reliability, not the permission model.
- "Staff adding" means the full onboarding path: creating the employee record, editing it, and provisioning its login account — not just the single create call.
- Findings and fixes ship within this same effort; documenting-only is insufficient given observed breakage.
- Existing employee/account data stays valid after fixes (no destructive resets).
- The external identity provider remains the source of truth for login credentials; this audit covers how the center's system uses it, not the provider itself.
- HR attendance logging (currently a stub) is out of scope except where it misrepresents employee data.
