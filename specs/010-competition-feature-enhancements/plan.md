# Implementation Plan: Competition Module Bug Fixes

**Branch**: `010-competition-feature-enhancements` | **Date**: 2026-05-17 | **Spec**: [spec.md](./spec.md)
**Input**: Bug report from audit (`bug-report.md`) — 8 open bugs identified across competition module.

## Summary

Fix 8 bugs identified in the comprehensive audit of the competition module. Two CRITICAL (payment atomicity gap, non-existent field references), two HIGH (duplicate student hard-block, 30-day placement window), two MEDIUM (TOCTOU race, kwargs injection), two LOW (dead code). All fixes are in-place edits to existing files. No new endpoints or schema changes required.

## Technical Context

**Language/Version**: Python 3.11, FastAPI 0.110+
**Primary Dependencies**: FastAPI, SQLModel 0.14+, Supabase py client
**Storage**: PostgreSQL 15 (Supabase, 5+5=10 pool, sslmode=require, 30s statement timeout)
**Testing**: pytest (run `pytest tests/test_competitions.py -v`)
**Target Platform**: Linux server (Leapcell/Railpack, gunicorn + uvicorn workers)
**Project Type**: Web API service (RESTful, single-tenant school management)
**Performance Goals**: Competition lists <2s for up to 100 teams / 500 members (already achieved via N+1 fixes)
**Constraints**: Stateless service pattern (competitions module opens own sessions). No UoW-based session management. Dead code removal required per constitution.
**Scale/Scope**: ~10k students, 100s of competitions/year, single PostgreSQL instance

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| **§I Router → Service → Repository** | ✅ PASS | Bug fixes stay within existing layer boundaries. No new layer skipping. |
| **§II Module Organization** | ✅ PASS | All fixes are in existing competition module files. No new slices. |
| **§III Typed Contracts** | ✅ PASS | No new loose return types introduced. Bug B1 fix removes broken field references. |
| **§IV Response Envelope** | ✅ PASS | B3 fix uses existing `message` field for warnings. No new envelope structure. |
| **§V Auth-Guarded Endpoints** | ✅ PASS | B5 fix improves existing guard, no new auth bypass. |
| **Session Lifecycle (Stateless)** | ⚠️ VIOLATION | B2 fix requires consolidating 3 transactions into 1 — may require cross-module coordination with finance. Justified below. |
| **Dead Code Discipline** | ✅ PASS | B7/B8 fixes remove dead code per constitution requirement. |

**Complexity Tracking**:

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| B2: Single-transaction payment | FR-023 requires atomicity; current 3-transaction pattern violates spec | Compensating rollback is not atomic — refund can fail, creating orphan data |

**Re-check after Phase 1 design**: Verified B2 fix design does not introduce new constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/010-competition-feature-enhancements/
├── plan.md              # This file
├── bug-report.md        # Bug inventory (source of this plan)
├── audit-report.md      # Full audit with diagrams
└── tasks.md             # Task list (updated with bug fix tasks)
```

### Source Code (repository root)

```text
app/modules/finance/services/receipt_service.py     # B1: Fix _link_competition_payment
app/modules/competitions/services/team_service.py   # B2: Fix payment atomicity
                                                     # B3: Fix duplicate student warning
                                                     # B4: Fix 30-day placement window
app/modules/competitions/repositories/team_repository.py  # B7: Remove dead code
                                                          # B8: Remove dead fee parameter
app/api/dependencies.py                              # B5: Fix TOCTOU race
app/modules/competitions/services/competition_service.py  # B6: Add kwargs whitelist
app/modules/competitions/repositories/competition_repository.py  # B6: Add kwargs whitelist
tests/test_competitions.py                           # Tests for all bug fixes
```

**Structure Decision**: Single project modification — all fixes are in-place edits to existing files within the existing module structure. No new directories or modules.

## Complexity Tracking

> See Constitution Check table above. Only B2 (payment atomicity) requires cross-module coordination.
