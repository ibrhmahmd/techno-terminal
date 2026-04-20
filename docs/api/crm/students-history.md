# CRM Students History & Activity API

Activity tracking and history endpoints for student lifecycle events.

**Base Path:** `/crm`  
**Authentication:** JWT Bearer token required for all endpoints.

---

## Quick Reference

| Endpoint | Method | Auth | Response Type |
|----------|--------|------|---------------|
| `/students/{id}/history` | GET | `require_any` | `ApiResponse<List<ActivityLogResponseDTO>>` |
| `/students/{id}/activity-summary` | GET | `require_any` | `ApiResponse<List<ActivitySummaryItem>>` |
| `/students/{id}/enrollment-history` | GET | `require_any` | `PaginatedResponse<EnrollmentHistoryEntry>` |
| `/students/{id}/status-history` | GET | `require_any` | `PaginatedResponse<StatusHistoryEntry>` |
| `/students/{id}/competition-history` | GET | `require_any` | `PaginatedResponse<CompetitionHistoryEntry>` |
| `/students/{id}/log-activity` | POST | `require_admin` | `ApiResponse<ManualActivityResponseDTO>` |
| `/history/recent` | GET | `require_admin` | `ApiResponse<List<RecentActivityItemDTO>>` |
| `/history/search` | POST | `require_any` | `ApiResponse<List<ActivitySearchResultItemDTO>>` |

---

## Common Patterns

### Pagination Parameters

History endpoints use `PaginatedResponse`:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `limit` | integer | 50 | Max records (1-200) |
| `offset` | integer | 0 | Records to skip |

### PaginatedResponse Structure

```json
{
  "data": [...],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

### ApiResponse Structure

```json
{
  "data": T,
  "message": "Optional message",
  "success": true
}
```

---

## Endpoints

### GET /crm/students/{student_id}/history

Get student activity history (audit log).

**Query Parameters:** `activity_types`, `date_from`, `date_to`, `limit`

**Response:** `ApiResponse<List<ActivityLogResponseDTO>>`

---

### GET /crm/students/{student_id}/activity-summary

Get activity summary grouped by type.

**Query Parameters:** `date_from`, `date_to`

**Response:** `ApiResponse<List<ActivitySummaryItem>>`

---

### GET /crm/students/{student_id}/enrollment-history

Get enrollment lifecycle history with pagination.

**Query Parameters:** `limit` (default: 50), `offset` (default: 0)

**Response:** `PaginatedResponse<EnrollmentHistoryEntry>`

---

### GET /crm/students/{student_id}/status-history

Get status change history with pagination.

**Query Parameters:** `limit` (default: 50), `offset` (default: 0)

**Response:** `PaginatedResponse<StatusHistoryEntry>`

---

### GET /crm/students/{student_id}/competition-history

Get competition participation history with pagination.

**Query Parameters:** `limit` (default: 50), `offset` (default: 0)

**Response:** `PaginatedResponse<CompetitionHistoryEntry>`

---

### POST /crm/students/{student_id}/log-activity

Log a manual activity entry (admin only).

**Request Body:** `ActivityLogRequest`

**Response:** `ApiResponse<ManualActivityResponseDTO>`

---

### GET /crm/history/recent

Get recent activities across all students (admin/finance only).

**Query Parameters:** `limit` (default: 20), `activity_types`

**Response:** `ApiResponse<List<RecentActivityItemDTO>>`

---

### POST /crm/history/search

Search activities with advanced filters.

**Request Body:** `ActivitySearchParams`

**Response:** `ApiResponse<List<ActivitySearchResultItemDTO>>`

---

## Enums

### ActivityType

| Value | Description |
|-------|-------------|
| `registration` | Student registration |
| `status_change` | Status change (active/waiting/inactive) |
| `enrollment` | New enrollment |
| `enrollment_change` | Enrollment modification (transfer, drop) |
| `payment` | Payment recorded |
| `note_added` | Manual note or communication |
| `competition` | Competition registration |
| `deletion` | Student deletion |

### ReferenceType

| Value | Description |
|-------|-------------|
| `student` | Student record |
| `enrollment` | Enrollment record |
| `payment` | Payment record |
| `group` | Academic group |
| `course` | Course |
| `competition` | Competition |

---

## Schemas

### ActivityLogResponseDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Activity ID |
| student_id | integer | Yes | Student ID |
| activity_type | ActivityType | Yes | Type of activity |
| activity_subtype | string | No | Subtype (max 50 chars) |
| description | string | No | Human-readable description |
| reference_type | ReferenceType | No | Type of referenced entity |
| reference_id | integer | No | ID of referenced entity |
| performed_by_user_id | integer | Yes | User who performed action |
| performed_by_name | string | No | User's name |
| created_at | datetime | Yes | Timestamp |
| metadata | dict | No | Additional JSON data |

### ActivitySummaryItem

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| activity_type | ActivityType | Yes | Activity type |
| count | integer | Yes | Number of activities |

### EnrollmentHistoryEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| enrollment_id | integer | Yes | Enrollment ID |
| group_id | integer | Yes | Group ID |
| group_name | string | Yes | Group name |
| course_id | integer | Yes | Course ID |
| course_name | string | Yes | Course name |
| level_number | integer | Yes | Course level |
| enrollment_status | string | Yes | Enrollment status |
| action | string | Yes | Action type (enrolled, transferred, dropped) |
| action_date | datetime | Yes | When action occurred |
| previous_group_id | integer | No | Previous group (if transferred) |
| previous_level_number | integer | No | Previous level (if transferred) |
| amount_due | float | No | Amount due |
| discount_applied | float | No | Discount applied |
| transfer_reason | string | No | Reason for transfer |
| performed_by | integer | No | User ID who performed action |
| performed_by_name | string | No | User name |
| notes | string | No | Additional notes |

### StatusHistoryEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Activity log ID |
| student_id | integer | Yes | Student ID |
| old_status | string | No | Previous status |
| new_status | string | Yes | New status |
| changed_at | datetime | Yes | When status changed |
| changed_by | integer | No | User ID who made change |
| changed_by_name | string | No | User name |
| reason | string | No | Reason for change |
| notes | string | No | Additional notes |

### CompetitionHistoryEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Activity log ID |
| student_id | integer | Yes | Student ID |
| competition_id | integer | Yes | Competition ID |
| competition_name | string | No | Competition name |
| team_id | integer | No | Team ID |
| team_name | string | No | Team name |
| participation_type | string | Yes | Type (individual/team) |
| registration_date | datetime | No | Registration date |
| subscription_amount | float | No | Subscription amount |
| subscription_paid | boolean | No | Whether subscription is paid |

### ActivityLogRequest

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| activity_type | ActivityType | Yes | - | Activity type from enum |
| activity_subtype | string | No | max 50 chars | Subtype classification |
| description | string | No | max 500 chars | Description |
| reference_type | ReferenceType | No | - | Referenced entity type |
| reference_id | integer | No | > 0 | Referenced entity ID |

### ActivitySearchParams

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| search_term | string | No | max 100 chars | Search in description |
| activity_types | List<ActivityType> | No | max 10 items | Filter by types |
| date_from | datetime | No | - | Start date |
| date_to | datetime | No | must be ≥ date_from | End date |
| performed_by | integer | No | > 0 | User ID who performed |
| student_id | integer | No | > 0 | Filter by student |
| limit | integer | No | 1-100, default 50 | Max results |

### ManualActivityResponseDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Activity ID |
| student_id | integer | Yes | Student ID |
| activity_type | ActivityType | Yes | Activity type |
| description | string | No | Description |
| created_at | datetime | Yes | Timestamp |
| performed_by | integer | Yes | User ID |

### RecentActivityItemDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Activity ID |
| student_id | integer | Yes | Student ID |
| student_name | string | Yes | Student name |
| activity_type | ActivityType | Yes | Activity type |
| description | string | No | Description |
| created_at | datetime | Yes | Timestamp |
| performed_by_name | string | No | User name |

### ActivitySearchResultItemDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Activity ID |
| student_id | integer | Yes | Student ID |
| student_name | string | Yes | Student name |
| activity_type | ActivityType | Yes | Activity type |
| description | string | No | Description |
| created_at | datetime | Yes | Timestamp |
| performed_by_name | string | No | User name |

---

## Error Response

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

---

## Notes

- **ActivityType and ReferenceType** are enforced enums - invalid values return 400
- **Date validation:** `date_to` must be ≥ `date_from` if both provided
- **Pagination:** History endpoints use `PaginatedResponse` with `total`, `skip`, `limit`
- **Metadata:** Flexible JSON object for storing additional context
- **Automatic logging:** System logs registration, enrollment, status changes, payments, competitions
- **Manual logging:** Use `POST /crm/students/{id}/log-activity` for notes and custom events
