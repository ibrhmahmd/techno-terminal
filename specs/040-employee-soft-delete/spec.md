# Feature Specification: Employee Soft Delete with Restore & Re-hire

**Feature Branch**: `040-employee-soft-delete`
**Created**: 2026-08-24
**Status**: Draft
**Input**: User request: "we must plan for a delete feature" (for employees). Design decisions locked via interactive clarification on 2026-08-24.

## Clarifications

### Session 2026-08-24

- Q: What delete semantics apply? → A: Soft delete — `deleted_at`/`deleted_by` markers, mirroring the existing student pattern; rows are never physically removed.
- Q: What happens to the employee's linked login account on delete? → A: It is blocked automatically in the same transaction and the employee disappears from the staff accounts overview.
- Q: Can a deleted employee's national ID / phone / email be reused (re-hire)? → A: Yes — uniqueness is enforced only among non-deleted records, via partial unique indexes.
- Q: Is an undo/restore path included? → A: Yes — a restore endpoint clears the deletion markers; it does NOT reactivate a blocked login account (admins reactivate explicitly via update).
- Q: When restoring would collide with a live employee's identity fields (possible after a re-hire), what happens? → A: Restore is rejected — the live set must never contain duplicates; every colliding field is named in the rejection. Re-hire itself remains allowed.
- Q: How do admins discover which employees are deleted so they can restore them? → A: The existing staff list gains an admin-only `include_deleted=true` query flag returning deleted rows with `deleted_at`/`deleted_by` populated.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Safe Removal from All Surfaces (Priority: P1)

An administrator removes a staff member who has left the center (e.g., an instructor who resigned mid-term). The employee disappears from every read surface — detail lookups, staff lists, and the staff accounts overview — their login account can no longer authenticate, and every historical reference (assigned tasks, past instructor assignments, time logs) remains intact. Nothing is ever physically destroyed.

**Why this priority**: Removal is the core capability being requested; without it there is no feature. Blocking the login in the same breath closes a real security gap (a departed staffer retaining access).

**Independent Test**: Can be fully tested by creating an employee with a linked account, deleting them, then verifying absence across all read endpoints, failed authentication, and intact referencing history.

**Acceptance Scenarios**:

1. **Given** an authenticated admin, **When** they delete an existing employee, **Then** the response confirms success and subsequent lookups of that employee return "not found".
2. **Given** a deleted employee who held an active login account, **When** anyone attempts to sign in with that account, **Then** authentication is refused.
3. **Given** the staff accounts overview, **When** an admin reviews it after deleting a provisioned employee, **Then** that account no longer appears.
4. **Given** historical data referencing the deleted employee (task assignments, instructor/coach references), **When** any of those records is viewed, **Then** the history remains present and unaltered.

---

### User Story 2 - Re-hire Without Data Conflicts (Priority: P2)

The same person returns to work at the center months after being removed. The administrator re-creates their record using the same national ID, phone number, and email that the deleted record still holds — and creation succeeds without any manual database intervention, because deleted records no longer occupy those unique identifiers.

**Why this priority**: Re-hiring is a routine real-world flow; if deleted records kept blocking identity fields, admins would need DBA help for one of the most common outcomes of deletion.

**Independent Test**: Can be tested by deleting an employee and immediately creating a new one with identical national ID, phone, and email, verifying acceptance; then verifying a duplicate against a NON-deleted employee is still rejected.

---

### User Story 3 - Recoverable Mistakes via Restore (Priority: P3)

An administrator deletes the wrong person in error. They restore the employee from the same interface: the record becomes visible again everywhere, exactly as before deletion. Restoring someone who was never deleted, or restoring an unknown ID, produces clear specific errors instead of silent state changes.

**Why this priority**: Deletion is irreversible-feeling to users; recovery protects against operational mistakes. It depends on Story 1's delete existing first, hence P3.

**Independent Test**: Can be tested by deleting an employee, restoring them, and verifying full visibility returns; plus attempting restores of live and unknown employees to confirm precise rejections.

**Acceptance Scenarios**:

1. **Given** a recently deleted employee, **When** an admin restores them, **Then** the employee appears again in detail views and lists with their prior data intact.
2. **Given** an employee who is not deleted, **When** a restore is attempted, **Then** the system rejects the request naming the conflict rather than succeeding silently.
3. **Given** an unknown or already-deleted employee ID targeted by delete, **When** any delete attempt repeats, **Then** the outcome is a uniform not-found rejection, never a double-delete side effect.
4. **Given** a restored employee whose login was auto-blocked at delete time, **When** the admin wants them signing in again, **Then** reactivation happens only through the explicit update endpoint — restore alone never silently re-enables access.
5. **Given** a re-hire occurred after Employee A was deleted (a live employee now holds A's identity fields), **When** an admin attempts to restore A, **Then** the restore is rejected naming every colliding field, and no duplicate live record ever exists.
6. **Given** one or more deleted employees, **When** an admin lists staff with `include_deleted=true`, **Then** deleted rows appear with their deletion timestamp and actor; the default listing (no flag) still hides them.

---

### Edge Cases

- What happens when two admins delete the same employee simultaneously? (Second must observe the uniform not-found/conflict outcome, never partial state.)
- What happens when an admin deletes an employee who never had a login account? (Delete succeeds; no account step occurs.)
- What happens when a deleted employee's identity details match a NEW active employee? (Duplicate probes must ignore the deleted row and allow the new one.)
- When identity fields collide on restore after a re-hire, the restore is rejected naming every colliding field; no duplicate live records may ever exist (resolved: see FR-010).
- What happens when the actor performing the delete cannot be resolved to a local user? (Deletion must fail closed with a typed auth error, never record `deleted_by` as unknown.)
- How do reports or listings behave for attendance/time-log rows belonging to deleted employees? (Rows persist untouched by soft delete.)

## Requirements *(mandatory)*

### Functional Requirements

**Deletion behavior**

- **FR-001**: System MUST expose `DELETE /api/v1/hr/employees/{id}` that soft-deletes the employee: sets `deleted_at` to the operation timestamp and `deleted_by` to the acting local user's ID, inside a single transaction. No row is ever physically removed.
- **FR-002**: Deleted employees MUST be excluded from every default read surface: single lookup (returns 404), paginated lists, active lists, and the staff accounts overview JOIN — with the sole exception of the explicit deleted-records view defined in FR-014.
- **FR-003**: When the deleted employee holds a linked login account, the system MUST block that account (`is_active = false`) within the SAME transaction as the delete — a deleted employee must never retain sign-in access.
- **FR-004**: Deleting a non-existent OR already-deleted employee MUST return the standard not-found envelope uniformly (no double-delete side effects).
- **FR-005**: The system MUST preserve all historical references to the deleted employee — task assignments, instructor/coach/group references, time logs, and attendance rows remain byte-identical after deletion.

**Re-hire support**

- **FR-006**: Uniqueness of email, national ID, and phone MUST be enforced only among non-deleted employees, implemented via partial unique indexes (`WHERE deleted_at IS NULL`) so deleted records never block re-creation of a person with the same identifiers.
- **FR-007**: Duplicate-check probes used by create/update flows MUST ignore deleted employees entirely.
- **FR-008**: `user_id` uniqueness between employees and login accounts MUST remain absolute (one account links to at most one employee, deleted or not).

**Restore**

- **FR-009**: System MUST expose `POST /api/v1/hr/employees/{id}/restore` that clears both deletion markers, making the employee visible again across all surfaces.
- **FR-010**: Restoring MUST be rejected with an explicit, field-named conflict when: (a) the employee is not deleted, (b) the restore would place the record's email, national ID, or phone into collision with ANY live employee — every colliding field is reported together; restoring an unknown ID MUST return the not-found envelope. The live employee set must never contain duplicate identity fields.
- **FR-011**: Restore MUST NOT automatically reactivate a login account blocked at delete time; reactivation remains an explicit admin action via the existing update flow.

**Cross-cutting**

- **FR-012**: Both new endpoints MUST require admin authentication and use only typed domain exceptions mapped through the global handlers — no router-level try/except translation.
- **FR-013**: Every behavior above MUST have an automated regression check in the HR test suite.
- **FR-014**: The existing staff list endpoint MUST accept an admin-only `include_deleted=true` query flag that returns deleted employees alongside live ones, each deleted row carrying its `deleted_at` and `deleted_by`; without the flag, behavior is unchanged (live rows only). Non-admin callers MUST receive the uniform rejection regardless of the flag.

### Key Entities *(include if feature involves data)*

- **Employee**: Gains two nullable columns — `deleted_at` (timestamp) and `deleted_by` (FK to users.id). A row with non-null `deleted_at` is invisible to all reads and exempt from identity uniqueness, but keeps occupying its `user_id` link and full payload for audit/history.
- **Staff Account (User)**: Unchanged structurally; gains a new lifecycle edge — auto-blocked when its employee is deleted. Link fields are intentionally preserved (not nulled) so restore context survives.
- **Migration artifacts**: One numbered migration adding both columns and replacing three plain UNIQUE constraints with same-named partial unique indexes; schema files updated in lockstep so CI applies an identical fresh schema.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a successful delete, the employee is absent from 100% of read surfaces (lookup, lists, overview) immediately — verified per surface.
- **SC-002**: 100% of delete operations on provisioned employees result in the linked account being unable to authenticate afterward.
- **SC-003**: Re-creating an employee with the exact identity triple (national ID + phone + email) of a deleted record succeeds without manual intervention; the same triple against a live record still fails 100% of the time.
- **SC-004**: An accidental delete is fully reversed by the admin alone via restore in under 1 minute, with zero data loss.
- **SC-005**: Re-running the full HR verification suite produces zero failures.

## Assumptions

- Only administrators delete or restore; the permission model does not change.
- Soft delete is permanent storage policy — no purge job or hard-delete path exists anywhere in this feature.
- Restore deliberately does not touch the linked account's activation state beyond what FR-011 states.
- Existing constraint names are preserved during the partial-index migration so the IntegrityError translation layer keeps functioning unchanged.
- HR attendance logging remains out of scope except that its stored rows are preserved by deletion.
