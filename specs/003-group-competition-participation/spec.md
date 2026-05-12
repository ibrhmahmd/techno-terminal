# Feature Specification: Group Competition Participation Fixes

**Feature Branch**: `003-group-competition-participation`
**Created**: 2026-05-12
**Status**: Draft
**Input**: Fix bugs in group competition participation tracking: placement sync gap, missing auto-creation on team registration, unt typed DTOs, wrong timestamp utility

## User Scenarios & Testing

### User Story 1 - Admin registers a team for a group and participation is tracked automatically (Priority: P1)

An admin creates a team for a group in a competition. The team gets linked to the group (`teams.group_id`), and a `group_competition_participation` record is created automatically without requiring a separate API call.

**Why this priority**: Currently requires two manual steps (create team + register participation). This is the primary workflow — the two-step process is a known gap that causes missed participation records.

**Independent Test**: Can be tested by creating a team with `group_id` and verifying a participation record exists in the database.

**Acceptance Scenarios**:

1. **Given** an admin is on the team registration screen, **When** they create a team with `group_id=123`, `competition_id=456`, `team_name="RoboWarriors"`, **Then** a `group_competition_participation` record is created with `group_id=123`, `team_id=<new_team_id>`, `competition_id=456`, `is_active=True`
2. **Given** a team is registered WITHOUT a `group_id`, **When** the team is created, **Then** no `group_competition_participation` record is created
3. **Given** an admin attempts to register a team with `group_id` for a competition where the group already has an active participation with that team, **When** the team is created, **Then** the existing behavior of preventing duplicate active participations is preserved

---

### User Story 2 - Competition placement is visible in group participation history (Priority: P1)

When an admin updates a team's placement rank after the competition ends, the group's participation history also reflects the placement.

**Why this priority**: Currently `teams.placement_rank` is set but `group_competition_participation.final_placement` stays NULL. This means group analytics and history reports are missing placement data.

**Independent Test**: Can be tested by updating placement on a team and checking the group's participation record.

**Acceptance Scenarios**:

1. **Given** a group has an active participation record for a team, **When** an admin sets placement to rank 1 on the team, **Then** the participation record's `final_placement` is updated to 1
2. **Given** a group has NO active participation record for a team, **When** an admin sets placement on the team, **Then** no participation record is affected (no error, just skip)
3. **Given** a group's participation is marked as withdrawn (`is_active=False`), **When** an admin updates placement, **Then** only the `teams.placement_rank` is set (withdrawn participation is not updated)

---

### User Story 3 - Developers can work with typed DTOs instead of raw dicts (Priority: P2)

The group competition service and analytics repository return typed DTOs instead of inline dictionaries, following the project's typed interface convention.

**Why this priority**: Three `list[dict]` return values exist in the group competition service and three more in the analytics repository. These violate Principle III of the constitution and create maintenance risk.

**Independent Test**: Can be verified by importing the DTOs and checking type signatures.

**Acceptance Scenarios**:

1. **Given** `get_group_competitions()` is called, **When** it returns, **Then** the return type is `list[GroupCompetitionDTO]` (typed) instead of `list[dict]`
2. **Given** `withdraw_from_competition()` is called, **When** it returns, **Then** the return type is `WithdrawalResultDTO` (typed) instead of `dict`
3. **Given** `link_existing_team()` is called, **When** it returns, **Then** the return type is `TeamLinkResultDTO` (typed) instead of `dict`
4. **Given** analytics repository functions are called, **When** they return, **Then** they use typed DTOs instead of `list[dict]` or `dict`

---

### User Story 4 - Consistent timestamp utilities across the module (Priority: P3)

The `complete_participation` repository function uses the same shared `utc_now()` utility as the rest of the codebase.

**Why this priority**: Minor inconsistency — `datetime.utcnow()` is used in one place instead of the shared `utc_now()` from `app.shared.datetime_utils`. Low risk but worth fixing for consistency.

**Independent Test**: Can be verified by inspecting the import and call in the repository function.

**Acceptance Scenarios**:

1. **Given** `complete_participation()` is called, **When** it sets `left_at`, **Then** it uses `utc_now()` from `app.shared.datetime_utils` instead of `datetime.utcnow()`

---

### Edge Cases

- What happens when a team is registered with `group_id` but the group no longer exists? (FK constraint on `group_competition_participation.group_id` handles this)
- What happens when placement is updated on a team that has two active participation records? (Should be prevented by UNIQUE constraint, but if it occurs, update the most recent active one)
- What happens when `get_group_competitions()` is called for a group with no participations? (Returns empty list — no change in behavior)

## Requirements

### Functional Requirements

- **FR-001**: System MUST auto-create `GroupCompetitionParticipation` record when `register_team()` is called with a non-null `group_id`
- **FR-002**: Auto-created participation MUST have `is_active=True`, `entered_at` set to current time, and all three FKs populated
- **FR-003**: System MUST NOT create a participation record when `group_id` is None/null in `register_team()`
- **FR-004**: System MUST sync `teams.placement_rank` to `group_competition_participation.final_placement` for the active participation record when `update_placement()` is called
- **FR-005**: System MUST only sync placement to active participation records (skip withdrawn/completed)
- **FR-006**: System MUST NOT throw an error when no active participation exists during placement sync (graceful no-op)
- **FR-007**: `get_group_competitions()` MUST return `list[GroupCompetitionDTO]` instead of `list[dict]`
- **FR-008**: `withdraw_from_competition()` MUST return `WithdrawalResultDTO` instead of `dict`
- **FR-009**: `link_existing_team()` MUST return `TeamLinkResultDTO` instead of `dict`
- **FR-010**: Analytics repository functions MUST use typed DTO return types instead of `list[dict]` or raw `dict`
- **FR-011**: `complete_participation()` MUST use `utc_now()` from `app.shared.datetime_utils` instead of `datetime.utcnow()`

### Key Entities

- **GroupCompetitionParticipation**: Tracks a group's lifecycle in a competition — when they entered, when they left, their placement. Links group → team → competition.
- **GroupCompetitionDTO**: Typed return DTO for group competition participation data including participation fields, competition name, team name, category, placement.
- **WithdrawalResultDTO**: Typed DTO for withdrawal result containing participation ID, status, and timestamp.
- **TeamLinkResultDTO**: Typed DTO for team link result containing team ID, team name, group ID.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Admin creates a team with `group_id` in a single step — no second API call needed for participation tracking
- **SC-002**: Group competition history reports show accurate placement data for all completed participations
- **SC-003**: All six `list[dict]` return values in the group competition domain are replaced with typed DTOs
- **SC-004**: All timestamp operations in group competition repository use the shared `utc_now()` utility
- **SC-005**: Backward compatible — no breaking changes to existing API contracts

## Assumptions

- Existing UNIQUE constraint on `(group_id, team_id, competition_id)` is sufficient to prevent duplicates
- Placement sync only needs to update one active participation per team (no team should have multiple active participations in the same competition)
- The `group_competition_participation` table will continue to be defined in the Academics module (no consolidation planned for this spec)
- Router-layer DTO conversions (`GroupCompetitionPublic`, etc.) that already use unpacking from `dict` will be updated to accept typed DTOs in their constructors
