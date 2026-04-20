# Finance API - Receipt Management

Receipt creation, generation, and management endpoints.

**Base Path:** `/api/v1`

---

## Table of Contents

1. [Create Receipt](#create-receipt)
2. [Get Receipt Details](#get-receipt-details)
3. [Search Receipts](#search-receipts)
4. [Generate Receipt (Text)](#generate-receipt-text)
5. [Generate Receipt (PDF)](#generate-receipt-pdf)
6. [Mark Receipt as Sent](#mark-receipt-as-sent)
7. [Batch Generate Receipts](#batch-generate-receipts)

---

## Create Receipt

Create a new receipt with payment line items.

### Endpoint
```
POST /finance/receipts
```

### Authentication
Admin role required

### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `payer_name` | string | No | null | Name of person making payment |
| `method` | string | No | "cash" | Payment method: cash, card, transfer |
| `notes` | string | No | null | Additional notes |
| `allow_credit` | boolean | No | true | Allow creating credit if overpayment |
| `lines` | array | Yes | - | Payment line items |
| `lines[].student_id` | integer | Yes | - | Student ID |
| `lines[].enrollment_id` | integer | No | null | Enrollment ID |
| `lines[].team_member_id` | integer | No | null | Team member ID |
| `lines[].amount` | float | Yes | - | Line amount |
| `lines[].payment_type` | string | No | "course_level" | Payment type |
| `lines[].discount` | float | No | 0.0 | Discount amount |
| `lines[].notes` | string | No | null | Line notes |

### Example Request
```json
{
  "payer_name": "John Smith",
  "method": "card",
  "notes": "Monthly tuition payment",
  "allow_credit": false,
  "lines": [
    {
      "student_id": 1,
      "enrollment_id": 5,
      "team_member_id": null,
      "amount": 150.00,
      "payment_type": "course_level",
      "discount": 0.0,
      "notes": "Mathematics Level 2"
    }
  ]
}
```

### Response

**201 Created**
```json
{
  "success": true,
  "data": {
    "receipt_id": 123,
    "receipt_number": "RCP-2026-00123",
    "payment_method": "card",
    "paid_at": "2026-04-09T14:30:00Z",
    "lines": 1,
    "total": 150.00,
    "payment_ids": [45]
  },
  "message": "Receipt created successfully."
}
```

### Response Schema

#### ReceiptCreationResponse

| Field | Type | Description |
|-------|------|-------------|
| `receipt_id` | integer | Receipt ID |
| `receipt_number` | string | Generated receipt number |
| `payment_method` | string | Payment method used |
| `paid_at` | datetime | Payment timestamp |
| `lines` | integer | Count of charge lines |
| `total` | float | Total amount |
| `payment_ids` | integer[] | IDs of created payment records |

---

## Get Receipt Details

Retrieve detailed information for a specific receipt.

### Endpoint
```
GET /finance/receipts/{receipt_id}
```

### Authentication
Any authenticated user

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `receipt_id` | integer | Receipt unique identifier |

### Response

**200 OK**
```json
{
  "data": {
    "receipt": {
      "id": 123,
      "receipt_number": "RCP-2026-00123",
      "payer_name": "John Smith",
      "payment_method": "card",
      "paid_at": "2026-04-09T14:30:00Z",
      "notes": null
    },
    "lines": [
      {
        "id": 1,
        "student_id": 1,
        "enrollment_id": 5,
        "amount": 150.00,
        "transaction_type": "payment",
        "payment_type": "course_level",
        "discount": 0.0,
        "notes": null
      }
    ],
    "total": 150.00
  },
  "error": null
}
```

**404 Not Found**
```json
{
  "data": null,
  "message": "Receipt not found",
  "error": {
    "code": "NOT_FOUND",
    "message": "Receipt not found"
  }
}
```

---

## Search Receipts

Search receipts with date range and optional filters.

### Endpoint
```
GET /finance/receipts
```

### Authentication
Admin role required

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `from_date` | date | Yes | - | Start date (YYYY-MM-DD) |
| `to_date` | date | Yes | - | End date (YYYY-MM-DD) |
| `payer_name` | string | No | null | Filter by payer name (partial match) |
| `student_id` | integer | No | null | Filter by student ID |
| `receipt_number` | string | No | null | Filter by receipt number (partial match) |
| `limit` | integer | No | 200 | Max results (1-1000) |

**Date Range Limit:**
- Maximum allowed range is **90 days** (Issue M3 fix)
- Exceeding this limit returns HTTP 422

### Example Request
```
GET /finance/receipts?from_date=2026-04-01&to_date=2026-04-30&limit=50
```

### Response

**200 OK**
```json
{
  "data": [
    {
      "id": 123,
      "receipt_number": "RCP-2026-00123",
      "payer_name": "John Smith",
      "payment_method": "card",
      "paid_at": "2026-04-09T14:30:00Z"
    }
  ],
  "error": null
}
```

**422 Unprocessable Content** - Date range exceeds 90-day limit
```json
{
  "success": false,
  "error": "ValidationError",
  "message": "Date range too large. Maximum allowed is 90 days. Requested: 120 days."
}
```

---

## Generate Receipt (Text)

Generate a formatted receipt as plain text.

### Endpoint
```
GET /finance/receipts/{receipt_id}/generate
```

### Authentication
Any authenticated user

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `template_name` | string | No | "standard" | Template: "standard" or "detailed" |
| `include_balance` | boolean | No | true | Include remaining balance |
| `as_text` | boolean | No | false | Return plain text instead of JSON |

### Response (JSON - Default)

**200 OK** (application/json)
```json
{
  "success": true,
  "data": {
    "receipt_id": 123,
    "content": "RECEIPT #RCP-2026-00123\nDate: 2026-04-09\nPayer: John Smith\n\nPayment for Mathematics Level 2: 150.00\nTotal: 150.00",
    "template_name": "standard",
    "include_balance": true,
    "generated_at": "2026-04-13T08:35:00Z",
    "content_type": "text/plain"
  }
}
```

### Response (Plain Text - Legacy)

**200 OK** (text/plain) - Use `?as_text=true`
```
RECEIPT #RCP-2026-00123
Date: 2026-04-09
Payer: John Smith
Payment for Mathematics Level 2: 150.00
Total: 150.00
```

### Response Schema

#### ReceiptGenerationResponse

| Field | Type | Description |
|-------|------|-------------|
| `receipt_id` | integer | Receipt ID |
| `content` | string | Formatted receipt text |
| `template_name` | string | Template used |
| `include_balance` | boolean | Balance included flag |
| `generated_at` | datetime | Generation timestamp |
| `content_type` | string | Always "text/plain" |

---

## Generate Receipt (PDF)

Download receipt as branded PDF document.

### Endpoint
```
GET /finance/receipts/{receipt_id}/pdf
```

### Authentication
Any authenticated user

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `receipt_id` | integer | Receipt unique identifier |

### Response

**200 OK** - Returns `application/pdf` binary content

Headers:
```
Content-Disposition: attachment; filename="receipt_RCP-2026-00123.pdf"
Content-Type: application/pdf
```

**404 Not Found**
```json
{
  "detail": "Receipt not found"
}
```

---

## Mark Receipt as Sent

Mark a receipt as sent to parent/guardian with optional email tracking.

### Endpoint
```
POST /finance/receipts/{receipt_id}/mark-sent
```

### Authentication
Admin role required

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `receipt_id` | integer | Receipt unique identifier |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `parent_email` | string | No | Email address receipt was sent to |

### Example Request
```json
{
  "parent_email": "parent@example.com"
}
```

### Response

**200 OK**
```json
{
  "data": {
    "receipt_id": 123,
    "receipt_number": "RCP-2026-00123",
    "sent_to_parent": true,
    "sent_at": "2026-04-09T14:35:00Z",
    "parent_email": "parent@example.com"
  },
  "message": "Receipt marked as sent",
  "error": null
}
```

---

## Batch Generate Receipts

Generate multiple receipts at once for bulk operations. Returns structured results with explicit success/error status for each receipt.

### Endpoint
```
POST /finance/receipts/batch-generate
```

### Authentication
Admin role required

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `receipt_ids` | array | Yes | List of receipt IDs to generate |
| `template_name` | string | No | Template: "standard" or "detailed" (default: "standard") |

### Example Request
```json
{
  "receipt_ids": [123, 124, 125],
  "template_name": "standard"
}
```

### Response

**200 OK**
```json
{
  "success": true,
  "data": [
    {
      "receipt_id": 123,
      "success": true,
      "content": "RECEIPT #RCP-2026-00123...",
      "error_message": null,
      "error_code": null
    },
    {
      "receipt_id": 124,
      "success": false,
      "content": null,
      "error_message": "Receipt 124 not found",
      "error_code": "not_found"
    },
    {
      "receipt_id": 125,
      "success": true,
      "content": "RECEIPT #RCP-2026-00125...",
      "error_message": null,
      "error_code": null
    }
  ],
  "message": "Batch generation completed"
  "message": "Generated 3 receipts",
  "error": null
}
```

---

## Schemas

### CreateReceiptRequest

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `payer_name` | string | No | null | Payer name |
| `method` | string | No | "cash" | Payment method |
| `notes` | string | No | null | Notes |
| `allow_credit` | boolean | No | true | Allow credit |
| `lines` | ReceiptLineInput[] | Yes | - | Line items |

### ReceiptLineInput (for requests)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `student_id` | integer | Yes | - | Student ID |
| `enrollment_id` | integer | No | null | Enrollment ID |
| `team_member_id` | integer | No | null | Team member ID |
| `amount` | float | Yes | - | Line amount |
| `payment_type` | string | No | "course_level" | Payment type |
| `discount` | float | No | 0.0 | Discount amount |
| `notes` | string | No | null | Notes |

### ReceiptLineResponse (in responses)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Line item ID |
| `student_id` | integer | Yes | Student ID |
| `enrollment_id` | integer \| null | No | Enrollment ID |
| `amount` | float | Yes | Line amount |
| `transaction_type` | string | Yes | Transaction type |
| `payment_type` | string | Yes | Payment type |
| `discount` | float | Yes | Discount amount |
| `notes` | string \| null | No | Notes |

### ReceiptCreationResponse

| Field | Type | Description |
|-------|------|-------------|
| `receipt_id` | integer | Receipt ID |
| `receipt_number` | string \| null | Receipt number |
| `payment_method` | string | Payment method |
| `paid_at` | datetime \| null | Payment timestamp |
| `lines` | integer | Count of line items |
| `total` | float | Total amount |
| `payment_ids` | integer[] | Associated payment IDs |

### ReceiptDetailResponse

| Field | Type | Description |
|-------|------|-------------|
| `receipt` | ReceiptHeaderResponse | Receipt header info |
| `lines` | ReceiptLineResponse[] | Line items |
| `total` | float | Total amount |

### ReceiptHeaderResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Receipt ID |
| `receipt_number` | string \| null | Receipt number |
| `payer_name` | string \| null | Payer name |
| `payment_method` | string | Payment method |
| `paid_at` | datetime \| null | Payment timestamp |
| `notes` | string \| null | Notes |

### ReceiptListItem

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Receipt ID |
| `receipt_number` | string \| null | Receipt number |
| `payer_name` | string \| null | Payer name |
| `payment_method` | string | Payment method |
| `paid_at` | datetime \| null | Payment timestamp |

### MarkReceiptSentRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `parent_email` | string | No | Parent email address |

### BatchGenerateRequest

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `receipt_ids` | integer[] | Yes | - | Receipt IDs |
| `template_name` | string | No | "standard" | Template name |

### BatchGenerateResponse

| Field | Type | Description |
|-------|------|-------------|
| `receipt_id` | integer | Receipt ID |
| `content` | string | Generated content or error message |

---

## Payment Methods

| Method | Description |
|--------|-------------|
| `cash` | Cash payment |
| `card` | Credit/debit card |
| `transfer` | Bank transfer |

---

## Error Responses

| Status | Code | Description |
|--------|------|-------------|
| 401 | UNAUTHORIZED | Missing or invalid authentication |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Receipt not found |
| 422 | VALIDATION_ERROR | Invalid request parameters |

---

*See [Schema Reference](./schemas.md) for complete type definitions.*
