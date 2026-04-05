# Techno Terminal - API Documentation Index

Complete API reference split by domain. All endpoints require Bearer token authentication unless noted.

---

## 🔐 Global Authentication

```http
Authorization: Bearer <access_token>
```

Get token via `POST /api/v1/auth/login`

---

## API Modules

| Module | File | Base Path | Endpoints |
|--------|------|-----------|-----------|
| **Academics** | [academics.md](academics.md) | `/api/v1/academics` | 26 endpoints |
| **Analytics** | [analytics.md](analytics.md) | `/api/v1/analytics` | 16 endpoints |
| **Attendance** | [attendance.md](attendance.md) | `/api/v1/attendance` | 2 endpoints |
| **Authentication** | [auth.md](auth.md) | `/api/v1/auth` | 6 endpoints |
| **CRM** | [crm.md](crm.md) | `/api/v1/crm` | 14 endpoints |
| **Competitions** | [competitions.md](competitions.md) | `/api/v1/competitions` | 8 endpoints |
| **Enrollments** | [enrollments.md](enrollments.md) | `/api/v1/enrollments` | 7 endpoints |
| **Finance** | [finance.md](finance.md) | `/api/v1/finance` | 8 endpoints |
| **HR** | [hr.md](hr.md) | `/api/v1/hr` | 6 endpoints |
| **Health** | [health.md](health.md) | `/` | 1 endpoint |

**Total: 90 API Endpoints**

---

## Quick Reference by Frontend Page

### Login Page
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/auth/login` | POST | User authentication |

### Dashboard
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/analytics/dashboard/summary` | GET | KPI cards |
| `/api/v1/academics/sessions/daily-schedule` | GET | Today's schedule |
| `/api/v1/analytics/academics/unpaid-attendees` | GET | Alert badges |

### Directory (Parents & Students)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/crm/parents` | GET | List/search parents |
| `/api/v1/crm/parents` | POST | Register parent |
| `/api/v1/crm/parents/{id}` | GET | Parent details |
| `/api/v1/crm/parents/{id}` | PATCH | Update parent |
| `/api/v1/crm/students` | GET | List/search students |
| `/api/v1/crm/students` | POST | Register student |
| `/api/v1/crm/students/{id}` | GET | Student details |
| `/api/v1/crm/students/{id}` | PATCH | Update student |
| `/api/v1/crm/students/{id}/parents` | GET | Student's parents |

### Group Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/academics/courses` | GET | Course dropdown |
| `/api/v1/academics/groups` | GET | List groups |
| `/api/v1/academics/groups` | POST | Create group |
| `/api/v1/academics/groups/{id}` | GET | Group details |
| `/api/v1/academics/groups/{id}` | PATCH | Update group |
| `/api/v1/academics/groups/{id}/sessions` | GET | Group sessions |
| `/api/v1/academics/groups/{id}/progress-level` | POST | Advance level |
| `/api/v1/analytics/academics/groups/{id}/roster` | GET | Group roster |
| `/api/v1/analytics/academics/groups/{id}/heatmap` | GET | Attendance heatmap |

### Attendance Grid
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/attendance/session/{id}` | GET | Current attendance |
| `/api/v1/attendance/session/{id}/mark` | POST | Save attendance |
| `/api/v1/finance/balance/student/{id}` | GET | Balance badges |

### Enrollment Center
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/enrollments` | POST | Enroll student |
| `/api/v1/enrollments/{id}` | DELETE | Drop enrollment |
| `/api/v1/enrollments/transfer` | POST | Transfer student |
| `/api/v1/enrollments/student/{id}` | GET | Enrollment history |

### Finance Desk
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/finance/receipts` | POST | Create receipt |
| `/api/v1/finance/receipts` | GET | Search receipts |
| `/api/v1/finance/receipts/{id}` | GET | Receipt details |
| `/api/v1/finance/receipts/{id}/pdf` | GET | Download PDF |
| `/api/v1/finance/refunds` | POST | Issue refund |
| `/api/v1/finance/balance/student/{id}` | GET | Student balance |
| `/api/v1/finance/competition-fees/student/{id}` | GET | Unpaid comp fees |
| `/api/v1/finance/receipts/preview-risk` | POST | Check overpayment |

### Competitions
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/competitions` | GET | List competitions |
| `/api/v1/competitions` | POST | Create competition |
| `/api/v1/competitions/{id}` | GET | Competition details |
| `/api/v1/competitions/{id}/categories` | GET | List categories |
| `/api/v1/competitions/{id}/categories` | POST | Add category |
| `/api/v1/competitions/register` | POST | Register team |
| `/api/v1/competitions/{comp_id}/categories/{cat_id}/teams` | GET | List teams |
| `/api/v1/competitions/team-members/{id}/pay` | POST | Mark fee paid |

### Reports & Analytics
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/analytics/finance/revenue-by-date` | GET | Revenue trend |
| `/api/v1/analytics/finance/revenue-by-method` | GET | Payment methods |
| `/api/v1/analytics/finance/outstanding-by-group` | GET | Group debts |
| `/api/v1/analytics/finance/top-debtors` | GET | Debtor list |
| `/api/v1/analytics/bi/enrollment-trend` | GET | Enrollment chart |
| `/api/v1/analytics/bi/retention` | GET | Retention metrics |
| `/api/v1/analytics/bi/instructor-performance` | GET | Instructor stats |
| `/api/v1/analytics/competitions/fee-summary` | GET | Competition fees |

### HR Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/hr/employees` | GET | List employees |
| `/api/v1/hr/employees` | POST | Create employee |
| `/api/v1/hr/employees/{id}` | GET | Employee details |
| `/api/v1/hr/employees/{id}` | PUT | Update employee |
| `/api/v1/hr/staff-accounts` | GET | List staff accounts |

### User Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/auth/me` | GET | Current user |
| `/api/v1/auth/refresh` | POST | Refresh token |
| `/api/v1/auth/logout` | POST | Logout |
| `/api/v1/auth/users` | POST | Create user |
| `/api/v1/auth/users/{id}/reset-password` | POST | Reset password |

---

## Common Response Envelopes

### Success Response (Single Item)
```json
{
  "success": true,
  "data": { ... },
  "message": null
}
```

### Success Response (Paginated List)
```json
{
  "success": true,
  "data": [ ... ],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

### Error Response
```json
{
  "success": false,
  "error": "NotFoundError",
  "message": "Student 123 not found"
}
```

---

## HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PATCH, PUT, DELETE |
| 201 | Created | Successful POST (new resource) |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Business rule violation (e.g., duplicate enrollment) |
| 422 | Validation Error | Invalid request data |
| 500 | Server Error | Unexpected server error |
