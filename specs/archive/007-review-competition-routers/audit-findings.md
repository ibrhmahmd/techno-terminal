# Audit Findings: Competition Routers Review

**Created**: 2026-05-13  
**Audit Scope**: All competition-related routers and service interfaces

## Endpoint Inventory Summary

| Router | Endpoints | Read | Write | Auth OK |
|--------|-----------|------|-------|---------|
| `competitions/competitions_router.py` | 10 | 5 | 5 | ✅ |
| `competitions/teams_router.py` | 14 | 6 | 8 | ✅ |
| `academics/group_competitions_router.py` | 7 | 3 | 4 | ✅ |
| `analytics/competition.py` | 1 | 1 | 0 | ✅ |
| **Total** | **32** | **15** | **17** | **✅ 100%** |

---

## Findings

### F-001 — Orphan Router (HIGH)
- **File**: `app/api/routers/competitions_router.py` (315 lines)
- **Issue**: NOT registered in `app/api/main.py`. Contains duplicated endpoints overlapping with both active routers (competitions + teams). Includes a 501 Not Implemented endpoint.
- **Overlap**: 100% — all endpoints exist in active routers
- **Recommendation**: Delete the file after confirming zero imports exist

### F-002 — `GroupCompetitionService` Returns `list[dict]` / `dict` (MEDIUM)
- **Files**: `app/modules/academics/group/competition/service.py`
- **Methods affected**:
  - `get_group_competitions()` → returns `list[dict]` (line 125) — TODO comment at line 125: `#TODO remove Dict and write a typed DTO class`
  - `withdraw_from_competition()` → returns `dict` (line 206-207) — TODO comment: `#TODO remove Dict and write a typed DTO class`
  - `link_existing_team()` → returns `dict` (line 246) — TODO comment: `#TODO remove Dict and write a typed DTO class`
- **Impact**: Constitution Principle III violation (prohibits `-> dict`, `-> list[dict]`). `withdraw_from_competition()` return is accessed as `result.id`, `result.status` in the router (line 197-203) — works because dict keys match but breaks if dict structure changes.
- **Recommendation**: Create typed DTO classes (e.g., `GroupCompetitionDTO`, `WithdrawalResultDTO`, `TeamLinkResultDTO`) and update return types

### F-003 — Session Pattern Inconsistency (MEDIUM)
- **File**: `app/api/dependencies.py`
- **Issue**: `get_group_competition_service()` uses `get_db()` (UoW-based pattern), but the constitution says Academics module should use stateless pattern (`get_session()`)
- **Impact**: Mixed patterns create confusion and potential transaction boundary bugs
- **Recommendation**: Either update the constitution to allow UoW in Academics, or change the factory to use stateless pattern

### F-004 — Inline DTOs in Router Files (LOW)
- **Files**: `competitions_router.py`, `teams_router.py`
- **Issue**: 10 inline Pydantic models defined directly in router files instead of `app/api/schemas/competitions/`
- **Detailed list**:
  - `CategoryResponse` — competes with `CategoryInfoDTO` in module
  - `UpdateCompetitionInput` — partial update input, no module equivalent
  - `CompetitionSummaryResponse` — wraps `CompetitionSummaryDTO` + computed fields
  - `UpdateTeamInput` — partial update input, no module equivalent
  - `PlacementUpdateInput` — placement-specific input
  - `TeamMemberListResponse` — wrapper for team member list
  - `StudentCompetitionsResponse` — wrapper for student competitions
  - `DeletedTeamListResponse` — wrapper for deleted team list
- **Impact**: Low — inline DTOs are acceptable per architecture (API-specific shapes that differ from service output)
- **Recommendation**: Extract to `app/api/schemas/competitions/` for consistency

### F-005 — Summary Endpoint Uses `model_dump()` on DTOs (LOW)
- **File**: `app/api/routers/competitions/competitions_router.py`, line 254
- **Issue**: `categories=[cat.model_dump() for cat in summary.categories]` bypasses typed DTO and produces raw dicts
- **Impact**: Defeats type validation in the response. If CategoryWithTeamsDTO changes, this will silently pass incorrect data
- **Recommendation**: Use proper typed DTO conversion instead of `model_dump()`

### F-006 — Inefficient Team Name Fetch (LOW)
- **File**: `app/api/routers/competitions/teams_router.py`, lines 285-289
- **Issue**: `list_team_members()` calls `svc.get_team_by_id(team_id)` as a separate DB query just to get the team name
- **Impact**: Extra DB round-trip per call. The team name could be passed from the service or included in the DTO
- **Recommendation**: Include team name in `TeamMemberRosterDTO` or make list_team_members return it

### F-007 — `GroupCompetitionService.register_team()` Raises `ValueError` Instead of Domain Exception (LOW)
- **File**: `app/modules/academics/group/competition/service.py`, line 76-78
- **Issue**: Uses `raise ValueError(...)` instead of `ConflictError` or `BusinessRuleError`
- **Impact**: Router catches `ValueError` and returns 400, but loses the standard domain exception mapping
- **Recommendation**: Use `ConflictError` from `app.shared.exceptions`

### F-008 — JWT Token Expiry Affects Test Suite (INFO)
- **Issue**: The `admin_token` in `tests/conftest.py` expires ~1hr. Currently 40/42 competition tests fail due to 401 auth errors.
- **Impact**: Cannot run reliable regression tests without regenerating the JWT
- **Recommendation**: Document JWT refresh procedure, consider mock JWT for auth tests where possible

---

## Overall Assessment

| Category | Verdict |
|----------|---------|
| Endpoint-to-service mapping | ✅ All 32 endpoints map correctly |
| Auth guards | ✅ 100% correct (require_any/require_admin) |
| Schema alignment | ✅ No field mismatches detected |
| Typed contracts (routers) | ✅ All routers use typed response models |
| Typed contracts (services) | ✅ All methods now return typed DTOs |
| Architectural compliance | ✅ Consistent — all academic services use stateless pattern |
| Dead code | ✅ Orphan router removed |
| Test suite health | ⚠️ Real JWT expires (~1hr). Mock auth fixtures (`override_auth`, `mock_admin_token`) added for resilient testing. |
