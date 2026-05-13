# Implementation Plan: Review Competition Routers

**Branch**: `007-review-competition-routers` | **Date**: 2026-05-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/007-review-competition-routers/spec.md`

## Summary

Conduct a comprehensive audit of all competition-related API routers against the competitions module to verify correct endpoint-to-service mapping, DTO alignment, auth guard usage, and architectural compliance. Key deliverables: endpoint inventory, orphan router disposition, compliance report, and remediation plan.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, SQLModel, Pydantic v2  
**Storage**: PostgreSQL 15+  
**Testing**: pytest (TestClient)  
**Target Platform**: Linux server (Leapcell/Railway)  
**Project Type**: Web service (REST API) — audit/review  
**Performance Goals**: N/A — code review, no performance impact  
**Constraints**: Zero tolerance for dead code (per constitution); must not break existing 42 tests  
**Scale/Scope**: 5 router files (4 active + 1 orphan), 2 cross-module endpoints, ~30 endpoints total

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle I (Layer Separation)**: ✅ Spec mandates verification that routers contain no business logic, services don't import from `app.api.*`. No violations — audit scope aligns with enforcement.

**Principle III (Typed Contracts)**: ✅ Spec requires checking inline DTOs against module DTOs for duplication. No loose return types introduced.

**Principle IV (Response Envelope)**: ✅ No response envelope changes. Verifying existing usage.

**Principle V (Auth-Guarded Endpoints)**: ✅ Spec requires verifying that all competition endpoints use correct guards (`require_any`/`require_admin`).

**Result**: PASS — no constitution violations anticipated. Audit findings will recommend fixes if violations are discovered.

## Project Structure

### Documentation (this feature)

```text
specs/007-review-competition-routers/
├── plan.md              # This file
├── research.md          # Phase 0 output — codebase analysis
├── data-model.md        # Phase 1 output — audit entity definitions
├── quickstart.md        # Phase 1 output — how to run the audit
├── contracts/           # Phase 1 output — empty (no new interfaces)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Single project — audit changes limited to router files
app/
├── api/
│   ├── routers/
│   │   ├── competitions/
│   │   │   ├── competitions_router.py    # 🔧 Possibly migrated inline DTOs
│   │   │   └── teams_router.py           # 🔧 Possibly migrated inline DTOs
│   │   ├── academics/
│   │   │   └── group_competitions_router.py  # 🔧 Possibly migrated response models
│   │   ├── analytics/
│   │   │   └── competition.py            # 🔧 Possibly migrated response models
│   │   └── competitions_router.py        # 🗑️ Orphan — recommended for deletion
│   └── schemas/
│       └── competitions/                 # 🆕 If inline DTOs are extracted
├── modules/
│   └── competitions/
│       ├── services/
│       ├── repositories/
│       └── schemas/
tests/
├── test_competitions.py                  # ✅ 22 existing — regression safety net
└── test_academics_competitions.py         # ✅ 20 existing — regression safety net
```

**Structure Decision**: Single backend project. Changes limited to existing router files — no new source modules. All audit artifacts are documentation files under `specs/007-review-competition-routers/`.

## Complexity Tracking

No constitution violations — section not applicable.
