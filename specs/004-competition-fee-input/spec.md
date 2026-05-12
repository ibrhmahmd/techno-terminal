# Feature Specification: Competition Fee User Input

**Feature Branch**: `004-competition-fee-input`
**Created**: 2026-05-12
**Status**: Draft
**Input**: Remove auto-splitting of competition fees, allow user to input per-student fee, remove team.fee column, keep fee_per_student on Competition as UI reference default, convenience default to 0

## User Scenarios & Testing

### User Story 1 - Admin registers a team with per-student fees (Priority: P1)

An admin creates a team and specifies a different fee for each student. Students without a specified fee default to 0.

**Why this priority**: This is the core behavioral change — the system currently splits `team_fee / len(students)` equally, which doesn't match real-world needs where students may have different fee arrangements.

**Independent Test**: Can be tested by creating a team with explicit student fees and verifying each `TeamMember.member_share` matches the input.

**Acceptance Scenarios**:

1. **Given** an admin is registering a team for competition "Robotics 2026" (which has `fee_per_student=50`), **When** they submit `student_ids=[1, 2]` and `student_fees={1: 50, 2: 30}`, **Then** `TeamMember[student_id=1].member_share = 50` and `TeamMember[student_id=2].member_share = 30`
2. **Given** an admin registers a team with `student_ids=[1, 2, 3]` and no `student_fees` map, **When** the team is created, **Then** all three `TeamMember.member_share` values are 0
3. **Given** an admin registers a team with `student_ids=[1, 2]` and `student_fees={1: 50}`, **When** the team is created, **Then** student 1 gets `member_share=50` and student 2 gets `member_share=0`
4. **Given** an admin registers a team without specifying `student_fees` at all (None), **When** the team is created, **Then** all members get `member_share=0`

---

### User Story 2 - Admin adds a member to an existing team with a fee (Priority: P1)

An admin adds a student to an existing team and specifies the fee for that student. The system no longer auto-calculates `team.fee / 2`.

**Why this priority**: The current hardcoded `team.fee / 2` is incorrect for teams with more than 2 members and doesn't allow per-student fee variation.

**Independent Test**: Can be tested by adding a member with a specific fee and checking the `member_share`.

**Acceptance Scenarios**:

1. **Given** an existing team with 3 members, **When** an admin adds student 4 with `fee=50`, **Then** the new `TeamMember.member_share = 50` (no division by 4 or 2)
2. **Given** an existing team, **When** an admin adds student 5 without specifying `fee`, **Then** the new `TeamMember.member_share = 0`
3. **Given** an existing team, **When** an admin adds student 6 with `fee=0`, **Then** the new `TeamMember.member_share = 0`

---

### User Story 3 - Team.fee column is removed with no disruption (Priority: P2)

The `teams.fee` column is dropped from the database schema and removed from the Team model. No existing functionality depends on it after the auto-splitting removal.

**Why this priority**: Fees are now per-student only. The team-level `fee` column was used as the source for auto-splitting, which is being removed.

**Independent Test**: Can be verified by checking the Team SQLModel has no `fee` field and the database schema has no `teams.fee` column.

**Acceptance Scenarios**:

1. **Given** the migration is applied, **When** a new team is created, **Then** no `fee` column exists on the teams table
2. **Given** existing teams had `fee` values, **When** the migration runs, **Then** the column is dropped (data loss is acceptable — `member_share` on each `TeamMember` already snapshots the per-student fee)
3. **Given** the Team SQLModel is read, **When** the model is instantiated, **Then** there is no `fee` field available

---

### User Story 4 - Competitions retain fee_per_student as reference (Priority: P3)

The `competitions.fee_per_student` field remains as a reference/hint for the UI. It is NOT used in any automatic calculation.

**Why this priority**: Useful for displaying suggested fee in the UI without enforcing it as the actual charge per student.

**Independent Test**: Can be verified by creating a competition with `fee_per_student` and checking the DTO still includes it.

**Acceptance Scenarios**:

1. **Given** a competition is created with `fee_per_student=50`, **When** the competition is fetched via the API, **Then** `fee_per_student=50` is returned in the DTO
2. **Given** `fee_per_student` is set on a competition, **When** a team is registered with no `student_fees`, **Then** members default to `member_share=0` (fee_per_student is NOT used as default)

---

### Edge Cases

- What happens when `student_fees` contains a student_id not in `student_ids`? → Ignore the extraneous key (no error)
- What happens when `student_fees` is provided but empty dict `{}`? → All students get 0 (same as None/missing)
- What happens when an admin updates a team's fee after members are added? → `team.fee` column no longer exists, so this endpoint option is removed from the update schema
- What happens to existing teams that had a `fee` value in the database? → The migration drops the column — existing `member_share` values on `TeamMember` are the source of truth

## Requirements

### Functional Requirements

- **FR-001**: `RegisterTeamInput` MUST accept an optional `student_fees: Optional[dict[int, float]]` field mapping student_id to fee
- **FR-002**: When `student_fees` is None or a student_id is missing from the map, the student's `member_share` MUST default to 0
- **FR-003**: `register_team()` MUST NOT perform any fee auto-calculation (remove `team_fee / len(student_ids)` logic)
- **FR-004**: `AddTeamMemberInput` in the teams router MUST accept a `fee: float = 0.0` field
- **FR-005**: `add_team_member_to_existing()` MUST accept a `fee: float = 0.0` parameter and use it directly as `member_share`
- **FR-006**: The hardcoded `team.fee / 2` split MUST be removed from `add_team_member_to_existing()`
- **FR-007**: The `fee` field MUST be removed from `TeamBase` SQLModel
- **FR-008**: The `teams.fee` column MUST be dropped via migration (existing `member_share` values are the source of truth)
- **FR-009**: The `fee` field MUST be removed from `TeamDTO` output schema
- **FR-010**: The `fee` field MUST be removed from `UpdateTeamInput` in the router
- **FR-011**: `Competition.fee_per_student` field MUST remain on model and DTOs (UI reference only)
- **FR-012**: `fee_per_student` MUST NOT be used as a default value for `member_share` in any calculation
- **FR-013**: `pay_competition_fee()`, `mark_fee_paid()`, finance receipt creation, analytics fee summary, and CRM activity logging MUST remain unchanged

### Key Entities

- **RegisterTeamInput.student_fees**: New optional field — a dictionary mapping `student_id` to their individual fee amount
- **AddTeamMemberInput.fee**: New optional field on the existing input DTO — the fee for the new member
- **TeamMember.member_share**: No change to this field — still snapshots the per-student fee at registration time. Only the source of this value changes (user input vs auto-calculated)
- **Competition.fee_per_student**: Unchanged — remains as reference/hint only

## Success Criteria

### Measurable Outcomes

- **SC-001**: Admin can register 3 students on the same team with fees 50, 30, and 0 respectively — each `member_share` matches exactly
- **SC-002**: No `team_fee / N` calculation exists anywhere in the codebase
- **SC-003**: `teams.fee` column no longer exists in the database schema
- **SC-004**: `Competition.fee_per_student` is still present in `CompetitionDTO`
- **SC-005**: All existing fee payment endpoints (`pay_competition_fee`), finance integration, and analytics work without modification
- **SC-006**: Backward compatible for API consumers that don't use `student_fees` (all members default to 0)

## Assumptions

- Existing `member_share` values on `TeamMember` records are the source of truth — no need to migrate old data
- No UI/client currently depends on `teams.fee` being returned in API responses
- The `student_fees` dictionary approach is preferred over a separate list of `StudentFeeInput` objects for minimal schema change (Principle II: Clean Interfaces)
- All existing fee infrastructure (CRM logging, finance receipt creation, analytics) is preserved and continues to work exactly as before
