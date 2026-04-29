# SOLID Module Architecture Guide & Debugging Checklist

A comprehensive migration guide and debugging checklist for refactoring modules to follow SOLID principles, based on the CRM module's proven architecture.

---

## Part 1: Target Architecture Overview

### Folder Structure (Per-Entity Organization)

```
app/
├── api/schemas/                 # API Response Envelopes ONLY
│   ├── common.py                # ApiResponse[T], PaginatedResponse[T]
│   └── {module}/                # Module-specific API shapes (if needed)
│       └── {entity}_responses.py
│
└── modules/{module_name}/
    ├── __init__.py              # Facade exports only (no logic)
    ├── models/                  # SQLModel entities
    │   ├── __init__.py
    │   └── {entity}_models.py   # One file per entity
    ├── schemas/                 # Module DTOs (input, internal, output)
    │   ├── __init__.py
    │   ├── {entity}_schemas.py  # CRUD DTOs
    │   └── {operation}_dtos.py # Complex internal DTOs
    ├── interfaces/              # Protocols ONLY (no dtos/)
    │   └── __init__.py          # IRepository, IService protocols
    ├── repositories/
    │   ├── __init__.py
    │   ├── {entity}_repository.py
    │   └── unit_of_work.py
    ├── services/
    │   ├── __init__.py
    │   ├── {entity}_crud_service.py
    │   └── {operation}_service.py
    └── validators/
        └── ...
```

**DTO Rule**: Use `modules/{module}/schemas/` for ALL module DTOs. Only use `api/schemas/` for:
1. Generic response envelopes (`ApiResponse[T]`, `PaginatedResponse[T]`)
2. API-specific shapes that differ from service outputs (rare)

---

## Part 2: The 7-Phase Migration Playbook

### Phase 1: Foundation & Constants

**Actions:**
1. Create `constants.py` with domain enums, status lists, magic numbers
2. Move hard-coded strings to named constants
3. Create `validators/` folder for pure validation functions

**Debugging Checklist:**
- [ ] No string literals in business logic (use constants)
- [ ] All domain values have single source of truth

---

### Phase 2: Model Separation

**Actions:**
1. Create `models/` folder
2. Split monolithic `*_models.py` into per-entity files
3. Each model file: Base class → Create → Read/Update

**Debugging Checklist:**
- [ ] SQLModel classes match database schema exactly
- [ ] No `Field()` for columns that don't exist in DB
- [ ] Soft-delete mixin applied where needed

---

### Phase 3: Schema Layer Consolidation (2-Layer Architecture)

**Rule: All module DTOs go in `schemas/`. Remove `interfaces/dtos/` entirely.**

| Use Case | Location | Type |
|----------|----------|------|
| Service input validation | `schemas/{entity}_schemas.py` | Pydantic BaseModel |
| Service internal contracts | `schemas/{operation}_dtos.py` | Pydantic BaseModel (frozen) |
| Service output DTOs | `schemas/{entity}_schemas.py` | Pydantic BaseModel |
| API response envelopes | `api/schemas/common.py` | Generic `ApiResponse[T]` |
| API-specific shapes | `api/schemas/{module}/` | Only if different from service output |

**Anti-Patterns to Avoid:**
1. Don't create `interfaces/dtos/` - it duplicates schemas/
2. Don't put DTOs in interfaces/__init__.py - that's for Protocols only
3. Don't duplicate the same shape in api/schemas/ and module/schemas/

**Debugging Checklist:**
- [ ] No `dict` parameters in service methods
- [ ] No `list[dict]` return types
- [ ] All function signatures use concrete DTO classes
- [ ] Pydantic DTOs validate at API boundary

---

### Phase 4: Repository Layer with Unit of Work

**Actions:**
1. Create `repositories/{entity}_repository.py` per entity
2. Implement `unit_of_work.py` for transaction management
3. Repository methods: NEVER call `commit()`, only `flush()`

**Unit of Work Pattern:**
```python
class StudentUnitOfWork:
    def __init__(self, session: Session):
        self._session = session
        self.students = StudentRepository(session)
        self.parents = ParentRepository(session)
    
    def commit(self) -> None:
        self._session.commit()
    
    def flush(self) -> None:
        self._session.flush()
    
    def rollback(self) -> None:
        self._session.rollback()
```

**Debugging Checklist:**
- [ ] All queries live in repositories (not services, not routers)
- [ ] Repositories receive Session via constructor (not created internally)
- [ ] Complex joins are abstracted behind repository methods
- [ ] Soft-delete queries use `deleted_at IS NULL`
- [ ] Aggregate queries use `.scalar()` not `.one()` (avoids Row tuple)
- [ ] ORM list queries use `.scalars().all()` not `.all()` (avoids Row tuples)
- [ ] Boolean comparisons use `.is_(True)` not `== True`
- [ ] DI providers use `Depends(get_session)` not `with get_session()`

---

### Phase 5: Service Layer Split

**Actions:**
1. Create per-entity service classes (e.g., `StudentCrudService`)
2. Services receive UoW or repositories via constructor
3. Split complex functions into focused methods

**SRP Violations to Fix:**
- Function does > 1 thing → Split into 2+ methods
- Function has > 50 lines → Extract helper methods
- Function has nested loops + business logic → Separate query from processing

**Debugging Checklist:**
- [ ] Service methods under 30 lines (ideally)
- [ ] One public method = one business operation
- [ ] Private helpers for shared logic
- [ ] Activity logging injected (not hardcoded)

---

### Phase 6: Interface Protocols (Optional but Clean)

**Actions:**
1. Define Protocols in `interfaces/__init__.py`
2. Repository classes implement Protocol
3. Services depend on Protocols (DIP)

**Example:**
```python
@runtime_checkable
class IStudentRepository(Protocol):
    def create(self, student: Student) -> Student: ...
    def get_by_id(self, student_id: int) -> Optional[Student]: ...

class StudentRepository(IStudentRepository, SoftDeleteMixin):
    # Implementation
```

**Debugging Checklist:**
- [ ] Protocols define method signatures only
- [ ] Implementations match Protocol exactly
- [ ] Services use Protocol type hints

---

### Phase 7: Facade & API Integration

**Actions:**
1. Root `__init__.py` exports public API only
2. Update API routers to use new services
3. Run full test suite

**Root `__init__.py` Pattern:**
```python
# Models
from app.modules.crm.models import Student, Parent

# DTOs (API-facing)
from app.modules.crm.schemas import RegisterStudentDTO, UpdateStudentDTO

# Services (for DI)
from app.modules.crm.services import StudentCrudService, ParentCrudService

__all__ = ["Student", "Parent", "RegisterStudentDTO", ...]
```

**Debugging Checklist:**
- [ ] No internal imports leaked from root
- [ ] API routers import from module root
- [ ] All tests pass with new structure
- [ ] Old monolithic files deleted (no `hr_service.py`, `hr_repository.py`, etc.)
- [ ] No deprecated functions kept "for backward compatibility"
- [ ] No `interfaces/dtos/` folder remaining (DTOs in `schemas/` only)
- [ ] No inline imports in router endpoints
- [ ] Run `ruff check --select F401 app/modules/{module}/` for unused imports

---

## Part 3: Common Violations & Fixes

### Violation 1: Loose Return Types

**Bad:**
```python
def get_student_summary(student_id: int) -> dict:
def get_enrollments(student_id: int) -> list[dict]
def register_student(data: dict) -> tuple[Student, list]
```

**Good:**
```python
def get_student_summary(student_id: int) -> StudentSummaryDTO:
def get_enrollments(student_id: int) -> list[EnrollmentDTO]:
def register_student(data: RegisterStudentDTO) -> StudentRegistrationResult
```

---

### Violation 2: Queries Outside Repositories

**Bad (in Service):**
```python
class StudentService:
    def get_with_details(self, student_id: int):
        stmt = select(Student, Parent).join(...).where(Student.id == student_id)
        return self._session.exec(stmt).first()  # Query in service!
```

**Good:**
```python
class StudentService:
    def get_with_details(self, student_id: int):
        return self._repo.get_with_parent(student_id)  # Repo handles query

class StudentRepository:
    def get_with_parent(self, student_id: int) -> Optional[tuple[Student, Parent]]:
        stmt = select(Student, Parent).join(...).where(Student.id == student_id)
        return self._session.exec(stmt).first()
```

---

### Violation 3: Dict Parameters

**Bad:**
```python
def update_student(student_id: int, data: dict) -> Student:
    student.full_name = data.get("full_name", student.full_name)
    student.status = data.get("status", student.status)
```

**Good:**
```python
class UpdateStudentDTO(BaseModel):
    full_name: Optional[str] = None
    status: Optional[StudentStatus] = None

def update_student(student_id: int, data: UpdateStudentDTO) -> Student:
    if data.full_name is not None:
        student.full_name = data.full_name
    if data.status is not None:
        student.status = data.status
```

---

### Violation 4: Function Too Complex

**Bad (1 function, 80+ lines):**
```python
def process_enrollment(student_id, group_id, payment_data, discount, ...):
    # Validate student
    # Validate group
    # Check capacity
    # Calculate balance
    # Create enrollment
    # Process payment
    # Send notification
    # Log activity
    # Return result
```

**Good (split into focused methods):**
```python
class EnrollmentService:
    def enroll_student(self, cmd: EnrollStudentCommand) -> Enrollment:
        self._validate_eligibility(cmd.student_id, cmd.group_id)
        enrollment = self._create_enrollment_record(cmd)
        self._process_payment_if_provided(cmd.payment, enrollment)
        self._log_enrollment_activity(enrollment)
        return enrollment
    
    def _validate_eligibility(self, student_id: int, group_id: int) -> None:
        # 10 lines
    
    def _create_enrollment_record(self, cmd: EnrollStudentCommand) -> Enrollment:
        # 15 lines
    
    def _process_payment_if_provided(self, payment: Optional[PaymentDTO], enrollment: Enrollment) -> None:
        # 10 lines
```

---

## Part 4: Naming Conventions

| Layer | Convention | Example |
|-------|------------|---------|
| Models | `{Entity}` | `Student`, `Parent` |
| Repositories | `{Entity}Repository` | `StudentRepository` |
| Services | `{Entity}{Operation}Service` | `StudentCrudService`, `SearchService` |
| DTOs | `{Operation}{Entity}DTO` | `RegisterStudentDTO`, `UpdateStudentDTO` |
| Protocols | `I{Entity}{Layer}` | `IStudentRepository`, `IStudentService` |
| Unit of Work | `{Entity}UnitOfWork` | `StudentUnitOfWork` |

**Input DTOs:** `RegisterStudentDTO`, `UpdateParentDTO`, `CreateReceiptDTO`
**Output DTOs:** `StudentResponseDTO`, `StudentSummaryDTO`, `EnrollmentResultDTO`
**Command DTOs:** `RegisterStudentCommandDTO` (when multiple inputs combined)

---

## Part 5: Quick Reference Checklist

### Before Refactoring
- [ ] Identify all dict/list[dict] parameters and return types
- [ ] Identify all functions > 50 lines
- [ ] Identify queries outside repositories
- [ ] Map circular import risks

### During Refactoring
- [ ] One entity = one model file
- [ ] One entity = one repository file
- [ ] One service class = one responsibility
- [ ] DTOs before services (bottom-up)

### After Refactoring
- [ ] All tests pass
- [ ] No mypy errors
- [ ] No dict parameters in services
- [ ] No queries in services
- [ ] Import cycle check: `python -c "from app.modules.{module} import *"`

---

## Part 6: Decision Matrix

| Scenario | Approach |
|----------|----------|
| Simple CRUD module | schemas/ + repositories/ + services/ (no interfaces/) |
| Complex business logic | schemas/ with separate `{operation}_dtos.py` files |
| Module with 3+ entities | Per-entity organization mandatory |
| Activity logging needed | Inject ActivityService into CRUD services |
| Cross-module queries | Use repository composition, not direct model access |
| Soft-delete needed | Extend SoftDeleteMixin in repository |
| When to use api/schemas/{module}/ | Only when API shape differs from service output |

---

## Part 7: Common Pitfalls & Solutions

> **These pitfalls were discovered during actual module refactoring.** Each includes the exact error, root cause, and prevention strategy.

### Pitfall 1: SQLAlchemy 2.0 Aggregate Queries Return Row Tuples

**Error:**
```
pydantic_core._pydantic_core.ValidationError: Input should be a valid integer
[type=int_type, input_value=(5,), input_type=Row]
```

**Root Cause:** `session.exec(select(func.count())).one()` returns a `Row` tuple `(5,)` not an `int`.

**Fix:**
```python
# WRONG - returns Row tuple like (5,)
total = session.exec(select(func.count()).select_from(Employee)).one()

# CORRECT - returns int
total = session.exec(select(func.count()).select_from(Employee)).scalar() or 0
```

**Prevention:** Always use `.scalar()` for aggregate functions (`count`, `sum`, `avg`). Use `.one()` only when you need the full Row.

**SQLAlchemy 2.0 Query Method Cheat Sheet:**

| Method | Returns | Use Case |
|--------|---------|----------|
| `.scalar()` | Single value (int, str, etc.) | `func.count()`, `func.sum()` |
| `.scalars().all()` | `list[Model]` | List of ORM objects |
| `.scalars().first()` | `Model or None` | Optional single result |
| `.one()` | `Row` tuple | When you need tuple columns |
| `.first()` | `Row or None` | Optional Row result |

---

### Pitfall 2: Inline Imports in Router Endpoints

**Error:**
```
Ruff: Module level import not at top of file
```

**Root Cause:** Importing modules inside endpoint functions to "avoid circular imports" or "keep it local".

**Bad:**
```python
@router.post("/hr/employees/{employee_id}/create-account")
def create_employee_account_endpoint(employee_id: int, body: ...):
    from app.modules.hr.hr_service import create_employee_account  # WRONG
    from app.modules.hr.interfaces.dtos import CreateEmployeeAccountDTO  # WRONG
    from app.shared.exceptions import NotFoundError  # WRONG
    ...
```

**Good:**
```python
# All imports at top of file
from app.modules.hr import CreateEmployeeAccountDTO
from app.shared.exceptions import NotFoundError, ConflictError, ValidationError

@router.post("/hr/employees/{employee_id}/create-account")
def create_employee_account_endpoint(employee_id: int, body: ...):
    ...
```

**Prevention:** If circular imports are a concern, use `TYPE_CHECKING`:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.hr.schemas import EmployeeReadDTO  # Type-only import
```

---

### Pitfall 3: Unused Imports After Refactoring

**Error:**
```
Ruff: `app.modules.hr.models.EmployeeCreate` imported but unused
```

**Root Cause:** When replacing old module references with new DTOs, old imports are left behind.

**Prevention Checklist:**
- After each phase, run `ruff check --select F401 app/modules/{module}/` to find unused imports
- Remove any import that was only used by the old monolithic code
- If an import is needed only for type hints, move it under `TYPE_CHECKING`

---

### Pitfall 4: Mixing Old and New Service Patterns

**Error:** Router still calls `hr.list_all_employees()` (old flat module) alongside `service.list_paginated()` (new SOLID service).

**Root Cause:** Leaving deprecated functions "for backward compatibility" creates confusion and dual code paths.

**Bad:**
```python
# dependencies.py - DON'T keep both
def get_hr_service():  # OLD - deprecated
    import app.modules.hr.hr_service as hr_service_module
    return hr_service_module

def get_employee_crud_service() -> EmployeeCrudService:  # NEW
    ...
```

**Good:**
```python
# dependencies.py - ONLY the new service
def get_employee_crud_service() -> EmployeeCrudService:
    with get_session() as session:
        uow = HRUnitOfWork(session)
        return EmployeeCrudService(uow)
```

**Zero Tech Debt Rule:** Delete old code immediately. If tests break, fix the tests — don't keep the old code.

---

### Pitfall 5: DTOs Without `from_attributes` Config

**Error:**
```
ValidationError: Input should be a valid dictionary [type=dict_type, input_value=<Employee object>, input_type=Model]
```

**Root Cause:** `EmployeeReadDTO.model_validate(orm_object)` fails without `from_attributes=True`.

**Bad:**
```python
class EmployeeReadDTO(BaseModel):
    id: int
    full_name: str
    # Missing model_config!
```

**Good:**
```python
class EmployeeReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Required for ORM → DTO

    id: int
    full_name: str
```

**Prevention:** Every DTO that receives data from an ORM model must have `from_attributes=True`. Output DTOs always need it. Input DTOs never need it.

---

### Pitfall 6: Boolean Comparisons in SQLAlchemy Where Clauses

**Error:**
```
Ruff: Avoid equality comparisons to `True`; use `Employee.is_active:` for truth checks
```

**Root Cause:** SQLAlchemy columns use `== True` which is both a Python anti-pattern and can cause issues with some database drivers.

**Bad:**
```python
stmt = select(Employee).where(Employee.is_active == True)
```

**Good:**
```python
stmt = select(Employee).where(Employee.is_active.is_(True))
```

**Prevention:** Always use `.is_(True)` / `.is_(False)` for boolean column comparisons in SQLAlchemy queries.

---

### Pitfall 7: `interfaces/dtos/` Duplication with `schemas/`

**Error:** Same DTO defined in both `interfaces/dtos/` and `schemas/`, causing import confusion and redefinition warnings.

**Root Cause:** The old 3-layer architecture (api/schemas + module/schemas + interfaces/dtos) created overlap.

**2-Layer Rule:**
- `schemas/` = ALL module DTOs (input, output, internal)
- `api/schemas/` = Generic envelopes ONLY (`ApiResponse[T]`, `PaginatedResponse[T]`)
- `interfaces/` = Protocols ONLY (no DTOs)

**Prevention:** After creating `schemas/`, immediately delete `interfaces/dtos/`. Don't leave both.

---

### Pitfall 8: Dependency Injection with `with` Statement

**Error:** Service session is closed before the endpoint returns its response.

**Root Cause:** Using `with get_session() as session:` in dependency provider closes the session before the response is serialized.

**Bad:**
```python
def get_employee_crud_service() -> EmployeeCrudService:
    with get_session() as session:  # Session closes after function returns!
        uow = HRUnitOfWork(session)
        return EmployeeCrudService(uow)
```

**Good:**
```python
def get_employee_crud_service(
    session: Session = Depends(get_session),  # FastAPI manages lifecycle
) -> EmployeeCrudService:
    uow = HRUnitOfWork(session)
    return EmployeeCrudService(uow)
```

**Prevention:** Let FastAPI's dependency injection manage session lifecycle. Never use `with` in dependency providers.

---

## Part 8: Debugging Quick Reference

### SQLAlchemy Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Input should be a valid integer [type=int_type, input_value=(5,)]` | `.one()` returns Row tuple | Use `.scalar()` |
| `Input should be a valid dictionary [type=dict_type]` | Missing `from_attributes=True` | Add `ConfigDict(from_attributes=True)` |
| `AttributeError: 'Row' has no attribute 'id'` | Accessing Row instead of Model | Use `.scalars().all()` |
| `DetachedInstanceError` | Session closed before access | Use FastAPI `Depends(get_session)` |

### Pydantic Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ValidationError: field required` | DTO missing field from ORM | Add Optional field or default |
| `ValidationError: Input should be a valid integer` | Row tuple instead of scalar | Use `.scalar()` |
| `model_validate()` fails on ORM | Missing `from_attributes` | Add `ConfigDict(from_attributes=True)` |

### Import Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Module level import not at top` | Inline import in function | Move to top of file |
| `Imported but unused` | Stale import after refactor | Remove or use `TYPE_CHECKING` |
| `Redefinition of unused X` | Same name imported twice | Remove duplicate import |
| `Undefined name X` | Import removed but still used | Add import back at top |

### Runtime Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `500 Internal Server Error` on list endpoint | Count returns Row not int | Use `.scalar() or 0` |
| `DetachedInstanceError` | Session closed in DI provider | Use `Depends(get_session)` |
| `TypeError: got unexpected keyword` | DTO field mismatch | Check DTO matches API input |
