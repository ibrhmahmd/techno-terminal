# Feature Specification: Competition Module Enhancements

**Feature Branch**: `010-competition-feature-enhancements`
**Created**: 2026-05-16
**Status**: Draft
**Input**: User request to align competition module with clarified business requirements covering group-team relationship, project tracking, enrollment-style fee management, hard delete, and subcategory search.

## Clarifications

### Session 2026-05-16

- Q: What user roles can perform write operations on competitions/teams? → A: All write operations (create, edit, delete, payments, placements) require admin role. Coaches (employees linked as team coach) can view their own teams' data read-only but cannot modify.
- Q: What is explicitly out of scope? → A: Certificate generation, bulk operations (CSV import/export), public student-facing portal, and competition event email notifications are all out of scope for this iteration.
- Q: How should payment failures be handled when finance module is involved? → A: Atomic rollback — if receipt creation or fee status update fails, the entire operation reverts with no change and no orphan data.
- Q: Is competition reporting/export needed? → A: No — existing list/filter endpoints are sufficient. CSV export and dashboard summaries are not needed.
- Q: Should team lifecycle be modeled as a formal state machine? → A: No — derive state from existing data fields (amount_due vs amount_paid for payment status, placement_rank for results). No explicit status field needed.

### Session 2026-05-17

- Q: Who is authorized to process competition fee refunds? → A: Admin only — same authorization as payments (consistent with FR-004a)
- Q: What happens when a student is already in a team for the same competition and admin tries to add them to another? → A: Warn but allow — show warning in response envelope's `message` field (Option A: no two-step flow, single request with warning)
- Q: What happens when admin selects a group with zero active students for team pre-fill? → A: Show warning "Group has no active students" and allow manual student entry
- Q: What is the maximum time window after a competition date during which placements can be recorded/modified? → A: 30 days — placements locked after 30 days post-competition

## User Scenarios & Testing

### User Story 1 - Admin manages competition lifecycle with hard delete (Priority: P1)

An admin creates, edits, reads, and deletes competitions. Deletion is permanent (hard delete) with no soft delete or restore. If a competition has associated teams, deletion is blocked until all teams are removed.

**Why this priority**: Competition lifecycle management is the foundation — without it no other feature works.

**Independent Test**: Can be fully tested by creating a competition, editing its details, viewing it, and permanently deleting it (with and without teams). Delivers the core CRUD capability.

**Acceptance Scenarios**:

1. **Given** an admin user, **When** they create a competition with name, date, location, and fee per student, **Then** the competition appears in the competition list
2. **Given** an existing competition, **When** an admin edits its name, date, or other details, **Then** the changes are reflected immediately
3. **Given** a competition with no teams, **When** an admin deletes it, **Then** the competition is permanently removed and no longer appears in any list
4. **Given** a competition that has teams registered under it, **When** an admin attempts to delete it, **Then** the system blocks the deletion and explains that teams must be removed first

---

### User Story 2 - Admin manages teams with project info and hard delete (Priority: P1)

An admin creates a team for a competition with a category, optional subcategory, project name, and project description. The admin can optionally select a group to pre-fill the student roster. Team members (students) can be edited after creation. Deletion is hard delete — if any member has a paid fee, deletion is blocked.

**Why this priority**: Team registration is the second fundamental operation — competitions exist to register teams.

**Independent Test**: Can be tested by creating a team with a category and project info, verifying members can be added/removed, and deleting the team (with and without paid members). Delivers team CRUD with project tracking.

**Acceptance Scenarios**:

1. **Given** an existing competition, **When** an admin creates a team with a team name, category, project name, project description, and student members, **Then** the team appears in the team list for that competition
2. **Given** a team with no paid fees, **When** an admin deletes it, **Then** the team and all its members are permanently removed
3. **Given** a team that has at least one member with a paid fee, **When** an admin attempts to delete it, **Then** the system blocks the deletion and explains the reason
4. **Given** a team with existing members, **When** an admin adds a new student to the team, **Then** the student appears in the team roster
5. **Given** a team member who has not paid, **When** an admin removes them from the team, **Then** they are removed
6. **Given** a team member who has already paid, **When** an admin tries to remove them, **Then** the system blocks the removal and explains that the fee must be refunded first

---

### User Story 3 - Admin tracks team project information (Priority: P2)

Each team registered in a competition has a project name and a project description visible on the team detail page and in team lists. This allows admins to identify and differentiate teams by their project work.

**Why this priority**: Project info distinguishes teams meaningfully within a competition.

**Independent Test**: Can be tested by creating a team with a project name and description, verifying they appear in team details, and updating them later.

**Acceptance Scenarios**:

1. **Given** a team creation form, **When** an admin fills in project name and description, **Then** both fields are saved and visible on the team detail page
2. **Given** an existing team, **When** an admin edits the project name or description, **Then** the changes are reflected immediately

---

### User Story 4 - Admin manages competition fees like enrollment fees (Priority: P2)

Each student in a team has a fee amount due (`amount_due`). The system tracks how much has been paid (`amount_paid`). A student can make multiple partial payments toward their fee. A fee is considered paid when `amount_paid >= amount_due`. Payments are linked to the finance module (receipts). Partial payments are supported.

**Why this priority**: Fee tracking is essential for financial accountability, and enrollment-style tracking provides the flexibility needed for real-world payment patterns.

**Independent Test**: Can be tested by creating a team member with a fee, making a partial payment, verifying the balance updates, making a full payment, and verifying the fee shows as paid. All receipts are created in the finance module.

**Acceptance Scenarios**:

1. **Given** a student added to a team with a fee amount due, **When** viewing their fee status, **Then** the system shows `amount_due`, `amount_paid` (0), and balance (`amount_due - amount_paid`)
2. **Given** a student with an outstanding fee balance, **When** an admin processes a partial payment, **Then** `amount_paid` increases by the payment amount and a receipt is created in the finance module
3. **Given** a student who has made multiple partial payments, **When** viewing their fee status, **Then** the total `amount_paid` reflects the sum of all payments
4. **Given** a student whose `amount_paid >= amount_due`, **When** an admin views the team, **Then** the student's fee is marked as fully paid
5. **Given** an overpayment scenario (`amount_paid > amount_due`), **When** the system calculates fee status, **Then** it handles the excess gracefully (overpayment is tracked but fee is considered paid)

---

### User Story 5 - Admin filters and groups teams by category and subcategory (Priority: P3)

An admin can view teams filtered by competition, category, and subcategory. The system allows grouping teams by subcategory within a category for easier review and management.

**Why this priority**: Subcategory grouping improves navigation and reporting when a competition has many teams across multiple categories.

**Independent Test**: Can be tested by creating teams across multiple categories and subcategories, then using filter options to view only teams in a specific subcategory.

**Acceptance Scenarios**:

1. **Given** teams registered in different categories and subcategories, **When** an admin views the team list filtered by a specific category, **Then** only teams in that category are shown
2. **Given** teams with various subcategories, **When** an admin groups by subcategory, **Then** teams are organized under their subcategory headings

---

### User Story 6 - Admin records competition results (Priority: P2)

After a competition date has passed, an admin can record the placement (rank and label) for each team. The placement is visible on the team detail page and in reports. Placement can only be set after the competition date.

**Why this priority**: Recording results is a primary reason for using the system — it closes the competition lifecycle.

**Independent Test**: Can be tested by setting a placement on a team after the competition date, verifying it appears on team details, and attempting (and failing) to set placement before the competition date.

**Acceptance Scenarios**:

1. **Given** a competition whose date has passed and is within 30 days, **When** an admin sets a placement (rank and label) for a team, **Then** the placement is saved and visible on the team detail page
2. **Given** a competition whose date is in the future, **When** an admin attempts to set a placement, **Then** the system blocks the action
3. **Given** a competition whose date was more than 30 days ago, **When** an admin attempts to set or modify a placement, **Then** the system blocks the action with a message explaining the window has closed

---

### Out of Scope (This Iteration)

- Certificate generation (handled externally)
- Bulk operations (CSV/Excel import and export of teams or members)
- Public student-facing portal for competition registration or results viewing
- Automated email notifications for competition events (registration confirmation, payment receipts, placement announcements)

### Edge Cases

- What happens when a competition date is today? Placement should be allowed (competition day has arrived).
- What if a competition date was more than 30 days ago? Placement recording is blocked — the window has closed.
- What if a student is registered in a second team for the same competition? The system warns the admin but allows the registration after explicit confirmation. Each team's fee tracking remains independent.
- What if a competition has no teams registered? The competition list and detail views should handle empty states gracefully.
- What if a team is created without any students? Blocked — at least one student is required. If a group is selected for pre-fill but has zero active students, the system shows a warning and allows manual student entry.
- What if a refund is processed against a competition fee? The `amount_paid` should decrease by the refunded amount.
- What if a competition's fee_per_student is zero? Teams can still be created with member_share = 0; no payment needed.
- What if the finance module fails mid-payment? The entire operation rolls back atomically — no orphan receipt, no phantom fee update.
- What if a payment is partially processed (receipt created but fee not updated)? This should never occur due to atomic rollback; if it does due to an unexpected error, it is a critical system bug requiring manual inspection of the finance module.

## Requirements

### Functional Requirements

- **FR-001**: Admins MUST be able to create competitions with name, edition year, date, location, and fee per student
- **FR-002**: Admins MUST be able to edit and view competition details
- **FR-003**: Admins MUST be able to permanently delete competitions (hard delete) — only if no teams are associated
- **FR-004**: Any authenticated user MUST be able to view a list of competitions
- **FR-004a**: Only admins MAY create, edit, or delete competitions, teams, members, payments, and placements
- **FR-004b**: Coaches (employees linked as team coach) MAY read their own teams' data but MUST NOT modify any data
- **FR-005**: Admins MUST be able to create teams with team name, category, optional subcategory, project name, project description, and student members
- **FR-006**: When creating a team, admins MAY optionally select a group to pre-fill the student roster (the group serves as a student source, not an ownership constraint)
- **FR-007**: Admins MUST be able to edit team details (name, category, subcategory, project name, project description)
- **FR-008**: Admins MUST be able to add and remove students from a team (removal blocked if student has paid)
- **FR-009**: Admins MUST be able to permanently delete teams (hard delete) — only if no members have paid fees
- **FR-010**: The system MUST warn an admin when attempting to register a student in a second team for the same competition, but allow the registration after explicit confirmation
- **FR-011**: Students added to a team MUST be verified as active students in the system
- **FR-012**: The coach of a team MUST be an existing employee in the system
- **FR-013**: Each team member MUST have a fee amount due (`amount_due`) and a running total paid (`amount_paid`)
- **FR-014**: Admins MUST be able to process partial payments toward a student's competition fee
- **FR-015**: Each payment MUST create a receipt in the finance module
- **FR-016**: A team member's fee is considered paid when `amount_paid >= amount_due`
- **FR-017**: Admins MUST be able to view team lists filtered by competition, category, and subcategory
- **FR-018**: Admins MUST be able to group teams by subcategory within a category
- **FR-019**: Admins MUST be able to record placement results (rank and label) for a team after the competition date, within 30 days of the competition date
- **FR-020**: Placements MUST be blocked for competitions whose date is in the future OR more than 30 days past the competition date
- **FR-021**: When a fee payment is refunded, the student's `amount_paid` MUST decrease by the refunded amount and the fee payment link must be updated
- **FR-022**: The system MUST log competition registration, payment, and placement events to the student activity log
- **FR-023**: Fee payment operations MUST be atomic — if receipt creation or fee status update fails, the entire operation MUST roll back with no orphan data

### Key Entities

- **Competition**: A competition event with name, edition year, date, location, fee per student. Can be permanently deleted (hard delete). Must have no teams to be deleted.
- **Team**: A group of students participating in a competition under a specific category (and optional subcategory). Has a project name and project description. Has an optional coach (employee) and an optional group reference (for student pre-fill). Can be permanently deleted if no member fees have been paid.
- **Team Member**: A student's participation in a team. Each member has an amount due (`amount_due`) and a running paid total (`amount_paid`). Supports partial payments. Linked to the finance module via receipts. A student cannot be in two teams for the same competition.
- **Category/Subcategory**: Classification for teams within a competition. Category is required; subcategory is optional. Teams can be filtered and grouped by these.
- **Placement**: A team's result in a competition — rank (1, 2, 3, etc.) and label ("Gold", "Honorable Mention", etc.). Can only be set after the competition date.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Admins can complete the full competition lifecycle (create → register teams → record results) without any soft-delete or restore functionality
- **SC-002**: Team creation includes project name and description that are visible immediately on the team detail page
- **SC-003**: Fee status (due, paid, partial) is accurately displayed for each team member based on `amount_due` vs `amount_paid`
- **SC-004**: Partial payments update the fee balance correctly and generate proper receipts in the finance module
- **SC-005**: Hard delete permanently removes competitions and teams from all lists, and no restore operation exists
- **SC-006**: Category and subcategory filters return the correct subset of teams in under 2 seconds for competitions with up to 100 teams
- **SC-007**: An admin can complete team creation with group-based student pre-fill in under 1 minute
- **SC-008**: Placement recording is blocked before the competition date and succeeds after, with clear error messaging

## Assumptions

- Admins have the same role/permission level as the current `require_admin` guard
- The competition coach is always an existing employee in the system (no external coaches)
- Existing student activity logging (CRM integration) will be reused for registration, payment, and placement events
- Certificates are handled outside the system (manually)
- The finance module's existing receipt and refund infrastructure will be extended to support competition payments
- Competition fee per student is a flat rate per competition; individual team member fees can differ
- Performance target for competition lists is under 2 seconds for typical competition sizes (up to 100 teams, 500 members)
