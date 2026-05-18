# Performance Fix Plan: N+1 Query Elimination

**Branch**: `010-competition-feature-enhancements`
**Date**: 2026-05-17
**Scope**: Fix 4 N+1 query hotspots in competition module using batch loading and JOINs.

## Summary

Replace N+1 query patterns with batch-loaded JOINs across 4 service methods. Total query reduction: **~746 → 4 queries** for a typical competition with 100 teams × 5 members.

## Technical Context

**Pattern**: All 4 hotspots follow the same anti-pattern — iterate over parent records, then query child records one-by-one inside the loop.

**Fix strategy**: Batch-load all child records in a single query, group them in Python by parent ID, then assemble DTOs from the in-memory dictionary.

**No schema changes required** — only repository and service layer modifications.

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| §I Router → Service → Repository | ✅ PASS | New repo functions added, service layer updated. No layer skipping. |
| §III Typed Contracts | ✅ PASS | All new repo functions return typed models. DTOs unchanged. |
| §IV Response Envelope | ✅ PASS | No API contract changes — same DTOs, same response shapes. |

## Affected Files

```text
app/modules/competitions/repositories/team_repository.py  — Add 3 new batch functions
app/modules/competitions/repositories/competition_repository.py  — Add 1 batch function
app/modules/competitions/services/competition_service.py  — Fix get_competition_summary
app/modules/competitions/services/team_service.py  — Fix get_teams_with_members, list_team_members, get_student_competitions
tests/test_competitions.py  — Add performance regression tests
```

## Implementation Tasks

### Phase 1: Repository Batch Functions

**Purpose**: Add batch-loading repository functions that fetch all child records in a single query.

- [ ] T101 [P] Add `list_team_members_with_students(db, team_ids: list[int])` in `team_repository.py` — single JOIN query: `SELECT tm.*, s.full_name FROM team_members tm LEFT JOIN students s ON s.id = tm.student_id WHERE tm.team_id IN :team_ids`. Returns `dict[int, list[TeamMemberWithStudent]]` grouped by team_id.
- [ ] T102 [P] Add `list_teams_with_members(db, competition_id: int)` in `team_repository.py` — single JOIN query: `SELECT t.*, tm.*, s.full_name FROM teams t LEFT JOIN team_members tm ON tm.team_id = t.id LEFT JOIN students s ON s.id = tm.student_id WHERE t.competition_id = :competition_id`. Returns `(list[Team], dict[int, list[TeamMemberWithStudent]])`.
- [ ] T103 [P] Add `list_student_memberships_enriched(db, student_id: int)` in `team_repository.py` — single JOIN query: `SELECT tm.*, t.*, c.* FROM team_members tm JOIN teams t ON t.id = tm.team_id LEFT JOIN competitions c ON c.id = t.competition_id WHERE tm.student_id = :student_id`. Returns `list[MembershipEnrichedRow]`.
- [ ] T104 [P] Add `get_competition_summary_data(db, competition_id: int)` in `competition_repository.py` — single query that returns competition + all teams + all members + all student names in one result set. Returns `CompetitionSummaryRawData` named tuple.

### Phase 2: Service Layer Refactoring

**Purpose**: Replace N+1 loops with batch-loaded data assembly.

- [ ] T105 [US1] Refactor `get_competition_summary()` in `competition_service.py` — replace nested loops (lines 104-166) with single `get_competition_summary_data()` call. Assemble DTOs from pre-fetched data. Query count: 602 → 1.
- [ ] T106 [US2] Refactor `get_teams_with_members()` in `team_service.py` — replace loop (lines 308-326) with `list_teams_with_members()` call. Assemble DTOs from pre-fetched data. Query count: 101 → 1.
- [ ] T107 [US2] Refactor `list_team_members()` in `team_service.py` — replace loop (lines 466-490) with `list_team_members_with_students()` call for single team. Query count: 22 → 1.
- [ ] T108 [US5] Refactor `get_student_competitions()` in `team_service.py` — replace loop (lines 25-62) with `list_student_memberships_enriched()` call. Query count: 21 → 1.

### Phase 3: Verification

**Purpose**: Confirm query counts are reduced and responses are identical.

- [ ] T109 Add performance regression test for `get_competition_summary` — assert ≤ 3 queries for 100 teams × 5 members
- [ ] T110 Add performance regression test for `get_teams_with_members` — assert ≤ 2 queries for 100 teams
- [ ] T111 Add performance regression test for `list_team_members` — assert ≤ 2 queries for 20 members
- [ ] T112 Add performance regression test for `get_student_competitions` — assert ≤ 2 queries for 10 memberships
- [ ] T113 Run `pytest tests/test_competitions.py -v` — all existing tests pass (no behavioral regression)
- [ ] T114 Run `pytest tests/ -v` — full suite passes

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: No dependencies — new repo functions are additive, no breaking changes
- **Phase 2**: Depends on Phase 1 — service methods call new repo functions
- **Phase 3**: Depends on Phase 2 — tests verify refactored behavior

### Execution Order

1. T101-T104 (parallel — different repo files, no dependencies)
2. T105-T108 (parallel — different service methods, no cross-dependencies)
3. T109-T114 (sequential — run tests after all refactoring)

## Parallel Opportunities

```bash
# Launch all repository batch functions together:
Task: "Add list_team_members_with_students (T101)"
Task: "Add list_teams_with_members (T102)"
Task: "Add list_student_memberships_enriched (T103)"
Task: "Add get_competition_summary_data (T104)"

# Launch all service refactors together:
Task: "Refactor get_competition_summary (T105)"
Task: "Refactor get_teams_with_members (T106)"
Task: "Refactor list_team_members (T107)"
Task: "Refactor get_student_competitions (T108)"
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| JOIN query returns duplicate rows (1:N × 1:N) | Medium | High | Use `GROUP BY` or Python-side deduplication |
| Large result set memory pressure | Low | Medium | Batch loading already limits scope to single competition |
| Behavioral regression in DTO assembly | Low | High | Existing tests verify response shape; add regression tests |
| SQLModel doesn't support complex JOINs | Low | Medium | Use raw SQL via `db.exec(text(...))` if needed |

## Success Criteria

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| `get_competition_summary` queries (100 teams × 5 members) | 602 | 1 | ≤ 3 |
| `get_teams_with_members` queries (100 teams) | 101 | 1 | ≤ 2 |
| `list_team_members` queries (20 members) | 22 | 1 | ≤ 2 |
| `get_student_competitions` queries (10 memberships) | 21 | 1 | ≤ 2 |
| All existing tests pass | — | — | 22/22 |
| Response DTOs unchanged | — | — | Identical |

## Implementation Strategy

### MVP First (T105 only)

1. Complete Phase 1: Add `get_competition_summary_data()` repo function
2. Complete Phase 2: Refactor `get_competition_summary()` service method
3. **STOP AND VALIDATE**: Run existing tests, verify response is identical, confirm query count ≤ 3
4. Proceed to remaining 3 hotspots

### Incremental Delivery

1. Fix `get_competition_summary` (biggest win: 602 → 1 queries)
2. Fix `get_teams_with_members` (101 → 1 queries)
3. Fix `list_team_members` (22 → 1 queries)
4. Fix `get_student_competitions` (21 → 1 queries)
5. Each fix is independent — can be merged separately

### Rollback Plan

If any refactor introduces a regression:
1. Revert the service method to its original N+1 implementation
2. Keep the new repo function (it's additive, no harm)
3. Debug and fix in a follow-up PR
