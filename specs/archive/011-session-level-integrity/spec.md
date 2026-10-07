# Feature Specification: Session Level Integrity & Course Validation

**Feature Branch**: `011-session-level-integrity`
**Created**: 2026-05-16
**Status**: Draft
**Input**: Fix data integrity gap where `group_level_id` FK on sessions is always NULL, prevent unbounded session queries, and add course-level validation limits.

## User Scenarios & Testing

### User Story 1 - Group sessions show only current level content (Priority: P1)

An admin viewing a group's sessions only sees the current level's sessions (~12), not ALL historical sessions across 50+ levels. The system automatically defaults to the group's active level.

**Why this priority**: This is the primary bug — 600 sessions returned when 12 are needed. Causes slow load times and UI issues.

**Independent Test**: Can be tested by viewing any group with multiple completed levels. The session list should show only the current active level's sessions (not all historical levels). Delivers immediate performance fix.

**Acceptance Scenarios**:

1. **Given** a group with 50 completed levels (600 sessions total), **When** an admin views the group's sessions, **Then** only ~12 sessions from the current active level are returned
2. **Given** a group session list, **When** an admin selects a specific level number from a filter, **Then** only that level's sessions are shown
3. **Given** the sessions endpoint with no explicit level filter, **When** a request is made, **Then** the system defaults to the group's current `level_number`

---

### User Story 2 - Sessions are linked to their GroupLevel record (Priority: P1)

When sessions are created (group creation, level progression, or individual extra sessions), each session is properly linked to the corresponding `GroupLevel` record via `group_level_id`.

**Why this priority**: Fixes the data integrity gap that prevents precise session filtering by level. Without this, sessions cannot be reliably traced back to their level configuration.

**Independent Test**: Can be tested by creating a group (which generates Level 1 sessions) and verifying each session's `group_level_id` points to the correct `GroupLevel` record. Delivers correct data for all future session queries.

**Acceptance Scenarios**:

1. **Given** a new group is being created, **When** the first level's sessions are generated, **Then** each session has `group_level_id` set to the newly created `GroupLevel` record's ID
2. **Given** a group progresses to the next level, **When** the new level's sessions are generated, **Then** each session has `group_level_id` set to the new level's `GroupLevel` record
3. **Given** an admin adds an extra session to a group, **When** the session is created, **Then** `group_level_id` is populated with the correct active level's ID
4. **Given** existing historical sessions where `group_level_id` is NULL, **When** a data migration runs, **Then** those sessions are backfilled by matching `(group_id, level_number)` to the corresponding `GroupLevel` record

---

### User Story 3 - Course creation enforces reasonable limits (Priority: P2)

When a course is created or edited, the system enforces validation limits to prevent accidentally creating courses with excessive levels or sessions that lead to data volume problems.

**Why this priority**: Prevention is better than cleanup — course limits stop the root cause at the source.

**Independent Test**: Can be tested by attempting to create a course with extreme values (e.g., 1000 levels or 200 sessions per level) and verifying the system rejects them with clear messages.

**Acceptance Scenarios**:

1. **Given** a course creation form, **When** an admin enters a number of levels exceeding the maximum (e.g., > 100), **Then** the system rejects it with a clear error message
2. **Given** a course creation form, **When** an admin enters sessions per level exceeding the maximum (e.g., > 100), **Then** the system rejects it with a clear error message
3. **Given** a course creation form, **When** an admin enters values within allowed limits, **Then** the course is created successfully

---

### Edge Cases

- What happens to existing sessions with `group_level_id = NULL` after the migration? They will be backfilled by matching `(group_id, level_number)` to `GroupLevel` records. If no matching `GroupLevel` exists, keep NULL — don't force a link.
- What if a session's `level_number` doesn't match any `GroupLevel` for that group? The backfill migration should skip that session (leave NULL) and log it for manual review.
- What if an admin queries sessions by `group_level_id` that was just backfilled? The new query function will return correct results immediately after migration.
- What about cancelled sessions? They should also be linked to `GroupLevel` — cancellation doesn't remove the session from the level.
- What is the maximum practical number of levels? Consider the typical education cycle — a 3-year course might have 6-8 levels. Set the max at 100 as a generous safety limit.
- What if a course needs more levels than the limit? The limit should be configurable or overrideable by an admin setting.

## Requirements

### Functional Requirements

- **FR-001**: When bulk-generating sessions for a level (via `create_sessions_in_session` or similar), each session MUST have its `group_level_id` set to the corresponding `GroupLevel.id`
- **FR-002**: When creating an individual session (extra session, manual session), `group_level_id` MUST be populated with the group's active level's `GroupLevel.id`
- **FR-003**: When a group progresses to a new level, sessions generated for that new level MUST have `group_level_id` pointing to the new level's `GroupLevel` record
- **FR-004**: The system MUST provide a query method that returns sessions filtered by `group_level_id` (exact level, not just `level_number` integer)
- **FR-005**: The default session list for a group MUST return only the current active level's sessions
- **FR-006**: Users MUST still be able to view sessions from previous levels via an explicit level filter
- **FR-007**: A data migration MUST backfill `group_level_id` for existing sessions where it is NULL, by matching `(group_id, level_number)` to the corresponding `GroupLevel` record
- **FR-008**: If no matching `GroupLevel` record exists during backfill, the session MUST keep `group_level_id = NULL` and be logged for manual review
- **FR-009**: Course creation MUST enforce a maximum number of levels (suggested: 100)
- **FR-010**: Course creation MUST enforce a maximum number of sessions per level (suggested: 100)
- **FR-011**: Course edit MUST also enforce the same limits as creation (FR-009, FR-010)
- **FR-012**: The default `level` parameter on the group sessions endpoint MUST be the group's current `level_number`, not `None`
- **FR-013**: The `get_levels_detailed` endpoint MUST NOT return sessions from inactive/completed levels by default — only active level sessions

### Key Entities

- **CourseSession**: Represents a single class session. Already has `group_level_id FK → group_levels.id` but it's never populated. This is the core data integrity fix.
- **GroupLevel**: A level within a group's progression. Has `id` that should be referenced by all sessions belonging to that level. Currently sessions only store `level_number` (integer) without the FK link.
- **Course**: The template for creating groups. Defines `sessions_per_level` and implied number of levels. Needs validation limits to prevent excessive data volume.
- **Group**: An active class. Tracks `level_number` to indicate current level. This value should be the default filter for session queries.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of newly created sessions have a non-null `group_level_id` pointing to a valid `GroupLevel` record
- **SC-002**: The default group session query returns at most `sessions_per_level` records (typically 12-16), never the total historical count
- **SC-003**: Course creation rejects values exceeding maximum levels (100) and maximum sessions per level (100) with clear error messages
- **SC-004**: The backfill migration populates `group_level_id` for at least 95% of existing sessions (sessions without a matching `GroupLevel` record are the exception)
- **SC-005**: An admin can still access any level's sessions by explicitly selecting a level filter — no data is lost, only scoped by default

## Assumptions

- The `GroupLevel` record always exists before sessions are created for that level (group creation creates `GroupLevel` first, then sessions; level progression does the same)
- The `(group_id, level_number)` pair is sufficient to uniquely identify a `GroupLevel` record for backfilling
- The maximum levels limit (100) is generous enough for all real-world courses — a 3-year weekly course typically has 6-8 levels
- Sessions that cannot be backfilled (no matching `GroupLevel`) will be rare and indicate orphaned data that warrants manual review
- This spec does NOT address fixing the existing 600-session data for Group 540 — that group's session count is correct for its 50 completed levels. The fix prevents the volume from being returned, not from existing.
