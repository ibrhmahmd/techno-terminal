# Finance API - Refunds and Credits

Refund processing, overpayment risk assessment, and credit management endpoints.

**Base Path:** `/api/v1`

---

## Table of Contents

1. [Issue Refund](#issue-refund)
2. [Preview Overpayment Risk](#preview-overpayment-risk)
3. [Get Student Credit Info](#get-student-credit-info)

---

## Issue Refund

Issue a refund for a previous payment.

### Endpoint
```
POST /finance/refunds
```

### Authentication
Admin role required

### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `payment_id` | integer | Yes | - | Payment ID to refund |
| `amount` | float | Yes | - | Refund amount |
| `reason` | string | Yes | - | Reason for refund |
| `method` | string | Yes | "cash" | Refund method: cash, card, transfer |

### Example Request
```json
{
  "payment_id": 45,
  "amount": 50.00,
  "reason": "Student withdrawal",
  "method": "transfer"
}
```

### Response

**200 OK**
```json
{
  "data": {
    "refund_id": 67,
    "payment_id": 45,
    "amount": 50.00,
    "method": "transfer",
    "reason": "Student withdrawal",
    "new_balance": 100.00,
    "processed_at": "2026-04-09T14:30:00Z"
  },
  "message": "Refund issued successfully.",
  "error": null
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `refund_id` | integer | Refund record ID |
| `payment_id` | integer | Original payment ID |
| `amount` | float | Refund amount |
| `method` | string | Refund method |
| `reason` | string | Refund reason |
| `new_balance` | float | Updated balance after refund |
| `processed_at` | datetime | Processing timestamp |

---

## Preview Overpayment Risk

Preview potential overpayment/credit creation before creating a receipt.

### Endpoint
```
POST /finance/receipts/preview-risk
```

### Authentication
Admin role required

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lines` | array | Yes | Receipt line items to preview |
| `lines[].student_id` | integer | Yes | Student ID |
| `lines[].enrollment_id` | integer | Yes | Enrollment ID |
| `lines[].amount` | float | Yes | Payment amount |
| `lines[].description` | string | No | Description |

### Example Request
```json
{
  "lines": [
    {
      "student_id": 1,
      "enrollment_id": 5,
      "amount": 200.00,
      "description": "Overpayment test"
    }
  ]
}
```

### Response

**200 OK**
```json
{
  "data": [
    {
      "student_id": 1,
      "enrollment_id": 5,
      "amount": 200.00,
      "debt_before": -50.00,
      "projected_balance": 150.00,
      "excess_credit": 150.00
    }
  ],
  "message": "Risk preview completed",
  "error": null
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `student_id` | integer | Student ID |
| `enrollment_id` | integer | Enrollment ID |
| `amount` | float | Payment amount |
| `debt_before` | float | Current debt before payment |
| `projected_balance` | float | Projected balance after payment |
| `excess_credit` | float | Credit/overpayment amount |

---

## Get Student Credit Info

Get detailed credit information for a student including allocations.

### Endpoint
```
GET /finance/credit/student/{student_id}
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
    "total_credit": 100.00,
    "available_credit": 75.00,
    "reserved_credit": 25.00,
    "credit_records": [
      {
        "credit_id": 10,
        "amount": 100.00,
        "available": 75.00,
        "reserved": 25.00,
        "created_at": "2026-04-01T10:00:00Z"
      }
    ]
  },
  "message": "Credit info retrieved successfully",
  "error": null
}
```

---

## Schemas

### IssueRefundRequest

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `payment_id` | integer | Yes | - | Payment to refund |
| `amount` | float | Yes | - | Refund amount |
| `reason` | string | Yes | - | Refund reason |
| `method` | string | Yes | "cash" | Refund method |

### RefundResultPublic

| Field | Type | Description |
|-------|------|-------------|
| `refund_id` | integer | Refund record ID |
| `payment_id` | integer | Original payment ID |
| `amount` | float | Refund amount |
| `method` | string | Refund method |
| `reason` | string | Refund reason |
| `new_balance` | float | Updated balance |
| `processed_at` | datetime | Processing timestamp |

### PreviewRiskRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lines` | ReceiptLineInput[] | Yes | Lines to preview |

### OverpaymentRiskItem

| Field | Type | Description |
|-------|------|-------------|
| `student_id` | integer | Student ID |
| `enrollment_id` | integer | Enrollment ID |
| `amount` | float | Payment amount |
| `debt_before` | float | Current debt |
| `projected_balance` | float | Balance after payment |
| `excess_credit` | float | Credit amount |

### CreditInfoDTO

| Field | Type | Description |
|-------|------|-------------|
| `student_id` | integer | Student ID |
| `total_credit` | float | Total credit amount |
| `available_credit` | float | Available for use |
| `reserved_credit` | float | Reserved/allocated |
| `credit_records` | array | Credit record details |

### ApplyCreditRequestDTO

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_id` | integer | Yes | Student with credit |
| `enrollment_id` | integer | Yes | Target enrollment |
| `amount` | float | No | Amount to apply (defaults to all) |

### ApplyCreditResponseDTO

| Field | Type | Description |
|-------|------|-------------|
| `student_id` | integer | Student ID |
| `enrollment_id` | integer | Target enrollment |
| `amount_applied` | float | Amount applied |
| `remaining_credit` | float | Credit remaining |
| `applied_at` | datetime | Timestamp |

---

## Refund Methods

| Method | Description |
|--------|-------------|
| `cash` | Cash refund |
| `card` | Card refund |
| `transfer` | Bank transfer refund |

---

## Error Responses

| Status | Code | Description |
|--------|------|-------------|
| 400 | INSUFFICIENT_BALANCE | Cannot refund more than paid |
| 401 | UNAUTHORIZED | Missing or invalid authentication |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | PAYMENT_NOT_FOUND | Payment does not exist |
| 422 | VALIDATION_ERROR | Invalid request parameters |

---

*See [Schema Reference](./schemas.md) for complete type definitions.*
