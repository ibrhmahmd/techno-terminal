# Techno Kids CRM — Refactoring Task Backlog

> **Source:** Architecture Review (2026-03-18)  
> **Updated:** Added design patterns + API layer planning per task  
> **Order logic:** Sequenced so no later task overwrites work done by an earlier one. Foundation first, structural second, coupling-fix third, naming last.

---

## API Layer — Strategic Overview

The `app/api/` directory exists but is empty (`.gitkeep` only). This is the intended future FastAPI REST layer. **Every refactoring task below has been designed with this layer in mind.** The following principles govern all decisions:

### The Transport-Agnostic Service Contract

```
Streamlit UI  ──→  app/modules/*/service.py  ──→  repository  ──→  DB
FastAPI Router ──→  app/modules/*/service.py  ──→  repository  ──→  DB
```

Services must be callable from both transports with **zero modification**. This means:

- Services **never** import `streamlit` (they don't — currently clean ✅)
- Services receive **plain Python types** (int, str, dict) not HTTP request objects
- Services return **ORM objects or dicts** — the router layer handles serialization
- Services raise **domain exceptions** — the router maps them to HTTP status codes

### What the API Layer Will Need (Pre-built by these tasks)

| Need | Built by |
|---|---|
| Typed domain exceptions → HTTP status codes | TASK-01 |
| Input validation reusable in Pydantic schemas | TASK-02 |
| Status enums usable in Pydantic response models | TASK-03 |
| Mockable repository interfaces for API tests | TASK-04 |
| Services that don't leak DB queries | TASK-05, TASK-06 |
| Services that don't reach into foreign modules | TASK-07, TASK-08 |
| Atomic operations (no partial-commit bugs) | TASK-09 |
| Clear public module interfaces for router imports | TASK-10 |

### What the API Layer Will Add (Not part of these tasks)

```
app/api/
├── dependencies.py      ← FastAPI Depends: get_db(), get_current_user()
├── exception_handlers.py ← Maps AppError subclasses to JSONResponse
├── routers/
│   ├── students.py      ← GET /students, POST /students/:id
│   ├── enrollments.py   ← POST /enroll, PUT /transfer
│   ├── finance.py       ← POST /receipts, POST /refund
│   └── ...
└── schemas/
    ├── student_schema.py ← Pydantic request/response DTOs
    └── ...
```

---

## Task Ordering Rationale

```
TASK-01 → TASK-02 → TASK-03   (shared foundation — must exist before any fix)
         ↓
       TASK-04                 (base repo protocol — enables API-layer mocking)
         ↓
     TASK-05 → TASK-06         (service query discipline)
         ↓
       TASK-07                 (cross-module coupling — enrollments)
         ↓
       TASK-08                 (cross-module coupling — finance→competitions)
         ↓
       TASK-09                 (multi-session atomic transactions)
         ↓
       TASK-10                 (file naming — done last, no logic impact)
```

---

---

# TASK-01 — Shared Exception Hierarchy

**Priority:** 🔴 Critical — Foundation for everything else  
**Effort:** Small (1–2 h)  
**Phase:** A — Shared Foundation  
**API Impact:** 🔴 Direct — exception classes map 1:1 to HTTP status codes

---

## Problem

Every service raises `ValueError` for all error types. The UI cannot differentiate "not found" from "validation failed" from "business rule violated". The future API router has no way to map these to correct HTTP status codes.

```python
raise ValueError("Student ID not found.")         # should be 404
raise ValueError("Phone already registered.")     # should be 409
raise ValueError("Already enrolled in group.")    # should be 409
raise ValueError("Amount must be > 0.")           # should be 422
```

---

## Solution

### Option A — Flat Typed Hierarchy ✅ Recommended

```python
# app/shared/exceptions.py

class AppError(Exception):
    """Base for all domain errors."""
    def __init__(self, message: str, detail: str | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail

class NotFoundError(AppError): pass        # → HTTP 404
class ValidationError(AppError): pass     # → HTTP 422
class BusinessRuleError(AppError): pass   # → HTTP 409
class ConflictError(AppError): pass       # → HTTP 409
class AuthError(AppError): pass           # → HTTP 401 / 403
```

**Pros:** Simple, maps to HTTP status codes, UI can differentiate  
**Cons:** Less granular — "Student not found" and "Group not found" are the same class

---

### Option B — Exceptions with Field Metadata

```python
class ValidationError(AppError):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field
```

**Pros:** API can return per-field validation errors (standard REST practice); Streamlit can highlight the specific input  
**Cons:** Every `raise` must include the `field=` kwarg — more discipline required

---

### Option C — Subclass ValueError (Backward-compatible half-measure)

```python
class NotFoundError(ValueError): ...
```

**Pros:** Existing `except ValueError` handlers still work  
**Cons:** Defeats the purpose — API router can't tell the classes apart from ValueError

---

## ✅ Recommendation: Option A now, evolve ValidationError toward Option B

---

## Design Patterns

| Pattern | Application |
|---|---|
| **Exception Hierarchy** | Parent `AppError` → typed children. Caller catches the most specific class it can handle |
| **Chain of Responsibility** | UI/Router catches in order: `NotFoundError` → `BusinessRuleError` → `ValidationError` → `AppError` → fallback |
| **Fail Fast** | Services raise immediately on first violation — no silent failures |

```python
# Streamlit UI — Chain of Responsibility
try:
    service.enroll_student(...)
except NotFoundError as e:
    st.warning(f"Not found: {e.message}")
except BusinessRuleError as e:
    st.error(f"Not allowed: {e.message}")
except ValidationError as e:
    st.error(f"Invalid input: {e.message}")

# FastAPI router — exception_handlers.py
@app.exception_handler(NotFoundError)
def handle_not_found(request, exc):
    return JSONResponse(status_code=404, content={"error": exc.message})

@app.exception_handler(BusinessRuleError)
def handle_conflict(request, exc):
    return JSONResponse(status_code=409, content={"error": exc.message})
```

---

## API Layer Impact

When the FastAPI router is added, `app/api/exception_handlers.py` registers one handler per exception class. **Zero changes to services.** The exception classes built in TASK-01 are the bridge between the domain and the HTTP layer.

---

## Files

| Action | File |
|---|---|
| **CREATE** | `app/shared/__init__.py` |
| **CREATE** | `app/shared/exceptions.py` |
| **MODIFY** | All 7 `service.py` files — replace `ValueError` |
| **MODIFY** | All UI components — add typed `except` blocks |

---

---

# TASK-02 — Shared Validators Module

**Priority:** 🔴 High  
**Effort:** Small (1 h)  
**Phase:** A — Shared Foundation  
**Depends on:** TASK-01  
**API Impact:** 🔴 Direct — validators reused inside Pydantic schemas

---

## Problem

`validate_phone()` is trapped inside `crm/service.py`. Any future module (HR, self-service portal) needing phone validation must either re-implement it or create an illegal cross-module import. Amount validation is inline and duplicated across finance and enrollments.

---

## Solution

### Option A — Module-level functions ✅ Recommended

```python
# app/shared/validators.py
import re
from app.shared.exceptions import ValidationError

def validate_phone(phone: str) -> str:
    if not phone:
        raise ValidationError("Phone is required.", field="phone")
    cleaned = re.sub(r"\D", "", phone)
    if len(cleaned) < 10:
        raise ValidationError(
            f"Phone '{phone}' must have at least 10 digits.", field="phone"
        )
    return cleaned

def validate_positive_amount(value: float, field: str = "amount") -> None:
    if value <= 0:
        raise ValidationError(f"{field} must be greater than 0.", field=field)

def validate_date_range(start, end, label: str = "date range") -> None:
    if start > end:
        raise ValidationError(f"Start must be before end in {label}.")
```

**Pros:** Pythonic — module as namespace; selective imports; no class overhead  
**Cons:** No grouping per domain

---

### Option B — Static method class

```python
class Validators:
    @staticmethod
    def phone(value: str) -> str: ...
    @staticmethod
    def positive_amount(value: float) -> None: ...
```

**Pros:** `Validators.phone(x)` is highly readable  
**Cons:** Class-as-namespace is un-Pythonic when there's no state

---

## ✅ Recommendation: Option A

---

## Design Patterns

| Pattern | Application |
|---|---|
| **Specification Pattern** | Each validator is a single, named rule. Compose them: `validate_phone(x); validate_positive_amount(y)` |
| **Guard Clause** | Fail at the top of the function on invalid input, then proceed with guaranteed-clean data |
| **Single Responsibility** | One function = one rule. Never combine phone + amount in the same validator |

### API Layer Reuse — Pydantic Integration

```python
# app/api/schemas/student_schema.py
from pydantic import BaseModel, field_validator
from app.shared.validators import validate_phone

class StudentCreateRequest(BaseModel):
    full_name: str
    phone: str | None = None

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v):
        if v:
            return validate_phone(v)   # ← reuse shared validator directly
        return v
```

The same rule enforced in the service is now also enforced at the API boundary — **one source of truth**.

---

## API Layer Impact

Pydantic schema validators call `shared.validators` functions. Invalid API requests are rejected before the service is ever called. The service still calls validators too (defense-in-depth). No duplication of rules.

---

## Files

| Action | File |
|---|---|
| **CREATE** | `app/shared/validators.py` |
| **MODIFY** | `app/modules/crm/service.py` — remove local `validate_phone`, import from shared |
| **MODIFY** | `app/modules/finance/service.py` — replace inline amount checks |

---

---

# TASK-03 — Shared Constants and Type Aliases

**Priority:** 🔴 High  
**Effort:** Small (1–2 h)  
**Phase:** A — Shared Foundation  
**Depends on:** TASK-01  
**API Impact:** 🟡 Indirect — enums used in Pydantic response models

---

## Problem

Status strings (`"active"`, `"dropped"`, etc.) are magic strings duplicated across 5+ modules. A single typo returns silent empty results. `WEEKDAYS`, time bounds, and payment method strings are scattered with no central definition.

---

## Solution

### Option A — `Literal` type aliases + constants ✅ Recommended for now

```python
# app/shared/constants.py
from typing import Literal
from datetime import time

EnrollmentStatus  = Literal["active", "completed", "transferred", "dropped"]
GroupStatus       = Literal["active", "completed", "cancelled"]
AttendanceStatus  = Literal["present", "absent", "late", "excused"]
PaymentMethod     = Literal["cash", "card", "transfer", "online"]
TransactionType   = Literal["charge", "payment", "refund"]
PaymentType       = Literal["course_level", "competition", "other"]
CourseCategory    = Literal["software", "hardware", "steam", "other"]
UserRole          = Literal["admin", "system_admin"]

WEEKDAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
CLASS_OPEN  = time(11, 0)   # 11:00 AM
CLASS_CLOSE = time(21, 0)   # 9:00 PM
```

**Pros:** IDE autocomplete; type-checker catches typos; non-breaking  
**Cons:** Runtime strings can still be wrong — `Literal` is only a static check

---

### Option B — `StrEnum` (Python 3.11+) ✅ Recommended for models

```python
from enum import StrEnum

class EnrollmentStatus(StrEnum):
    ACTIVE      = "active"
    COMPLETED   = "completed"
    TRANSFERRED = "transferred"
    DROPPED     = "dropped"
```

**Pros:** Runtime-safe; `EnrollmentStatus("typo")` raises immediately; works in SQLModel fields; Pydantic serializes `.value` automatically with `use_enum_values=True`  
**Cons:** Breaking change — `enrollment.status == "active"` must become `== EnrollmentStatus.ACTIVE`

---

## ✅ Recommendation: Option A now, migrate models to Option B progressively

`Literal` today gives type-checking. Migrate to `StrEnum` field-by-field when touching each model (no big-bang migration).

---

## Design Patterns

| Pattern | Application |
|---|---|
| **Value Object** | An enrollment status is a value with constrained domain. `StrEnum` makes it immutable and comparable by value |
| **Ubiquitous Language** | One name per concept across all layers: same constant used in service, repo, Pydantic schema, and API response |
| **Open/Closed** | Adding a new status means adding one line in `constants.py` — no grepping |

### API Layer Reuse

```python
# app/api/schemas/enrollment_schema.py
from pydantic import BaseModel
from app.shared.constants import EnrollmentStatus   # same type as the service uses

class EnrollmentResponse(BaseModel):
    id: int
    status: EnrollmentStatus     # Pydantic validates incoming JSON against the Literal
    student_id: int
```

Clients sending `{"status": "activee"}` get a 422 automatically — no service call needed.

---

## API Layer Impact

Constants flow directly into Pydantic schema field types. API responses document valid values in OpenAPI spec via `Literal` or `StrEnum`. Zero duplication.

---

## Files

| Action | File |
|---|---|
| **CREATE** | `app/shared/constants.py` |
| **MODIFY** | `app/modules/academics/service.py` — import `WEEKDAYS`, `CLASS_OPEN`, `CLASS_CLOSE` |
| **MODIFY** | `app/modules/enrollments/repository.py`, `service.py` |
| **MODIFY** | `app/modules/finance/service.py` |
| **MODIFY** | `app/modules/attendance/service.py` |

---

---

# TASK-04 — Base Repository Protocol

**Priority:** 🟡 High  
**Effort:** Medium (2–3 h)  
**Phase:** A — Shared Foundation  
**Depends on:** TASK-01, TASK-03  
**API Impact:** 🔴 Direct — enables dependency injection and mocking in API tests

---

## Problem

All 8 repos have inconsistent function naming. No enforced CRUD contract. Writing tests (unit or API integration) requires knowing the specific function name for each repo — impossible to mock generically.

| Module | Get by ID | Create | List |
|---|---|---|---|
| crm | `get_guardian_by_id` | `create_guardian` | `search_guardians` |
| enrollments | `get_enrollment` | `create_enrollment` | `list_enrollments` |
| finance | (none) | `create_receipt` | `list_receipts_by_date` |

---

## Solution

### Option A — `Protocol` (Structural subtyping) ✅ Recommended

```python
# app/shared/base_repository.py
from typing import Protocol, TypeVar, Sequence
from sqlmodel import Session

T = TypeVar("T")

class RepositoryProtocol(Protocol[T]):
    def get_by_id(self, session: Session, id: int) -> T | None: ...
    def create(self, session: Session, entity: T) -> T: ...
    def list_all(self, session: Session) -> Sequence[T]: ...
```

Each repo adds `get_by_id` as an alias — no inheritance required:

```python
# enrollments/repository.py
get_by_id = get_enrollment          # backward-compat alias
```

**Pros:** Duck typing — no inheritance; no runtime cost; type checkers verify conformance  
**Cons:** Aliases add minor noise

---

### Option B — Abstract Base Class (ABC)

```python
from abc import ABC, abstractmethod

class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    def get_by_id(self, session: Session, id: int) -> T | None: ...
```

**Pros:** Runtime-enforced — missing method raises `TypeError` on instantiation  
**Cons:** Requires converting free functions → class methods — breaks all service call sites

---

### Option C — Naming Convention Documentation Only

Document the standard in `MEMORY_BANK.md`. No code change.

**Pros:** Zero risk  
**Cons:** Not enforced — already drifted in current codebase

---

## ✅ Recommendation: Option A

---

## Design Patterns

| Pattern | Application |
|---|---|
| **Repository Pattern** (formal) | Repos become a defined abstraction, not an ad-hoc collection of functions |
| **Dependency Inversion Principle** | Services depend on the `RepositoryProtocol` interface, not concrete implementations |
| **Test Double / Stub** | API tests inject a fake repo that satisfies `RepositoryProtocol` — no real DB required |

### API Layer Impact — Dependency Injection for Testing

```python
# app/api/dependencies.py
from app.db.connection import get_session

def get_db():
    with get_session() as session:
        yield session   # FastAPI injects this into every route

# In tests — override with in-memory repo stub
app.dependency_overrides[get_db] = lambda: FakeSession()
```

Without a repo protocol, `FakeSession` has no typed interface to conform to. With TASK-04 in place, the test stub just needs to satisfy `RepositoryProtocol[T]`.

---

## Files

| Action | File |
|---|---|
| **CREATE** | `app/shared/base_repository.py` |
| **MODIFY** | `app/modules/enrollments/repository.py` |
| **MODIFY** | `app/modules/crm/repository.py` |
| **MODIFY** | `app/modules/finance/repository.py` |
| **MODIFY** | `MEMORY_BANK.md` |

---

---

# TASK-05 — Fix Service Layer Query Leaks

**Priority:** 🔴 Critical  
**Effort:** Medium (2–3 h)  
**Phase:** B — Service Layer Discipline  
**Depends on:** TASK-04  
**API Impact:** 🔴 Direct — leaky services cannot be tested without a live DB

---

## Problem

Two services bypass the repository layer with inline queries:

```python
# crm/service.py:143 — service opens session AND writes select()
with get_session() as session:
    stmt = sql_select(StudentGuardian).where(...)
    links = session.exec(stmt).all()
    ...

# enrollments/service.py:164 — same violation
with get_session() as session:
    stmt = select(Enrollment).where(Enrollment.student_id == student_id)
```

Testing these functions requires a real PostgreSQL connection. With the API layer, every route that calls these services becomes untestable without a live DB.

---

## Solution

### Option A — Move Queries to Repository ✅ Recommended

```python
# crm/repository.py
def get_students_by_guardian_id(
    session: Session, guardian_id: int, active_only: bool = True
) -> list[Student]:
    stmt = (
        select(Student)
        .join(StudentGuardian, StudentGuardian.student_id == Student.id)
        .where(StudentGuardian.guardian_id == guardian_id)
    )
    if active_only:
        stmt = stmt.where(Student.is_active == True)
    return list(session.exec(stmt).all())

# crm/service.py — now a pure orchestrator
def get_guardian_students(guardian_id: int) -> list[Student]:
    with get_session() as session:
        return repo.get_students_by_guardian_id(session, guardian_id)
```

**Pros:** Service is testable by mocking the repo; query is visible in repo's public API  
**Cons:** One additional function per module (minor)

---

### Option B — Comment and Leave (Technical debt acceptance)

**Pros:** Zero effort  
**Cons:** API tests require live DB; pattern spreads to new features

---

## ✅ Recommendation: Option A

---

## Design Patterns

| Pattern | Application |
|---|---|
| **Command Query Separation (CQS)** | Repos handle queries (read) and commands (write). Services only orchestrate — they don't query |
| **Humble Object** | The service becomes a thin coordinator. All testable logic lives in the repo (mockable) or service business rules (pure functions) |
| **Façade** | Service exposes a clean public method (`get_guardian_students`) while the complexity of joining through `StudentGuardian` lives inside the repo |

### API Layer Impact

```python
# app/api/routers/students.py
@router.get("/{student_id}/guardian")
def get_guardian(student_id: int, db: Session = Depends(get_db)):
    # After TASK-05: directly calls repo — mockable in tests
    return crm_repo.get_students_by_guardian_id(db, student_id)
```

Without TASK-05, the API route would have to call the service (which opens its own internal session), making the `db` dependency injection pointless and tests impossible.

---

## Files

| Action | File |
|---|---|
| **MODIFY** | `app/modules/crm/repository.py` — add `get_students_by_guardian_id()` |
| **MODIFY** | `app/modules/crm/service.py` — delegate; remove inline query |
| **MODIFY** | `app/modules/enrollments/repository.py` — add `get_enrollments_by_student()` |
| **MODIFY** | `app/modules/enrollments/service.py` — delegate; remove inline query |

---

---

# TASK-06 — Remove Raw SQL Leak from CRM Repository

**Priority:** 🟡 Medium  
**Effort:** Small (30 min)  
**Phase:** B — Service Layer Discipline  
**Depends on:** TASK-05  
**API Impact:** 🟢 Low

---

## Problem

`crm/repository.py` has a `from sqlalchemy import text` import buried at **line 86**, after all ORM functions. This violates PEP 8, mixes ORM and raw SQL in a module that should be ORM-only, and sets a bad precedent.

```python
# crm/repository.py — line 86 (mid-file import)
from sqlalchemy import text
def get_siblings(session, student_id):
    stmt = text("SELECT sibling_id, sibling_name FROM v_siblings ...")
```

---

## Solution

### Option A — Move import to top only (Minimal)

Move `from sqlalchemy import text` to line 1 alongside other imports.  
**Cons:** Still mixes ORM and raw SQL in a CRUD repo

---

### Option B — Replace with ORM join query ✅ Recommended

```python
def get_siblings(session: Session, student_id: int) -> list[dict]:
    guardian_links = session.exec(
        select(StudentGuardian).where(StudentGuardian.student_id == student_id)
    ).all()
    guardian_ids = [l.guardian_id for l in guardian_links]
    if not guardian_ids:
        return []

    sibling_links = session.exec(
        select(StudentGuardian)
        .where(StudentGuardian.guardian_id.in_(guardian_ids))
        .where(StudentGuardian.student_id != student_id)
    ).all()
    sibling_ids = {l.student_id for l in sibling_links}
    return [
        {"sibling_id": s.id, "sibling_name": s.full_name}
        for sid in sibling_ids
        if (s := session.get(Student, sid))
    ]
```

**Pros:** Pure ORM; consistent with rest of CRM repo; mockable by test stubs  
**Cons:** Two queries instead of one view query (negligible at this scale)

---

### Option C — Dedicated `crm_views.py` file

```python
# crm/crm_views.py — raw SQL against views
from sqlalchemy import text
def get_siblings_from_view(session, student_id) -> list[dict]: ...
```

**Pros:** Clear ORM vs view-SQL boundary per module  
**Cons:** Adds a new file pattern that all modules would eventually need

---

## ✅ Recommendation: Option B

---

## Design Patterns

| Pattern | Application |
|---|---|
| **Layer Isolation** | ORM repos stay ORM. Raw SQL is the analytics module's domain (ADR-9). CRM crosses the boundary only for a sibling query — replace with ORM |
| **Adapter** | If raw SQL must stay (performance reason emerges), wrap it in an adapter class that exposes the same `list[dict]` interface — the repo caller never sees it |

---

## Files

| Action | File |
|---|---|
| **MODIFY** | `app/modules/crm/repository.py` — replace `get_siblings`, remove `text` import |

---

---

# TASK-07 — Fix Cross-Module Coupling (Enrollments)

**Priority:** 🔴 Critical  
**Effort:** Medium (2–3 h)  
**Phase:** C — Cross-Module Coupling  
**Depends on:** TASK-05, TASK-01  
**API Impact:** 🔴 Direct — coupling prevents independent API routing per module

---

## Problem

`enrollments/service.py` imports from two foreign module **repositories** directly:

```python
from app.modules.crm.repository import get_student_by_id       # ← crosses boundary
from app.modules.academics.repository import list_groups_by_course  # ← crosses boundary
```

**Rule being violated:** Services may call other **services**, never another module's **repository**.

If CRM's repo is renamed or refactored (TASK-10), `enrollments/service.py` silently breaks. When the API layer adds independent routers per module, this coupling prevents deploying modules separately.

---

## Solution

### Option A — Route Through Service Layer ✅ Recommended

```python
# enrollments/service.py — after fix
from app.modules.crm.service import get_student_by_id as crm_get_student
from app.modules.academics.service import get_group_by_id as acad_get_group

def enroll_student(student_id, group_id, ...) -> tuple[Enrollment, bool]:
    student = crm_get_student(student_id)
    if not student:
        raise NotFoundError(f"Student {student_id} not found.")
    if not student.is_active:
        raise BusinessRuleError(f"Student '{student.full_name}' is inactive.")

    group = acad_get_group(group_id)
    if not group:
        raise NotFoundError(f"Group {group_id} not found.")
    ...
```

**Pros:** Clean module boundaries; each `get_*` call opens its own read session (fine for validation)  
**Cons:** Extra sessions for lookups — acceptable since they're read-only

---

### Option B — Pass Pre-Loaded Objects from the UI (Dependency Injection)

UI loads student + group before calling enrollment service, passes them in:  
**Pros:** No inter-service calls  
**Cons:** Business validation logic (active? status?) leaks into UI layer

---

### Option C — Shared Read Models (Data Transfer Objects)

```python
# app/shared/read_models.py
from dataclasses import dataclass

@dataclass(frozen=True)
class StudentRef:
    id: int
    full_name: str
    is_active: bool

@dataclass(frozen=True)
class GroupRef:
    id: int
    name: str
    status: str
    level_number: int
    max_capacity: int | None
```

Services return `StudentRef` / `GroupRef` for inter-module communication — no SQLModel model shared.

**Pros:** True decoupling — modules share a DTO contract, not a model class  
**Cons:** Added type layer to maintain; over-engineering for current team size

---

## ✅ Recommendation: Option A now, evolve toward Option C when API microservices are planned

---

## Design Patterns

| Pattern | Application |
|---|---|
| **Anti-Corruption Layer (ACL)** | The enrollment service translates between its own language and the CRM/Academics domain via service calls — it never sees the CRM schema directly |
| **Façade** | `crm.service.get_student_by_id()` is a façade that hides the repo, the session, and the model — enrollment only sees the result |
| **Dependency Inversion** | Enrollments depends on the CRM *service interface*, not the CRM *repository implementation* |
| **Data Transfer Object (DTO)** | Option C's `StudentRef` — a flat, immutable snapshot used only for cross-module reading |

### API Layer Impact

When the API adds independent routers:

```python
# app/api/routers/enrollments.py
@router.post("/enroll")
def enroll(payload: EnrollRequest, db: Session = Depends(get_db)):
    # Calls enrollment service — which calls crm.service and academics.service
    # Each module stays responsible for its own data
    enrollment, over_cap = enrollment_service.enroll_student(
        payload.student_id, payload.group_id, ...
    )
    return EnrollmentResponse.from_orm(enrollment)
```

With Option A, each module can later be extracted to a microservice and communication becomes an HTTP call between services — the same interface already used by the service layer.

---

## Files

| Action | File |
|---|---|
| **MODIFY** | `app/modules/enrollments/service.py` — replace repo imports with service imports |
| **MODIFY** | `app/modules/crm/service.py` — ensure `get_student_by_id()` is publicly exposed |
| **MODIFY** | `app/modules/academics/service.py` — verify `get_group_by_id()` is public |

---

---

# TASK-08 — Fix Cross-Module Coupling (Finance → Competitions)

**Priority:** 🔴 Critical  
**Effort:** Medium (2–3 h)  
**Phase:** C — Cross-Module Coupling  
**Depends on:** TASK-07  
**API Impact:** 🔴 Direct — finance router must not mutate competition domain data

---

## Problem

`finance/service.py` directly imports and mutates `TeamMember` (a competitions-domain model) inside `issue_refund()`:

```python
# finance/service.py:124 — Finance is doing Competitions work
if payment_type == "competition":
    from app.modules.competitions.models import TeamMember
    stmt = select(TeamMember).where(TeamMember.payment_id == payment_id)
    for m in db.exec(stmt).all():
        m.fee_paid = False
        m.payment_id = None
        db.add(m)
```

Finance owns receipts and payments. Competitions owns team membership and fee status. The `fee_paid` flag on `TeamMember` is **competitions data** — finance has no business touching it directly.

---

## Solution

### Option A — Finance Calls Competition Service ✅ Recommended

```python
# competitions/service.py — new function
def unmark_team_fee_for_payment(payment_id: int) -> None:
    """Revert fee_paid status when a competition payment is refunded."""
    with get_session() as db:
        stmt = select(TeamMember).where(TeamMember.payment_id == payment_id)
        for m in db.exec(stmt).all():
            m.fee_paid = False
            m.payment_id = None
            db.add(m)

# finance/service.py — after fix (competitions model import removed)
if payment_type == PaymentType.COMPETITION:
    from app.modules.competitions.service import unmark_team_fee_for_payment
    unmark_team_fee_for_payment(payment_id)
```

**Pros:** Competitions controls its own data; finance only triggers the action  
**Cons:** Still a direct import coupling between finance and competitions modules

---

### Option B — Event / Observer Pattern (Loose coupling)

```python
# app/shared/events.py
_handlers: dict[str, list] = {}

def on(event: str):
    def decorator(fn):
        _handlers.setdefault(event, []).append(fn)
        return fn
    return decorator

def emit(event: str, **kwargs):
    for fn in _handlers.get(event, []):
        fn(**kwargs)

# competitions/service.py — registers at import time
@events.on("payment.refunded")
def handle_payment_refunded(payment_id: int, payment_type: str, **_):
    if payment_type == "competition":
        unmark_team_fee_for_payment(payment_id)

# finance/service.py — no competition import at all
events.emit("payment.refunded", payment_id=payment_id, payment_type=payment_type)
```

**Pros:** Finance has zero knowledge of competitions — true decoupling; easily extensible  
**Cons:** Event flow is harder to trace/debug; ordering of handlers is implicit; over-engineering for current scale

---

### Option C — Move Finance-Competition Link Handling to UI

UI calls `finance.issue_refund()` then `competitions.unmark_fee()` separately.  
**Pros:** Dead simple  
**Cons:** Business logic in UI; refund and unmark are not atomic

---

## ✅ Recommendation: Option A now, Option B when the API adds webhooks or async events

---

## Design Patterns

| Pattern | Application |
|---|---|
| **Domain Ownership** | `fee_paid` belongs to the competitions domain. Finance triggers; competitions decides what to do |
| **Tell, Don't Ask** | Finance tells competitions "a payment was refunded" via a service call — it doesn't inspect competitions data to decide the action |
| **Observer / Event-Driven** | Option B applies this — finance emits a fact, competitions subscribes to act on it |
| **Bounded Context** | Finance context and Competitions context share `payment_id` as a linking key — not model objects |

### API Layer Impact

```python
# app/api/routers/finance.py
@router.post("/receipts/{receipt_id}/refund")
def refund(receipt_id: int, payload: RefundRequest, ...):
    result = finance_service.issue_refund(...)
    # finance_service internally calls competitions_service.unmark_team_fee_for_payment()
    # The API layer never touches competitions directly
    return RefundResponse(**result)
```

With Option A in place, the finance router stays completely isolated from the competitions router. The API's module boundaries match the code's module boundaries.

---

## Files

| Action | File |
|---|---|
| **MODIFY** | `app/modules/competitions/service.py` — add `unmark_team_fee_for_payment()` |
| **MODIFY** | `app/modules/finance/service.py` — remove inline `TeamMember` import; call competition service |

---

---

# TASK-09 — Fix Multi-Session Transaction Anti-Patterns

**Priority:** 🔴 Critical — Data integrity risk  
**Effort:** High (4–6 h)  
**Phase:** B/C — Service Layer & Integrity  
**Depends on:** TASK-07, TASK-08  
**API Impact:** 🔴 Direct — partial commits cause inconsistencies that API clients cannot detect or recover from

---

## Problem

### Case 1: `academics/service.py` — `schedule_group()` — 3 sessions

```
Session 1: group created → COMMITTED
Session 2: sessions created → (if this fails, group exists with no sessions)
Session 3: re-reads group → wasted round-trip
```

### Case 2: `finance/service.py` — `issue_refund()` — 3 sessions

```
Session 1: reads original payment → CLOSED
Session 2: refund receipt created → COMMITTED
Session 3: adds refund line + unmarks team fee → (if this fails, receipt exists with no payment line)
```

**API consequence:** A client that calls `POST /receipts/refund` and gets a 500 on Session 3 now has a dangling receipt in the DB. Re-trying the request creates a duplicate receipt. No `idempotency_key` protection exists.

---

## Solution

### Option A — Unit of Work (Single Session) ✅ Recommended

Refactor so one logical operation = one `with get_session()` block. Sub-functions accept the session as a parameter rather than opening their own.

```python
# academics/service.py — schedule_group() after fix
def schedule_group(data: dict) -> tuple[Group, list[CourseSession]]:
    _validate_times(data["default_time_start"], data["default_time_end"])

    with get_session() as session:                    # ← ONE session
        course = session.get(Course, data["course_id"])
        if not course:
            raise NotFoundError(f"Course {data['course_id']} not found.")

        group = Group(
            name=f"{data['default_day']} {_fmt_12h(data['default_time_start'])} - {course.name}",
            course_id=data["course_id"],
            instructor_id=data["instructor_id"],
            level_number=1,
            max_capacity=data.get("max_capacity", 15),
            default_day=data["default_day"],
            default_time_start=data["default_time_start"],
            default_time_end=data["default_time_end"],
        )
        session.add(group)
        session.flush()                               # get group.id without commit

        sessions = _create_sessions_in_session(      # ← uses SAME session
            session, group.id, 1,
            _next_weekday(date.today(), data["default_day"]),
            course.sessions_per_level,
            data["default_time_start"], data["default_time_end"],
            group.instructor_id,
        )
        return group, sessions
    # ← SINGLE commit here — group + sessions or nothing


def _create_sessions_in_session(
    session: Session, group_id: int, level_number: int,
    start_date: date, count: int, start_time: time,
    end_time: time, instructor_id: int
) -> list[CourseSession]:
    """Creates sessions within an existing session — does NOT commit."""
    created, d = [], start_date
    for i in range(count):
        cs = CourseSession(
            group_id=group_id, level_number=level_number,
            session_number=i + 1, session_date=d.isoformat(),
            start_time=start_time, end_time=end_time,
            actual_instructor_id=instructor_id,
            is_extra_session=False,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        session.add(cs)
        session.flush()
        created.append(cs)
        d += timedelta(weeks=1)
    return created
```

**Pros:** All-or-nothing atomicity; simpler mental model; eliminates orphaned rows  
**Cons:** Public `_create_sessions()` can no longer be called standalone (becomes private `_create_sessions_in_session()`)

---

### Option B — Savepoints (Nested Transactions)

```python
with get_session() as session:
    group = create_group(session, ...)
    session.flush()
    with session.begin_nested():      # PostgreSQL SAVEPOINT
        sessions = create_sessions_in_session(session, ...)
```

**Pros:** Can roll back sessions without rolling back the group  
**Cons:** Savepoint semantics are complex; you almost never want partial rollback here

---

### Option C — Compensating Transactions

On Session 2+ failure, explicitly delete what Session 1 committed.  
**Pros:** Keeps multi-session model  
**Cons:** Compensation logic is hard to write correctly; hard to test all failure paths

---

## ✅ Recommendation: Option A for all three affected functions

---

## Design Patterns

| Pattern | Application |
|---|---|
| **Unit of Work (UoW)** | All changes in one logical operation share one session. Commit once on success, rollback on any failure |
| **Transaction Script** | The service function is the transaction boundary — it opens a session, calls multiple repo functions within it, and closes (commits) at the end |
| **Idempotency Key** | Future API enhancement: API clients send `Idempotency-Key: uuid` header; server checks if the key already produced a committed result before re-executing |

### API Layer Impact

```python
# app/api/routers/academics.py
@router.post("/groups")
def create_group(payload: GroupCreateRequest, db: Session = Depends(get_db)):
    # After TASK-09: schedule_group() is one atomic transaction
    # If it raises NotFoundError → 404; if it raises any exception → full rollback
    group, sessions = academics_service.schedule_group(payload.dict())
    return GroupResponse.from_orm(group)
```

With Option A, the API route gets a guarantee: either the group AND its sessions are created, or nothing is. No cleanup logic needed in the router layer.

---

## Files

| Action | File |
|---|---|
| **MODIFY** | `app/modules/academics/service.py` — merge `_create_sessions` into single-session variant |
| **MODIFY** | `app/modules/crm/service.py` — `register_student()` sibling detection in fresh session (acceptable — read after commit) |
| **MODIFY** | `app/modules/finance/service.py` — `issue_refund()` merged into single session |

---

---

# TASK-10 — File Naming & Module API Surface

**Priority:** 🟡 Medium  
**Effort:** Medium (2–4 h)  
**Phase:** D — Naming / Structure  
**Depends on:** All previous tasks (done last)  
**API Impact:** 🟡 Indirect — clean `__init__.py` surfaces define the router's import contract

---

## Problem

Identical filenames across all 8 modules:

- Stack traces say `service.py line 45` — zero domain context
- IDE tab bar: three `service.py` tabs open simultaneously
- `grep "def create_"` returns 20+ results from all modules

Additionally, modules have no declared **public API surface** — callers import from deep internal paths (`from app.modules.crm.service import ...`) that expose internal structure.

---

## Solution

### Option A — `__init__.py` Re-exports Only

Declare what each module publicly exposes. No file renaming.

```python
# app/modules/crm/__init__.py
from .service import (
    register_guardian,
    find_or_create_guardian,
    search_guardians,
    register_student,
    search_students,
    find_siblings,
    get_guardian_students,
    get_student_by_id,
)
from .models import Student, Guardian, StudentGuardian

__all__ = [
    "register_guardian", "find_or_create_guardian", "search_guardians",
    "register_student", "search_students", "find_siblings",
    "get_guardian_students", "get_student_by_id",
    "Student", "Guardian", "StudentGuardian",
]
```

API routers then import cleanly:

```python
# app/api/routers/students.py
from app.modules.crm import search_students, get_student_by_id, Student
```

**Pros:** Clean public API without any file moves; caller never sees `service.py` or `repository.py`  
**Cons:** Stack traces still reference `service.py` internally

---

### Option B — Domain-Prefix File Renaming ✅ Recommended Option

| Old | New |
|---|---|
| `crm/service.py` | `crm/crm_service.py` |
| `crm/repository.py` | `crm/crm_repository.py` |
| `crm/models.py` | `crm/crm_models.py` |

**Pros:** Stack traces become `crm_service.py` — immediately informative  
**Cons:** Large find-and-replace of all internal imports

---

### Option C — Full Vertical Slice Directories

```
modules/crm/
├── register_student/
│   ├── handler.py
│   └── student_repo.py
├── search_students/
│   └── handler.py
```

**Pros:** Each use case is fully self-contained; perfect vertical slice  
**Cons:** Major restructure; shared models need a new home; overkill for a Streamlit internal tool

---

## ✅ Recommendation: Option A now, Option B if team grows beyond 2 developers

---

## Design Patterns

| Pattern | Application |
|---|---|
| **Vertical Slice Architecture** | Option C — organize by feature/use case, not by layer. Each slice owns its model, query, service logic |
| **Façade Pattern** | `__init__.py` is the module's façade — exposes a curated API, hides internal file structure |
| **Information Hiding** | Callers importing from `app.modules.crm` don't know whether the function lives in `service.py` or `repository.py` — the module decides |

### API Layer Impact

```python
# Without TASK-10 (current):
from app.modules.crm.service import register_student, search_students
from app.modules.crm.models import Student

# After TASK-10 Option A:
from app.modules.crm import register_student, search_students, Student
# ↑ router imports are clean; module internals can be reorganized freely
```

The API's router files become the primary beneficiary — they import a clean, stable interface instead of reaching into implementation files.

---

## Files

| Action | File |
|---|---|
| **MODIFY** | `app/modules/crm/__init__.py` |
| **MODIFY** | `app/modules/enrollments/__init__.py` |
| **MODIFY** | `app/modules/finance/__init__.py` |
| **MODIFY** | `app/modules/academics/__init__.py` |
| **MODIFY** | `app/modules/competitions/__init__.py` |
| **MODIFY** | `app/modules/analytics/__init__.py` |
| **MODIFY** | `app/modules/attendance/__init__.py` |
| **MODIFY** | `app/modules/auth/__init__.py` |
| **UPDATE** | `MEMORY_BANK.md` — document the new import convention |

---

---

# Appendix A: Design Pattern Index

| Pattern | Tasks Using It |
|---|---|
| Chain of Responsibility | TASK-01 (UI error handling) |
| Exception Hierarchy | TASK-01 |
| Fail Fast / Guard Clause | TASK-01, TASK-02 |
| Specification Pattern | TASK-02 (validators as named rules) |
| Value Object | TASK-03 (status enums are immutable domain values) |
| Ubiquitous Language | TASK-03 (one constant name used across all layers) |
| Repository Pattern (formal) | TASK-04 |
| Dependency Inversion Principle | TASK-04, TASK-07 |
| Test Double / Stub | TASK-04 (API test injection) |
| Command Query Separation (CQS) | TASK-05 (repos = query; services = orchestrate) |
| Humble Object | TASK-05 (thin service, testable repo) |
| Adapter | TASK-06 (wrap raw SQL behind ORM interface) |
| Anti-Corruption Layer (ACL) | TASK-07 (enrollments never sees CRM schema) |
| Data Transfer Object (DTO) | TASK-07 Option C (StudentRef, GroupRef) |
| Bounded Context | TASK-08 (finance and competitions share payment_id as key, not objects) |
| Domain Ownership / Tell Don't Ask | TASK-08 |
| Observer / Event-Driven | TASK-08 Option B |
| Unit of Work (UoW) | TASK-09 |
| Transaction Script | TASK-09 |
| Idempotency Key | TASK-09 (future API enhancement) |
| Façade | TASK-05, TASK-07, TASK-10 |
| Vertical Slice Architecture | TASK-10 Option C |
| Information Hiding | TASK-10 |

---

# Appendix B: API Layer Migration Path

Once all 10 tasks are complete, adding the FastAPI layer requires:

```
Step 1 — Add fastapi, uvicorn to requirements.txt
Step 2 — Create app/api/dependencies.py
          get_db() → yields Session (FastAPI Depends)
          get_current_user() → validates JWT token

Step 3 — Create app/api/exception_handlers.py
          Maps AppError subclasses (TASK-01) to JSONResponse with HTTP codes:
          NotFoundError     → 404
          ValidationError   → 422
          BusinessRuleError → 409
          ConflictError     → 409
          AuthError         → 401

Step 4 — Create app/api/schemas/
          Pydantic request/response DTOs per module
          Reuse shared validators (TASK-02) inside @field_validator
          Reuse constants (TASK-03) as field types

Step 5 — Create app/api/routers/ (one file per module)
          Import from module __init__.py (TASK-10)
          Call services with plain Python args
          Return Pydantic schemas

Step 6 — Mount routers in app/api/main.py
          Register exception handlers
          Services unchanged — transport-agnostic by design
```

**Total estimated effort to add the API layer after all TASK-01–10 are done: 1–2 days.**  
**Without these tasks done first: 1–2 weeks** (debugging coupling, rewriting session logic for FastAPI's dependency injection model, adding exception mapping).

---

# Appendix C: Task Summary Table

| Task | Problem | Design Pattern | API Impact | Effort |
|---|---|---|---|---|
| TASK-01 | Flat ValueError | Exception Hierarchy, Chain of Responsibility | HTTP status mapping | Small |
| TASK-02 | Validator trapped in CRM | Specification, Guard Clause | Pydantic reuse | Small |
| TASK-03 | Magic status strings | Value Object, Ubiquitous Language | Pydantic field types | Small |
| TASK-04 | No repo contract | Repository Pattern, DIP | Test mocking | Medium |
| TASK-05 | Service writes queries | CQS, Humble Object | Testability | Medium |
| TASK-06 | Raw SQL in ORM module | Adapter, Layer Isolation | Minor | Small |
| TASK-07 | Enrollments → CRM repo | ACL, Façade, DIP | Independent routing | Medium |
| TASK-08 | Finance → Competition model | Bounded Context, Observer | Isolated routers | Medium |
| TASK-09 | Multi-session partial commits | Unit of Work, Transaction Script | Idempotency | High |
| TASK-10 | Identical file names | Façade, Information Hiding | Clean router imports | Medium |
