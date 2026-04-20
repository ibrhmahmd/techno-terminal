# Finance API - Competition Fees

Competition fee management and payment tracking endpoints.

**Base Path:** `/api/v1`

---

## Table of Contents

1. [Get Unpaid Competition Fees](#get-unpaid-competition-fees)

---

## Get Unpaid Competition Fees

Retrieve pending competition fees for a student to be paid via Financial Desk setup.

### Endpoint
```
GET /finance/competition-fees?student_id={student_id}
```

### Authentication
Any authenticated user

### Description

This endpoint returns a list of unpaid competition fees for a specific student. These fees are separate from regular enrollment fees and need to be processed through the Financial Desk workflow. Each fee item includes competition details, amount due, and payment status.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `student_id` | integer | Yes | Student unique identifier |

### Response

**200 OK**
```json
{
  "data": [
    {
      "id": 15,
      "student_id": 1,
      "competition_name": "Math Olympiad 2026",
      "competition_date": "2026-05-15",
      "fee_amount": 25.00,
      "fee_type": "registration",
      "is_paid": false,
      "due_date": "2026-04-30"
    },
    {
      "id": 16,
      "student_id": 1,
      "competition_name": "Science Fair 2026",
      "competition_date": "2026-06-20",
      "fee_amount": 15.00,
      "fee_type": "materials",
      "is_paid": false,
      "due_date": "2026-06-01"
    }
  ],
  "message": "Unpaid competition fees retrieved",
  "error": null
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Competition fee record ID |
| `student_id` | integer | Student ID |
| `competition_name` | string | Name of the competition |
| `competition_date` | date | Date of the competition |
| `fee_amount` | float | Amount due |
| `fee_type` | string | Type of fee (registration, materials, etc.) |
| `is_paid` | boolean | Payment status |
| `due_date` | date | Payment deadline |

---

## Schemas

### UnpaidCompFeeItem

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Fee record ID |
| `student_id` | integer | Student ID |
| `competition_name` | string | Competition name |
| `competition_date` | date | Competition date |
| `fee_amount` | float | Fee amount |
| `fee_type` | string | Fee type |
| `is_paid` | boolean | Paid status |
| `due_date` | date | Due date |

---

## Fee Types

| Type | Description |
|------|-------------|
| `registration` | Competition registration fee |
| `materials` | Materials/supplies fee |
| `transportation` | Transportation fee |
| `accommodation` | Accommodation fee |

---

## Error Responses

| Status | Code | Description |
|--------|------|-------------|
| 401 | UNAUTHORIZED | Missing or invalid authentication |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | STUDENT_NOT_FOUND | Student does not exist |
| 422 | VALIDATION_ERROR | Invalid student ID |

---

*See [Schema Reference](./schemas.md) for complete type definitions.*
