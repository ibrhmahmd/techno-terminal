# Implementation Plan: Competition Module Enhancements

**Branch**: `010-competition-feature-enhancements` | **Date**: 2026-05-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-competition-feature-enhancements/spec.md`
**Clarifications**: 4 decisions recorded in spec.md (2026-05-17 session) — refund auth, duplicate student warning (Option A), 30-day placement window, empty group pre-fill warning.

## Summary

Enhance the competition module with hard-delete lifecycle, enrollment-style fee tracking (amount_due/amount_paid + partial payments), team project tracking (project_name/project_description), group-as-student-source (drop GroupCompetitionParticipation), subcategory filtering, coach read-only access, and placement validation with 30-day window. All 6 user stories from P1-P3. No new module — modify existing competitions module files.

**Clarification-driven additions**:
- Refund endpoint (`POST /teams/{id}/members/{sid}/refund`) — admin-only, mirrors payment flow
- Duplicate student registration returns warning in response envelope `message` field (Option A — no two-step flow)
- Placement recording blocked if competition date > 30 days past
- Empty group pre-fill shows warning but allows manual student entry

## Technical Context

**Language/Version**: Python 3.11, FastAPI 0.110+
**Primary Dependencies**: FastAPI, SQLModel 0.14+, ReportLab, Supabase py client
**Storage**: PostgreSQL 15 (Supabase, 5+5=10 pool, sslmode=require, 30s statement timeout)
**Testing**: pytest (no CI, manual review — run `pytest tests/test_competitions.py -v`)
**Target Platform**: Linux server (Leapcell/Railpack, gunicorn + uvicorn workers)
**Project Type**: Web API service (RESTful, single-tenant school management)
**Performance Goals**: Competition lists <2s for up to 100 teams / 500 members
**Constraints**: Stateless service pattern (competitions module opens own sessions). No UoW-based session management. Atomic payment rollback required (no orphan data). Dead code removal required per constitution.
**Scale/Scope**: ~10k students, 100s of competitions/year, single PostgreSQL instance

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| **§I Router → Service → Repository** | ✅ PASS | All three layers preserved. No layer skipping. No service import from `app.api.*`. |
| **§II Module Organization** | ✅ PASS | Competitions has ≤2 entities (Competition, Team+TeamMember) — flat horizontal layer (Pattern A). No D+ Hybrid needed. |
| **§III Typed Contracts** | ⚠️ PEDANTIC | Pre-existing `dict` return in `CategoryInfoDTO.__init__` (see AGENTS.md gotcha). NEW code must use proper DTOs. Duplicate student warning uses existing `message` field — no new DTO needed. |
| **§IV Response Envelope** | ✅ PASS | All endpoints already use `ApiResponse` envelope. Warning pattern (Option A) populates `message` field alongside `data`. |
| **§V Auth-Guarded Endpoints** | ✅ PASS | All endpoints gated by `require_any` (read) or `require_admin` (write). Refunds and placements are admin-only. Coach read-only needs new guard. |
| **Session Lifecycle (Stateless)** | ✅ PASS | Competitions is stateless — services open own sessions via `get_session()`. No change. |
| **Dead Code Discipline** | ✅ PASS | Must remove: `GroupCompetitionParticipation` model/slice, restore/list-deleted endpoints, soft-delete repos. |

**Complexity Tracking**: (none — no constitution violations to justify)

**Re-check after Phase 1 design**: Verified phase 1 generates `data-model.md` and validates §III typed contracts.

## Project Structure

### Documentation (this feature)

```text
specs/010-competition-feature-enhancements/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (contract overview, not generated code)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
# Existing files being modified (no new structure needed)
app/modules/competitions/
├── models/
│   ├── competition_models.py    # Remove deleted_at, deleted_by
│   └── team_models.py           # Add project_name, project_description, amount_due, amount_paid; remove fee_paid, payment_id
├── repositories/
│   ├── competition_repository.py  # Hard delete; remove soft delete, restore, list_deleted
│   └── team_repository.py         # Hard delete; remove soft delete, restore, list_deleted; new payment methods; duplicate student check
├── services/
│   ├── competition_service.py     # Hard delete; remove restore, list_deleted
│   └── team_service.py            # Multi-payment model; remove GroupCompetitionParticipation; project fields; duplicate student warning; 30-day placement validation; refund flow
└── schemas/
    ├── competition_schemas.py     # No change (CompetitionDTO already omits deleted_at/deleted_by)
    └── team_schemas.py            # New DTO fields for project_name, project_description, amount_due, amount_paid

app/modules/finance/models/payment.py  # Add team_member_id FK

app/api/
├── schemas/competitions/
│   ├── competition_schemas.py     # No structural change
│   └── team_schemas.py            # Update UpdateTeamInput with new fields
├── routers/competitions/
│   ├── competitions_router.py     # Remove restore; hard delete
│   └── teams_router.py            # Remove restore; hard delete; update payment; add refund endpoint; coach read-only; duplicate student warning in response
├── main.py                        # Remove group_competitions_router registration
└── dependencies.py                # Add require_coach_or_admin (or inline)

app/modules/academics/
├── models/group_level_models.py   # Remove GroupCompetitionParticipation
├── group/competition/              # Remove entire slice (service, repository, interface)
└── group/analytics/repository.py  # Update query removing GroupCompetitionParticipation

tests/
├── test_competitions.py           # Update for hard delete, new payment model, duplicate student warning, 30-day placement window, refund flow
└── test_academics_competitions.py # Update/remove for GroupCompetitionParticipation removal

db/migrations/
└── 054_competition_hard_delete_and_payment_model.sql  # New migration
```

**Structure Decision**: Single project modification — no new directories or modules. All changes are in-place edits to existing files within the existing module structure.

## Clarification-Driven Implementation Notes

### 1. Duplicate Student Registration Warning (Option A)

**Flow**: `POST /api/v1/teams/{team_id}/members` always succeeds if student is valid, but returns a warning in the `message` field if the student is already registered in another team for the same competition.

**Service layer**: `add_team_member_to_existing()` returns `(result, warning_message_or_none)`. The router checks for the warning and populates the envelope.

**No additional endpoints** — single request, no two-step confirmation flow.

### 2. 30-Day Placement Window

**Validation**: `validate_placement_window(competition_date)` returns `True` if `today <= competition_date + 30 days`. Two error conditions:
- Future date → "Cannot record placement for a competition that has not yet occurred."
- Window expired → "Placement recording window closed. Placements must be recorded within 30 days of the competition date."

**Both return 409** with `BusinessRuleError`.

### 3. Refund Endpoint (Admin-Only)

**New endpoint**: `POST /api/v1/teams/{team_id}/members/{student_id}/refund`
**Body**: `{ "amount": float }` — refund amount (must be <= current `amount_paid`)
**Flow**: Create refund receipt via FinanceUnitOfWork → `refund_payment()` repo → update payment row with `original_payment_id` → log activity → commit. Atomic rollback on failure.
**Auth**: `require_admin` — same as payments.

### 4. Empty Group Pre-Fill Warning

**Flow**: When `group_id` is provided in `RegisterTeamInput` but the group has zero active students, the service returns a warning in the `message` field. Team creation proceeds if at least one student is provided via `student_ids`.

## Complexity Tracking

> *Empty — all constitution gates pass with no violations.*
