# Student Finance & Balance Operations API

Endpoints for student balance inquiry, enrollment balances, and financial operations.

**Base Path:** `/api/v1`

---

## Get Student Balance

Retrieve comprehensive balance information for a student across all enrollments.

### Endpoint
```
GET /students/{student_id}/balance
```

### Authentication
Any authenticated user

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

## Get Enrollment Balance

Get detailed balance for a specific enrollment.

### Endpoint
```
GET /students/{student_id}/balance/enrollments/{enrollment_id}
```

### Authentication
Any authenticated user

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `student_id` | integer | Student unique identifier |
| `enrollment_id` | integer | Enrollment unique identifier |

### Response

**200 OK**
```json
{
  "data": {
    "enrollment_id": 5,
    "student_id": 1,
    "group_id": 3,
    "level_number": 2,
    "amount_due": 150.00,
    "discount_applied": 25.00,
    "total_paid": 100.00,
    "total_refunded": 0.00,
    "remaining_balance": -25.00,
    "status": "active",
    "is_paid": false
  },
  "message": "Enrollment balance retrieved successfully",
  "error": null
}
```

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

---

## Adjust Student Balance

Manually adjust a student's balance (admin only).

### Endpoint
```
POST /students/{student_id}/balance/adjust
```

### Authentication
Admin only

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `student_id` | integer | Student unique identifier |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `adjustment_amount` | decimal | Yes | Amount to adjust (positive = credit, negative = debit) |
| `reason` | string | Yes | Explanation for the adjustment |
| `adjustment_type` | string | Yes | Type: "correction", "refund", "discount", "other" |

### Example Request
```json
{
  "adjustment_amount": -25.00,
  "reason": "Applied sibling discount",
  "adjustment_type": "discount"
}
```

### Response

**200 OK**
```json
{
  "data": {
    "student_id": 1,
    "previous_balance": -100.00,
    "adjustment_amount": -25.00,
    "new_balance": -75.00,
    "reason": "Applied sibling discount",
    "adjustment_type": "discount",
    "adjusted_at": "2026-04-09T14:30:00Z",
    "adjusted_by": 3
  },
  "message": "Balance adjusted successfully",
  "error": null
}
```

---

## Apply Credit to Enrollment

Apply available credit balance to a specific enrollment.

### Endpoint
```
POST /students/{student_id}/balance/enrollments/{enrollment_id}/apply-credit
```

### Authentication
Admin only

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `student_id` | integer | Student unique identifier |
| `enrollment_id` | integer | Enrollment unique identifier |

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `amount` | decimal | No | Amount to apply (defaults to remaining balance or available credit) |

### Response

**200 OK**
```json
{
  "data": {
    "student_id": 1,
    "enrollment_id": 5,
    "amount_applied": 25.00,
    "credit_applications": [
      {
        "allocation_id": 10,
        "amount": 25.00,
        "applied_at": "2026-04-09T14:30:00Z"
      }
    ],
    "enrollment_balance_after": 0.00,
    "applied_at": "2026-04-09T14:30:00Z",
    "applied_by": 3
  },
  "message": "Credit applied successfully",
  "error": null
}
```

---

## Reverse Payment Allocation

Reverse a previous payment allocation (admin only).

### Endpoint
```
POST /balance/allocations/{allocation_id}/reverse
```

### Authentication
Admin only

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `allocation_id` | integer | Payment allocation identifier to reverse |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | Yes | Reason for reversal |

### Example Request
```json
{
  "reason": "Incorrect allocation - should apply to different enrollment"
}
```

### Response

**200 OK**
```json
{
  "data": {
    "original_allocation_id": 15,
    "reversal_allocation_id": 25,
    "amount_reversed": 50.00,
    "reason": "Incorrect allocation",
    "reversed_at": "2026-04-09T14:30:00Z",
    "reversed_by": 3
  },
  "message": "Allocation reversed successfully",
  "error": null
}
```

---

## Get Student Credit Info

Get credit balance information for a student.

### Endpoint
```
GET /students/{student_id}/credit
```

### Authentication
Any authenticated user

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `student_id` | integer | Student unique identifier |

### Response

**200 OK**
```json
{
  "data": {
    "student_id": 1,
    "total_credit": 50.00,
    "available_credit": 25.00,
    "reserved_credit": 25.00,
    "credit_allocations": [
      {
        "allocation_id": 10,
        "enrollment_id": 5,
        "amount": 25.00,
        "allocated_at": "2026-04-08T10:00:00Z"
      }
    ]
  },
  "message": "Credit info retrieved successfully",
  "error": null
}
```

---

## Related Schemas

### StudentBalanceDTO
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
```json
{
  "enrollment_id": 5,
  "student_id": 1,
  "group_id": 3,
  "level_number": 2,
  "amount_due": 150.00,
  "discount_applied": 25.00,
  "total_paid": 100.00,
  "total_refunded": 0.00,
  "remaining_balance": -25.00,
  "status": "active",
  "is_paid": false
}
```

### UnpaidEnrollmentResponse
```json
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
```

### BalanceAdjustmentRequest
```json
{
  "adjustment_amount": -25.00,
  "reason": "Applied sibling discount",
  "adjustment_type": "discount"
}
```

### BalanceAdjustmentResponseDTO
```json
{
  "student_id": 1,
  "previous_balance": -100.00,
  "adjustment_amount": -25.00,
  "new_balance": -75.00,
  "reason": "Applied sibling discount",
  "adjustment_type": "discount",
  "adjusted_at": "2026-04-09T14:30:00Z",
  "adjusted_by": 3
}
```

### ApplyCreditRequest / Response
```json
{
  "student_id": 1,
  "enrollment_id": 5,
  "amount": 25.00,
  "credit_applications": [],
  "enrollment_balance_after": 0.00,
  "applied_at": "2026-04-09T14:30:00Z",
  "applied_by": 3
}
```

### AllocationReversalResponseDTO
```json
{
  "original_allocation_id": 15,
  "reversal_allocation_id": 25,
  "amount_reversed": 50.00,
  "reason": "Incorrect allocation",
  "reversed_at": "2026-04-09T14:30:00Z",
  "reversed_by": 3
}
```

---

## Adjustment Types

| Type | Description |
|------|-------------|
| `correction` | Error correction |
| `refund` | Partial or full refund |
| `discount` | Special discount applied |
| `other` | Other adjustment reason |

---

*See [Schema Reference](./schemas.md) for complete type definitions.*
