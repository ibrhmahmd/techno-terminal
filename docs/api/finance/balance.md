# Finance API - Balance Operations

Student balance inquiry endpoints.

**Base Path:** `/api/v1`

---

## Table of Contents

1. [Get Student Balance](#get-student-balance)
2. [List Unpaid Enrollments](#list-unpaid-enrollments)

---

## Get Student Balance

Retrieve comprehensive balance information for a student including all enrollment details.

### Endpoint
```
GET /students/{student_id}/balance
```

### Authentication
Any authenticated user (Bearer token required)

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `student_id` | integer | Student unique identifier |

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `use_materialized` | boolean | No | true | Use fast materialized balance if available |

### Response

**200 OK**
```json
{
  "data": {
    "student_id": 1,
    "total_amount_due": 450.00,
    "total_discounts": 50.00,
    "total_paid": 300.00,
    "net_balance": -100.00,
    "enrollments": [
      {
        "enrollment_id": 5,
        "group_id": 3,
        "group_name": "Mathematics A",
        "level_number": 2,
        "amount_due": 150.00,
        "discount_applied": 25.00,
        "total_paid": 100.00,
        "remaining_balance": -25.00,
        "status": "active"
      }
    ]
  },
  "message": "Student balance retrieved successfully",
  "error": null
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `student_id` | integer | Student identifier |
| `total_amount_due` | decimal | Sum of all enrollment amounts |
| `total_discounts` | decimal | Total discounts applied |
| `total_paid` | decimal | Total payments received |
| `net_balance` | decimal | Negative = debt, Positive = credit |
| `enrollments` | array | Per-enrollment balance details |

---

## List Unpaid Enrollments

Get all unpaid enrollments with balance details, optionally filtered by group.

### Endpoint
```
GET /balance/unpaid-enrollments
```

### Authentication
Any authenticated user

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `group_id` | integer | No | null | Filter by specific group |
| `skip` | integer | No | 0 | Number of records to skip |
| `limit` | integer | No | 50 | Records per page (1-200) |

### Response

**200 OK**
```json
{
  "data": [
    {
      "enrollment_id": 5,
      "student_id": 1,
      "student_name": "John Doe",
      "group_id": 3,
      "group_name": "Mathematics A",
      "course_name": "Mathematics",
      "level_number": 2,
      "amount_due": 150.00,
      "discount_applied": 25.00,
      "total_paid": 50.00,
      "remaining_balance": -75.00,
      "enrolled_at": "2026-01-15T08:00:00Z"
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 50
}
```

## Schemas

### StudentBalanceResponse

```json
{
  "student_id": 1,
  "total_amount_due": 450.00,
  "total_discounts": 50.00,
  "total_paid": 300.00,
  "net_balance": -100.00,
  "enrollments": [
    {
      "enrollment_id": 5,
      "group_id": 3,
      "group_name": "Mathematics A",
      "level_number": 2,
      "amount_due": 150.00,
      "discount_applied": 25.00,
      "total_paid": 100.00,
      "remaining_balance": -25.00,
      "status": "active"
    }
  ]
}
```

### EnrollmentBalanceResponse

| Field | Type | Description |
|-------|------|-------------|
| `enrollment_id` | integer | Enrollment ID |
| `student_id` | integer | Student ID |
| `group_id` | integer | Group ID |
| `level_number` | integer | Current level number |
| `amount_due` | decimal | Amount owed for enrollment |
| `discount_applied` | decimal | Discount applied |
| `total_paid` | decimal | Total payments received |
| `total_refunded` | decimal | Total refunds issued |
| `remaining_balance` | decimal | Balance remaining |
| `status` | string | Enrollment status |
| `is_paid` | boolean | Fully paid flag |

---

## Error Responses

| Status | Code | Description |
|--------|------|-------------|
| 401 | UNAUTHORIZED | Missing or invalid authentication |
| 404 | STUDENT_NOT_FOUND | Student does not exist |
| 404 | ENROLLMENT_NOT_FOUND | Enrollment does not exist |
| 422 | VALIDATION_ERROR | Invalid request parameters |

---

*See [Schema Reference](./schemas.md) for complete type definitions.*
