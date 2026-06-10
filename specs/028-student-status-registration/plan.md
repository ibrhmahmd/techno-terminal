# Implementation Plan: Student Status Registration Bug Investigation

**Branch**: `028-student-status-registration` | **Date**: 2026-06-10 | **Spec**: `specs/028-student-status-registration/spec.md`
**Input**: Feature specification from `specs/028-student-status-registration/spec.md`

## Summary

Investigate why POST /crm/students returns an error (displayed as "not found") when registering a student with status `"waiting"`, while status `"active"` works fine. The investigation will trace the full code path from API endpoint → DTO validation → service layer → repository to identify the failure origin, then apply fixes (lowercase normalization on RegisterStudentDTO.status, ensure all three status values are accepted) and verify with targeted pytest.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: FastAPI, SQLModel, Pydantic v2, PostgreSQL, Supabase Auth  
**Storage**: PostgreSQL (pool_size=10, max_overflow=5)  
**Testing**: pytest (with mock auth tokens via tests/utils/jwt_mocks.py)  
**Target Platform**: Linux server (Leapcell, uvicorn/gunicorn)  
**Project Type**: Web service (FastAPI backend)  
**Performance Goals**: N/A — bug investigation, correctness over speed  
**Constraints**: Must not break existing registration flow for `active` status  
**Scale/Scope**: Single endpoint investigation: POST /crm/students + supporting layers

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Post-Design Re-check (Phase 1 Complete)

All constitution gates re-verified after completing research, data model analysis, and contract design:

- ✅ **Gate 1 — Layer Separation**: The `@field_validator` is on `RegisterStudentDTO` (domain schema layer). The `RegisterStudentCommandDTO` (API input) stays unaffected. No layer mixing introduced.
- ✅ **Gate 2 — Typed Contracts**: `RegisterStudentDTO.status` remains `Optional[StudentStatus]`. The validator pre-processes the raw input string before the typed field validator runs — a standard Pydantic pattern.
- ✅ **Gate 3 — Exception Mapping**: Error responses unchanged. 422 for invalid input, 201 for success.
- ✅ **Gate 4 — Dead Code**: No dead code added or removed.

**Overall: ✅ ALL GATES PASS**

### Gate 1 — Layer Separation (Constitution §I)
- ✅ **PASS**: The fix stays within existing CRM module layers. Router (`students_router.py`) → Service (`StudentCrudService.register_student`) → Repository (`StudentRepository`). No layer skipping.
- ⚠️ Watch: The `RegisterStudentDTO.status` field is defined in the domain DTO (app/modules/crm/schemas/), not in API schemas — correct. Keep it that way.

### Gate 2 — Typed Contracts (Constitution §III)
- ✅ **PASS**: `RegisterStudentDTO` is a typed Pydantic model. The `status` field uses `Optional[StudentStatus]` which is a typed enum. No bare `-> dict` in the affected code path.
- ⚠️ Note: The `register_student()` service method returns `Tuple[Student, List[dict]]` — the `List[dict]` part is flagged with a TODO in the code. This is pre-existing and not part of this investigation scope.

### Gate 3 — Exception Mapping (Constitution §IV)
- ✅ **PASS**: If the bug cause is a Pydantic validation error (e.g., case mismatch), it's caught by `RequestValidationError` handler → 422 with standard envelope. If it's a `NotFoundError` from a lookup, it's caught → 404 with standard envelope. No change needed to exception mapping.

### Gate 4 — Dead Code Discipline (Constitution §Dead Code)
- ✅ **PASS**: No dead code being introduced or migrated. The fix adds a `@field_validator` to an existing DTO — no code deletion involved.

**Overall: ✅ GATE PASSED** — No violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/028-student-status-registration/
├── plan.md              # This file
├── spec.md              # Feature specification (with clarifications applied)
├── research.md          # Phase 0 output — bug reproduction findings
├── data-model.md        # Phase 1 output — status model & validation analysis
├── quickstart.md        # Phase 1 output — how to run the reproduction test
├── contracts/           # Phase 1 output — API contract for status field
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
# Backend monorepo — this is the root structure relevant to this investigation
app/
├── api/
│   ├── routers/crm/
│   │   └── students_router.py       # POST /crm/students endpoint
│   └── schemas/crm/
│       └── student.py               # StudentPublic API response DTO
├── modules/crm/
│   ├── models/
│   │   └── student_models.py        # StudentStatus enum, Student model
│   ├── schemas/
│   │   └── student_schemas.py        # RegisterStudentDTO, RegisterStudentCommandDTO
│   ├── services/
│   │   └── student_crud_service.py   # register_student() business logic
│   └── repositories/
│       ├── student_repository.py     # DB queries
│       └── unit_of_work.py           # Transaction boundary

tests/
└── test_crm.py                       # Existing test file; new test will be added
```

**Structure Decision**: Single project (backend monorepo). This is a bug investigation confined to CRM module in `app/modules/crm/` with the relevant API entry point in `app/api/routers/crm/students_router.py`. No new directories needed.

## Complexity Tracking

*No constitution violations to justify. Table omitted.*
