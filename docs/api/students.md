# Student API Documentation

Complete reference for all student-related API endpoints in the Techno Terminal system.

## Base URL

All student API endpoints are prefixed with:
```
/api/v1
```

## Authentication

Authentication is required for all endpoints. Two permission levels are used:

- **Any authenticated user** (`require_any`) - Basic read access
- **Admin only** (`require_admin`) - Write/modify operations

Include a valid JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## API Modules

| Module | Description | File |
|--------|-------------|------|
| [Profile Management](./students/profile.md) | Student CRUD, registration, parent linking | `crm/students.py` |
| [Status & Enrollment](./students/status.md) | Status management, waiting list, priority | `crm/students.py` |
| [History & Activity](./students/history.md) | Activity tracking, enrollment history, search | `crm/students_history.py` |
| [Finance & Balance](./students/finance.md) | Balance inquiry, payments, receipts | `finance/` |
| [Schema Reference](./students/schemas.md) | All DTOs and request/response schemas | Various |

## Common Response Patterns

All API responses follow a consistent envelope pattern:

### Single Object Response
```json
{
  "data": { ... },
  "message": "Success message",
  "error": null
}
```

### Paginated List Response
```json
{
  "data": [ ... ],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

### Error Response
```json
{
  "data": null,
  "message": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Student not found"
  }
}
```

## HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PATCH, DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Validation errors, invalid input |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Schema validation failed |
| 500 | Internal Server Error | Server-side error |

## Error Codes

Common error codes used across student APIs:

- `NOT_FOUND` - Resource not found
- `VALIDATION_ERROR` - Input validation failed
- `BUSINESS_RULE_VIOLATION` - Operation violates business rules
- `ALREADY_EXISTS` - Duplicate resource
- `INVALID_STATUS_TRANSITION` - Invalid status change

## Quick Reference

### Student Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/crm/students` | Any | List/search students |
| GET | `/crm/students/{id}` | Any | Get student details |
| POST | `/crm/students` | Admin | Register new student |
| PATCH | `/crm/students/{id}` | Admin | Update student |
| DELETE | `/crm/students/{id}` | Admin | Delete student |
| GET | `/crm/students/{id}/parents` | Any | Get linked parents |
| PATCH | `/crm/students/{id}/status` | Admin | Update status |
| GET | `/crm/students/waiting-list` | Admin | Get waiting list |
| GET | `/students/{id}/history` | Any | Activity history |
| GET | `/students/{id}/balance` | Any | Get balance |

---

*Last updated: 2026-04-09*
