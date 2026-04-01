# FastAPI Directory — Detailed Phased Implementation Plan

## Locked Design Decisions (Non-Negotiable)

| Decision | Choice |
|---|---|
| Role enforcement | **Option B** — full per-endpoint role gating |
| Session injection | **Option A (Pragmatic)** — services self-manage sessions for now |
| Read DTO location | **Option B** — `app/api/schemas/` owns all public-facing models |
| Response format | **Envelope** — `{ success, data, message }` on every response |

---

## Phase 0 — Foundation ✅ Already Done

| Item | File | Status |
|------|------|--------|
| FastAPI app factory + CORS | `app/api/main.py` | ✅ |
| Supabase JWT validation | `app/api/dependencies.py` | ✅ |
| Global exception mapping | `app/api/exceptions.py` | ✅ |
| Auth /me endpoint | `app/api/routers/auth.py` | ✅ |
| Health check | `app/api/main.py` | ✅ |

---

## Phase 1 — Shared Infrastructure

**Goal:** Create the plumbing every router will depend on.  
**Files to create:** 3

---

### [NEW] `app/api/schemas/common.py`

```python
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    """Single-item success wrapper."""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """List endpoint success wrapper."""
    success: bool = True
    data: list[T]
    total: int
    skip: int = 0
    limit: int = 50

class ErrorResponse(BaseModel):
    """Error response shape (also auto-emitted by exceptions.py)."""
    success: bool = False
    error: str    # machine-readable e.g. "NotFoundError"
    message: str  # human-readable detail
```

---

### [MODIFY] `app/api/dependencies.py`

Append to existing file (keep `get_db` and `get_current_user` intact):

```python
# ── Role guard factory ─────────────────────────────────────────────
from app.modules.auth.models import UserRole

def require_any_role(*roles: UserRole):
    def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, detail=f"Requires one of: {[r.value for r in roles]}")
        return user
    return _guard

require_admin      = require_any_role(UserRole.admin, UserRole.system_admin)
require_instructor = require_any_role(UserRole.instructor, UserRole.admin, UserRole.system_admin)
require_any        = get_current_user  # just: must be authenticated

# ── Service factories (Pragmatic Bridge) ───────────────────────────
from app.modules.crm.services.student_service import StudentService
from app.modules.crm.services.parent_service import ParentService
from app.modules.academics.services.course_service import CourseService
from app.modules.academics.services.group_service import GroupService
from app.modules.academics.services.session_service import SessionService
from app.modules.enrollments.services.enrollment_service import EnrollmentService
from app.modules.finance.finance_service import FinanceService

def get_student_service()    -> StudentService:    return StudentService()
def get_parent_service()     -> ParentService:     return ParentService()
def get_course_service()     -> CourseService:     return CourseService()
def get_group_service()      -> GroupService:      return GroupService()
def get_session_service()    -> SessionService:    return SessionService()
def get_enrollment_service() -> EnrollmentService: return EnrollmentService()
def get_finance_service()    -> FinanceService:    return FinanceService()
```

---

### [NEW] `app/api/middleware/logging_middleware.py`

```python
import time, uuid, logging
from fastapi import Request

logger = logging.getLogger("api.access")

async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000)
    logger.info(f"[{request_id}] {request.method} {request.url.path} → {response.status_code} ({duration}ms)")
    response.headers["X-Request-ID"] = request_id
    return response
```

Mount in `main.py`:
```python
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.middleware.logging_middleware import logging_middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)
```

**Acceptance:** `GET /health` logs a structured line with method, path, status, and latency.

---

## Phase 2 — CRM API 🔴

**Priority:** Highest — Students and Parents are the root of all other domain objects.

---

### [NEW] `app/api/schemas/crm/student.py`

```python
from pydantic import BaseModel
from datetime import date
from typing import Optional

class StudentPublic(BaseModel):
    """Full student profile — safe for API consumers."""
    id: int
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None

    model_config = {"from_attributes": True}

class StudentListItem(BaseModel):
    """Slim student for list endpoints."""
    id: int
    full_name: str
    phone: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}
```

---

### [NEW] `app/api/schemas/crm/parent.py`

```python
from pydantic import BaseModel
from typing import Optional

class ParentPublic(BaseModel):
    id: int
    full_name: str
    phone_primary: str
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}

class ParentListItem(BaseModel):
    id: int
    full_name: str
    phone_primary: str

    model_config = {"from_attributes": True}
```

---

### [NEW] `app/api/routers/crm.py`

```python
from fastapi import APIRouter, Depends, Query
from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.crm.student import StudentPublic, StudentListItem
from app.api.schemas.crm.parent import ParentPublic, ParentListItem
from app.api.dependencies import (
    require_admin, require_any,
    get_student_service, get_parent_service,
)
from app.modules.crm.schemas import RegisterStudentCommandDTO, UpdateStudentDTO
from app.modules.crm.schemas import RegisterParentInput, UpdateParentDTO
from app.modules.auth.models import User

router = APIRouter(prefix="/crm", tags=["CRM"])

# ── Students ───────────────────────────────────────────────────────

@router.get("/students", response_model=PaginatedResponse[StudentListItem])
def list_students(
    q: str = Query("", description="Search by name/phone"),
    skip: int = 0, limit: int = 50,
    _user: User = Depends(require_any),
    svc = Depends(get_student_service),
):
    results = svc.search_students(query=q)
    return PaginatedResponse(data=results[skip:skip+limit], total=len(results), skip=skip, limit=limit)

@router.get("/students/{student_id}", response_model=ApiResponse[StudentPublic])
def get_student(student_id: int, _user: User = Depends(require_any), svc = Depends(get_student_service)):
    student = svc.get_student_by_id(student_id)
    return ApiResponse(data=StudentPublic.model_validate(student))

@router.post("/students", response_model=ApiResponse[StudentPublic], status_code=201)
def create_student(body: RegisterStudentCommandDTO, _user: User = Depends(require_admin), svc = Depends(get_student_service)):
    student = svc.register_student(body)
    return ApiResponse(data=StudentPublic.model_validate(student), message="Student registered")

@router.patch("/students/{student_id}", response_model=ApiResponse[StudentPublic])
def update_student(student_id: int, body: UpdateStudentDTO, _user: User = Depends(require_admin), svc = Depends(get_student_service)):
    student = svc.update_student(student_id, body)
    return ApiResponse(data=StudentPublic.model_validate(student))

@router.get("/students/{student_id}/parents", response_model=ApiResponse[list[ParentPublic]])
def get_student_parents(student_id: int, _user: User = Depends(require_any), svc = Depends(get_student_service)):
    parents = svc.get_student_parents(student_id)
    return ApiResponse(data=[ParentPublic.model_validate(p) for p in parents])

# ── Parents ───────────────────────────────────────────────────────

@router.get("/parents", response_model=PaginatedResponse[ParentListItem])
def list_parents(q: str = Query(""), skip: int = 0, limit: int = 50, _user: User = Depends(require_any), svc = Depends(get_parent_service)):
    results = svc.search_parents(query=q)
    return PaginatedResponse(data=results[skip:skip+limit], total=len(results), skip=skip, limit=limit)

@router.get("/parents/{parent_id}", response_model=ApiResponse[ParentPublic])
def get_parent(parent_id: int, _user: User = Depends(require_any), svc = Depends(get_parent_service)):
    parent = svc.get_parent_by_id(parent_id)
    return ApiResponse(data=ParentPublic.model_validate(parent))

@router.post("/parents", response_model=ApiResponse[ParentPublic], status_code=201)
def create_parent(body: RegisterParentInput, _user: User = Depends(require_admin), svc = Depends(get_parent_service)):
    parent = svc.register_parent(body)
    return ApiResponse(data=ParentPublic.model_validate(parent), message="Parent registered")

@router.patch("/parents/{parent_id}", response_model=ApiResponse[ParentPublic])
def update_parent(parent_id: int, body: UpdateParentDTO, _user: User = Depends(require_admin), svc = Depends(get_parent_service)):
    parent = svc.update_parent(parent_id, body)
    return ApiResponse(data=ParentPublic.model_validate(parent))
```

**Acceptance:** 9 endpoints visible in `/docs`; `GET /crm/students` returns `PaginatedResponse`; `POST /crm/students` as instructor returns HTTP 403.

---

## Phase 3 — Academics + Attendance API 🔴

**Files:**
- `app/api/schemas/academics/course.py` — `CoursePublic`
- `app/api/schemas/academics/group.py` — `GroupPublic`
- `app/api/schemas/academics/session.py` — `SessionPublic`
- `app/api/routers/academics.py` — Courses, Groups, Sessions
- `app/api/routers/attendance.py` — Attendance (separate file — high-frequency, isolated)

**Key endpoints:**

| Method | Path | Auth |
|--------|------|------|
| GET | `/academics/courses` | any |
| POST | `/academics/courses` | admin |
| GET | `/academics/groups` | any |
| POST | `/academics/groups` | admin |
| GET | `/academics/groups/{id}` | any |
| GET | `/academics/groups/{id}/sessions` | any |
| POST | `/academics/groups/{id}/sessions` | admin |
| GET | `/attendance/session/{session_id}` | instructor |
| POST | `/attendance/mark` | instructor |

**Acceptance:** Instructors can `GET /attendance/session/{id}` and `POST /attendance/mark` but cannot `POST /academics/groups`.

---

## Phase 4 — Enrollments + Finance API 🟡

**Files:**
- `app/api/schemas/enrollments/enrollment.py` — `EnrollmentPublic`
- `app/api/schemas/finance/receipt.py` — `ReceiptPublic`, `ReceiptListItem`
- `app/api/schemas/finance/balance.py` — `BalanceSummaryPublic`
- `app/api/routers/enrollments.py`
- `app/api/routers/finance.py`

**Key endpoints:**

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/enrollments` | admin | `enroll_student` |
| DELETE | `/enrollments/{id}` | admin | `drop_enrollment` |
| POST | `/enrollments/{id}/transfer` | admin | `transfer_student` |
| GET | `/enrollments/student/{id}` | any | student enrollment history |
| POST | `/finance/receipts` | admin | `create_receipt_with_charge_lines` |
| GET | `/finance/receipts/{id}` | any | receipt detail |
| GET | `/finance/receipts` | admin | search (date, payer_name, receipt#) |
| POST | `/finance/receipts/{id}/refund` | admin | `issue_refund` |
| GET | `/finance/balance/student/{id}` | any | student financial summary |

**Acceptance:** `POST /finance/receipts` returns a receipt with a non-null `receipt_number` (B2 fix must be in place).

---

## Phase 5 — Auxiliary APIs 🟢

**Files:**
- `app/api/routers/competitions.py` — read-first
- `app/api/routers/hr.py` — read-only
- `app/api/routers/analytics.py` — dashboard aggregates

These are **stub routers** initially. Each file is created, mounted in `main.py`, and returns real data from the existing services. Write operations are added post-delivery.

---

## Phase 6 — Wire Everything into `main.py`

### [MODIFY] `app/api/main.py`

```python
from app.api.routers import auth, crm, academics, attendance, enrollments, finance, competitions, hr, analytics
from app.api.middleware.logging_middleware import logging_middleware
from starlette.middleware.base import BaseHTTPMiddleware

def create_app() -> FastAPI:
    app = FastAPI(title="Techno Terminal API", version="1.0.0", ...)
    
    app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)
    app.add_middleware(CORSMiddleware, ...)

    register_exception_handlers(app)

    app.include_router(auth.router,         prefix="/api/v1/auth",         tags=["Auth"])
    app.include_router(crm.router,          prefix="/api/v1",              tags=["CRM"])
    app.include_router(academics.router,    prefix="/api/v1",              tags=["Academics"])
    app.include_router(attendance.router,   prefix="/api/v1",              tags=["Attendance"])
    app.include_router(enrollments.router,  prefix="/api/v1",              tags=["Enrollments"])
    app.include_router(finance.router,      prefix="/api/v1",              tags=["Finance"])
    app.include_router(competitions.router, prefix="/api/v1",              tags=["Competitions"])
    app.include_router(hr.router,           prefix="/api/v1",              tags=["HR"])
    app.include_router(analytics.router,    prefix="/api/v1",              tags=["Analytics"])

    return app
```

---

## Verification Plan

1. `python run_api.py` starts cleanly with no import errors.
2. Open `http://localhost:8000/api/v1/docs` — all tags and endpoint groups visible.
3. Use Swagger "Authorize" with a valid Supabase token.
4. Smoke test per phase:
   - Phase 2: `GET /crm/students` → paginated list
   - Phase 2: `POST /crm/students` as instructor → HTTP 403
   - Phase 3: `GET /academics/groups` → enriched list
   - Phase 4: `POST /enrollments` → 201 created
   - Phase 4: `GET /finance/balance/student/1` → balance summary
5. Confirm all errors return `{ success: false, error: "...", message: "..." }` shape.

---

## Open Questions Before Execution

> [!IMPORTANT]
> **Do you want me to begin Phase 1 immediately?** I can generate all 3 Phase 1 files (`common.py`, updated `dependencies.py`, `logging_middleware.py`) in the next response, then proceed through the phases sequentially.
