# API Changes Log — April 2026

**Date:** 2026-04-02  
**Scope:** API Code Review — Medium-Term Fixes Complete

---

## Overview

This document summarizes the major API restructuring and improvements completed during the API code review session.

---

## 1. Router Restructuring

### Deleted Monolithic Routers
- `app/api/routers/analytics_router.py` (324 lines) → Split into 4 domain routers
- `app/api/routers/academics_router.py` (237 lines) → Split into 3 domain routers
- `app/api/routers/crm_router.py` (226 lines) → Split into 2 domain routers

### New Router Structure

```
app/api/routers/
├── analytics/
│   ├── __init__.py           # Exports: academic_router, financial_router, competition_router, bi_router
│   ├── academic.py           # 4 endpoints: dashboard, unpaid attendees, roster, heatmap
│   ├── financial.py          # 4 endpoints: revenue by date/method, outstanding, top debtors
│   ├── competition.py        # 1 endpoint: fee summary
│   └── bi.py                 # 7 endpoints: trends, retention, performance, funnel, value, utilization, flight-risk
│
├── academics/
│   ├── __init__.py           # Exports: courses_router, groups_router, sessions_router
│   ├── courses.py            # 3 endpoints: list, create, update
│   ├── groups.py             # 5 endpoints: list, get, create, update, list sessions
│   └── sessions.py           # 2 endpoints: add extra, update
│
├── crm/
│   ├── __init__.py           # Exports: students_router, parents_router
│   ├── students.py           # 5 endpoints: list/search, get, create, update, get parents
│   └── parents.py            # 4 endpoints: list/search, get, create, update
│
├── attendance_router.py      # 2 endpoints (unchanged)
├── enrollments_router.py     # 3 endpoints (unchanged)
├── finance_router.py         # 7 endpoints + 1 new (preview-risk)
├── competitions_router.py    # 2 endpoints (unchanged)
├── hr_router.py              # 7 endpoints + 4 new CRUD endpoints
└── auth_router.py            # 1 endpoint (unchanged)
```

---

## 2. New API Endpoints

### Analytics Endpoints (14 new)

| Method | Path | Description | Auth |
|:---|:---|:---|:---|
| GET | `/analytics/dashboard/summary` | High-level dashboard aggregates | admin |
| GET | `/analytics/academics/unpaid-attendees` | Students with unpaid balances | admin |
| GET | `/analytics/academics/groups/{id}/roster` | Group roster by level | admin |
| GET | `/analytics/academics/groups/{id}/heatmap` | Attendance heatmap | admin |
| GET | `/analytics/finance/revenue-by-date` | Daily revenue totals | admin |
| GET | `/analytics/finance/revenue-by-method` | Revenue by payment method | admin |
| GET | `/analytics/finance/outstanding-by-group` | Outstanding balances by group | admin |
| GET | `/analytics/finance/top-debtors` | Students with highest debt | admin |
| GET | `/analytics/competitions/fee-summary` | Competition fee summary | admin |
| GET | `/analytics/bi/enrollment-trend` | Enrollment trend over time | admin |
| GET | `/analytics/bi/retention` | Retention metrics by course | admin |
| GET | `/analytics/bi/instructor-performance` | Instructor performance | admin |
| GET | `/analytics/bi/retention-funnel` | Level retention funnel | admin |
| GET | `/analytics/bi/instructor-value` | Instructor value matrix | admin |
| GET | `/analytics/bi/schedule-utilization` | Schedule utilization % | admin |
| GET | `/analytics/bi/flight-risk` | Flight-risk students | admin |

### HR Endpoints (4 new)

| Method | Path | Description | Auth |
|:---|:---|:---|:---|
| GET | `/hr/employees/{id}` | Get employee by ID | admin |
| POST | `/hr/employees` | Create employee | admin |
| PUT | `/hr/employees/{id}` | Update employee | admin |
| GET | `/hr/staff-accounts` | List staff accounts | admin |

### Finance Endpoints (1 new)

| Method | Path | Description | Auth |
|:---|:---|:---|:---|
| POST | `/finance/receipts/preview-risk` | Preview overpayment risk | admin |

---

## 3. New DTOs (Data Transfer Objects)

### HR Schemas (`app/api/schemas/hr/`)

**employee.py:**
- `EmployeeListItem` — Slim employee for list views
- `EmployeeCreateInput` — Input for create/update operations
- `StaffAccountPublic` — Staff account with linked employee info

**attendance.py (new file):**
- `AttendanceLogInput` — Input for logging attendance
- `AttendanceLogOutput` — Output confirming log entry

### Finance Schemas

**finance_router.py (inline):**
- `PreviewRiskRequest` — Request body for preview-risk endpoint
- `OverpaymentRiskItem` — Risk item showing projected credit

---

## 4. Dependency Injection Updates

### New Service Factories (`app/api/dependencies.py`)

```python
# CRM Services
get_student_service() → StudentService
get_parent_service() → ParentService

# Academics Services
get_course_service() → CourseService
get_group_service() → GroupService
get_session_service() → SessionService

# Finance Service
get_finance_service() → FinanceModule

# Existing (unchanged)
get_attendance_service() → AttendanceService
get_competition_service() → CompetitionService
get_hr_service() → hr_service_module
get_academic_analytics_service() → AcademicAnalyticsService
get_financial_analytics_service() → FinancialAnalyticsService
get_bi_analytics_service() → BIAnalyticsService
get_competition_analytics_service() → CompetitionAnalyticsService
```

---

## 5. Error Handling Improvements

### HTTPException Handler (`app/api/exceptions.py`)

Added handler to convert FastAPI's `HTTPException` to standard `ErrorResponse` envelope:

```python
{
    "success": False,
    "error": "NotFound",  # Mapped from status code
    "message": "Employee not found"
}
```

Status code mappings:
- 400 → BadRequest
- 401 → Unauthorized
- 403 → Forbidden
- 404 → NotFound
- 409 → Conflict
- 422 → ValidationError
- 500 → InternalServerError

---

## 6. API Tags (Swagger UI)

| Old Tag | New Tags |
|:---|:---|
| `Analytics` | `Analytics — Academic`, `Analytics — Financial`, `Analytics — Competition`, `Analytics — BI` |
| `Academics` | `Academics — Courses`, `Academics — Groups`, `Academics — Sessions` |
| `CRM` | `CRM — Students`, `CRM — Parents` |
| `HR` | `HR` (unchanged) |
| `Finance` | `Finance` (unchanged) |
| `Competitions` | `Competitions` (unchanged) |
| `Attendance` | `Attendance` (unchanged) |
| `Enrollments` | `Enrollments` (unchanged) |

---

## 7. Files Created

### New Files
```
app/api/routers/analytics/__init__.py
app/api/routers/analytics/academic.py
app/api/routers/analytics/financial.py
app/api/routers/analytics/competition.py
app/api/routers/analytics/bi.py

app/api/routers/academics/__init__.py
app/api/routers/academics/courses.py
app/api/routers/academics/groups.py
app/api/routers/academics/sessions.py

app/api/routers/crm/__init__.py
app/api/routers/crm/students.py
app/api/routers/crm/parents.py

app/api/schemas/hr/attendance.py
```

### Files Deleted
```
app/api/routers/analytics_router.py
app/api/routers/academics_router.py
app/api/routers/crm_router.py
```

### Files Modified
```
app/api/main.py                    # Updated router imports
app/api/dependencies.py            # Added service factories
app/api/exceptions.py              # Added HTTPException handler
app/api/schemas/hr/employee.py   # Added StaffAccountPublic DTO
app/api/routers/hr_router.py     # Added typed DTOs to endpoints
app/api/routers/finance_router.py # Added preview-risk endpoint
```

---

## 8. Verification Checklist

- [x] All endpoints return typed `ApiResponse[T]` or `PaginatedResponse[T]`
- [x] No `ApiResponse[list[dict]]` or `ApiResponse[Any]` remaining
- [x] All services accessible via `Depends()` factories
- [x] Router imports updated in `main.py`
- [x] Exception handlers provide consistent error envelopes
- [x] Old monolithic router files deleted
- [x] All new packages have `__init__.py` with exports

---

## 9. Backward Compatibility

**Breaking Changes:** None for API consumers (all path prefixes unchanged)

**Internal Changes:**
- Router imports in `main.py` changed
- Old monolithic files removed (no longer importable)

---

## 10. Next Steps (Recommended)

1. **Testing:** Verify all endpoints in Swagger UI (`/docs`)
2. **Client Generation:** Regenerate API client if using OpenAPI generator
3. **Documentation:** Update external API documentation
4. **Monitoring:** Watch for any 500 errors after deployment

---

**Total Changes:**
- 16 new endpoints
- 4 new DTO files
- 9 new router files
- 3 deleted router files
- 6 modified supporting files
