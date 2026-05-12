# Tasks: Group Competition Participation Fixes

**Generated**: 2026-05-12 | **Phase**: Phase 2 — Task Breakdown
**Plan**: [plan.md](./plan.md) | **Quickstart**: [quickstart.md](./quickstart.md)

---

## Implementation Order (4 steps, 9 files)

---

### Step 1 — Timestamp fix (US4, 1 file, 1 task)

#### Task 1: Replace `datetime.utcnow()` with shared `utc_now()`

| Field | Detail |
|-------|--------|
| File | `app/modules/academics/group/competition/repository.py` |
| Method | `complete_participation()` at line 68 |
| Change | `datetime.utcnow()` → `utc_now()` |
| Import | Add `from app.shared.datetime_utils import utc_now` (line 8 `datetime` import can be kept if used elsewhere, or removed) |
| Acceptance | `complete_participation()` sets `record.left_at` using `utc_now()` |
| Risk | None — drop-in replacement |

---

### Step 2 — Typed DTOs (US3, 7 files, 6 tasks)

> Core change: replace 3 `list[dict]`/`dict` return types + 1 `Sequence[tuple]` return type with typed DTOs.

#### Task 2: Add 3 DTO classes to competition schemas

| Field | Detail |
|-------|--------|
| File | `app/modules/academics/group/competition/schemas.py` |
| Add | `GroupCompetitionDTO`, `WithdrawalResultDTO`, `TeamLinkResultDTO` |
| Import | `from pydantic import BaseModel` (exists), `ConfigDict` (add if needed) |
| Shapes | See [`data-model.md`](./data-model.md#groupcompetitiondto) for exact field definitions |
| Pattern | Follow `TeamReadDTO` style — `BaseModel`, optional `model_config` |

#### Task 3: Add `ParticipationBriefDTO` to analytics schemas

| Field | Detail |
|-------|--------|
| File | `app/modules/academics/group/analytics/schemas.py` |
| Add | `ParticipationBriefDTO` |
| Shape | See [`data-model.md`](./data-model.md#participationbriefdto-analytics) — fields: `participation: GroupCompetitionParticipation`, `competition_name: str`, `team_name: str`, `category: str`, `subcategory: Optional[str]` |
| Import needed | `from app.modules.academics.models.group_level_models import GroupCompetitionParticipation` |

#### Task 4: Update 3 service methods to return typed DTOs

| Field | Detail |
|-------|--------|
| File | `app/modules/academics/group/competition/service.py` |
| Methods | 3 methods need return type + body changes |

| Method | Line | Current return | New return | Body change |
|--------|------|---------------|------------|-------------|
| `get_group_competitions()` | 123 | `list[dict]` | `list[GroupCompetitionDTO]` | Build `GroupCompetitionDTO(...)` instead of dict literal; add `session.refresh()` calls to ensure FK objects are loaded, or construct from the participation + queried data. Remove `# TODO` comment. |
| `withdraw_from_competition()` | 205 | `dict` | `WithdrawalResultDTO` | Return `WithdrawalResultDTO(id=..., status="withdrawn", withdrawn_at=...)` instead of dict literal. Remove `# TODO` comment. |
| `link_existing_team()` | 246 | `dict` | `TeamLinkResultDTO` | Return `TeamLinkResultDTO(team_id=..., team_name=..., group_id=...)` instead of dict literal. Remove `# TODO` comment. |

| Imports needed | `from app.modules.academics.group.competition.schemas import GroupCompetitionDTO, WithdrawalResultDTO, TeamLinkResultDTO` (add to existing schemas import on line 16) |
| Note | `get_group_competitions()` currently queries Competition + Team inside the loop — consider extracting to a single join query, but out of scope for this task. Minimum: wrap dict construction in DTO. |

#### Task 5: Update interface protocol signatures

| Field | Detail |
|-------|--------|
| File | `app/modules/academics/group/competition/interface.py` |
| Changes | 3 method signatures |
| `get_group_competitions()` | `-> list[dict]` → `-> list[GroupCompetitionDTO]` |
| `withdraw_from_competition()` | `-> dict` → `-> WithdrawalResultDTO` |
| `link_existing_team()` | `-> dict` → `-> TeamLinkResultDTO` |
| Imports needed | `GroupCompetitionDTO`, `WithdrawalResultDTO`, `TeamLinkResultDTO` from schemas |

#### Task 6: Update analytics repository to return typed DTOs

| Field | Detail |
|-------|--------|
| File | `app/modules/academics/group/analytics/repository.py` |
| Function | `get_group_competition_participations()` at line 291 |
| Return type | `Sequence[tuple]` → `list[ParticipationBriefDTO]` |
| Body | After `session.exec(stmt).all()`, map each row to `ParticipationBriefDTO(participation=..., competition_name=..., team_name=..., category=..., subcategory=...)` |
| Import needed | `from app.modules.academics.group.analytics.schemas import ParticipationBriefDTO` |
| ⚠️ Dependency | **Requires updating analytics service** — see Task 7 |

#### Task 7: Update analytics service to use DTO attributes

| Field | Detail |
|-------|--------|
| File | `app/modules/academics/group/analytics/service.py` |
| Location | `get_competition_history()` at line 104 |
| Current | `for participation, competition_name, team_name, category_name in participations:` |
| New | `for p in participations:` then access `p.participation`, `p.competition_name`, `p.team_name`, `p.category` |
| Total changes | ~2-3 lines in the unpacking + field accesses in `CompetitionHistoryItemDTO` construction (lines 110-121) |
| ⚠️ | This file is NOT in the original plan's "8 files" list — it is a **necessary dependency** of Task 6 |

#### Task 8: Update router endpoints to use typed DTOs

| Field | Detail |
|-------|--------|
| File | `app/api/routers/academics/group_competitions_router.py` |
| Endpoints | 3 need changes |

| Endpoint | Line | Current | New |
|----------|------|---------|-----|
| `list_group_competitions()` | 53-56 | `GroupCompetitionPublic(**p)` where `p` is dict | `GroupCompetitionPublic.model_validate(p)` where `p` is `GroupCompetitionDTO` |
| `link_team_to_group()` | 104-107 | `TeamLinkResponse(**result)` where `result` is dict | `TeamLinkResponse.model_validate(result)` where `result` is `TeamLinkResultDTO` |
| `withdraw_from_competition()` | 197-203 | `result["id"]`, `result["status"]`, `result["withdrawn_at"]` | `result.id`, `result.status`, `result.withdrawn_at` where `result` is `WithdrawalResultDTO` |

| Import changes | None needed — DTOs are constructed in the service layer, router only uses public response models |

---

### Step 3 — Auto-create participation (US1, 1 file, 1 task)

#### Task 9: Create `GroupCompetitionParticipation` in `register_team()`

| Field | Detail |
|-------|--------|
| File | `app/modules/competitions/services/team_service.py` |
| Method | `register_team()` at line 64 |
| Insert point | After team creation + member loop (after line 136), before `_log_team_registration_activity` call (line 139) |
| Code | If `cmd.group_id is not None`, create `GroupCompetitionParticipation(group_id=cmd.group_id, team_id=team.id, competition_id=cmd.competition_id, entered_at=utc_now(), is_active=True)` and `db.add()` |
| No commit | Session is committed by caller (`get_session()` context manager) |
| Imports needed | `from app.modules.academics.models.group_level_models import GroupCompetitionParticipation` (function-level import preferred, following existing pattern) |
| Imports needed | `from app.shared.datetime_utils import utc_now` (function-level or module-level) |
| Acceptance | Team registered with `group_id` → participation record exists in DB. Team registered without `group_id` → no participation record. |

---

### Step 4 — Placement sync (US2, 1 file, 1 task)

#### Task 10: Sync `final_placement` in `update_placement()`

| Field | Detail |
|-------|--------|
| File | `app/modules/competitions/services/team_service.py` |
| Method | `update_placement()` at line 326 |
| Insert point | After team placement update (after line 352, before activity logging at line 355) |
| Code | Query `GroupCompetitionParticipation` with `select(...).where(team_id == team_id, is_active == True)`, get first, and set `active.final_placement = placement_rank`. Use existing `db` session. |
| Graceful no-op | If no active participation found, skip (don't raise error) |
| Imports needed | `from app.modules.academics.models.group_level_models import GroupCompetitionParticipation` (function-level) |
| Imports needed | `from sqlalchemy import select` (function-level, if not already available via SQLModel) |

---

## Summary

| Step | Tasks | Files | US |
|------|-------|-------|----|
| 1 | Task 1 | 1 | US4 |
| 2 | Tasks 2-8 | 7 | US3 |
| 3 | Task 9 | 1 | US1 |
| 4 | Task 10 | 1 | US2 |
| **Total** | **10 tasks** | **9 files** | **4 US** |

### Gap found vs plan
- `app/modules/academics/group/analytics/service.py` is **not** in the plan's 8-file list but **must** be updated because Task 6 changes the repository return type from `Sequence[tuple]` to `list[ParticipationBriefDTO]`, breaking tuple unpacking at line 104.

## Verification

```bash
# Run existing competition tests
pytest tests/test_academics_competitions.py -v

# Run fee regression tests
pytest tests/test_competitions.py -v -k "fee"

# Run full test suite
pytest tests/ -v
```
