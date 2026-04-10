# Student API Schema Reference

Complete reference for all DTOs, request schemas, and response models used in the Student API.

---

## Table of Contents

1. [Profile Schemas](#profile-schemas)
2. [Status Management Schemas](#status-management-schemas)
3. [Activity & History Schemas](#activity--history-schemas)
4. [Finance & Balance Schemas](#finance--balance-schemas)
5. [Common Schemas](#common-schemas)

---

## Profile Schemas

### StudentPublic

**File:** `app/api/schemas/crm/student.py`

Full student profile returned by detail endpoints.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Student unique identifier |
| `full_name` | string | Yes | Student's full name |
| `date_of_birth` | date | No | Date of birth (ISO 8601) |
| `gender` | string | No | "male", "female", or "other" |
| `phone` | string | No | Contact phone number |
| `is_active` | boolean | Yes | Active status flag |
| `notes` | string | No | Additional notes |

**Example:**
```json
{
  "id": 1,
  "full_name": "John Doe",
  "date_of_birth": "2010-05-15",
  "gender": "male",
  "phone": "+1234567890",
  "is_active": true,
  "notes": "Math enthusiast"
}
```

---

### StudentListItem

**File:** `app/api/schemas/crm/student.py`

Slim representation for paginated list responses.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Student unique identifier |
| `full_name` | string | Yes | Student's full name |
| `phone` | string | No | Contact phone number |
| `is_active` | boolean | Yes | Active status flag |
| `notes` | string | No | Additional notes |
| `current_group_id` | integer | No | Current group assignment ID |
| `current_group_name` | string | No | Current group name |

**Example:**
```json
{
  "id": 1,
  "full_name": "John Doe",
  "phone": "+1234567890",
  "is_active": true,
  "notes": null,
  "current_group_id": 5,
  "current_group_name": "Mathematics Level 1"
}
```

---

### RegisterStudentCommandDTO

**File:** `app/modules/crm/schemas/student_schemas.py`

Request body for student registration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_data` | object | Yes | Student profile data |
| `student_data.full_name` | string | Yes | Student's full name |
| `student_data.date_of_birth` | date | No | Date of birth |
| `student_data.gender` | string | No | "male", "female", or "other" |
| `student_data.phone` | string | No | Contact phone |
| `student_data.notes` | string | No | Additional notes |
| `parent_id` | integer | No | Parent ID to link |
| `relationship` | string | No | Relationship to parent |
| `created_by_user_id` | integer | Yes | User creating the record |

**Example:**
```json
{
  "student_data": {
    "full_name": "Jane Smith",
    "date_of_birth": "2012-03-20",
    "gender": "female",
    "phone": "+1987654321",
    "notes": "New student"
  },
  "parent_id": 5,
  "relationship": "mother",
  "created_by_user_id": 1
}
```

---

### UpdateStudentDTO

**File:** `app/modules/crm/schemas/student_schemas.py`

Request body for updating student profile. All fields optional.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | string | No | Student's full name |
| `date_of_birth` | date | No | Date of birth |
| `gender` | string | No | "male", "female", or "other" |
| `phone` | string | No | Contact phone |
| `notes` | string | No | Additional notes |

**Example:**
```json
{
  "phone": "+1111222333",
  "notes": "Updated contact info"
}
```

---

## Status Management Schemas

### StudentStatus (Enum)

**File:** `app/modules/crm/schemas/student_schemas.py`

Enumeration of student enrollment statuses.

**Values:**
- `active` - Currently enrolled in classes
- `waiting` - On waiting list for enrollment
- `inactive` - Temporarily or permanently inactive
- `graduated` - Completed program

---

### StudentResponseDTO

**File:** `app/modules/crm/schemas/student_schemas.py`

API response wrapper for student operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Student ID |
| `full_name` | string | Yes | Student name |
| `status` | string | Yes | Current status |
| `waiting_since` | datetime | No | When added to waiting list |
| `waiting_priority` | integer | No | Priority on waiting list |
| `is_active` | boolean | Yes | Active flag |

**Example:**
```json
{
  "id": 1,
  "full_name": "John Doe",
  "status": "active",
  "waiting_since": null,
  "waiting_priority": null,
  "is_active": true
}
```

---

### UpdateStudentStatusDTO

**File:** `app/modules/crm/schemas/student_schemas.py`

Request body for status update.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | New status value |
| `notes` | string | No | Audit notes |

**Example:**
```json
{
  "status": "active",
  "notes": "Completed waiting period"
}
```

---

### SetWaitingPriorityDTO

**File:** `app/modules/crm/schemas/student_schemas.py`

Request body for setting waiting list priority.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `priority` | integer | Yes | Priority level (1=highest) |

**Example:**
```json
{
  "priority": 1
}
```

---

### StudentStatusSummaryDTO

**File:** `app/modules/crm/schemas/student_schemas.py`

Response with counts by status.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `active` | integer | Yes | Count of active students |
| `waiting` | integer | Yes | Count of waiting students |
| `inactive` | integer | Yes | Count of inactive students |
| `graduated` | integer | Yes | Count of graduated students |
| `total` | integer | Yes | Total count |

**Example:**
```json
{
  "active": 145,
  "waiting": 23,
  "inactive": 12,
  "graduated": 89,
  "total": 269
}
```

---

## Activity & History Schemas

### ActivityLogRequest

**File:** `app/api/schemas/students/history.py`

Request body for logging manual activity.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `activity_type` | string | Yes | Activity category |
| `activity_subtype` | string | No | Specific subtype |
| `reference_type` | string | No | Related entity type |
| `reference_id` | integer | No | Related entity ID |
| `description` | string | Yes | Human-readable description |
| `metadata` | object | No | Additional data |

**Example:**
```json
{
  "activity_type": "achievement",
  "activity_subtype": "exam_passed",
  "description": "Passed mid-term exam",
  "reference_type": "exam",
  "reference_id": 10,
  "metadata": {
    "score": 95,
    "exam_name": "Mathematics Mid-term"
  }
}
```

---

### ActivityLogResponseDTO

**File:** `app/api/schemas/students/activity.py`

Response for activity log entries.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `activity_id` | integer | Yes | Activity unique ID |
| `student_id` | integer | Yes | Student ID |
| `activity_type` | string | Yes | Activity category |
| `activity_subtype` | string | No | Specific subtype |
| `description` | string | Yes | Description |
| `reference` | object | No | Reference info |
| `performed_by` | object | No | Actor info |
| `meta` | object | No | Additional data |
| `created_at` | string | Yes | ISO timestamp |

**Example:**
```json
{
  "activity_id": 1,
  "student_id": 1,
  "activity_type": "enrollment",
  "activity_subtype": "transfer",
  "description": "Transferred to Group B",
  "reference": {
    "reference_type": "enrollment",
    "reference_id": 5
  },
  "performed_by": {
    "user_id": 3
  },
  "meta": {
    "previous_group_id": 2
  },
  "created_at": "2026-04-09T10:30:00Z"
}
```

---

### RecentActivityItemDTO

**File:** `app/api/schemas/students/activity.py`

Recent activity for admin dashboard.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `activity_id` | integer | Yes | Activity ID |
| `student_id` | integer | Yes | Student ID |
| `activity_type` | string | Yes | Activity category |
| `description` | string | Yes | Description |
| `created_at` | string | Yes | ISO timestamp |
| `performed_by_name` | string | No | User name |

**Example:**
```json
{
  "activity_id": 50,
  "student_id": 3,
  "activity_type": "payment",
  "description": "Payment received: $150.00",
  "created_at": "2026-04-09T15:45:00Z",
  "performed_by_name": "Admin User"
}
```

---

### ActivitySearchResultItemDTO

**File:** `app/api/schemas/students/activity.py`

Search result item for activity queries.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `activity_id` | integer | Yes | Activity ID |
| `student_id` | integer | Yes | Student ID |
| `activity_type` | string | Yes | Activity category |
| `description` | string | Yes | Description |
| `meta` | object | No | Additional data |
| `created_at` | string | Yes | ISO timestamp |

---

### ActivitySearchParams

**File:** `app/api/schemas/students/history.py`

Search parameters for activity queries.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `search_term` | string | No | Text search |
| `activity_types` | array | No | Filter by types |
| `date_from` | datetime | No | Start date |
| `date_to` | datetime | No | End date |
| `performed_by` | integer | No | User filter |
| `student_id` | integer | No | Student filter |
| `limit` | integer | No | Max results |

---

### EnrollmentHistoryEntry

**File:** `app/api/schemas/students/history.py`

Detailed enrollment history record.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Entry ID |
| `student_id` | integer | Yes | Student ID |
| `enrollment_id` | integer | Yes | Enrollment ID |
| `group_id` | integer | Yes | Group ID |
| `level_number` | integer | Yes | Level number |
| `action` | string | Yes | Action type |
| `action_date` | datetime | Yes | When action occurred |
| `previous_group_id` | integer | No | Previous group |
| `previous_level_number` | integer | No | Previous level |
| `amount_due` | decimal | Yes | Amount due |
| `amount_paid` | decimal | Yes | Amount paid |
| `final_status` | string | Yes | Final status |
| `notes` | string | No | Additional notes |

**Example:**
```json
{
  "id": 1,
  "student_id": 1,
  "enrollment_id": 5,
  "group_id": 3,
  "level_number": 2,
  "action": "transfer",
  "action_date": "2026-03-15T10:30:00Z",
  "previous_group_id": 2,
  "previous_level_number": 1,
  "amount_due": 150.00,
  "amount_paid": 150.00,
  "final_status": "completed",
  "notes": "Level promotion"
}
```

---

### ActivitySummaryItem

**File:** `app/api/schemas/students/history.py`

Activity count by type.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `activity_type` | string | Yes | Activity category |
| `count` | integer | Yes | Number of activities |

**Example:**
```json
{
  "activity_type": "enrollment",
  "count": 5
}
```

---

### Supporting DTOs

#### ActivityReferenceDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reference_type` | string | Yes | Entity type |
| `reference_id` | integer | Yes | Entity ID |

#### ActivityActorDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | integer | Yes | User ID |

#### ManualActivityResponseDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `activity_id` | integer | Yes | Activity ID |
| `student_id` | integer | Yes | Student ID |
| `activity_type` | string | Yes | Activity category |
| `description` | string | Yes | Description |
| `created_at` | string | Yes | ISO timestamp |

---

## Finance & Balance Schemas

### BalanceAdjustmentRequest

**File:** `app/api/schemas/finance/balance.py`

Request body for balance adjustment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `adjustment_amount` | decimal | Yes | Amount (neg=debit, pos=credit) |
| `reason` | string | Yes | Explanation |
| `adjustment_type` | string | Yes | Type: correction, refund, discount, other |

**Example:**
```json
{
  "adjustment_amount": -25.00,
  "reason": "Sibling discount",
  "adjustment_type": "discount"
}
```

---

### BalanceAdjustmentResponseDTO

**File:** `app/api/schemas/finance/balance.py`

Response for balance adjustment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_id` | integer | Yes | Student ID |
| `previous_balance` | decimal | Yes | Balance before |
| `adjustment_amount` | decimal | Yes | Amount adjusted |
| `new_balance` | decimal | Yes | Balance after |
| `reason` | string | Yes | Explanation |
| `adjustment_type` | string | Yes | Type |
| `adjusted_at` | datetime | Yes | Timestamp |
| `adjusted_by` | integer | Yes | User ID |

**Example:**
```json
{
  "student_id": 1,
  "previous_balance": -100.00,
  "adjustment_amount": -25.00,
  "new_balance": -75.00,
  "reason": "Sibling discount",
  "adjustment_type": "discount",
  "adjusted_at": "2026-04-09T14:30:00Z",
  "adjusted_by": 3
}
```

---

## Common Schemas

### ApiResponse<T>

Generic API response wrapper.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | T | No | Response data |
| `message` | string | No | Status message |
| `error` | Error | No | Error details |

### PaginatedResponse<T>

Paginated list response wrapper.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | T[] | Yes | List items |
| `total` | integer | Yes | Total count |
| `skip` | integer | Yes | Records skipped |
| `limit` | integer | Yes | Page size |

### Error

Error details object.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Error code |
| `message` | string | Yes | Error message |

---

*Last updated: 2026-04-09*
