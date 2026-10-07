# Feature Specification: Competitions Module

**Created**: 2026-05-11
**Status**: Draft

## User Scenarios & Testing

### User Story 1 — Competition Lifecycle (Priority: P1)

An admin creates, lists, views, edits, and removes competition events. Each competition has a name, edition year, date, location, and optional per-student registration fee. Admins can restore competitions that were removed.

**Why this priority**: Competition events are the foundation of the entire module — teams and members cannot exist without a competition to belong to.

**Independent Test**: An admin can create a competition with name and date, verify it appears in the list, view its details, edit its name, remove it, and restore it — all without any teams or members existing.

**Acceptance Scenarios**:

1. **Given** no competitions exist, **When** an admin creates a competition with name "Robotics Challenge" and edition_year 2026, **Then** the competition appears in the list with the provided details.
2. **Given** an active competition exists, **When** an admin views it, **Then** all fields (name, edition_year, date, location, fee_per_student) are displayed.
3. **Given** an active competition exists, **When** an admin edits its name, **Then** the updated name is reflected.
4. **Given** an active competition exists, **When** an admin removes it, **Then** it no longer appears in the active list.
5. **Given** a removed competition exists, **When** an admin restores it, **Then** it reappears in the active list.
6. **Given** a competition with registered teams exists, **When** an admin tries to remove it, **Then** the system prevents removal and explains why.
7. **Given** two competitions with the same name and edition_year exist, **When** an admin tries to create a third, **Then** the system prevents the duplicate.

---

### User Story 2 — Team & Member Management (Priority: P2)

An admin registers teams under a competition, assigns students as members, and records placement results after the competition ends. Each team has a name, category, optional subcategory, and optional coach. One student can be in only one team per competition. Team names must be unique within a competition.

**Why this priority**: Running a competition requires organising participants into teams and categories. This is the core operational workflow.

**Independent Test**: An admin can register a team with 3 students in a category, verify they appear in the team roster, add a 4th student, remove one student, and set placement after the competition date passes.

**Acceptance Scenarios**:

1. **Given** an active competition with categories, **When** an admin registers a team named "Alpha" in category "Robotics" with 3 students, **Then** the team appears in the competition roster with all members listed.
2. **Given** a team named "Alpha" exists in a competition, **When** an admin tries to register another team named "Alpha" in the same competition, **Then** the system rejects the duplicate name.
3. **Given** a student is already on team "Alpha" in a competition, **When** an admin tries to add them to team "Beta" in the same competition, **Then** the system rejects with a conflict.
4. **Given** a team with an active member exists, **When** an admin views the team roster, **Then** all members and their fee payment status are shown.
5. **Given** a student is a member of a team, **When** an admin removes them, **Then** the student is no longer listed.
6. **Given** a team has a member who has already paid, **When** an admin tries to remove that member, **Then** the system prevents removal.
7. **Given** a competition date has passed, **When** an admin sets a team's placement to rank 1 with label "Gold", **Then** the placement is recorded and visible.
8. **Given** a competition date is in the future, **When** an admin tries to set placement, **Then** the system prevents it.

---

### User Story 3 — Fee Payment Processing (Priority: P2)

An admin processes competition fee payments for individual team members. Each payment creates a financial receipt and marks the member's fee as paid. Paid members cannot be removed from their team.

**Why this priority**: Fee collection is a financial workflow that must be atomic — a receipt should never be created without marking the fee paid, or vice versa.

**Independent Test**: An admin can pay a student's competition fee, verify a receipt is created, confirm the member is marked paid, and confirm the member cannot be removed.

**Acceptance Scenarios**:

1. **Given** a team member with a fee balance, **When** an admin processes payment for that member, **Then** a receipt is created and the member is marked as paid.
2. **Given** a team member who has already paid, **When** an admin tries to pay again, **Then** the system rejects the duplicate payment.
3. **Given** a team member with fee paid, **When** an admin tries to remove them from the team, **Then** the system prevents removal.
4. **Given** a team has any member with fee paid, **When** an admin tries to delete the team, **Then** the system prevents deletion.

### Edge Cases

- What happens when an admin tries to create a competition with a name and edition_year that already exists? → Unique constraint prevents duplicates.
- What happens when a competition fee is changed after team registration? → Each member's fee share is snapshotted at registration time (member_share column). Later fee changes do not affect existing members.
- What happens when an admin tries to delete a team whose members have paid? → System blocks deletion with a business rule violation.
- What happens when the Finance module is unavailable during fee payment? → The entire payment operation fails atomically — no partial state (no receipt without fee marking).

## Requirements

### Functional Requirements

- **FR-001**: Admins MUST be able to create competitions with name, edition year, date, location, and optional fee.
- **FR-002**: Admins MUST be able to list, view, edit, soft-delete, and restore competitions.
- **FR-003**: The system MUST prevent deletion of competitions that have registered teams.
- **FR-004**: Competition name + edition_year combinations MUST be unique.
- **FR-005**: Admins MUST be able to register teams under a competition with category, optional subcategory, optional coach, and optional group link.
- **FR-006**: Team names MUST be unique within a competition.
- **FR-007**: A student MUST NOT be registered in more than one team per competition.
- **FR-008**: Admins MUST be able to add and remove students from teams.
- **FR-009**: The system MUST prevent removal of team members who have paid fees.
- **FR-010**: The system MUST prevent deletion of teams with members who have paid fees.
- **FR-011**: Admins MUST be able to record team placement (rank + label) after the competition date passes.
- **FR-012**: The system MUST prevent setting placement before the competition date.
- **FR-013**: Admins MUST be able to process fee payments for individual team members.
- **FR-014**: Fee payment MUST be atomic — either both receipt creation and fee marking succeed, or neither does.
- **FR-015**: The system MUST prevent duplicate fee payments for the same member.
- **FR-016**: Each member's fee share MUST be snapshotted at registration time and not affected by later fee changes.
- **FR-017**: Any authenticated user MUST be able to view competitions and teams.
- **FR-018**: Only admins MUST be able to create, edit, delete, restore competitions, register teams, manage members, process payments, and set placements.
- **FR-019**: Competition and team removal MUST be soft-delete (data preserved, hidden from active views).
- **FR-020**: Team registration and placement changes MUST log to each affected student's activity timeline.

### Key Entities

- **Competition**: A contest event with a name, edition year, date, location, and optional per-student fee. Multiple competitions can exist for different edition years.
- **Team**: A group of students participating together in a competition under a specific category (and optional subcategory). Belongs to exactly one competition.
- **TeamMember**: A student's membership in a team, with a snapshotted fee share and payment status. Connects students to teams.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An admin can complete the full competition lifecycle (create → view → edit → delete → restore) in under 2 minutes.
- **SC-002**: Team registration with 10 students and fee share calculation completes within 5 seconds.
- **SC-003**: Fee payment operation creates a receipt and marks fee paid with no partial-failure states detectable.
- **SC-004**: A student's full competition history (all teams, categories, competitions, placements) can be retrieved in under 3 seconds.

## Assumptions

- Competition categories are free-form text (citext, case-insensitive) defined per team at registration time, not pre-defined as a separate entity.
- Fee payment requires the Finance module to be operational.
- Student activity logging (for registrations and placements) is non-critical — failures are silently swallowed.
- Deployment target assumes PostgreSQL with citext extension and SSL connections.
- The module is accessed exclusively through the existing API layer (no direct service access).
