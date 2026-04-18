# CRM API Documentation

Complete API reference for the CRM (Customer Relationship Management) module.

## Overview

The CRM API provides endpoints for managing students, parents, and tracking student lifecycle activities. All endpoints require JWT Bearer token authentication.

**Base URL:** `/crm`  
**Authentication:** JWT Bearer token in `Authorization` header

## Documentation Files

| File | Description | Endpoints |
|------|-------------|-----------|
| [students.md](students.md) | Student management | 17 endpoints |
| [students-history.md](students-history.md) | Activity tracking & history | 7 endpoints |
| [parents.md](parents.md) | Parent management | 5 endpoints |

**Total: 29 endpoints**

## Quick Reference

### Student Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/crm/students` | any | List/search students |
| POST | `/crm/students` | admin | Register new student |
| GET | `/crm/students/{id}` | any | Get student by ID |
| PATCH | `/crm/students/{id}` | admin | Update student |
| DELETE | `/crm/students/{id}` | admin | Delete student |
| GET | `/crm/students/{id}/details` | any | Full student profile |
| GET | `/crm/students/{id}/siblings` | any | Get siblings |
| GET | `/crm/students/{id}/parents` | any | Get linked parents |
| PATCH | `/crm/students/{id}/status` | admin | Update status |
| POST | `/crm/students/{id}/status/toggle` | admin | Toggle active/waiting |
| PATCH | `/crm/students/{id}/waiting-priority` | admin | Set priority |
| GET | `/crm/students/grouped` | admin | Grouped statistics |
| GET | `/crm/students/waiting-list` | admin | Waiting list |
| GET | `/crm/students/by-status/{status}` | admin | Filter by status |
| GET | `/crm/students/status-summary` | admin | Status counts |

### History & Activity Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/crm/students/{id}/history` | any | Activity history |
| GET | `/crm/students/{id}/activity-summary` | any | Summary by type |
| GET | `/crm/students/{id}/enrollment-history` | any | Enrollment changes |
| POST | `/crm/students/{id}/log-activity` | admin | Log manual activity |
| GET | `/crm/history/recent` | admin | Recent activities |
| POST | `/crm/history/search` | any | Search activities |

### Parent Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/crm/parents` | any | List/search parents |
| POST | `/crm/parents` | admin | Create parent |
| GET | `/crm/parents/{id}` | any | Get parent by ID |
| PATCH | `/crm/parents/{id}` | admin | Update parent |
| DELETE | `/crm/parents/{id}` | admin | Delete parent |

## Authentication

All endpoints require a valid JWT Bearer token:

```
Authorization: Bearer <jwt_token>
```

### Permission Levels

- **`require_any`**: Any authenticated user can access
- **`require_admin`**: Only users with admin role can access

## Common Response Format

### Success Response

```json
{
  "data": { ... },
  "message": "Optional success message",
  "success": true
}
```

### Paginated Response

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
  "detail": "Error description",
  "status_code": 400
}
```

## Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing/invalid token |
| 404 | Not Found |
| 422 | Validation Error |

## Schema Conventions

- **IDs**: Integer, positive values only
- **Dates**: ISO 8601 format (YYYY-MM-DD)
- **Datetimes**: ISO 8601 format with timezone (UTC)
- **Decimals**: Numbers (not strings)
- **Enums**: Validated against predefined values
- **Optional fields**: May be omitted or null

## Rate Limits & Validation

- **Query `limit`**: 
  - Students/Parents: 1-200 (default 50)
  - History: 1-100 (default 50)
- **Search terms**: Max 100 characters
- **Activity types**: Max 10 items in filter arrays

## See Also

- [students.md](students.md) - Student management API details
- [students-history.md](students-history.md) - Activity tracking API details
- [parents.md](parents.md) - Parent management API details
