# CRM Student Module — Full Implementation Plan
## Finance-Pattern SOLID Architecture + Feature Expansion

---

## Clarifications Addressed

### `GRADUATED` status → **Removed**
`StudentStatus` = 3 values only: `active`, `waiting`, `inactive`.
Duplicate schema-level enum deleted. Canonical source: `student_models.py`.

### `waiting_priority` / `waiting_since` → **Kept, clarified**
- `waiting_since` — auto-stamped by DB trigger when status → `waiting`. Read-only.
- `waiting_priority` — admin-assigned integer for queue ordering (1 = highest).
- Both fields exposed **only** on `StudentResponseDTO` and `StudentWithDetails` (admin views), not on `StudentPublic` (basic profile).

---

## Answer: Does the Previous Plan Apply Your Architecture?

**No.** The previous plan kept the existing flat-module structure (`student_service.py` as a single class calling module-level repository functions). It did not:
- Create the `interfaces/` package with `Protocol` contracts
- Convert repositories to **class-based** with injected `Session` (the finance pattern)
- Implement `StudentUnitOfWork`
- Create the `validators/` module
- Separate into distinct service classes per responsibility (`SearchService`, `GroupingService`, etc.)

This revised plan implements **the full finance-pattern architecture** for the CRM student domain.

---

## Target Module Structure

```
app/modules/crm/                          ← existing package, restructured
├── __init__.py                           [MODIFY] clean public API exports only
├── models/                               [KEEP] unchanged ORM models
│   ├── __init__.py
│   ├── student_models.py                 [MODIFY] remove GRADUATED
│   ├── parent_models.py                  [KEEP]
│   └── link_models.py                    [KEEP]
│
├── interfaces/                           [CREATE] Protocol contracts (new)
│   └── __init__.py                       [CREATE] all Protocol definitions + frozen DTOs
│
├── schemas/                              [MODIFY] DTOs consolidation
│   ├── __init__.py                       [MODIFY]
│   ├── student_schemas.py                [MODIFY] fix enum, fix types, add typed DTOs
│   └── parent_schemas.py                 [KEEP]
│
├── repositories/                         [RESTRUCTURE] function → class-based
│   ├── __init__.py                       [MODIFY] exports + UoW
│   ├── student_repository.py             [REWRITE] class StudentRepository
│   ├── parent_repository.py              [REWRITE] class ParentRepository
│   └── unit_of_work.py                   [CREATE] StudentUnitOfWork
│
├── services/                             [RESTRUCTURE] single class → 4 focused classes
│   ├── __init__.py                       [MODIFY] exports
│   ├── student_service.py                [REWRITE] StudentService (CRUD + status)
│   ├── search_service.py                 [CREATE] SearchService (search + grouping queries)
│   ├── grouping_service.py               [CREATE] GroupingService (5 strategies)
│   └── reporting_service.py              [CREATE] ReportingService (summaries + history)
│
└── validators/                           [CREATE] new module
    ├── __init__.py                        [CREATE]
    └── student_validator.py              [CREATE] StudentValidator (pure validation)
```

---

## Complete File Checklist

### 📝 Files to Modify

| ID | File | Change |
|----|------|--------|
| M-01 | `app/modules/crm/models/student_models.py` | Remove `GRADUATED` from enum |
| M-02 | `app/modules/crm/schemas/student_schemas.py` | Delete local enum, import from model, add `StatusHistoryEntryDTO`, fix `UpdateStudentStatusDTO`, remove phantom fields |
| M-03 | `app/modules/crm/schemas/__init__.py` | Add new DTO exports |
| M-04 | `app/modules/crm/repositories/__init__.py` | Export class-based repos + `StudentUnitOfWork` |
| M-05 | `app/modules/crm/services/__init__.py` | Export all 4 service classes |
| M-06 | `app/modules/crm/__init__.py` | Strip to clean public API (no singletons, no facade) |
| M-07 | `app/api/schemas/crm/student.py` | Add `status` to `StudentPublic`, fix `StudentListItem` |
| M-08 | `app/api/schemas/crm/student_details.py` | Fix comment, fix `level_number`, fix `is_primary`, add `AttendanceStats` |
| M-09 | `app/api/schemas/students/activity.py` | Remove dead DTOs, fix `created_at` type, merge redundant DTOs |
| M-10 | `app/api/routers/crm/students.py` | Reorder routes, standardize errors, move notes to body |
| M-11 | `app/api/routers/crm/students_history.py` | Add `/crm` prefix, type `svc`, fix route paths |
| M-12 | `app/api/dependencies.py` | Remove duplicate factories, add new service factories |
| M-13 | `tests/test_crm.py` | Expand per test plan below |

### 🆕 Files to Create

| ID | File | Purpose |
|----|------|---------|
| C-01 | `app/modules/crm/interfaces/__init__.py` | All Protocol interfaces + frozen internal DTOs |
| C-02 | `app/modules/crm/repositories/student_repository.py` | `StudentRepository` class (Session-injected) |
| C-03 | `app/modules/crm/repositories/parent_repository.py` | `ParentRepository` class (Session-injected) |
| C-04 | `app/modules/crm/repositories/unit_of_work.py` | `StudentUnitOfWork` context-manager |
| C-05 | `app/modules/crm/services/student_service.py` | `StudentService` — CRUD + status management |
| C-06 | `app/modules/crm/services/search_service.py` | `SearchService` — search + listing |
| C-07 | `app/modules/crm/services/grouping_service.py` | `GroupingService` — 5 group-by strategies |
| C-08 | `app/modules/crm/services/reporting_service.py` | `ReportingService` — balance, attendance, history |
| C-09 | `app/modules/crm/validators/__init__.py` | `validators` module init |
| C-10 | `app/modules/crm/validators/student_validator.py` | `StudentValidator` — pure validation logic |
| C-11 | `app/api/schemas/crm/student_grouped.py` | `GroupedStudentsResponse`, `StudentGroup`, `GroupByMode` DTOs |
| C-12 | `app/api/routers/crm/students_grouped.py` | `GET /crm/students/grouped` router |
| C-13 | `db/migrations/022_student_indexes.sql` | Indexes on `status`, `date_of_birth` |
| C-14 | `tests/test_crm_grouped.py` | Grouped endpoint test suite |
| C-15 | `tests/test_crm_details.py` | Enriched details test suite |

---

## Phase 1 — Model & Critical Bug Fixes (Foundation)
> **Depends on:** Nothing. Must run first.
> **Goal:** Eliminate all critical correctness bugs before structural work begins.

---

### 1.1 — Unify `StudentStatus` Enum — Remove `GRADUATED` `(M-01, M-02)`

**`student_models.py`:**
```python
class StudentStatus(str, Enum):
    ACTIVE   = "active"
    WAITING  = "waiting"
    INACTIVE = "inactive"
    # GRADUATED removed — not a business requirement
```

**`student_schemas.py`:** Delete the local `StudentStatus` class entirely. Replace with:
```python
from app.modules.crm.models.student_models import StudentStatus  # single source of truth
```

Remove `graduated: int` from `StudentStatusSummaryDTO`.

---

### 1.2 — Add `StatusHistoryEntryDTO` — Replace `list[dict]` `(M-02)`

```python
class StatusHistoryEntryDTO(BaseModel):
    """Typed audit entry in student status trail. Replaces list[dict]."""
    timestamp: datetime
    changed_by: Optional[int] = None
    old_status: Optional[str] = None
    new_status: str
    notes: Optional[str] = None
    action: Optional[str] = None       # e.g. "priority_change"
    new_priority: Optional[int] = None
```

Update `StudentResponseDTO.status_history: list[StatusHistoryEntryDTO] = []`.

---

### 1.3 — Fix `UpdateStudentStatusDTO` to Use Enum `(M-02)`

```python
class UpdateStudentStatusDTO(BaseModel):
    status: StudentStatus   # was str — Pydantic now owns the 422
    notes: Optional[str] = None
```

---

### 1.4 — DB Index Migration `(C-13)`

```sql
-- db/migrations/022_student_indexes.sql
CREATE INDEX IF NOT EXISTS idx_students_status   ON students(status);
CREATE INDEX IF NOT EXISTS idx_students_dob      ON students(date_of_birth);
CREATE INDEX IF NOT EXISTS idx_students_active   ON students(is_active);
COMMENT ON COLUMN students.is_active IS 'Deprecated: use status column instead';
```

---

**Phase 1 verification:**
```bash
pytest tests/test_crm.py::TestCRMAuth -v      # fast smoke test
python -c "from app.modules.crm.models.student_models import StudentStatus; print(list(StudentStatus))"
```

---

## Phase 2 — Finance-Pattern SOLID Architecture Migration
> **Depends on:** Phase 1 (unified enum)
> **Goal:** Replace the flat-module + module-level-function architecture with Protocol interfaces, class-based repositories, UnitOfWork, and segregated service classes — matching the finance module exactly.

---

### 2.1 — Create `interfaces/__init__.py` `(C-01)`

Mirrors `app/modules/finance/interfaces/__init__.py`. Contains:

#### Internal frozen DTOs (for service-to-service communication):

```python
@dataclass(frozen=True)
class StudentSummaryDTO:
    """Immutable summary row — used internally between services."""
    id: int
    full_name: str
    phone: Optional[str]
    gender: Optional[str]
    status: str
    is_active: bool
    current_group_id: Optional[int]
    current_group_name: Optional[str]
    date_of_birth: Optional[date]

@dataclass(frozen=True)
class StudentGroupedResultDTO:
    """Result of a grouping operation."""
    group_by: str
    total_unique_students: int
    groups: list  # list[StudentGroupBucketDTO]

@dataclass(frozen=True)
class StudentGroupBucketDTO:
    key: str
    label: str
    count: int
    students: list  # list[StudentSummaryDTO]

@dataclass(frozen=True)
class StudentBalanceSummaryDTO:
    total_due: float
    total_discounts: float
    total_paid: float
    net_balance: float
    enrollment_count: int
    unpaid_enrollments: int

@dataclass(frozen=True)
class AttendanceStatsDTO:
    total_sessions: int
    attended: int
    absent: int
    cancelled: int
    attendance_rate: float
```

#### Repository Protocol interfaces (`@runtime_checkable`):

```python
@runtime_checkable
class IStudentRepository(Protocol):
    def create(self, student: Student) -> Student: ...
    def get_by_id(self, student_id: int) -> Optional[Student]: ...
    def get_all(self, skip: int, limit: int) -> list[Student]: ...
    def get_all_enriched(self, include_inactive: bool) -> list[StudentSummaryDTO]: ...
    def search(self, query: str) -> list[Student]: ...
    def count(self, active_only: bool) -> int: ...
    def count_by_status(self, status: StudentStatus) -> int: ...
    def update_status(self, student_id: int, new_status: StudentStatus,
                      user_id: Optional[int], notes: Optional[str]) -> Optional[Student]: ...
    def set_waiting_priority(self, student_id: int, priority: int) -> Optional[Student]: ...
    def delete(self, student_id: int) -> bool: ...
    def get_with_parent(self, student_id: int) -> Optional[tuple]: ...
    def get_enriched_details(self, student_id: int) -> Optional[dict]: ...

@runtime_checkable
class IParentRepository(Protocol):
    def create(self, parent: Parent) -> Parent: ...
    def get_by_id(self, parent_id: int) -> Optional[Parent]: ...
    def get_by_phone(self, phone: str) -> Optional[Parent]: ...
    def get_all(self, skip: int, limit: int) -> list[Parent]: ...
    def search(self, query: str) -> list[Parent]: ...
    def count(self) -> int: ...
    def update(self, parent_id: int, data: dict) -> Optional[Parent]: ...
    def delete(self, parent_id: int) -> Optional[Parent]: ...
```

#### Service Protocol interfaces:

```python
@runtime_checkable
class IStudentService(Protocol):
    """CRUD + status operations on a single student record."""
    def register(self, command: RegisterStudentCommandDTO) -> tuple[Student, list]: ...
    def get_by_id(self, student_id: int) -> Optional[Student]: ...
    def update(self, student_id: int, data: UpdateStudentDTO) -> Student: ...
    def update_status(self, student_id: int, new_status: StudentStatus,
                      user_id: Optional[int], notes: Optional[str]) -> Student: ...
    def toggle_status(self, student_id: int, user_id: Optional[int],
                      notes: Optional[str]) -> Student: ...
    def set_waiting_priority(self, student_id: int, priority: int,
                             user_id: Optional[int]) -> Student: ...
    def delete(self, student_id: int) -> bool: ...

@runtime_checkable
class ISearchService(Protocol):
    """Search and listing operations."""
    def search(self, query: str) -> list[Student]: ...
    def list_all(self, skip: int, limit: int) -> list: ...
    def count(self, active_only: bool) -> int: ...
    def get_by_status(self, status: StudentStatus, skip: int, limit: int) -> list[Student]: ...
    def get_waiting_list(self, skip: int, limit: int, ordered: bool) -> list[Student]: ...
    def get_status_summary(self) -> StudentStatusSummaryDTO: ...

@runtime_checkable
class IGroupingService(Protocol):
    """Group students by a specified dimension."""
    def get_grouped(self, group_by: str, include_inactive: bool) -> StudentGroupedResultDTO: ...

@runtime_checkable
class IReportingService(Protocol):
    """Cross-domain summary and history reporting."""
    def get_student_details(self, student_id: int) -> StudentWithDetails: ...
    def get_balance_summary(self, student_id: int) -> StudentBalanceSummaryDTO: ...
    def get_attendance_stats(self, student_id: int) -> AttendanceStatsDTO: ...
    def get_siblings(self, student_id: int) -> list: ...
```

---

### 2.2 — Rewrite `student_repository.py` as Class `(C-02)`

Replaces the existing flat-function file. Mirrors `PaymentRepository`:

```python
class StudentRepository(IStudentRepository):
    """
    Repository for student data access.
    Session is injected via constructor — never acquired internally.
    Never calls session.commit(). Only flush().
    """
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, student_id: int) -> Optional[Student]:
        return self._session.get(Student, student_id)

    def count(self, active_only: bool = True) -> int:
        """Uses SELECT COUNT(*) — never loads rows into memory."""
        stmt = select(func.count()).select_from(Student)
        if active_only:
            stmt = stmt.where(Student.is_active.is_(True))
        return self._session.exec(stmt).one()

    def count_by_status(self, status: StudentStatus) -> int:
        return self._session.exec(
            select(func.count()).select_from(Student).where(Student.status == status)
        ).one()

    def get_all_enriched(self, include_inactive: bool = False) -> list[StudentSummaryDTO]:
        """
        Enriched listing with current_group_id/name via LEFT JOIN.
        Single query — no N+1.
        """
        # LEFT JOIN enrollments → groups for active enrollment only
        ...

    def get_student_balance_summary(self, student_id: int) -> StudentBalanceSummaryDTO:
        """
        Single GROUP BY aggregate for payments — fixes CRIT-5.
        """
        # 1 query for enrollments, 1 GROUP BY for payments — not N+1
        ...

    def get_student_siblings_with_details(self, student_id: int) -> list:
        """
        Pre-aggregates sibling enrollment counts — fixes CRIT-6.
        """
        # 1 join query for siblings, 1 GROUP BY for enrollment counts
        ...

    def search(self, query: str) -> list[Student]:
        """Searches full_name OR phone — fixes HIGH-9."""
        term = f"%{query}%"
        return list(self._session.exec(
            select(Student).where(
                or_(Student.full_name.ilike(term), Student.phone.ilike(term))
            ).limit(50)
        ).all())

    def delete(self, student_id: int) -> bool:
        """
        Deletes ONLY student + cascade via ORM.
        Cross-domain cleanup (attendance, payments) delegated to StudentService.
        Fixes CRIT-3.
        """
        student = self.get_by_id(student_id)
        if not student:
            return False
        self._session.delete(student)
        self._session.flush()
        return True
```

---

### 2.3 — Rewrite `parent_repository.py` as Class `(C-03)`

```python
class ParentRepository(IParentRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def count(self) -> int:
        """SELECT COUNT(*) — fixes CRIT-7 for parents."""
        return self._session.exec(
            select(func.count()).select_from(Parent)
        ).one()

    def delete(self, parent_id: int) -> Optional[Parent]:
        """flush() only — no commit(). Fixes CRIT-2."""
        parent = self._session.get(Parent, parent_id)
        if parent:
            self._session.delete(parent)
            self._session.flush()
        return parent
```

---

### 2.4 — Create `unit_of_work.py` `(C-04)`

Mirrors `FinanceUnitOfWork` exactly:

```python
class StudentUnitOfWork:
    """
    Unit of Work for student operations.
    Manages a single DB session across StudentRepository and ParentRepository.
    Ensures atomic commits/rollbacks.

    Usage:
        with StudentUnitOfWork() as uow:
            student = uow.students.create(student_obj)
            uow.parents.link(student.id, parent_id)
            uow.commit()
    """
    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session
        self._own_session = session is None
        self._students: Optional[StudentRepository] = None
        self._parents: Optional[ParentRepository] = None

    def __enter__(self) -> "StudentUnitOfWork":
        if self._own_session:
            self._session_cm = get_session()
            self._session = self._session_cm.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        if self._own_session:
            self._session_cm.__exit__(exc_type, exc_val, exc_tb)

    @property
    def students(self) -> StudentRepository:
        if self._students is None:
            self._students = StudentRepository(self._session)
        return self._students

    @property
    def parents(self) -> ParentRepository:
        if self._parents is None:
            self._parents = ParentRepository(self._session)
        return self._parents

    def commit(self) -> None: self._session.commit()
    def rollback(self) -> None: self._session.rollback()
    def flush(self) -> None: self._session.flush()
```

---

### 2.5 — Create `validators/student_validator.py` `(C-09, C-10)`

**SRP:** Validation logic lives here, not in services.

```python
class StudentValidator:
    """
    Pure validation — no DB access, no side effects.
    Services call this before mutating any student record.
    """

    @staticmethod
    def validate_status_transition(
        current: StudentStatus, new: StudentStatus
    ) -> None:
        """Raises BusinessRuleError for illegal transitions."""
        ILLEGAL = {
            (StudentStatus.INACTIVE, StudentStatus.WAITING),  # must reactivate first
        }
        if (current, new) in ILLEGAL:
            raise BusinessRuleError(
                f"Cannot transition from '{current.value}' to '{new.value}' directly."
            )

    @staticmethod
    def validate_waiting_priority(priority: int) -> None:
        if not 1 <= priority <= 1000:
            raise ValidationError("Waiting priority must be between 1 and 1000.")

    @staticmethod
    def compute_age(dob: Optional[date]) -> Optional[int]:
        """Pure function. Returns integer age or None."""
        if not dob:
            return None
        dob_d = dob.date() if hasattr(dob, 'date') else dob
        today = date.today()
        age = today.year - dob_d.year
        if (today.month, today.day) < (dob_d.month, dob_d.day):
            age -= 1
        return age

    @staticmethod
    def classify_age_bracket(age: Optional[int]) -> str:
        """Returns age bracket key per grouping spec."""
        if age is None:
            return "unknown"
        if 4 <= age < 7:   return "age_4_7"
        if 7 <= age < 9:   return "age_7_9"
        if 9 <= age < 12:  return "age_9_12"
        if 12 <= age < 15: return "age_12_15"
        if age >= 15:      return "age_15_plus"
        return "unknown"
```

---

### 2.6 — Create 4 Focused Service Classes `(C-05, C-06, C-07, C-08)`

**ISP compliance:** Each service implements exactly one Protocol.

#### `StudentService` `(C-05)` — implements `IStudentService`
Handles: `register`, `get_by_id`, `update`, `update_status`, `toggle_status`, `set_waiting_priority`, `delete`.
Uses `StudentUnitOfWork` internally.
Delegates validation to `StudentValidator`.
Delegates cross-domain cascade (attendance, payments, enrollments) inside `delete`.

```python
class StudentService(IStudentService):
    def __init__(self, validator: StudentValidator = None):
        self._validator = validator or StudentValidator()

    def update_status(self, student_id, new_status, user_id=None, notes=None):
        with StudentUnitOfWork() as uow:
            student = uow.students.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student {student_id} not found")
            self._validator.validate_status_transition(student.status, new_status)
            return uow.students.update_status(student_id, new_status, user_id, notes)

    def delete(self, student_id: int) -> bool:
        """Orchestrates cross-domain cascade. Fixes CRIT-3."""
        from app.modules.enrollments.repositories import EnrollmentRepository
        from app.modules.attendance.repositories import AttendanceRepository

        with StudentUnitOfWork() as uow:
            enrollment_ids = EnrollmentRepository(uow._session).get_ids_for_student(student_id)
            if enrollment_ids:
                AttendanceRepository(uow._session).delete_by_enrollment_ids(enrollment_ids)
                # payments handled by DB cascade
            EnrollmentRepository(uow._session).delete_by_student_id(student_id)
            return uow.students.delete(student_id)
```

#### `SearchService` `(C-06)` — implements `ISearchService`
Handles: `search`, `list_all`, `count`, `get_by_status`, `get_waiting_list`, `get_status_summary`.

#### `GroupingService` `(C-07)` — implements `IGroupingService`
Handles all 5 `group_by` strategies. Uses `StudentUnitOfWork` + `StudentValidator.classify_age_bracket`.

#### `ReportingService` `(C-08)` — implements `IReportingService`
Handles: `get_student_details`, `get_balance_summary`, `get_attendance_stats`, `get_siblings`.

---

### 2.7 — Clean Up `crm/__init__.py` `(M-06)`

Remove `_CRMServiceFacade`, `parent_svc`, `student_svc` singletons.
Export only models, schemas, and the UoW:

```python
from app.modules.crm.models import Student, Parent, StudentParent
from app.modules.crm.schemas import (
    RegisterStudentCommandDTO, UpdateStudentDTO,
    RegisterParentInput, UpdateParentDTO, StudentStatus,
)
from app.modules.crm.repositories import StudentUnitOfWork

__all__ = ["Student", "Parent", "StudentParent", "StudentUnitOfWork", ...]
```

---

### 2.8 — Update `dependencies.py` `(M-12)`

```python
from app.modules.crm.services.student_service   import StudentService
from app.modules.crm.services.search_service    import SearchService
from app.modules.crm.services.grouping_service  import GroupingService
from app.modules.crm.services.reporting_service import ReportingService
from app.modules.crm.services.parent_service    import ParentService  # stays

def get_student_service()   -> StudentService:   return StudentService()
def get_search_service()    -> SearchService:    return SearchService()
def get_grouping_service()  -> GroupingService:  return GroupingService()
def get_reporting_service() -> ReportingService: return ReportingService()
def get_parent_service()    -> ParentService:    return ParentService()

# Remove: duplicate get_group_history_service / get_group_level_service definitions
```

---

**Phase 2 verification:**
```bash
python -c "from app.modules.crm.repositories import StudentRepository, StudentUnitOfWork"
python -c "from app.modules.crm.interfaces import IStudentService, ISearchService"
python -c "from app.modules.crm.validators import StudentValidator"
pytest tests/test_crm.py -v
```

---

## Phase 3 — API Contract Fixes
> **Depends on:** Phase 2 (new service classes must exist before routers are updated)
> **Goal:** Ensure every endpoint returns exactly its declared contract.

---

### 3.1 — Fix `StudentPublic` — Add `status` Field `(M-07)`

```python
class StudentPublic(BaseModel):
    id: int
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool                   # retained (deprecated)
    status: StudentStatus             # ← NEW canonical field
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
```

---

### 3.2 — Fix `StudentListItem` — Real Data via Enriched Query `(M-07)`

```python
class StudentListItem(BaseModel):
    id: int
    full_name: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    is_active: bool
    status: StudentStatus
    current_group_id: Optional[int] = None      # populated by SearchService join
    current_group_name: Optional[str] = None    # populated by SearchService join
    notes: Optional[str] = None
    model_config = {"from_attributes": False}   # manual mapping from StudentSummaryDTO
```

`SearchService.list_all()` returns `list[StudentSummaryDTO]`. The router maps `StudentSummaryDTO → StudentListItem`.

---

### 3.3 — Fix `student_details.py` `(M-08)`

- Fix wrong comment: `gender: Optional[str] = None  # stored field, NOT computed`
- Fix nullability: `level_number: Optional[int] = None`
- Add `AttendanceStats` DTO and field on `StudentWithDetails`
- Fix `is_primary` population (populated from `get_with_parent` tuple)

---

### 3.4 — Fix `students_history.py` Prefix + Typed `svc` `(M-11)`

```python
from app.modules.students.services.activity_service import ActivityService
from app.modules.auth import User

router = APIRouter(prefix="/crm", tags=["CRM — History"])

def get_student_history(
    ...
    svc: ActivityService = Depends(get_activity_service),  # ← typed
):
```

Route renames:
- `GET /history/recent` → `GET /students/history/recent`
- `POST /history/search` → `POST /students/history/search`

---

### 3.5 — Fix `students.py` Router `(M-10)`

- Remove manual `try/except ValueError` around status (Pydantic handles it after 2.3)
- Replace all `raise HTTPException(404)` with `raise NotFoundError(...)`
- Move `notes` on `toggle_student_status` from query param to request body
- Reorder: Collection → Item → Sub-resources (no static/dynamic interleaving)
- Update service calls: `svc.search(...)` → `search_svc.search(...)`, `svc.update_status(...)` → `student_svc.update_status(...)`, etc.

Update `students.py` to inject the correct service per operation:
```python
@router.get("/students")
def list_students(
    ...
    search_svc: SearchService = Depends(get_search_service),
):

@router.post("/students")
def create_student(
    ...
    student_svc: StudentService = Depends(get_student_service),
):

@router.get("/students/{student_id}/details")
def get_student_details(
    ...
    reporting_svc: ReportingService = Depends(get_reporting_service),
):
```

---

### 3.6 — Remove Dead DTOs from `activity.py` `(M-09)`

Remove: `ActivitySearchResultDTO`, `ActivityTimelineResponseDTO`, `ActivityTimelineItemDTO`, `StudentHistoryItemDTO`, `ActivityTimelineItemDTO`.
Merge `RecentActivityItemDTO` + `ManualActivityResponseDTO` into `ActivityLogResponseDTO` (add `performed_by_name: Optional[str] = None`).
Fix `created_at: Optional[datetime]` — let Pydantic serialize, remove manual `.isoformat()` in router.

---

**Phase 3 verification:**
```bash
pytest tests/test_crm.py -v
# Manual:
# GET /crm/students/1            → has 'status' field in response
# PATCH /crm/students/1/status   {"status":"invalid"} → 422
# GET /crm/students?q=0100       → returns phone matches
```

---

## Phase 4 — Grouped Students Endpoint (New Feature)
> **Depends on:** Phase 2 (`GroupingService` + `StudentSummaryDTO`), Phase 3 (`StudentListItem` corrected)
> **Goal:** Implement `GET /crm/students/grouped` per `backend_student_grouping_request.md`

---

### 4.1 — Create Response DTOs `(C-11)`

**`app/api/schemas/crm/student_grouped.py`:**
```python
class GroupByMode(str, Enum):
    DAY         = "day"
    COMPETITION = "competition"
    COURSE      = "course"
    AGE         = "age"
    GROUP       = "group"

class StudentGroup(BaseModel):
    key: str
    label: str
    count: int
    students: List[StudentListItem]

class GroupedStudentsResponse(BaseModel):
    group_by: GroupByMode
    total_unique_students: int
    groups: List[StudentGroup]
```

---

### 4.2 — Implement `GroupingService` strategies `(C-07)`

All rules from spec document are enforced:

| Strategy | Uniqueness | Unassigned bucket |
|----------|------------|-------------------|
| `day` | Student appears in EACH matching day | `"unassigned"` |
| `competition` | Student appears in EACH active competition | `"unassigned"` |
| `course` | Student in at most one course | `"unassigned"` |
| `age` | Student in exactly one bracket | `"unknown"` |
| `group` | Student in at most one group | `"unassigned"` |

Age brackets (fixed, uses `StudentValidator.classify_age_bracket`):
```python
AGE_BRACKETS = [
    ("age_4_7",    "4 – 7 years",   4,  7),
    ("age_7_9",    "7 – 9 years",   7,  9),
    ("age_9_12",   "9 – 12 years",  9, 12),
    ("age_12_15",  "12 – 15 years",12, 15),
    ("age_15_plus","15+ years",    15, None),
]
```

Day ordering (per spec):
```python
DAY_ORDER = ["saturday","sunday","monday","tuesday","wednesday","thursday","friday"]
```

Global constraints:
- No archived groups/courses/competitions
- Empty groups omitted from response
- `include_inactive=false` by default
- `unassigned`/`unknown` always last

---

### 4.3 — Create Router `(C-12)`

```python
# app/api/routers/crm/students_grouped.py
router = APIRouter(prefix="/crm", tags=["CRM — Students"])

@router.get(
    "/students/grouped",    # ← registered BEFORE /students/{id} in main.py
    response_model=ApiResponse[GroupedStudentsResponse],
    summary="Get students grouped by a dimension",
)
def get_students_grouped(
    group_by: GroupByMode = Query(...),
    include_inactive: bool = Query(False),
    current_user: User = Depends(require_any),
    svc: GroupingService = Depends(get_grouping_service),
):
    result = svc.get_grouped(group_by, include_inactive)
    return ApiResponse(data=GroupedStudentsResponse(...))
```

> [!IMPORTANT]
> Register `students_grouped.py` router **before** the main `students.py` router in `app/api/main.py` to prevent FastAPI from matching `/grouped` as a student ID.

---

**Phase 4 verification:**
```bash
pytest tests/test_crm_grouped.py -v
# Manual:
# GET /crm/students/grouped?group_by=day
# GET /crm/students/grouped?group_by=age
# GET /crm/students/grouped?group_by=invalid  → 422
# GET /crm/students/grouped?group_by=age&include_inactive=true
```

---

## Phase 5 — Enriched Student Details
> **Depends on:** Phase 2 (`ReportingService`), Phase 3 (corrected DTOs)
> **Goal:** Enrich `GET /crm/students/{id}/details` with attendance statistics.

---

### 5.1 — Add `AttendanceStats` to Details DTO `(M-08)`

```python
class AttendanceStats(BaseModel):
    total_sessions: int = 0
    attended: int = 0
    absent: int = 0
    cancelled: int = 0
    attendance_rate: float = 0.0

class StudentWithDetails(BaseModel):
    ...
    attendance_stats: AttendanceStats = Field(default_factory=AttendanceStats)  # NEW
```

---

### 5.2 — Implement `ReportingService.get_attendance_stats` `(C-08)`

Single aggregate query using `GROUP BY status` on the attendance table:

```python
def get_attendance_stats(self, student_id: int) -> AttendanceStatsDTO:
    with StudentUnitOfWork() as uow:
        return uow.students.get_attendance_stats(student_id)
```

In `StudentRepository.get_attendance_stats`:
```python
def get_attendance_stats(self, student_id: int) -> AttendanceStatsDTO:
    """Single DB query — GROUP BY status."""
    counts = dict(self._session.exec(
        select(Attendance.status, func.count(Attendance.id))
        .join(Enrollment, Attendance.enrollment_id == Enrollment.id)
        .where(Enrollment.student_id == student_id)
        .group_by(Attendance.status)
    ).all())
    total = sum(counts.values())
    attended  = counts.get("present", 0)
    absent    = counts.get("absent", 0)
    cancelled = counts.get("cancelled", 0)
    denom = total - cancelled
    return AttendanceStatsDTO(
        total_sessions=total,
        attended=attended, absent=absent, cancelled=cancelled,
        attendance_rate=round(attended / denom, 3) if denom > 0 else 0.0,
    )
```

---

**Phase 5 verification:**
```bash
pytest tests/test_crm_details.py -v
# Manual:
# GET /crm/students/1/details  → includes attendance_stats
# GET /crm/students/1/details  → primary_parent.is_primary == true
# GET /crm/students/1/details  → enrollments[0].level_number can be null (no 500)
```

---

## Phase 6 — Test Suite Expansion
> **Depends on:** Phases 1–5 complete
> **Goal:** ≥90% coverage on `app/modules/crm/` and `app/api/routers/crm/`

---

### Additions to `tests/test_crm.py` `(M-13)`

```python
# Status enum fixes (Phase 1)
def test_status_graduated_returns_422()
def test_status_summary_has_no_graduated_field()

# Contract fixes (Phase 3)
def test_student_list_has_status_field()
def test_student_detail_has_status_field()
def test_phone_search_returns_matching_student()
def test_delete_parent_no_double_commit()
def test_toggle_status_notes_via_body_not_query()
def test_update_status_invalid_value_returns_422()
def test_student_list_current_group_fields_populated()
def test_student_list_no_phantom_fields()

# Architecture (Phase 2)
def test_student_repository_is_class_based()
def test_student_uow_commits_atomically()
def test_student_validator_illegal_transition_raises()
def test_count_uses_select_count_not_len()   # performance guard
```

### `tests/test_crm_grouped.py` `(C-14)`

```python
class TestStudentsGrouped:
    def test_group_by_day_correct_structure()
    def test_group_by_day_unassigned_last()
    def test_group_by_day_order_sat_to_fri()
    def test_group_by_day_multi_appear_student()    # student in 2 days
    def test_group_by_age_bracket_boundaries()      # exact boundary: age 7 → age_7_9
    def test_group_by_age_excludes_empty_brackets()
    def test_group_by_age_unknown_for_null_dob()
    def test_group_by_course_each_student_once()
    def test_group_by_competition_multi_appear()
    def test_group_by_group_excludes_archived()
    def test_invalid_group_by_returns_422()
    def test_empty_groups_omitted()
    def test_include_inactive_flag()
    def test_total_unique_count_correct_for_multi_appear()
    def test_no_archived_data_in_any_mode()
```

### `tests/test_crm_details.py` `(C-15)`

```python
class TestStudentDetails:
    def test_details_includes_attendance_stats()
    def test_details_attendance_rate_calculation()
    def test_details_balance_summary_correct_totals()
    def test_details_null_level_number_no_500()
    def test_details_primary_parent_is_primary_true()
    def test_details_siblings_empty_for_only_child()
    def test_details_siblings_deduplicated_two_parents()
    def test_details_no_n1_queries()             # assert DB call count ≤ 5
    def test_details_student_not_found_returns_404()
```

---

## Dependency Graph

```
Phase 1   Model fixes + enum unification
    │
    ▼
Phase 2   SOLID architecture migration (interfaces, class repos, UoW, validators, services)
    │
    ├──▶ Phase 3   API contract fixes (routers updated to use new services)
    │         │
    │         ├──▶ Phase 4   Grouped endpoint (uses GroupingService + corrected StudentListItem)
    │         │
    │         └──▶ Phase 5   Enriched details (uses ReportingService + corrected DTOs)
    │
    └──▶ Phase 6   Tests (validates everything above)
```

---

## Breaking Changes Summary

| Change | Old | New |
|--------|-----|-----|
| `StudentStatus.GRADUATED` | Existed (silently failed in schemas) | Removed — 422 on attempt |
| `StudentStatusSummaryDTO.graduated` | Present | Removed |
| `StudentPublic.status` | Missing | Always present |
| `StudentListItem` group fields | Phantom nulls | Real data from JOIN |
| Repository style | Module-level functions | Class instances with injected Session |
| Service granularity | 1 class (StudentService) with all methods | 4 classes: Student, Search, Grouping, Reporting |
| `GET /history/recent` | `/history/recent` | `/crm/students/history/recent` |
| `POST /history/search` | `/history/search` | `/crm/students/history/search` |
| Toggle notes | `?notes=` query param | `{"notes":""}` request body |

> [!CAUTION]
> The 2 history route prefix changes are URL-breaking. Frontend must update fetch calls before this ships.
