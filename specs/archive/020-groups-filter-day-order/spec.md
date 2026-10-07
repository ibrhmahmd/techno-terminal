# Feature Specification: Groups Day Order & Search Filter

**Feature Branch**: `020-groups-filter-day-order`  
**Created**: 2026-06-02  
**Status**: Draft  
**Input**: "Investigate groups by day ordering to start by Friday (Arabic week), and add filtering/search for groups similar to student filter"

## Clarifications

### Session 2026-06-02

- Q: What fields should the filter endpoint return? → A: Return enriched group data matching `EnrichedGroupDTO` (nested instructor/course/level objects, schedule, capacity, enrolled count), consistent with the student filter pattern of returning rich data.
- Q: What sort behavior should the filter endpoint have? → A: Default sort by group name ascending, with optional `sort_by` (name, day, status) and `sort_order` (asc, desc) parameters.
- Q: Where should the day-order sort mapping live? → A: Add to `app/modules/academics/constants.py` alongside `WEEKDAYS`. Defer broader day-definition consolidation to a separate cleanup story.

### Session 2026-06-03

- Q: Course exclusion filter → A: Filter groups that have NEVER been related to a course (historical), not just current course_id mismatch.
- Q: Instructor history filter → A: Filter groups that have EVER had (or never had) a certain instructor, not just current instructor.
- Q: Level number vs level id → A: Filter by `level_number` (numeric rank, e.g., level 1, 2, 3), not the database level_id.
- Q: Session number filter → A: Both single value (`current_session_number`) and range (`session_number_from`/`session_number_to`) to find groups currently at a specific curriculum session point.
- Q: Search scope for `q` → A: Broadest — group name, course name, instructor name, schedule time, group notes/description, enrolled student names.
- Q: Additional approved filter params → A: price_min/price_max, start_date_from/start_date_to, time_from/time_to, gender, instructor_id, course_name (separate from `q`), name (group name field), age_min/age_max (target age range).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Groups Grouped by Day Show Correct Week Order (Priority: P1)

An admin views the groups page grouped by day and sees the weekdays in the correct Arabic/Islamic order starting with Friday. This makes the schedule readable and matches the cultural expectation that the work week begins on Friday.

**Why this priority**: This is a data presentation bug fix — the current alphabetical sort produces a confusing order. Fixing it restores usability with no new infrastructure needed.

**Independent Test**: Call `GET /academics/groups/grouped?group_by=day` and verify the returned groups are ordered: Friday, Saturday, Sunday, Monday, Tuesday, Wednesday, Thursday, Unspecified.

**Acceptance Scenarios**:

1. **Given** groups exist with various `default_day` values, **When** `GET /academics/groups/grouped?group_by=day` is called, **Then** the keys in the response appear in the order: Friday, Saturday, Sunday, Monday, Tuesday, Wednesday, Thursday, Unspecified
2. **Given** a group has `default_day = null` or empty, **When** the grouped endpoint is called, **Then** it appears in the "Unspecified" bucket at the end of the list
3. **Given** the `next_weekday()` function in `time_helpers.py`, **When** it is called with any day name, **Then** it still correctly computes the next occurrence relative to the current date (no regression)

---

### User Story 2 - Admin Filters Groups by Multiple Criteria (Priority: P1)

An admin navigates to the groups management page and uses a multi-criteria filter panel to narrow down groups by name, course, instructor, level, day of week, and status. The results update instantly with paginated results.

**Why this priority**: The existing student filter is heavily used. Groups lack equivalent filtering, forcing admins to scroll through long lists. This directly improves daily operations.

**Independent Test**: Can be tested by calling `GET /academics/groups/filter?q=robotics&course_ids=1&day=Saturday&status=active&skip=0&limit=20` and verifying only matching groups are returned.

**Acceptance Scenarios**:

1. **Given** multiple groups exist across different courses, instructors, days, and levels, **When** an admin filters by course ID, **Then** only groups belonging to that course are returned
2. **Given** groups with various `default_day` values, **When** an admin filters by day name (e.g., `Saturday`), **Then** only groups scheduled for that day are returned
3. **Given** an admin types a partial group name in the search field, **When** the filter is submitted, **Then** groups whose name contains the search term (case-insensitive) are returned
4. **Given** an admin filters by instructor name, **When** the filter is submitted, **Then** only groups taught by that instructor are returned
5. **Given** an admin filters by group level ID, **When** the filter is submitted, **Then** only groups at that level are returned
6. **Given** an admin filters by group status (active/inactive/completed), **When** the filter is submitted, **Then** only groups with that status are returned
7. **Given** filter results exceed the page size, **When** the response is returned, **Then** pagination metadata (`total`, `skip`, `limit`) is included so the client can page through results

---

### User Story 3 - Groups Used in Search Terms via Filter Pattern (Priority: P2)

An admin types into a free-text search field and the system searches across group name, course name, and instructor name simultaneously.

**Why this priority**: Free-text search across multiple fields reduces clicks and speeds up finding groups when the admin doesn't know which criterion matches.

**Independent Test**: Call `GET /academics/groups/filter?q=robot` and verify groups matching in name, course name, or instructor name are all returned.

**Acceptance Scenarios**:

1. **Given** a group named "Robotics A" taught by "Ahmed", **When** the admin searches `q=robot`, **Then** "Robotics A" is returned
2. **Given** a group named "Python Beginner" in the "Programming" course, **When** the admin searches `q=programming`, **Then** "Python Beginner" is returned
3. **Given** a group taught by instructor "Sara", **When** the admin searches `q=sara`, **Then** all groups taught by Sara are returned

---

### Edge Cases

- What happens when `q` parameter is provided but empty string? Should return all groups (same as no filter).
- What happens when no groups match the filter criteria? Should return an empty list with `total: 0`.
- What happens when a non-existent course ID or instructor ID is provided? Should return an empty result (no error).
- How does the system handle day name variations? Accept full day names (e.g., "Saturday", "Friday") and abbreviations (e.g., "sat", "fri").
- What happens when `default_day` for a group is empty/null in a day-filtered search? The group is excluded from day-specific results (not included in any day bucket).
- What happens when pagination `skip` exceeds total matching results? Return an empty list with correct `total`.

## Requirements *(mandatory)*

### Functional Requirements

#### Day Ordering Fix

- **FR-001**: The `get_groups_grouped()` method MUST sort grouped day keys in the Arabic/Islamic week order: Friday, Saturday, Sunday, Monday, Tuesday, Wednesday, Thursday, Unspecified
- **FR-002**: The system MUST define a canonical day-order mapping (Friday=0, Saturday=1, etc.) in `app/modules/academics/constants.py` as the single source of truth for day ordering, NOT relying on alphabetical sort
- **FR-003**: The "Unspecified" bucket (groups with null/empty `default_day`) MUST always appear last regardless of sort direction
- **FR-004**: The `WEEKDAYS` constant and `next_weekday()` function MUST NOT be affected by this change — session date calculation must continue to work correctly with Python's Monday=0 convention

#### Groups Filter/Search

- **FR-005**: System MUST provide a `GET /academics/groups/filter` endpoint accepting query parameters for multi-criteria filtering
- **FR-006**: System MUST support free-text search (`q` parameter) matching against: group name, course name, instructor name, schedule time, group notes/description, and enrolled student names (case-insensitive substring match across all)
- **FR-007**: System MUST support filtering by course (one or more course IDs via `course_ids`)
- **FR-007b**: System MUST support course **exclusion** via `course_not` parameter — filter groups that have NEVER been associated with a given course across their entire history
- **FR-008**: System MUST support filtering by day of week (one or more day names via `day`, accepting both full names and abbreviations)
- **FR-009**: System MUST support filtering by instructor name (partial match via `instructor_name`)
- **FR-009b**: System MUST support instructor history filters via `instructor_id` (current instructor equals ID), `instructor_has_id` (has EVER had this instructor), and `instructor_not_id` (has NEVER had this instructor)
- **FR-010**: System MUST support filtering by group level number via `level_number` (numeric rank, e.g., 1, 2, 3) — NOT the database record ID
- **FR-010b**: System MUST support filtering by group name via `name` parameter (case-insensitive substring match, separate from `q`)
- **FR-010c**: System MUST support filtering by course name via `course_name` parameter (case-insensitive substring match, separate from `q`)
- **FR-011**: System MUST support filtering by group status (active, inactive, completed via `status`)
- **FR-011b**: System MUST support filtering by gender via `gender` parameter
- **FR-011c**: System MUST support filtering by age range via `age_min` and `age_max` (group's target student age bracket)
- **FR-011d**: System MUST support filtering by price range via `price_min` and `price_max`
- **FR-011e**: System MUST support filtering by start date range via `start_date_from` and `start_date_to`
- **FR-011f**: System MUST support filtering by time range via `time_from` and `time_to`
- **FR-011g**: System MUST support filtering by current session number via `current_session_number` (single value) and `session_number_from` / `session_number_to` (range)
- **FR-012**: System MUST support offset-based pagination with `skip` and `limit` parameters (default `skip=0`, `limit=50`, max `limit=200`)
- **FR-013a**: System MUST default to sorting results by group name ascending
- **FR-013b**: System MUST support optional `sort_by` parameter (`name`, `day`, `status`) and `sort_order` parameter (`asc`, `desc`) to override the default sort
- **FR-014**: System MUST return pagination metadata (`total`, `skip`, `limit`) alongside the filtered results
- **FR-015**: System MUST return results in a typed response envelope matching the project's `ApiResponse` pattern
- **FR-016**: System MUST return an empty result set with `total: 0` when no groups match the filter criteria (not an error)
- **FR-017**: System MUST accept both full day names and abbreviations by normalizing inputs (same mapping as student filter: `mon/tue/wed/thu/thurs/fri/sat/sun`)

### Key Entities

- **Group**: Academic group with attributes: name, course, instructor, default_day, level, status, capacity, schedule
- **GroupFilterDTO**: Input filter parameters — `q`, `name`, `course_ids`, `course_not`, `course_name`, `day`, `instructor_id`, `instructor_name`, `instructor_has_id`, `instructor_not_id`, `level_number`, `gender`, `age_min`, `age_max`, `status`, `price_min`, `price_max`, `start_date_from`, `start_date_to`, `time_from`, `time_to`, `current_session_number`, `session_number_from`, `session_number_to`, `sort_by`, `sort_order`, `skip`, `limit`
- **GroupFilterResultDTO**: Output shape containing `groups` (list of enriched groups matching EnrichedGroupDTO shape) and pagination metadata

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The grouped-by-day endpoint returns days in correct Arabic/Islamic order (Friday through Thursday, Unspecified last) — verifiable by calling the endpoint and checking key order
- **SC-002**: The filter endpoint accepts all approved filter parameters (q, name, course_ids, course_not, course_name, day, instructor_id, instructor_name, instructor_has_id, instructor_not_id, level_number, gender, age_min, age_max, status, price_min, price_max, start_date_from, start_date_to, time_from, time_to, current_session_number, session_number_from, session_number_to) and returns correct filtered results — verifiable by testing each parameter independently
- **SC-003**: Free-text search across group name, course name, and instructor name returns correct results for each field — verifiable by test cases for each searchable field
- **SC-004**: Pagination correctly limits results to the requested page size and returns accurate `total` count — verifiable by comparing unfiltered count with paginated result totals
- **SC-005**: All filter parameters can be combined simultaneously — verifiable by a combined-query test that returns the correct intersection of results
- **SC-006**: Empty filter criteria returns all groups (unfiltered) with correct pagination — verifiable by comparing unfiltered count with filter endpoint with no criteria

## Assumptions

- The Arabic/Islamic week starts on Friday — this is the expected sorting order for the application's user base
- The existing `WEEKDAYS` constant in `app/modules/academics/constants.py` follows Python's Monday=0 convention for date math and should NOT be changed — only the display/sort order changes
- Day name abbreviations will follow the same mapping as the student filter (`DAY_ABBREV_MAP` in `students_router.py`)
- The filter endpoint follows the same architectural pattern as the student filter: `GroupFilterDTO` → service method → raw SQL query → `GroupFilterResultDTO` → `ApiResponse` envelope
- The existing `get_enriched_groups()` query is the starting point for the filter query, with dynamic WHERE clauses appended based on provided filter parameters
- Historical lookups (course exclusion, instructor history) may require additional queries or CTEs to check the full history of group-instructor and group-course associations — this adds complexity but is desired
- Session number filtering assumes groups track a `current_session_number` field or can derive it from session records
- Cross-param logic: AND between different parameters, OR within a single parameter's multiple values
