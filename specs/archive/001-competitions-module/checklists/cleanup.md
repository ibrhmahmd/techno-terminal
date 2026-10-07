# Cleanup Checklist: Competitions Module Legacy Items

**Purpose**: Track removal of deprecated code, dead code, and legacy artifacts identified during module indexing
**Created**: 2026-05-11
**Updated**: 2026-05-12 — items verified against live codebase before executing
**Feature**: [spec.md](../spec.md)

## Schema Cleanup

- [x] CHK001 SKIPPED — `group_competition_participation` is **actively used** by Academics module (group competition service, repository, analytics, interface, tests). NOT dead code despite `team.group_id` FK existing.
- [x] CHK002 SKIPPED — `competition_categories` still **referenced by analytics** (`app/modules/analytics/repositories/competition_repository.py:25`). Migration 036 to drop it was premature — the table is still needed.
- [x] CHK003 **DONE** — removed `is_active` column from competitions table in `db/schema/07_tables_competitions.sql`
- [x] CHK004 **DONE** — removed `enrollment_fee_per_student` column from teams table in `db/schema/07_tables_competitions.sql`
- [x] CHK005 **DONE** — removed `is_deleted` column from teams table in `db/schema/07_tables_competitions.sql`

## Test Cleanup

- [x] CHK006 **DONE** — updated stale endpoint paths in `tests/test_competitions.py`:
  - `/api/v1/competitions/register` → `POST /api/v1/teams`
  - `/api/v1/competitions/{id}/categories/{cat_id}/teams` → `GET /api/v1/teams?competition_id=1`
  - `/api/v1/competitions/team-members/{id}/pay` → `POST /api/v1/teams/{team_id}/members/{student_id}/pay`
- [x] CHK007 **DONE** — updated test request bodies to match 3-table schema (CreateCompetitionInput fields, RegisterTeamInput fields, removed category-related POST body)

## Migration Cleanup

- [ ] CHK008 Migration 014 (`add_competition_fee_per_student`) is a duplicate subset of migration 010 — verify no data loss risk and consider collapsing or documenting
- [x] CHK009 SKIPPED — `GroupCompetitionParticipation` SQLModel is **actively used** by Academics module, do NOT remove

## Integration Cleanup

- [x] CHK010 **DONE** — added `get_team_by_id()` to `TeamService` in `team_service.py:264`, updated `teams_router.py:154` and `teams_router.py:294`
- [x] CHK011 **DONE** — replaced `list[dict]` with `list[CategoryWithTeamsDTO]` in `CompetitionSummaryResponse` in `competitions_router.py`, added import from `team_schemas`

## Notes

- Items CHK001, CHK002, CHK009 were skipped after verifying they are actively used — the initial indexing incorrectly flagged them as dead code.
- CHK008 (migration 014 vs 010) remains open — needs human review of both migration files.
- Run `pytest tests/test_competitions.py -v` after cleanup to verify tests still pass.
