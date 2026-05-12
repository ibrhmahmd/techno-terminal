# Research: Group Competition Participation Fixes

## Resolved Unknowns

### Decision: Auto-create location

**Decision**: Add `GroupCompetitionParticipation` creation directly in `TeamService.register_team()` using the SQLModel and session, not via `GroupCompetitionService.register_team()`.
**Rationale**: `TeamService` already has the DB session and the `GroupCompetitionParticipation` model is available via import from `app.modules.academics.models`. Calling `GroupCompetitionService.register_team()` would create a second DB session (stateless pattern) and add unnecessary complexity. Direct model creation is simpler and consistent with how `TeamService` already handles business logic.

### Decision: Placement sync approach

**Decision**: Add a query to `team_repository.py` to find active participation by team_id, then update `final_placement` in `update_placement()`.
**Rationale**: The `list_team_participations()` function already exists in the academics repository. However, `team_service.py` should not import from academics repositories to maintain module independence. Instead, use a direct SQLModel query within the service method.

### Decision: Typed DTO naming

**Decision**: Use `GroupCompetitionDTO` (for the list return), `WithdrawalResultDTO`, `TeamLinkResultDTO` in `schemas.py`.
**Rationale**: Follows existing convention in the project (`CompetitionHistoryItemDTO`, `TeamReadDTO`).

### Decision: Analytics repository typed returns

**Decision**: Add `ParticipationBriefDTO` to `analytics/schemas.py` for `get_group_competition_participations()` return values.
**Rationale**: Currently returns `Sequence[tuple]` which is as bad as `list[dict]`. A typed DTO matches Constitution Principle III.

## Codebase Findings

### US1: Auto-create participation on team registration

**Current state**: `register_team()` in `TeamService` accepts `group_id` on `RegisterTeamInput` and passes it to `team_repo.create_team()`. No participation record is created.

**Change needed**: After creating the team and adding members, if `cmd.group_id` is not None, create a `GroupCompetitionParticipation(group_id=..., team_id=team.id, competition_id=cmd.competition_id, is_active=True, entered_at=now)` record.

**Import needed**: `from app.modules.academics.models.group_level_models import GroupCompetitionParticipation`
**Utility needed**: `from app.shared.datetime_utils import utc_now`

### US2: Sync placement to participation

**Current state**: `update_placement()` in `TeamService` sets `teams.placement_rank` and logs activity. `group_competition_participation.final_placement` is never updated.

**Change needed**: After setting `teams.placement_rank`, query `GroupCompetitionParticipation` for active records matching `team_id`, and update `final_placement`.

**Query needed**: `select(GroupCompetitionParticipation).where(GroupCompetitionParticipation.team_id == team_id, GroupCompetitionParticipation.is_active == True)`

### US3: Typed DTOs

Three methods in `GroupCompetitionService` return untyped dicts:

1. `get_group_competitions()` → `list[dict]` (service.py:55)
   - Router uses: `GroupCompetitionPublic(**p)` (group_competitions_router.py:55)
   - Replace with `list[GroupCompetitionDTO]`, update router to use `GroupCompetitionPublic.model_validate(p)`

2. `withdraw_from_competition()` → `dict` (service.py:115)
   - Router unpacks: `result["id"]`, `result["status"]`, `result["withdrawn_at"]` (group_competitions_router.py:197-205)
   - Replace with `WithdrawalResultDTO`, update router to use `result.id`, `result.status`, etc.

3. `link_existing_team()` → `dict` (service.py:125)
   - Router uses: `TeamLinkResponse(**result)` (group_competitions_router.py:106)
   - Replace with `TeamLinkResultDTO`, update router to use `TeamLinkResponse.model_validate(result)`

### US4: Timestamp fix

**Repository**: `complete_participation()` in `repository.py:43` uses `datetime.utcnow()`
**Fix**: Replace with `utc_now()` from `app.shared.datetime_utils`
**Import**: `from app.shared.datetime_utils import utc_now` (already imported in service.py but not in repository.py)

### Files modified (8 total)

| File | Change | US |
|------|--------|----|
| `app/modules/competitions/services/team_service.py` | Auto-create + placement sync | US1, US2 |
| `app/modules/academics/group/competition/service.py` | Typed DTO returns | US3 |
| `app/modules/academics/group/competition/repository.py` | `utc_now()` fix | US4 |
| `app/modules/academics/group/competition/schemas.py` | New DTO classes | US3 |
| `app/modules/academics/group/competition/interface.py` | Updated return types | US3 |
| `app/api/routers/academics/group_competitions_router.py` | Use typed DTOs in 3 endpoints | US3 |
| `app/modules/academics/group/analytics/repository.py` | Typed return from `get_group_competition_participations` | US3 |
| `app/modules/academics/group/analytics/schemas.py` | `ParticipationBriefDTO` | US3 |
