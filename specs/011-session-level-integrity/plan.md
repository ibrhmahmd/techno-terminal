# Implementation Plan: Session Level Integrity & Course Validation

**Branch**: `011-session-level-integrity` | **Date**: 2026-05-16 | **Spec**: [spec.md](spec.md)

## Summary

Fix 3 issues: (1) `group_level_id` FK on `CourseSession` is always NULL because no creation code path populates it — sessions cannot be reliably traced to their `GroupLevel` record; (2) group session queries return ALL historical sessions (600+ for a 50-level group) instead of defaulting to the current active level; (3) course creation has no upper bounds on levels or sessions per level, allowing excessive data volume.

## Constitution Check

| Principle | Check | Notes |
|-----------|-------|-------|
| I. Router→Service→Repository | ✅ All changes respect layer boundaries | Validation in schemas (router boundary) + service; queries in repository |
| II. Module Organization | ✅ Academics is stateless pattern | Session service creates its own sessions via `get_session()` — consistent |
| III. Typed Contracts | ✅ New repo methods return typed sequences | `list_sessions_by_group_level` returns `Sequence[CourseSession]` |
| IV. Response Envelope | ✅ No new exception types needed | Existing `ValidationError` for course limits |
| V. Auth-Guarded Endpoints | ✅ No changes to auth guards | |

## Technical Approach

### Phase 0: Repository Layer Additions

**File**: `app/modules/academics/session/repository.py`

1. **`get_group_level_id(session, group_id, level_number) -> int | None`** — Helper to look up `GroupLevel.id` by `(group_id, level_number)`. Needed by session service methods that create individual sessions.

2. **`list_sessions_by_group_level(session, group_level_id) -> Sequence[CourseSession]`** — Filter sessions by FK to `group_levels.id` (more precise than filtering by integer `level_number`). Used by the new default query path.

**File**: `app/modules/academics/group/level/repository.py`

3. **`get_current_group_level_id(session, group_id) -> int | None`** — Returns the `id` of the active `GroupLevel` for a group (where `status = 'active'`). Used to determine the default level filter.

### Phase 1: Session Creation — Populate `group_level_id`

**File**: `app/modules/academics/helpers/session_planning.py`

4. Add `group_level_id: int | None = None` parameter to `create_sessions_in_session()`. When provided, set it on each created `CourseSession`. The caller is responsible for passing the correct value.

**File**: `app/modules/academics/group/lifecycle/service.py`

5. In `create_group_with_first_level()` (line 126): Pass `group_level_id=level.id` to `create_sessions_in_session()` — the `level` is already created and flushed at line 113.

6. In `progress_to_next_level()` (line 249): Pass `group_level_id=new_level.id` to `create_sessions_in_session()` — the `new_level` is already created and flushed at line 244.

7. In `add_level_to_existing_group()` (line 375): Pass `group_level_id=level.id` to `create_sessions_in_session()` — the `level` is already created and flushed at line 370.

**File**: `app/modules/academics/session/service.py`

8. In `generate_level_sessions()` (line 75): Look up `group_level_id` via `repo.get_group_level_id()` before calling `create_sessions_in_session()`. Pass it through.

9. In `add_extra_session()` (line 93): Look up `group_level_id` via `repo.get_group_level_id()` and set it on the individual `CourseSession` being created.

10. In `cancel_session()` (line 189): The replacement session creation also needs `group_level_id`. Look it up using `cs.group_id` and `cs.level_number` (or ideally use `cs.group_level_id` if it's already set — but for existing sessions it will be NULL until backfill, so we need the fallback lookup).

### Phase 2: Session Query Defaults

**File**: `app/modules/academics/session/service.py`

11. In `list_group_sessions()`: Change `level_number: int | None = None` to `level_number: int | None = None`. When `level_number` is None, look up the group's current active `group_level_id` via the new repo method and filter by that. This replaces the current behavior of returning ALL sessions when no level is specified.

**File**: `app\api\routers\academics\groups_router.py` (or the actual file path of the group sessions endpoint)

12. Remove the `level` query parameter default of `None` — the service now handles the default internally. (Or keep it as-is since the service handles the fallback.)

### Phase 3: Course Creation Validation

**File**: `app/modules/academics/course/schemas.py`

13. Add `MAX_SESSIONS_PER_LEVEL = 100` constant (or use a module-level constant).
14. Add `MAX_LEVELS = 100` constant.
15. In `AddNewCourseInput.sessions_per_level` validator: Add `if v > MAX_SESSIONS_PER_LEVEL: raise ValidationError(...)`.
16. Add new field `max_levels: Optional[int] = Field(default=None, ge=1, le=MAX_LEVELS)` to both `AddNewCourseInput` and `UpdateCourseDTO`.

**File**: `app/modules/academics/course/service.py`

17. In `add_new_course()`: Validate `data.max_levels` if provided (upper bound check).
18. In `update_course()`: Validate `data.max_levels` if provided.

**Note**: For the initial implementation, the `max_levels` validation is a service-level guard against excessive progression. A future migration could add a `max_levels` column to the `courses` table if per-course configurability is needed.

### Phase 4: Data Migration (053)

**File**: `db/migrations/053_backfill_session_group_level_id.sql`

19. Backfill NULL `group_level_id` values by joining `sessions` to `group_levels` on `(group_id, level_number)`:

```sql
UPDATE sessions s
SET group_level_id = gl.id
FROM group_levels gl
WHERE s.group_level_id IS NULL
  AND gl.group_id = s.group_id
  AND gl.level_number = s.level_number;
```

20. Log the count of sessions where no matching `GroupLevel` was found (keep NULL).

### Phase 5: get_levels_detailed Default (FR-013)

**File**: `app/modules/academics/group/details/service.py`

21. In `get_levels_detailed()`: When `level_number` is None, instead of returning ALL levels (current behavior at line 134), default to only the group's current active level. Look up the group's current `level_number` from the `Group` model and only return that level's data.

This affects the "detailed view" — a full level browser should be added separately if needed.

## Affected Files

| File | Change |
|------|--------|
| `app/modules/academics/session/repository.py` | Add `get_group_level_id()`, `list_sessions_by_group_level()` |
| `app/modules/academics/group/level/repository.py` | Add `get_current_group_level_id()` (or reuse `get_current_group_level`) |
| `app/modules/academics/helpers/session_planning.py` | Add `group_level_id` param to `create_sessions_in_session()` |
| `app/modules/academics/group/lifecycle/service.py` | Pass `group_level_id` from all 3 callers (create, progress, add-level) |
| `app/modules/academics/session/service.py` | Look up `group_level_id` in 4 methods; change session query default |
| `app/modules/academics/group/details/service.py` | Change `get_levels_detailed` default to current level only |
| `app/modules/academics/course/schemas.py` | Add `max_levels` field, max validators |
| `app/modules/academics/course/service.py` | Add max-levels guard |
| `app/api/routers/academics/groups_router.py` | (if needed) update level query parameter |
| `db/migrations/053_backfill_session_group_level_id.sql` | New migration for backfill |

## Testing

### Unit Tests

| Test | File | What It Tests |
|------|------|---------------|
| T011-01 | `tests/test_session_level_integrity.py` | `create_sessions_in_session` with `group_level_id` param |
| T011-02 | Same | Session creation via lifecycle service sets `group_level_id` |
| T011-03 | Same | `add_extra_session` populates `group_level_id` |
| T011-04 | Same | `generate_level_sessions` populates `group_level_id` |
| T011-05 | Same | Default session list returns only current level sessions |
| T011-06 | Same | Explicit level filter still returns historical sessions |
| T011-07 | Same | Course creation rejects `sessions_per_level > 100` |
| T011-08 | Same | Course creation rejects `max_levels > 100` |
| T011-09 | Same | `get_levels_detailed` defaults to current level |
| T011-10 | Same | Backfill migration SQL handles NULL group_level_id |

### Integration Tests

- T011-INT-01: Full flow — create group → verify sessions have `group_level_id` → progress level → verify new sessions have new `group_level_id`
- T011-INT-02: Add extra session → verify `group_level_id` populated
- T011-INT-03: Course with extreme values rejected
- T011-INT-04: Group with 50 levels → default query returns only current level sessions

## Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Backfill migration finds sessions with no matching GroupLevel | Orphaned data stays NULL | Log count, manual review — spec explicitly allows this |
| Changing default query breaks callers that depend on all-sessions behavior | Regression | Flag as breaking change; add explicit `level` parameter where callers need historical data |
| Course max validation prevents admin use case | Admin blocked | Set limits generously (100 levels, 100 sessions/level) — far above any realistic course |
| `list_sessions_by_group` still called by other services with expectation of all sessions | Wrong data returned | Only change the default in `list_group_sessions()` service method — keep `list_sessions_by_group()` repo unchanged for backward compat |
