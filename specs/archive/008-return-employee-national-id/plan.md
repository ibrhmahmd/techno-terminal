# Implementation Plan: Return Employee National ID

**Branch**: `008-return-employee-national-id` | **Date**: 2026-05-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/008-return-employee-national-id/spec.md`

## Summary

Add `national_id` field to the `EmployeePublic` API schema so the `GET /hr/employees/:id` detail endpoint returns the employee's national ID. The field already exists in the `EmployeeReadDTO` internal DTO and `Employee` ORM model — only the API-facing Pydantic schema needs updating.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, SQLModel, Pydantic v2  
**Storage**: PostgreSQL 15+  
**Testing**: pytest (TestClient)  
**Target Platform**: Linux server (Leapcell/Railway)  
**Project Type**: Web service (REST API)  
**Performance Goals**: N/A — schema-only change, no performance impact  
**Constraints**: Backward-compatible (new optional field only)  
**Scale/Scope**: Single field addition in one file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle I (Layer Separation)**: ✅ Change is limited to API schema (`app/api/schemas/hr/`) — no business logic in routers, no SQL in routers.

**Principle III (Typed Contracts)**: ✅ Using typed `Optional[str]` — no bare dict/list/tuple returns. `model_config` already has `from_attributes=True`.

**Principle IV (Response Envelope)**: ✅ Existing `ApiResponse` envelope unchanged.

**Principle V (Auth-Guarded Endpoints)**: ✅ Endpoint already uses `require_admin` guard — unchanged.

**Result**: PASS — no constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/008-return-employee-national-id/
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
│   └── schemas/
│       └── hr/
│           └── employee.py            # 🔧 Add national_id to EmployeePublic

tests/
└── test_hr.py                         # 🔧 Add national_id assertion to test_get_employee_success
```

**Structure Decision**: Single backend project. Changes isolated to one API schema file and one test file.

## Key Technical Insight

The data pipeline already carries `national_id`:

```
DB (Employee ORM has national_id) → EmployeeReadDTO (has national_id) → EmployeePublic (missing national_id)
```

The fix is adding `national_id: str` to `EmployeePublic`. `model_validate` uses `from_attributes=True` and matches by field name — no new query logic, DTO changes, or repository changes needed.

## Complexity Tracking

No constitution violations — section not applicable.
