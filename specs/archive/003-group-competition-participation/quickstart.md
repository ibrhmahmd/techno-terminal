# Quickstart: Group Competition Participation Fixes

## Implementation Order

### Step 1: Timestamp fix (US4)
1. `app/modules/academics/group/competition/repository.py` — replace `datetime.utcnow()` with `utc_now()` in `complete_participation()`

### Step 2: Typed DTOs (US3)
2. `app/modules/academics/group/competition/schemas.py` — add `GroupCompetitionDTO`, `WithdrawalResultDTO`, `TeamLinkResultDTO`
3. `app/modules/academics/group/analytics/schemas.py` — add `ParticipationBriefDTO`
4. `app/modules/academics/group/competition/service.py` — update 3 methods to return typed DTOs
5. `app/modules/academics/group/competition/interface.py` — update protocol signatures
6. `app/modules/academics/group/analytics/repository.py` — return `ParticipationBriefDTO` from `get_group_competition_participations()`
7. `app/api/routers/academics/group_competitions_router.py` — update 3 endpoints that unpack dicts

### Step 3: Auto-create participation (US1)
8. `app/modules/competitions/services/team_service.py` — add `GroupCompetitionParticipation` creation in `register_team()` when `group_id` is provided

### Step 4: Placement sync (US2)
9. `app/modules/competitions/services/team_service.py` — sync `final_placement` from team to participation in `update_placement()`

## Key files

| File | Change |
|------|--------|
| `app/modules/competitions/services/team_service.py` | Add 2 new features (auto-create + placement sync) |
| `app/modules/academics/group/competition/service.py` | Typed DTO returns |
| `app/modules/academics/group/competition/repository.py` | `utc_now()` fix |
| `app/modules/academics/group/competition/schemas.py` | 3 new DTOs |
| `app/modules/academics/group/competition/interface.py` | Updated return types |
| `app/modules/academics/group/analytics/repository.py` | Typed returns |
| `app/modules/academics/group/analytics/schemas.py` | 1 new DTO |
| `app/api/routers/academics/group_competitions_router.py` | Use typed DTOs |

## Verification

```bash
pytest tests/test_academics_competitions.py -v
pytest tests/test_competitions.py -v -k "fee"  # confirm no regression
```
