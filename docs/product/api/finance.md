# Finance API Reference

Comprehensive API documentation for financial operations including receipts, balance management, refunds, and competition fees.

**Base path:** `/api/v1`

---

## Module Overview

| Module | File | Endpoints | Description |
|--------|------|-----------|-------------|
| **Balance Operations** | [balance.md](./finance/balance.md) | 6 | Student balance inquiry, adjustments, credit |
| **Receipt Management** | [receipts.md](./finance/receipts.md) | 7 | Receipt creation, generation, PDF |
| **Refunds & Credits** | [refunds.md](./finance/refunds.md) | 3 | Refund processing, risk preview |
| **Competition Fees** | [competition.md](./finance/competition.md) | 1 | Unpaid competition fees |
| **Schema Reference** | [schemas.md](./finance/schemas.md) | - | All DTOs and schemas |

**Total: 17 endpoints**

---

## 🔐 Authentication
All requests MUST include a Bearer token in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```

---

## Schemas

### ReceiptCreatedPublic
```json
{
  "receipt_id": 1,
  "receipt_number": "REC-2026-0001",
  "payment_method": "cash",
  "paid_at": "2026-04-01T10:30:00",
  "lines": 2,
  "total": 3000.0,
  "payment_ids": [1, 2]
}
```

### ReceiptLinePublic
```json
{
  "id": 1,
  "student_id": 1,
  "enrollment_id": 1,
  "amount": 1500.0,
  "transaction_type": "charge",
  "payment_type": "course_level",
  "discount": 0.0,
  "notes": "Level 1 payment"
}
```

### ReceiptHeaderPublic
```json
{
  "id": 1,
  "receipt_number": "REC-2026-0001",
  "payer_name": "Ahmed Mohamed",
  "payment_method": "cash",
  "paid_at": "2026-04-01T10:30:00",
  "notes": "Course payment"
}
```

### ReceiptDetailPublic
```json
{
  "receipt": {
    "id": 1,
    "receipt_number": "REC-2026-0001",
    "payer_name": "Ahmed Mohamed",
    "payment_method": "cash",
    "paid_at": "2026-04-01T10:30:00",
    "notes": "Course payment"
  },
  "lines": [
    {
      "id": 1,
      "student_id": 1,
      "enrollment_id": 1,
      "amount": 1500.0,
      "transaction_type": "charge",
      "payment_type": "course_level",
      "discount": 0.0,
      "notes": "Level 1 payment"
    }
  ],
  "total": 1500.0
}
```

### ReceiptListItem
```json
{
  "id": 1,
  "receipt_number": "REC-2026-0001",
  "payer_name": "Ahmed Mohamed",
  "payment_method": "cash",
  "paid_at": "2026-04-01T10:30:00"
}
```

### RefundResultPublic
```json
{
  "receipt_number": "REC-2026-0001",
  "refunded_amount": 500.0,
  "new_balance": -1000.0
}
```

### CreateReceiptRequest
```json
{
  "payer_name": "string (optional)",
  "method": "string (default: cash)",
  "notes": "string (optional)",
  "allow_credit": "boolean (default: true)",
  "lines": [
    {
      "student_id": "integer (required)",
      "enrollment_id": "integer (optional)",
      "team_member_id": "integer (optional) - for competition fees",
      "amount": "number (required, >0)",
      "payment_type": "string (default: course_level)",
      "discount": "number (default: 0)",
      "notes": "string (optional)"
    }
  ]
}
```

### IssueRefundRequest
```json
{
  "payment_id": "integer (required)",
  "amount": "number (required, >0)",
  "reason": "string (required)",
  "method": "string (default: cash)"
}
```

### FinancialSummaryPublic
```json
{
  "student_id": 1,
  "group_id": 1,
  "enrollment_id": 1,
  "group_name": "Sat 2PM Robotics",
  "net_due": 1500.0,
  "total_paid": 1000.0,
  "balance": -500.0
}
```

### UnpaidCompFeeItem
```json
{
  "team_member_id": 1,
  "team_id": 1,
  "team_name": "Techno Eagles",
  "competition_name": "National Robotics Championship",
  "category_name": "Junior League",
  "member_share": 500.0,
  "student_id": 1
}
```

### PreviewRiskRequest
```json
{
  "receipt_id": "integer (required)"
}
```

### OverpaymentRiskItem
```json
{
  "student_id": 1,
  "enrollment_id": 1,
  "current_balance": -500.0,
  "payment_amount": 1000.0,
  "projected_balance": 500.0,
  "risk_level": "high"
}
```

### ApiResponse (Envelope)
```json
{
  "success": true,
  "data": {},
  "message": null
}
```

---

## Endpoints

### Receipts

#### 1. Create a new receipt
**POST** `/api/v1/finance/receipts`

**Request Body:** `CreateReceiptRequest`

**Response (201):** `ApiResponse<ReceiptCreatedPublic>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Creates receipt with multiple charge lines
- Processes payments for each line
- Returns receipt ID and payment IDs

---

#### 2. Search receipts
**GET** `/api/v1/finance/receipts`

**Query Parameters:**
- `from_date` - string (required) - Format: YYYY-MM-DD
- `to_date` - string (required) - Format: YYYY-MM-DD
- `payer_name` - string (optional)
- `student_id` - string (optional)
- `receipt_number` - string (optional)
- `limit` - integer (optional)

**Response (200):** `ApiResponse<list<ReceiptListItem>>`

**Error Response (422):** `HTTPValidationError`

---

#### 3. Get receipt details
**GET** `/api/v1/finance/receipts/{receipt_id}`

**Path Parameters:**
- `receipt_id` - integer (required)

**Response (200):** `ApiResponse<ReceiptDetailPublic>`

**Error Response (422):** `HTTPValidationError`

---

#### 4. Download PDF receipt
**GET** `/api/v1/finance/receipts/{receipt_id}/pdf`

**Path Parameters:**
- `receipt_id` - integer (required)

**Response (200):** `application/pdf` with `Content-Disposition: attachment`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Returns branded A4 PDF receipt
- Optional logo configured via `PDF_LOGO_PATH` env var
- Includes company address and dual signature blocks

---

### Refunds

#### 5. Issue a refund
**POST** `/api/v1/finance/refunds`

**Request Body:** `IssueRefundRequest`

**Response (200):** `ApiResponse<RefundResultPublic>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Issues refund against a specific payment
- Creates refund record and updates balances
- Partial refunds allowed

---

### Balances

#### 6. Get student balances
**GET** `/api/v1/finance/balance/student/{student_id}`

**Path Parameters:**
- `student_id` - integer (required)

**Response (200):** `ApiResponse<list<FinancialSummaryPublic>>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Returns financial summary per enrollment
- Includes net_due, total_paid, and balance

---

#### 7. Get unpaid competition fees
**GET** `/api/v1/finance/competition-fees/student/{student_id}`

**Path Parameters:**
- `student_id` - integer (required)

**Response (200):** `ApiResponse<list<UnpaidCompFeeItem>>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Returns unpaid competition fees for student
- Used by Financial Desk to render payment lines

---

### Risk Assessment

#### 8. Preview overpayment risk
**POST** `/api/v1/finance/receipts/preview-risk`

**Request Body:** `PreviewRiskRequest`

**Response (200):** `ApiResponse<list<OverpaymentRiskItem>>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Analyzes receipt for potential overpayments
- Returns risk items with projected balances
- Helps prevent accidental overpayments

---

## Quick Reference

### All Endpoints Summary

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 1 | POST | `/finance/receipts` | Admin | Create receipt |
| 2 | GET | `/finance/receipts` | Admin | Search receipts |
| 3 | GET | `/finance/receipts/{id}` | Any | Get receipt |
| 4 | GET | `/finance/receipts/{id}/pdf` | Any | Download PDF |
| 5 | POST | `/finance/refunds` | Admin | Issue refund |
| 6 | GET | `/finance/balance/student/{id}` | Any | Student balance |
| 7 | GET | `/finance/competition-fees/student/{id}` | Any | Competition fees |
| 8 | POST | `/finance/receipts/preview-risk` | Admin | Risk preview |
| 9 | GET | `/students/{id}/balance` | Any | Full balance |
| 10 | GET | `/students/{id}/balance/enrollments/{eid}` | Any | Enrollment balance |
| 11 | GET | `/balance/unpaid-enrollments` | Any | Unpaid list |
| 12 | GET | `/students/{id}/balance/credit` | Any | Credit balance |
| 13 | POST | `/students/{id}/balance/adjust` | Admin | Adjust balance |
| 14 | GET | `/students/{id}/balance/summary` | Any | Quick summary |
| 15 | GET | `/receipts/{id}/generate` | Any | Generate text |
| 16 | POST | `/receipts/{id}/mark-sent` | Admin | Mark sent |
| 17 | POST | `/receipts/batch-generate` | Admin | Batch generate |

---

## Additional Documentation

- **[Balance Operations](./finance/balance.md)** - Complete balance endpoint details
- **[Receipt Management](./finance/receipts.md)** - Receipt creation and generation
- **[Refunds & Credits](./finance/refunds.md)** - Refund processing and risk assessment
- **[Competition Fees](./finance/competition.md)** - Competition fee endpoints
- **[Schema Reference](./finance/schemas.md)** - All DTOs and types
