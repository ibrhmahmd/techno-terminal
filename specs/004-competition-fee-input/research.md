# Research: Competition Fee User Input

## Resolved Unknowns

### Decision: Fee splitting logic location

**Decision**: Remove auto-splitting from `team_service.py:register_team()` and `add_team_member_to_existing()`
**Rationale**: The spec requires user-provided per-student fees instead of auto-calculated equal split. The two affected functions are the only places where auto-splitting occurs.
**Alternatives considered**: Keeping split as fallback when `student_fees` is absent (rejected — spec says default to 0)

### Decision: `team.fee` column removal impact

**Decision**: Drop the column — no code depends on it after splitting removal
**Rationale**: `team.fee` was used as the source for auto-splitting (`team.fee / len()` and `team.fee / 2`). After removal, fees live only on `TeamMember.member_share`. The `TeamDTO.fee` field is also removed from API responses.
**Files affected**: `team_models.py`, `team_schemas.py`, `teams_router.py` (UpdateTeamInput), `competitions_router.py` (UpdateCompetitionInput), migration 050, schema file

### Decision: `competition.fee_per_student` preservation

**Decision**: Keep as-is on Competition model, CompetitionDTO, CreateCompetitionInput, and UpdateCompetitionInput
**Rationale**: Spec requires it as UI reference/hint. No calculation logic uses it.

### Decision: Existing fee infrastructure preservation

**Decision**: No changes to `pay_competition_fee()`, `mark_fee_paid()`, finance receipt service, refund service, analytics fee summary, CRM activity logging
**Rationale**: These all operate on `TeamMember.member_share` and `fee_paid` — fields that remain unchanged. The only change is HOW `member_share` gets its value.

## Codebase Findings

### Files requiring modification (10 files)

| File | Change |
|------|--------|
| `app/modules/competitions/models/team_models.py` | Remove `fee` field from `TeamBase` |
| `app/modules/competitions/schemas/team_schemas.py` | Add `student_fees` to `RegisterTeamInput`, add `fee` to `AddTeamMemberInput` (as new inline DTO), remove `fee` from `TeamDTO` |
| `app/modules/competitions/services/team_service.py` | Replace auto-split logic with per-student fee assignment in `register_team()`; replace `team.fee / 2` with param in `add_team_member_to_existing()` |
| `app/api/routers/competitions/teams_router.py` | Add `fee` field to `AddTeamMemberInput`, remove `fee` from `UpdateTeamInput` |
| `app/api/routers/competitions/competitions_router.py` | Remove `fee` from `UpdateCompetitionInput` |
| `db/schema/07_tables_competitions.sql` | Remove `teams.fee` column |
| `db/migrations/050_remove_team_fee_column.sql` | New migration to drop column |
| `tests/test_competitions.py` | Update test bodies that reference `fee` field |

### Files requiring NO changes (confirmed zero impact)

| File | Why no change |
|------|--------------|
| `app/modules/competitions/repositories/team_repository.py` | `create_team()` accepts `fee` param but will receive `None` after removal — noop. `add_team_member()` `member_share` param stays. |
| `app/modules/competitions/repositories/competition_repository.py` | `fee_per_student` stays |
| `app/modules/competitions/repositories/__init__.py` | No fee-related exports |
| `app/modules/finance/services/receipt_service.py` | Uses `TeamMember.member_share` — unchanged |
| `app/modules/finance/services/refund_service.py` | Uses `member.fee_paid` — unchanged |
| `app/modules/finance/repositories/reporting_repository.py` | Uses `COALESCE(tm.fee_share, 0)` — but wait, this queries `fee_share` not `member_share`. See bug below. |
| `app/modules/analytics/repositories/competition_repository.py` | Uses `tm.member_share` — unchanged |
| `app/modules/notifications/services/competition_notifications.py` | Dead code (never wired) — unchanged |

### Bug discovered during research

**`finance/reporting_repository.py` line 69**: The `get_unpaid_competition_fees` query references `COALESCE(tm.fee_share, 0)` but the column is named `member_share` in the database schema and SQLModel. `fee_share` does not exist. This query would always return 0 for `member_share`. This is a pre-existing bug, not introduced by this feature. Recommend fixing in a separate task.
