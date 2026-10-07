# Implementation Plan: Group Level Management

**Branch**: `037-group-level-management` | **Date**: 2026-07-10 | **Spec**: `specs/037-group-level-management/spec.md`
**Input**: Feature specification from `specs/037-group-level-management/spec.md`

## Summary

This feature adds support for hard-deleting the latest group level (Feature A) to undo accidental level progressions, adds support for updating active group levels (Feature B), and resolves 5 runtime bugs/mismatches in existing group level routes and repositories.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastAPI, Pydantic, SQLModel, PostgreSQL
**Storage**: PostgreSQL (group_levels, groups, sessions, enrollments, enrollment_level_history tables)
**Testing**: pytest (with HS256 mock auth tokens)
**Target Platform**: Leapcell (uvicorn/gunicorn)
**Project Type**: FastAPI Backend Web Service
**Performance Goals**: Clean transactional database changes; execution time under 100ms per deletion.
**Constraints**: Level deletion must only target the highest level, and must be blocked if payments or attendance records exist.

## Constitution Check

- ✅ **Gate 1 — Layer Separation**: Router handles API endpoints and calls services. Business logic (delete cascade, validations) in `lifecycle/service.py` (multi-entity) and `level/service.py` (single-entity). Database interactions in repositories.
- ✅ **Gate 2 — Typed Contracts**: All public method boundaries in service use named DTOs (`DeleteLevelResult`, `GroupLevelDetailDTO`). Input uses `UpdateLevelInput` DTO.
- ✅ **Gate 3 — Exception Mapping**: Standard domain exceptions (`NotFoundError`, `ConflictError`, `BusinessRuleError`) map to standard HTTP status codes via global exception handlers.
- ✅ **Gate 4 — Dead Code**: Removing dead `soft_delete_level`, `GroupLevelCourseAssignment`, and the dead `complete_group_level` route.

**Overall: ✅ ALL GATES PASS**

## Project Structure

### Documentation (this feature)

```text
specs/037-group-level-management/
├── plan.md              # This file
└── spec.md              # Feature specification
```

### Source Code (repository root)

```text
app/
├── api/
│   └── routers/academics/
│       ├── group_details_router.py  # Update DELETE /academics/groups/{id}/levels/{number}
│       └── group_lifecycle_router.py# Remove complete route, fix cancel signature, add PATCH /academics/groups/{id}/levels/{number}
├── modules/academics/
│   ├── models/
│   │   └── group_level_models.py    # Delete GroupLevelCourseAssignment (dead model)
│   └── group/
│       ├── level/
│       │   ├── interface.py         # Add update_level, fix cancel_level signature
│       │   ├── repository.py        # Remove soft_delete_level, add hard delete + query guards
│       │   ├── schemas.py           # Add UpdateLevelInput DTO
│       │   └── service.py           # Implement update_level, fix cancel_level, add group.level_number sync
│       ├── lifecycle/
│       │   ├── interface.py         # Add delete_level
│       │   ├── schemas.py           # Add DeleteLevelResult DTO
│       │   └── service.py           # Implement cascading delete_level orchestrator
│       └── details/
│           ├── interface.py         # Remove delete_level from details protocol
│           └── service.py           # Remove delete_level from details service
```

## Complexity Tracking

*No constitution violations to justify.*
