# Production Delivery Plan — Week of March 28, 2026

## Locked Decisions

| Decision | Choice |
|---|---|
| **Session injection** | Deferred — Pragmatic API Bridge (service classes keep internal `get_session()`) |
| **Authentication** | 100% Supabase JWT — no custom auth implementation |
| **Deployment** | Single server: FastAPI (port 8000) + Streamlit (port 8501) co-deployed |
| **Frontend framework** | TBD (likely Next.js) — scaffolded Day 4, full discussion after delivery |
| **Test strategy** | Manual smoke testing for this week — automated tests in post-delivery sprint |
| **Legacy flat modules** | `finance` and `hr` — fix bugs, do NOT refactor architecture this week |

---

## Priority Feature Order

> [!IMPORTANT]
> This order is absolute. If time pressure forces cuts, cut from the bottom. Never cut from the top.

1. 🔴 **Authentication** — Login, session validation, role enforcement
2. 🔴 **CRM** — Student & parent registration, search, management
3. 🔴 **Academics + Attendance** — Group management, session tracking, attendance marking
4. 🟡 **Finance** — Receipt creation, payment, balance, refunds, daily collections
5. 🟢 **Competitions** — View/register (non-blocking if delayed to Day 4)
6. ⚪ **HR** — Basic read endpoints only (create/update after delivery)
7. ⚪ **Analytics** — Deferred entirely until after delivery

---

## Architecture: The Pragmatic API Bridge

```
┌─────────────────────────────────────────────────────────┐
│                  Streamlit UI (Port 8501)                │
│   app/ui/pages/*.py → imports directly from module      │
│   facades (current pattern, unchanged this week)        │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│              Module Service Classes                      │
│  CompetitionService, TeamService, StudentService...      │
│  [ KEEP internal get_session() — no refactor ]          │
└──────────────┬──────────────────────────────────────────┘
               │ instantiated by
               ▼
┌─────────────────────────────────────────────────────────┐
│           FastAPI Dependency Factories                   │
│           app/api/dependencies.py                       │
│   def get_student_service() -> StudentService:          │
│       return StudentService()   ← pragmatic bridge      │
└──────────────┬──────────────────────────────────────────┘
               │ injected into
               ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Routers (Port 8000)                 │
│   /api/v1/students, /api/v1/auth, /api/v1/receipts...   │
│   Protected by Supabase JWT middleware                  │
└──────────────┬──────────────────────────────────────────┘
               │ consumed by
               ▼
┌─────────────────────────────────────────────────────────┐
│          Frontend Client (Next.js — TBD)                │
│     Calls FastAPI with Supabase access_token            │
└─────────────────────────────────────────────────────────┘
```

**Post-delivery technical debt (logged, not forgotten):**
- Session injection refactor across all 7 service classes
- IService Protocol definitions (Phases 4-5 from the previous plan)
- `finance` and `hr` Deep-SOLID migration

---

## FastAPI Directory Structure (To Be Created)

```
app/
└── api/
    ├── __init__.py
    ├── main.py                 ← FastAPI app entrypoint
    ├── middleware/
    │   ├── __init__.py
    │   └── auth_middleware.py  ← Supabase JWT validation
    ├── dependencies.py         ← Service factory functions (the pragmatic bridge)
    ├── schemas/
    │   ├── __init__.py
    │   └── common.py           ← Shared response envelopes (ApiResponse, ErrorResponse)
    └── routers/
        ├── __init__.py
        ├── auth.py             ← POST /auth/login, GET /auth/me
        ├── students.py         ← CRUD /students
        ├── parents.py        ← CRUD /parents
        ├── groups.py           ← GET/POST /groups
        ├── sessions.py         ← GET/POST /sessions
        ├── attendance.py       ← POST /attendance
        ├── enrollments.py      ← POST /enrollments
        ├── finance.py          ← POST /receipts, GET /finance/summary
        ├── competitions.py     ← GET /competitions (read-first)
        └── hr.py               ← GET /employees (basic)
```

---

## Day-by-Day Execution Plan

---

### 🔴 Day 1 — Streamlit Stabilization
**Deadline: End of March 28**
**Goal: Zero crashes on all priority pages. UI signed off.**

#### Step 1A — Fix Competitions Crash (Active Bug)
Apply Option A — reroute team calls in UI files.

**`app/ui/components/competition_overview.py`**
- Import `team_service as team_srv` alongside `competition_service as comp_srv`
- Reroute: `list_teams`, `list_team_members`, `register_team`, `pay_competition_fee` → `team_srv`

**`app/ui/components/competition_detail.py`**
- Reroute: `delete_team`, `add_team_member_to_existing` → `team_srv`

**`app/ui/components/student_detail.py`** + **`parent_detail.py`**
- Reroute: `get_student_competitions` → `team_srv`

**`app/modules/competitions/__init__.py`**
- Export `CompetitionService` + `TeamService` classes cleanly
- Remove the `competition_service = _competition_svc` patch alias

#### Step 1B — Priority Page Audit
Manually navigate every priority page and record any crash or `AttributeError`.

Pages to audit (in priority order):
- [ ] Login / Auth flow
- [ ] Student Overview (`1_Directory.py`)
- [ ] Parent Detail
- [ ] Student Detail
- [ ] Group Overview + Group Detail
- [ ] Attendance Grid
- [ ] Finance Overview + Finance Receipt
- [ ] Enrollment page

Fix any import errors found using the same pattern as Step 1A.

#### Step 1C — Finance Correctness Smoke Test
- [x] Create a test receipt with 2 payment lines
- [x] Verify balance updates correctly
- [x] Verify refund flow works end-to-end
- [x] Verify daily collections report reflects the test receipt

**Deliverable: Streamlit UI navigable with no crashes on all priority pages ✅ [COMPLETED]**

> [!WARNING]
> **DELIVERY PLAN PAUSED:** The deployment of the FastAPI bridge (Days 2-5) is temporarily suspended. We are executing a new Core Logic Refactoring Sprint (Architecting independent student financials, breaking the mandatory parent link, automated level progression, and session cancellation cascading) before returning to API scaffolding.

---

### 🔴 Day 2 — FastAPI Foundation
**Goal: FastAPI app running, Supabase JWT auth working, service bridge ready**

#### Step 2A — Project Scaffold

**[NEW] `app/api/__init__.py`** — empty

**[NEW] `app/api/main.py`**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import auth, students, parents

app = FastAPI(title="Techno Terminal API", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(parents.router, prefix="/api/v1")
```

#### Step 2B — Supabase JWT Auth Middleware

**[NEW] `app/api/middleware/auth_middleware.py`**
- Validates `Authorization: Bearer <supabase_access_token>` on every protected route
- Fetches the user's `supabase_uid` from the JWT payload
- Injects a `CurrentUser` context object (uid, role) into the request state
- Returns `401 Unauthorized` for missing or expired tokens

```python
from fastapi import Request, HTTPException
from app.core.supabase_clients import get_supabase_admin

async def verify_supabase_jwt(request: Request) -> dict:
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Missing auth token")
    try:
        user = get_supabase_admin().auth.get_user(token)
        return {"uid": user.user.id, "email": user.user.email}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

#### Step 2C — Dependency Factories (The Pragmatic Bridge)

**[NEW] `app/api/dependencies.py`**
```python
from app.modules.crm.services.student_service import StudentService
from app.modules.crm.services.parent_service import ParentService
from app.modules.auth.services.auth_service import AuthService
from app.modules.enrollments.services.enrollment_service import EnrollmentService
...

def get_student_service() -> StudentService:     return StudentService()
def get_parent_service() -> ParentService:   return ParentService()
def get_auth_service() -> AuthService:           return AuthService()
def get_enrollment_service() -> EnrollmentService: return EnrollmentService()
```

#### Step 2D — Common Response Schema

**[NEW] `app/api/schemas/common.py`**
```python
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
```

#### Step 2E — Auth + CRM Routers

**[NEW] `app/api/routers/auth.py`**
- `POST /api/v1/auth/login` — validates credentials via Supabase, returns session
- `GET /api/v1/auth/me` — returns current user profile from DB

**[NEW] `app/api/routers/students.py`**
- `GET /api/v1/students` — list/search students
- `POST /api/v1/students` — register new student
- `GET /api/v1/students/{id}` — get student detail
- `PATCH /api/v1/students/{id}` — update student
- `GET /api/v1/students/{id}/enrollments` — get student enrollments
- `GET /api/v1/students/{id}/competitions` — competition history

**[NEW] `app/api/routers/parents.py`**
- `GET /api/v1/parents` — list/search parents
- `POST /api/v1/parents` — register parent
- `GET /api/v1/parents/{id}` — parent detail + children
- `PATCH /api/v1/parents/{id}` — update parent

**Deliverable: FastAPI running on port 8000. `/api/v1/docs` accessible. Auth + CRM endpoints tested via Swagger UI ✅**

---

### 🟡 Day 3 — FastAPI: Academics, Attendance, Finance
**Goal: All priority business logic accessible via API**

#### Step 3A — Group & Session Routers

**[NEW] `app/api/routers/groups.py`**
- `GET /api/v1/groups` — all active groups (enriched)
- `POST /api/v1/groups` — schedule new group
- `GET /api/v1/groups/{id}` — group detail
- `PATCH /api/v1/groups/{id}` — update group
- `GET /api/v1/groups/{id}/sessions` — list sessions
- `POST /api/v1/groups/{id}/sessions` — add session

**[NEW] `app/api/routers/attendance.py`**
- `GET /api/v1/attendance/session/{session_id}` — roster with attendance status
- `POST /api/v1/attendance` — mark session attendance (bulk)
- `GET /api/v1/attendance/summary/{enrollment_id}` — attendance summary

**[NEW] `app/api/routers/enrollments.py`**
- `POST /api/v1/enrollments` — enroll student
- `DELETE /api/v1/enrollments/{id}` — drop enrollment
- `POST /api/v1/enrollments/{id}/transfer` — transfer student

#### Step 3B — Finance Routers

**[NEW] `app/api/routers/finance.py`**
- `POST /api/v1/receipts` — create receipt with charge lines
- `GET /api/v1/receipts/{id}` — receipt detail
- `GET /api/v1/receipts/search` — search receipts by date/parent/student
- `POST /api/v1/receipts/{id}/refund` — issue refund
- `GET /api/v1/finance/collections/daily` — daily collections report
- `GET /api/v1/finance/balance/{enrollment_id}` — enrollment balance
- `GET /api/v1/finance/student/{student_id}/summary` — student financial summary

**Deliverable: All priority business logic accessible via API. Full Swagger UI review ✅**

---

### 🟢 Day 4 — Competitions, HR basics + `run_api.py` entry point

#### Step 4A — Competitions Read Endpoints

**[NEW] `app/api/routers/competitions.py`**
- `GET /api/v1/competitions` — list competitions
- `GET /api/v1/competitions/{id}/summary` — full summary with categories and teams
- `POST /api/v1/competitions` — create competition
- `POST /api/v1/competitions/{id}/categories` — add category
- `POST /api/v1/competitions/{id}/teams` — register team
- `POST /api/v1/competitions/fees` — pay competition fee

#### Step 4B — HR Basic Read Endpoints

**[NEW] `app/api/routers/hr.py`**
- `GET /api/v1/employees` — list employees
- `GET /api/v1/employees/{id}` — employee detail
- `GET /api/v1/employees/instructors` — active instructors only

#### Step 4C — API Entrypoint Script

**[NEW] `run_api.py`** (root level, alongside `run_ui.py`)
```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
```

**Deliverable: Complete API surface live. All routers included in `app.include_router()`. `python run_api.py` starts cleanly ✅**

---

### 🔵 Day 5 — Integration Testing + Frontend Kickoff

#### Step 5A — Full API Smoke Test (Manual via Swagger)
Run through every priority flow end-to-end via `/api/v1/docs`:
- [ ] Login → receive token → use token on protected endpoints
- [ ] Register parent + student
- [ ] Enroll student in group
- [ ] Mark attendance for a session
- [ ] Create receipt with payment line → verify balance
- [ ] Issue refund → verify balance correction
- [ ] Get student financial summary

#### Step 5B — CORS + Frontend Auth Setup
- Finalize CORS origins in `main.py` for local frontend dev URL
- Document the Supabase auth flow for the frontend:
  - Frontend calls `supabase.auth.signIn()` → receives `access_token`
  - Frontend passes `Authorization: Bearer <access_token>` on every API request
  - FastAPI middleware validates via `get_supabase_admin().auth.get_user(token)`

#### Step 5C — Next.js Project Scaffold (if framework confirmed)
- Initialize Next.js project in a new `frontend/` directory
- Set up Supabase client + auth provider
- Create API client wrapper (`frontend/lib/api.ts`)
- Build the Login screen (the only screen needed to confirm the auth handshake works)

**Deliverable: API fully tested. Frontend auth handshake confirmed working. Ready for feature screens ✅**

---

## Post-Delivery Technical Debt Register

These items are logged, prioritized, and explicitly NOT forgotten:

| Item | Impact | Sprint |
|---|---|---|
| Session injection refactor (all 7 modules) | High — unlocks true atomic transactions | Sprint after delivery |
| IService Protocol definitions (Phases 4-5) | Medium — enables full DI testability | Same sprint |
| `crm` virtual facade object removal | Medium — code clarity | Same sprint |
| `finance` + `hr` Deep-SOLID migration | Low-Medium — maintainability | Dedicated sprint |
| Automated test suite (unit + integration) | High — safety net for future changes | Dedicated sprint |

---

## Open Questions Before Execution Begins

> [!IMPORTANT]
> Only one decision is needed before I start writing code:

1. **Next.js confirmed?** If yes, I scaffold the frontend on Day 5. If not, Day 5 is purely API testing + documentation. You can confirm this on Day 4 without blocking Days 1-4.
