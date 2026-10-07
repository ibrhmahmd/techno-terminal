# Implementation Plan: Extend Employee Schemas

**Branch**: `005-extend-employee-schemas` | **Date**: 2026-05-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/005-extend-employee-schemas/spec.md`

## Summary

Add 5 optional fields (`university`, `major`, `is_graduate`, `monthly_salary`, `contract_percentage`) to the `EmployeePublic` detail response schema and 2 fields (`phone`, `email`) to the `EmployeeListItem` list response schema. All fields already exist in the `EmployeeReadDTO` internal DTO and the `Employee` ORM model — only the API-facing Pydantic schemas need updating.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, SQLModel, Pydantic v2  
**Storage**: PostgreSQL 15+  
**Testing**: pytest (TestClient)  
**Target Platform**: Linux server (Leapcell/Railway)  
**Project Type**: Web service (REST API)  
**Performance Goals**: N/A — schema-only change, no performance impact  
**Constraints**: Backward-compatible (new optional fields only)  
**Scale/Scope**: ~10 endpoints total in HR module, 2 endpoints modified

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle I (Layer Separation)**: ✅ No violations. Changes are limited to API schemas (`app/api/schemas/hr/`) — no business logic in routers, no SQL in routers, no service imports from `app.api.*`.

**Principle III (Typed Contracts)**: ✅ No new `-> dict` or loose return types. Existing DTOs already carry the needed fields.

**Principle IV (Response Envelope)**: ✅ Existing `ApiResponse` envelope unchanged.

**Principle V (Auth-Guarded Endpoints)**: ✅ Endpoints already use `require_admin` guard — unchanged.

**Result**: PASS — no constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/005-extend-employee-schemas/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (empty — no new external interfaces)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
app/
├── api/
│   ├── routers/
│   │   └── hr_router.py              # No changes needed
│   └── schemas/
│       └── hr/
│           └── employee.py            # 🔧 Add fields to EmployeePublic, EmployeeListItem

tests/
└── test_hr.py                         # 🔧 Update field assertions in existing tests
```

**Structure Decision**: Single backend project. Changes isolated to one API schema file and one test file.

## Key Technical Insight

The data pipeline already carries all needed fields:

```
DB (Employee ORM) → EmployeeReadDTO (has all fields) → EmployeePublic (drops them)
                                                      → EmployeeListItem (drops them)
```

The fix is adding the missing fields to the two API schema Pydantic models. `model_validate` uses `from_attributes=True` and matches by field name — no new query logic, DTO changes, or repository changes needed.

## Complexity Tracking

No constitution violations — section not applicable.
