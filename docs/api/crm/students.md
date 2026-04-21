# CRM Students API

Student management endpoints for the CRM module.

**Base Path:** `/crm`  
**Authentication:** JWT Bearer token required for all endpoints.

---

## Quick Reference

| Endpoint | Method | Auth | Response |
|----------|--------|------|----------|
| `/students` | GET | `require_any` | `PaginatedResponse<StudentListItem>` |
| `/students/filter` | GET | `require_any` | `ApiResponse<StudentFilterResultDTO>` |
| `/students` | POST | `require_admin` | `ApiResponse<StudentPublic>` |
| `/students/{id}` | GET | `require_any` | `ApiResponse<StudentPublic>` |
| `/students/{id}` | PATCH | `require_admin` | `ApiResponse<StudentPublic>` |
| `/students/{id}` | DELETE | `require_admin` | `ApiResponse<null>` |
| `/students/grouped` | GET | `require_admin` | `ApiResponse<StudentGroupedResultDTO>` |
| `/students/waiting-list` | GET | `require_admin` | `ApiResponse<List<StudentResponseDTO>>` |
| `/students/by-status/{status}` | GET | `require_admin` | `ApiResponse<List<StudentResponseDTO>>` |
| `/students/status-summary` | GET | `require_admin` | `ApiResponse<StudentStatusSummaryDTO>` |
| `/students/{id}/status` | PATCH | `require_admin` | `ApiResponse<StudentResponseDTO>` |
| `/students/{id}/status/toggle` | POST | `require_admin` | `ApiResponse<StudentResponseDTO>` |
| `/students/{id}/waiting-priority` | PATCH | `require_admin` | `ApiResponse<StudentResponseDTO>` |
| `/students/{id}/status-history` | GET | `require_admin` | `ApiResponse<List<StatusHistoryEntry>>` |
| `/students/{id}/details` | GET | `require_any` | `ApiResponse<StudentWithDetails>` |
| `/students/{id}/siblings` | GET | `require_any` | `ApiResponse<List<SiblingInfo>>` |
| `/students/{id}/parents` | GET | `require_any` | `ApiResponse<List<ParentPublic>>` |
| `/students/{id}/soft` | DELETE | `require_admin` | `ApiResponse<dict>` |
| `/students/{id}/restore` | POST | `require_admin` | `ApiResponse<dict>` |
| `/students/{id}/hard` | DELETE | `require_admin` | `ApiResponse<dict>` |
| `/admin/deleted-students` | GET | `require_admin` | `ApiResponse<List<StudentListItem>>` |

---

## Common Patterns

### Authentication
- `require_any` = Any authenticated user with valid JWT
- `require_admin` = User must have admin role

### Path Parameters
All `/{id}` endpoints require integer `student_id` as path parameter.

### Response Wrappers

**ApiResponse<T>**
```json
{
  "data": T,
  "message": "Optional message",
  "success": true
}
```

**PaginatedResponse<T>**
```json
{
  "data": [T],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

### Common Errors
- **401 Unauthorized** - Invalid or missing JWT
- **404 Not Found** - Resource doesn't exist
- **400 Bad Request** - Invalid input data

---

## List & Search Endpoints

### GET /crm/students

List and search students with pagination.

**Authentication:** `require_any` (any authenticated user)

**Query Parameters:**
| Name | Type | Required | Default | Constraints | Description |
|------|------|----------|---------|-------------|-------------|
| q | string | No | - | min 1, max 100 chars | Search by name or phone |
| skip | integer | No | 0 | ≥ 0 | Pagination offset |
| limit | integer | No | 50 | 1-200 | Page size |

**Response:** `PaginatedResponse<StudentListItem>`

---

### GET /crm/students/grouped

Group students by status, gender, or age bucket.

**Authentication:** `require_admin`

**Query Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| group_by | string | No | status | Group by: status, gender, age_bucket |
| include_inactive | boolean | No | false | Include inactive students |

**Response:** `ApiResponse<StudentGroupedResultDTO>`

---

### GET /crm/students/filter

Advanced student filtering with multiple criteria (age, status, courses, balance, etc.).

**Authentication:** `require_any`

**Full Documentation:** [students-filter.md](students-filter.md)

**Query Parameters:** See detailed documentation for all 14+ filter parameters.

**Response:** `ApiResponse<StudentFilterResultDTO>`

---

### GET /crm/students/waiting-list

Get students on the waiting list, ordered by priority.

**Query Parameters:** `skip`, `limit`, `order_by_priority`

**Response:** `ApiResponse<List<StudentResponseDTO>>`

---

### GET /crm/students/by-status/{status}

Get students filtered by enrollment status.

**Path Parameters:** `status` (active, waiting, inactive)

**Query Parameters:** `skip`, `limit`

**Response:** `ApiResponse<List<StudentResponseDTO>>`

**Errors:** 400 for invalid status

---

### GET /crm/students/status-summary

Get counts of students by enrollment status.

**Response:** `ApiResponse<StudentStatusSummaryDTO>`

```json
{
  "data": {
    "active": 120,
    "waiting": 15,
    "inactive": 5
  }
}
```

---

## CRUD Endpoints

### POST /crm/students

Register a new student. **Auth:** `require_admin`

**Request:** `RegisterStudentCommandDTO`

**Response:** `ApiResponse<StudentPublic>` (201 Created)

**Errors:** 400 for invalid input

---

### GET /crm/students/{student_id}

Get student by ID. **Auth:** `require_any`

**Response:** `ApiResponse<StudentPublic>`

**Errors:** 404

---

### PATCH /crm/students/{student_id}

Update student profile. **Auth:** `require_admin`

**Request:** `UpdateStudentDTO` (all fields optional)

**Response:** `ApiResponse<StudentPublic>`

**Errors:** 400, 404

---

### DELETE /crm/students/{student_id}

Delete a student by ID. **Auth:** `require_admin`

**Response:** `ApiResponse<null>`

**Errors:** 404

---

## Status Management Endpoints

### PATCH /crm/students/{student_id}/status

Update student enrollment status. **Auth:** `require_admin`

**Request:** `UpdateStudentStatusDTO` (`status`, `notes`)

**Response:** `ApiResponse<StudentResponseDTO>`

**Errors:** 400 for invalid status, 404

---

### POST /crm/students/{student_id}/status/toggle

Toggle student status between active and waiting. **Auth:** `require_admin`

**Query:** `notes` (optional audit notes)

**Response:** `ApiResponse<StudentResponseDTO>`

**Errors:** 400 (cannot toggle inactive), 404

---

### PATCH /crm/students/{student_id}/waiting-priority

Set waiting list priority. **Auth:** `require_admin`

**Request:** `SetWaitingPriorityDTO` (`priority`, `notes`)

**Response:** `ApiResponse<StudentResponseDTO>`

**Errors:** 404 if not on waiting list

---

### GET /crm/students/{student_id}/status-history

Get student status change history. **Auth:** `require_admin`

**Response:** `ApiResponse<List<StatusHistoryEntry>>`

**Errors:** 404

---

## Detail Endpoints

### GET /crm/students/{student_id}/details

Get complete student profile with enrollments, balance, siblings. **Auth:** `require_any`

**Response:** `ApiResponse<StudentWithDetails>` - see Schema section for full structure

**Errors:** 404

---

### GET /crm/students/{student_id}/siblings

Get student's siblings. **Auth:** `require_any`

**Response:** `ApiResponse<List<SiblingInfo>>`

**Errors:** 404

---

### GET /crm/students/{student_id}/parents

Get all parents linked to a student. **Auth:** `require_any`

**Response:** `ApiResponse<List<ParentPublic>>`

---

## Soft Delete Endpoints

### DELETE /crm/students/{student_id}/soft

Soft delete a student (logically removed, recoverable). Also cascades to payments. **Auth:** `require_admin`

**Response:** `ApiResponse<dict>` - `{student_id, status: "soft_deleted"}`

**Errors:** 404 (not found or already deleted)

---

### POST /crm/students/{student_id}/restore

Restore a previously soft-deleted student and their payments. **Auth:** `require_admin`

**Response:** `ApiResponse<dict>` - `{student_id, status: "restored"}`

**Errors:** 404 (not found or not deleted)

---

### DELETE /crm/students/{student_id}/hard

Permanently delete a student and all related data. Cannot be undone. **Auth:** `require_admin`

**Response:** `ApiResponse<dict>` - `{student_id, status: "permanently_deleted"}`

**Errors:** 404 (not found)

---

### GET /crm/admin/deleted-students

List all soft-deleted students for recovery. **Auth:** `require_admin`

**Query Parameters:** `skip` (default: 0), `limit` (default: 50, max: 100)

**Response:** `ApiResponse<List<StudentListItem>>`

---

## Schema Reference

### Core Student Schemas

**StudentPublic**
| Field | Type | Req | Description |
|-------|------|-----|-------------|
| id | integer | Y | Student ID |
| full_name | string | Y | Full name |
| date_of_birth | date | N | YYYY-MM-DD |
| gender | string | N | male, female, other |
| phone | string | N | Contact phone |
| status | string | Y | active, waiting, inactive |
| notes | string | N | Additional notes |
| is_active | boolean | Y | Active flag |
| created_at | datetime | Y | Creation timestamp |
| updated_at | datetime | Y | Last update timestamp |

**StudentListItem** - Subset of StudentPublic (id, full_name, phone, status, date_of_birth, gender)

**StudentResponseDTO** - Core fields (id, full_name, status, date_of_birth, gender, phone, is_active, waiting_since, waiting_priority)

**StudentWithDetails** extends StudentPublic with:
- `age`, `school_name`, `waiting_since`, `waiting_priority`, `waiting_notes`
- `primary_parent` (ParentInfo), `current_enrollment` (CurrentEnrollmentInfo)
- `enrollments`[], `balance_summary` (StudentBalanceSummary), `siblings`[]
- `sessions_attended_count`, `sessions_absent_count`, `last_session_attended`, `attendance_stats`

### Nested Objects

**ParentInfo**: id, full_name, phone, email, relationship

**ParentPublic**: id, full_name, phone, email, relationship (parent info for listings)

**CurrentEnrollmentInfo**: enrollment_id, group_id, group_name, course_id, course_name, level_number, instructor_name

**SiblingInfo**: id, full_name, date_of_birth, age, gender, parent_name, enrollment_count

**StudentBalanceSummary**: total_due, total_discount, total_paid, net_balance

**AttendanceStatsDTO**: attended, absent, late

**StatusHistoryEntry**: id, student_id, old_status, new_status, changed_at, changed_by, changed_by_name, reason, notes

### Request DTOs

**RegisterStudentCommandDTO**: full_name (Y), date_of_birth, gender, phone, parent_id, notes

**UpdateStudentDTO** (all optional): full_name, date_of_birth, gender, phone, notes

**UpdateStudentStatusDTO**: status (Y: active/waiting/inactive), notes

**SetWaitingPriorityDTO**: priority (Y: 1=highest), notes

### Summary DTOs

**StudentStatusSummaryDTO**: active, waiting, inactive counts

**StudentGroupedResultDTO**: groups (dict), total

---

## Notes

- All datetime fields are in ISO 8601 format (UTC)
- All decimal amounts are returned as numbers (not strings)
- `require_any` = any authenticated user with valid JWT
- `require_admin` = user must have admin role

### Error Response Format
```json
{
  "detail": "Error message",
  "status_code": 400
}
```
