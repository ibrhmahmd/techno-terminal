# Implementation Plan: Group Competition Participation Fixes

**Branch**: `003-group-competition-participation` | **Date**: 2026-05-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-group-competition-participation/spec.md`

## Summary

Fix 4 bugs in group competition participation tracking: (1) auto-create participation record when team is registered with `group_id`, (2) sync `teams.placement_rank` to `group_competition_participation.final_placement`, (3) replace 3 `list[dict]`/`dict` return types with typed DTOs, (4) replace `datetime.utcnow()` with shared `utc_now()`.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, SQLModel, Pydantic, SQLAlchemy
**Storage**: PostgreSQL via SQLModel ORM
**Testing**: pytest with TestClient integration tests
**Target Platform**: Linux server (Leapcell), Gunicorn + Uvicorn
**Project Type**: Web service (REST API)
**Performance Goals**: N/A — logic-only changes, no new endpoints
**Constraints**: Must preserve all existing API contracts; zero regression for group competition endpoints
**Scale/Scope**: ~8 files modified, no new migrations, no schema changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Status |
|-----------|-----------|--------|
| I. Layer Separation | Auto-create + placement sync added to `TeamService` (Service layer), typed DTOs added to `GroupCompetitionService`. Repository untouched for new features. No layer skipping. | PASS |
| II. Module Organization | Changes stay within existing `academics/group/competition/` slice + `competitions/` module. No new slices. | PASS |
| III. Typed Contracts | Replacing 3 `list[dict]`/`dict` return types with typed DTOs directly rectifies a constitution violation. New DTOs follow `{Entity}DTO` naming. | PASS |
| IV. Response Envelope | No new endpoint or exception types. Existing envelope unchanged. | PASS |
| V. Auth-Guarded Endpoints | Existing guards (`require_any`, `require_admin`) unchanged. | PASS |
| Dead Code Discipline | No dead code introduced. Removing TODO tech debt. | PASS |
| UoW Rollback | Academics uses stateless pattern (`get_session()`). Competitions also stateless. No UoW interaction in changed code. | PASS |

**Result**: All gates pass. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/003-group-competition-participation/
├── plan.md               # This file
├── research.md           # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/            # Phase 1 output (N/A — no new endpoints)
├── checklists/
│   └── requirements.md   # Spec quality checklist
├── spec.md               # Feature specification
└── tasks.md              # Phase 2 output (task breakdown)
```

### Source Code (repository root)

**Structure Decision**: Single-project backend. Changes follow existing module layout.

### Files requiring modification (8 files)

| File | Change |
|------|--------|
| `app/modules/competitions/services/team_service.py` | US1: create `GroupCompetitionParticipation` in `register_team()` when `group_id` provided. US2: sync `final_placement` in `update_placement()`. |
| `app/modules/academics/group/competition/service.py` | US3: return typed DTOs from `get_group_competitions()`, `withdraw_from_competition()`, `link_existing_team()` |
| `app/modules/academics/group/competition/repository.py` | US4: replace `datetime.utcnow()` with `utc_now()` in `complete_participation()` |
| `app/modules/academics/group/competition/schemas.py` | US3: add `GroupCompetitionDTO`, `WithdrawalResultDTO`, `TeamLinkResultDTO` |
| `app/modules/academics/group/competition/interface.py` | US3: update protocol signatures to match new return types |
| `app/api/routers/academics/group_competitions_router.py` | US3: update 3 endpoints that unpack dict results to use typed DTOs |
| `app/modules/academics/group/analytics/repository.py` | US3: return typed DTOs from `get_group_competition_participations()` (currently returns raw tuples) |
| `app/modules/academics/group/analytics/schemas.py` | US3: add participation tuple type if needed |

### Files NOT modified (confirmed zero impact)

| File | Why |
|------|-----|
| `app/modules/competitions/models/team_models.py` | `group_id` field already exists on `TeamBase` |
| `app/modules/academics/models/group_level_models.py` | `GroupCompetitionParticipation` model already complete |
| `db/schema/07_tables_competitions.sql` | Schema already has `group_competition_participation` table |
| `app/api/schemas/academics/competition.py` | Public DTOs stay — used only as response models, not affected by service return types |
| `app/api/dependencies.py` | `get_group_competition_service()` factory unchanged |
| `tests/test_academics_competitions.py` | Update if tests reference dict return values |

## Complexity Tracking

No constitution violations to justify.
