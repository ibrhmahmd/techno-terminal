# Enrollments Module — Refactoring Implementation Plan

> **Date:** 2026-03-27
> **Scope:** Full Deep-SOLID alignment of the `enrollments` module.
> **Status:** Planning complete. Awaiting execution.

## Target Directory Structure

```
app/modules/enrollments/
├── __init__.py                     ← public API facade (backward compatibility bindings)
│
├── models/                         ← NEW sub-folder
│   └── enrollment_models.py        ← pure SQLModel definitions (`EnrollmentBase`, `Enrollment`)
│
├── schemas/                        ← NEW sub-folder
│   ├── __init__.py
│   └── enrollment_schemas.py       ← `EnrollStudentInput`, `TransferStudentInput`, `EnrollmentDTO`, `EnrollmentCreate`
│
├── repositories/                   ← NEW sub-folder
│   ├── __init__.py
│   └── enrollment_repository.py    ← Raw SQL/ORM execution functions
│
└── services/                       ← NEW sub-folder
    ├── __init__.py
    └── enrollment_service.py       ← Encapsulated Object-Oriented `EnrollmentService` Class
```

---

## Phase 1 & 2: DTO Verification & Schema Decoupling
**Goal:** Isolate all schema definitions into the appropriate directories and prepare our typed outputs.

1. Create `schemas/` directory.
2. Move the existing `enrollment_schemas.py` inside it.
3. Migrate `EnrollmentCreate` and `EnrollmentRead` from `enrollment_models.py` over to `schemas/enrollment_schemas.py`.
4. Create a clean, strict Output Schema:
   ```python
   class EnrollmentDTO(EnrollmentBase):
       id: int
       enrolled_at: Optional[datetime]
       created_at: Optional[datetime]
       updated_at: Optional[datetime]
       # Additional relations (e.g., student name) can be nested here later if ever needed by the UI.
   ```
5. Export everything through `schemas/__init__.py`.

## Phase 3: Contract Migration (The DTO Enforcement)
**Goal:** Completely eliminate the usage of disconnected primitive parameters and direct SQLAlchemy ORM returns.

1. **Input Contracts:**
   - Overhaul `enroll_student` so its signature forces the Pydantic type: `def enroll_student(self, data: EnrollStudentInput)`.
   - Overhaul `transfer_student` so its signature forces `def transfer_student(self, data: TransferStudentInput)`.
2. **Output Contracts:**
   - Ensure all returns in the service (like `enroll_student` dropping out `(Enrollment, bool)`) are changed to return `(EnrollmentDTO, bool)`.
   - All `list[Enrollment]` returns must be actively parsed into `list[EnrollmentDTO]` using `[EnrollmentDTO.model_validate(e) for e in enrollments]`.

## Phase 4: Data Access Layer Split
**Goal:** Push all repository operations into their dedicated persistence envelope.

1. Create the `repositories/` directory explicitly.
2. Move `enrollment_repository.py` into it.
3. Keep the functions as pure DB access. The repository handles ORM instances; it DOES NOT deal with DTOs.
4. Export aliases via `repositories/__init__.py`.

## Phase 5: Business Logic Split (Classes)
**Goal:** Transition procedural global programming into an Object-Oriented service block.

1. Create the `services/` directory.
2. Move `enrollment_service.py` into it.
3. Create a parent class `EnrollmentService`.
4. Shift all top-level functions (`enroll_student`, `apply_sibling_discount`, `transfer_student`, `drop_enrollment`, `complete_enrollment`, `get_group_roster`, `get_student_enrollments`) as methods bounded to `self`.

## Phase 6: Model Split & Compatibility Facade
**Goal:** Migrate models to their new home and ensure the rest of the application ecosystem doesn’t crash.

1. Create the `models/` directory. Move the now-purified `enrollment_models.py` inside.
2. Immediately fix `app/db/init_db.py` to point to `app.modules.enrollments.models.enrollment_models` to prevent database wipedown anomalies.
3. In `app/modules/enrollments/__init__.py`, introduce the protective facade routing layer:
   ```python
   from .services.enrollment_service import EnrollmentService
   
   _enrollment_svc = EnrollmentService()
   
   enroll_student = _enrollment_svc.enroll_student
   transfer_student = _enrollment_svc.transfer_student
   drop_enrollment = _enrollment_svc.drop_enrollment
   # ... etc
   ```

## Phase 7: UI Update Adapter Patching
**Goal:** Since the signatures to functions like `enroll_student()` changed from sequential parameters to a hard Pydantic `data` param, the User Interface code initiating these operations must be patched.

1. Locate usages of `enrollment_srv.enroll_student` and `enrollment_srv.transfer_student` inside the `app/ui/` codebase.
2. Update the calls:
   ```python
   # OLD
   enrollment_srv.enroll_student(student_id=1, group_id=2, ...)
   
   # NEW
   payload = EnrollStudentInput(student_id=1, group_id=2, ...)
   enrollment_srv.enroll_student(data=payload)
   ```

## Acceptance Criteria
- [ ] No module-level python source files sit flatly in `app/modules/enrollments/`.
- [ ] The `EnrollmentService` acts as the sole access point to the application domain.
- [ ] No service call returns an `Enrollment` SQLAlchemy object.
- [ ] All forms in the frontend seamlessly compile their variables into Pydantic DTO constructs before attempting database transactions.
