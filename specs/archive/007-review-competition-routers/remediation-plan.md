# Remediation Plan: Competition Routers Audit

**Created**: 2026-05-13  
**Source**: [audit-findings.md](audit-findings.md)

## Prioritized Action Items

### P1 — Must Fix (HIGH Severity)

| ID | Finding | Effort | Action | Verification |
|----|---------|--------|--------|-------------|
| R-001 | F-001: Orphan router deleted | ✅ Done | File removed at `app/api/routers/competitions_router.py` | ✅ No regressions in main.py (was never imported) |

### P2 — Should Fix (MEDIUM Severity)

| ID | Finding | Effort | Action | Verification |
|----|---------|--------|--------|-------------|
| R-002 | F-002: `GroupCompetitionService` returns `dict`/`list[dict]` | ✅ Done | Typed DTOs created: `GroupCompetitionDTO`, `WithdrawalResultDTO`, `TeamLinkResultDTO` in `app/modules/academics/group/competition/schemas.py`. Return types and router access patterns updated. | `pytest tests/test_academics_competitions.py -v` |
| R-003 | F-003: Session pattern inconsistency | ✅ Done | Changed `get_group_competition_service()` in `app/api/dependencies.py` to stateless pattern (no `get_db()` dependency). | Code review |

### P3 — Nice to Fix (LOW Severity)

| ID | Finding | Effort | Action | Verification |
|----|---------|--------|--------|-------------|
| R-004 | F-004: Inline DTOs in routers | ✅ Done | Extracted to `app/api/schemas/competitions/competition_schemas.py` and `team_schemas.py`. Routers updated to import from new location. | Code review |
| R-005 | F-005: `model_dump()` in summary endpoint | ✅ Done | Replaced `cat.model_dump()` with typed `summary.categories` in `competitions_router.py:253` | Response schema validation |
| R-006 | F-006: Inefficient team name fetch | ✅ Done | Added `team_id`, `team_name` to `TeamMemberRosterDTO`. Service populates it; router uses `members[0].team_name` — no extra DB query. | Code review |
| R-007 | F-007: `ValueError` instead of domain exception | ✅ Done | Replaced all `ValueError` raises in `GroupCompetitionService` with `NotFoundError`, `ConflictError`, `BusinessRuleError`. Removed try/except ValueError in router. | Code review |
| R-008 | F-008: JWT token expiry | ✅ Done | Added `mock_admin_token`, `mock_admin_headers`, `override_auth` fixtures in `tests/conftest.py`. Tests can now bypass real Supabase auth using `override_auth`. | `pytest tests/ -v` |

## Effort Estimate

| Priority | Items | Est. Effort |
|----------|-------|-------------|
| P1 | 1 | ✅ Complete |
| P2 | 2 | ✅ Complete |
| P3 | 5 | ✅ Complete |
| **Total** | **8** | **✅ Complete (all 8 items implemented)** |
