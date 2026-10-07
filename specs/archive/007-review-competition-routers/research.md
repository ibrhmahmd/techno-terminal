# Research: Review Competition Routers

**Created**: 2026-05-13  
**Input**: spec.md, constitution.md

## Summary

Comprehensive codebase exploration to understand the current state of competition routers, modules, and services. All NEEDS CLARIFICATION markers resolved through direct code inspection.

---

## 1. Active Router Inventory

### 1.1 `app/api/routers/competitions/competitions_router.py`
- **Tag**: `Competitions`
- **Package**: `app.api.routers.competitions` (re-exported as `competitions_router`)
- **Endpoints**: 10 (5 read, 5 write)

| # | Method | Path | Auth | Service | Input DTO | Output DTO |
|---|--------|------|------|---------|-----------|------------|
| 1 | GET | `/competitions` | `require_any` | `svc.list_competitions(include_deleted)` | Query param | `ApiResponse[list[CompetitionDTO]]` |
| 2 | POST | `/competitions` | `require_admin` | `svc.create_competition(body)` | `CreateCompetitionInput` | `ApiResponse[CompetitionDTO]` |
| 3 | GET | `/competitions/deleted` | `require_admin` | `svc.list_deleted_competitions()` | — | `ApiResponse[list[CompetitionDTO]]` |
| 4 | GET | `/competitions/{competition_id}` | `require_any` | `svc.get_competition_by_id(competition_id)` | Path param | `ApiResponse[CompetitionDTO]` |
| 5 | PUT | `/competitions/{competition_id}` | `require_admin` | `svc.update_competition(competition_id, **update_data)` | `UpdateCompetitionInput` (inline) | `ApiResponse[CompetitionDTO]` |
| 6 | PATCH | `/competitions/{competition_id}` | `require_admin` | Delegates to PUT | `UpdateCompetitionInput` (inline) | `ApiResponse[CompetitionDTO]` |
| 7 | DELETE | `/competitions/{competition_id}` | `require_admin` | `svc.delete_competition(competition_id, deleted_by=current_user.id)` | Path param | `ApiResponse[bool]` |
| 8 | POST | `/competitions/{competition_id}/restore` | `require_admin` | `svc.restore_competition(competition_id)` | Path param | `ApiResponse[bool]` |
| 9 | GET | `/competitions/{competition_id}/summary` | `require_any` | `svc.get_competition_summary(competition_id)` | Path param | `ApiResponse[CompetitionSummaryResponse]` (inline) |
| 10 | GET | `/competitions/{competition_id}/categories` | `require_any` | `svc.list_categories(competition_id)` | Path param | `ApiResponse[list[CategoryResponse]]` (inline) |

### 1.2 `app/api/routers/competitions/teams_router.py`
- **Tag**: `Teams`
- **Package**: `app.api.routers.competitions` (re-exported as `teams_router`)
- **Endpoints**: 14 (6 read, 8 write)

| # | Method | Path | Auth | Service | Input DTO | Output DTO |
|---|--------|------|------|---------|-----------|------------|
| 1 | GET | `/teams` | `require_any` | `svc.get_teams_with_members()` or `list_teams()` | Query params | `ApiResponse[list[TeamWithMembersDTO]]` |
| 2 | POST | `/teams` | `require_admin` | `svc.register_team(body, current_user_id)` | `RegisterTeamInput` | `ApiResponse[TeamRegistrationResultDTO]` |
| 3 | GET | `/teams/{team_id}` | `require_any` | `svc.get_team_by_id(team_id)` | Path param | `ApiResponse[TeamDTO]` |
| 4 | PUT | `/teams/{team_id}` | `require_admin` | `svc.update_team(team_id, **update_data)` | `UpdateTeamInput` (inline) | `ApiResponse[TeamDTO]` |
| 5 | PATCH | `/teams/{team_id}` | `require_admin` | Delegates to PUT | `UpdateTeamInput` (inline) | `ApiResponse[TeamDTO]` |
| 6 | DELETE | `/teams/{team_id}` | `require_admin` | `svc.delete_team(team_id, deleted_by)` | Path param | `ApiResponse[bool]` |
| 7 | POST | `/teams/{team_id}/restore` | `require_admin` | `svc.restore_team(team_id)` | Path param | `ApiResponse[bool]` |
| 8 | GET | `/teams/deleted` | `require_admin` | `svc.list_deleted_teams(competition_id)` | Query param | `ApiResponse[DeletedTeamListResponse]` (inline) |
| 9 | GET | `/teams/{team_id}/members` | `require_any` | `svc.list_team_members(team_id)` | Path param | `ApiResponse[TeamMemberListResponse]` (inline) |
| 10 | POST | `/teams/{team_id}/members` | `require_admin` | `svc.add_team_member_to_existing(team_id, student_id, fee, current_user_id)` | `AddTeamMemberInput` | `ApiResponse[AddTeamMemberResultDTO]` |
| 11 | DELETE | `/teams/{team_id}/members/{student_id}` | `require_admin` | `svc.remove_team_member(team_id, student_id)` | Path params | `ApiResponse[bool]` |
| 12 | POST | `/teams/{team_id}/members/{student_id}/pay` | `require_admin` | `svc.pay_competition_fee(cmd)` | Query param + path params | `ApiResponse[PayCompetitionFeeResponseDTO]` |
| 13 | PATCH | `/teams/{team_id}/placement` | `require_admin` | `svc.update_placement(team_id, placement_rank, placement_label, current_user_id)` | `PlacementUpdateInput` (inline) | `ApiResponse[TeamDTO]` |
| 14 | GET | `/students/{student_id}/competitions` | `require_any` | `svc.get_student_competitions(student_id)` | Path param | `ApiResponse[StudentCompetitionsResponse]` (inline) |

### 1.3 `app/api/routers/academics/group_competitions_router.py`
- **Tag**: `Academics -- Group Competitions`
- **Endpoints**: 7 (3 read, 4 write)

| # | Method | Path | Auth | Service | Input DTO | Output DTO |
|---|--------|------|------|---------|-----------|------------|
| 1 | GET | `/academics/groups/{group_id}/competitions` | `require_any` | `svc.get_group_competitions(group_id, is_active)` | Query param | `ApiResponse[list[GroupCompetitionPublic]]` |
| 2 | GET | `/academics/groups/{group_id}/teams` | `require_any` | `svc.get_teams_by_group(group_id, include_inactive, skip, limit)` | Query params | `PaginatedResponse[TeamPublic]` |
| 3 | POST | `/academics/groups/{group_id}/teams/{team_id}/link` | `require_admin` | `svc.link_existing_team(group_id, team_id)` | Path params | `ApiResponse[TeamLinkResponse]` |
| 4 | POST | `/academics/groups/{group_id}/competitions/{competition_id}/register` | `require_admin` | `svc.register_team(group_id, team_id, competition_id)` | Query: team_id | `ApiResponse[CompetitionRegistrationResponse]` |
| 5 | PATCH | `/academics/groups/{group_id}/competitions/{participation_id}/complete` | `require_admin` | `svc.complete_participation(participation_id, final_placement)` | Query param | `ApiResponse[CompetitionCompletionResponse]` |
| 6 | DELETE | `/academics/groups/{group_id}/competitions/{participation_id}` | `require_admin` | `svc.withdraw_from_competition(participation_id, reason)` | Query param | `ApiResponse[CompetitionWithdrawalResponse]` |
| 7 | GET | `/academics/groups/{group_id}/competitions/analytics` | `require_any` | `svc.get_competition_history(group_id)` | Path param | `ApiResponse[GroupCompetitionHistoryResponseDTO]` |

### 1.4 `app/api/routers/analytics/competition.py`
- **Tag**: `Analytics -- Competition`
- **Endpoints**: 1

| # | Method | Path | Auth | Service | Input DTO | Output DTO |
|---|--------|------|------|---------|-----------|------------|
| 1 | GET | `/analytics/competitions/fee-summary` | `require_admin` | `svc.get_competition_fee_summary()` | — | `ApiResponse[list[CompetitionFeeSummaryDTO]]` |

---

## 2. Orphan Router Assessment

**File**: `app/api/routers/competitions_router.py` (315 lines)
**Status**: NOT registered in `app/api/main.py`
**Disposition**: Recommend deletion

### Endpoints defined (all orphaned):
| Endpoint | Overlap with active |
|----------|-------------------|
| GET `/competitions` | ✅ Duplicates `competitions_router.py` endpoint |
| POST `/competitions` | ✅ Duplicates `competitions_router.py` endpoint |
| GET `/competitions/deleted` | ✅ Duplicates `competitions_router.py` endpoint |
| GET `/competitions/{competition_id}` | ✅ Duplicates `competitions_router.py` endpoint |
| GET `/competitions/{competition_id}/categories` | ✅ Duplicates `competitions_router.py` endpoint |
| POST `/competitions/{competition_id}/teams` | 🔄 Uses different path pattern — active uses `/teams` (flat) |
| GET `/competitions/{competition_id}/teams` | 🔄 Uses nested path — active uses `/teams?competition_id=` |
| GET `/teams/{team_id}` | ✅ Returns 501 Not Implemented — dead code |
| PATCH `/teams/{team_id}/placement` | ✅ Duplicates `teams_router.py` endpoint |
| DELETE `/teams/{team_id}` | ✅ Duplicates `teams_router.py` endpoint |
| POST `/teams/{team_id}/restore` | ✅ Duplicates `teams_router.py` endpoint |
| POST `/competitions/{competition_id}/teams/{team_id}/members/{student_id}/pay` | 🔄 Different path — active uses `/teams/{team_id}/members/{student_id}/pay` |
| DELETE `/competitions/{competition_id}` | ✅ Duplicates `competitions_router.py` endpoint |
| POST `/competitions/{competition_id}/restore` | ✅ Duplicates `competitions_router.py` endpoint |

**Conclusion**: 100% overlap with active routers. Orphan uses alternative path structures (nested under `/competitions/{id}/teams/` vs. flat `/teams/`). No unique functionality. Safe to delete.

---

## 3. Architectural Compliance Analysis

### 3.1 Layer Separation (Principle I)
- **Routers with business logic**: None identified — all routers delegate to services
- **Services importing from `app.api.*`**: None identified
- **Repositories with business rules**: None identified
- **Inline DTOs in routers**: Found in `competitions_router.py` (`CategoryResponse`, `UpdateCompetitionInput`, `CompetitionSummaryResponse`) and `teams_router.py` (`UpdateTeamInput`, `PlacementUpdateInput`, `TeamMemberListResponse`, `StudentCompetitionsResponse`, `DeletedTeamListResponse`)

### 3.2 Session Lifecycle Pattern
- **Competitions module** (competitions_router, teams_router): Uses stateless pattern ✅
- **Group competitions** (group_competitions_router): `get_group_competition_service()` uses `get_db()` (UoW-based) — this is in the Academics module which the constitution says should be stateless ⚠️ **INCONSISTENCY**
- **Analytics competition** (competition.py): Uses stateless pattern ✅

### 3.3 Auth Guards
- All read endpoints use `require_any` ✅
- All write endpoints use `require_admin` ✅
- No unauthenticated competition endpoints ✅

### 3.4 Dead Code
- `app/api/routers/competitions_router.py` (315 lines) — orphan, not registered ⚠️ **DEAD CODE**

---

## 4. Cross-Module Competition Endpoints

### CRM (`app/api/routers/crm/students_history_router.py`)
- `GET /students/{student_id}/competition-history`
- Uses `StudentActivityService.get_competition_history()`
- Returns `PaginatedResponse[CompetitionHistoryEntry]` from `app.api.schemas.crm.activity`
- **Verdict**: Correctly references competition data through CRM service

### Finance (`app/api/routers/finance/finance_router.py`)
- `GET /finance/competition-fees`
- Uses `ReportingService.get_unpaid_competition_fees()`
- Returns `ApiResponse[list[UnpaidCompFeeItem]]`
- **Verdict**: Correctly references competition fee data through Finance service

---

## 5. Key Findings Summary

| # | Finding | Severity | Location | Recommendation |
|---|---------|----------|----------|---------------|
| F1 | Orphan router — 315 lines, not registered | HIGH | `app/api/routers/competitions_router.py` | Delete the file |
| F2 | Session pattern inconsistency — Acdademics module uses UoW per constitution, but `get_group_competition_service` uses UoW | MEDIUM | `app/api/dependencies.py` (factory) | Either update constitution (Academics allows UoW) or change factory to stateless |
| F3 | Inline DTOs duplicate or could be extracted | LOW | `competitions_router.py`, `teams_router.py` | Extract to `app/api/schemas/competitions/` |
| F4 | Group comp router uses API schemas from `app.api.schemas.academics.*` | INFO | `group_competitions_router.py` | Valid per Two-Layer Schema Rule — API schemas belong at router layer |
