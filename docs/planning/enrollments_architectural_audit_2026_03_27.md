# Enrollments Module — Architectural Audit

As part of the ongoing Deep-SOLID refactoring initiative, an audit was performed on the `enrollments` module on **2026-03-27** to measure its alignment with the target architecture defined in `docs/architecture/module_refactoring_guide.md`.

## Current State Analysis

Unlike heavily coupled modules such as `academics` or `competitions`, the `enrollments` module is highly cohesive and handles only **one** domain entity: `Enrollment`. However, despite its simplicity, it still violates the target architecture by utilizing flat module-level files, exposing non-object-oriented service interfaces, and ignoring Input/Output DTO enforcement.

**Current File Structure:**
```
app/modules/enrollments/
├── __init__.py                   (622 Bytes - Direct functional imports)
├── enrollment_models.py          (43 lines - Mixes SQL tables with DTO schemas)
├── enrollment_repository.py      (81 lines - Root level namespace)
├── enrollment_schemas.py         (25 lines - Defines unused Input DTOs)
└── enrollment_service.py         (169 lines - Procedural functions, primitive arguments)
```

## Matrix of Violations

| ID | Violation | Component | Severity | Resolution Phase |
|----|-----------|-----------|----------|------------------|
| **A-001** | **Flat Namespace Structure** <br> The module stores files directly in `modules/enrollments/` rather than explicitly in domain directories (`models/`, `schemas/`, `repositories/`, `services/`). | Global | Medium | 4, 5, 6 |
| **A-002** | **Primitive DTO Bypassing** <br> Functions like `enroll_student` accept arbitrary primitive lists (`student_id: int`, `group_id: int`, etc.) instead of properly enforcing the `EnrollStudentInput` Pydantic DTO physically stored in `enrollment_schemas.py`. | Service | Critical | 3 |
| **A-003** | **SQLAlchemy Leakage** <br> All service functions return live, raw `Enrollment` SQLAlchemy Objects instead of detached, validated `EnrollmentDTO` Pydantic schema representations. | Service | Critical | 3 |
| **A-004** | **Schema Contamination** <br> `enrollment_models.py` defines `EnrollmentCreate` and `EnrollmentRead` classes. These are explicitly data-transfer objects and violate the Model boundary. | Models | Medium | 1, 2 |
| **A-005** | **Procedural Anti-Pattern** <br> `enrollment_service.py` functions natively as a namespace of free-floating routines (`enroll_student()`, `transfer_student()`) rather than as an injectable `EnrollmentService` class encapsulating dependency contexts. | Service | High | 5 |
| **A-006** | **Facade Omission** <br> The module's `__init__.py` exposes files and raw functions instead of dynamically binding to a singleton `EnrollmentService`. | Facade | High | 6 |

## Concluding Remarks
While the module is fundamentally sound regarding business logic and SRP boundaries (due to it only managing one entity), it requires an aggressive restructuring loop to comply with the project-wide Deep-SOLID type-safety and architectural isolation dictates.
