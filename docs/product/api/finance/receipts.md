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
| `method` | string | Yes | "cash" | Payment method: cash, card, transfer |
| `notes` | string | No | null | Additional notes |
| `allow_credit` | boolean | No | false | Allow creating credit if overpayment |
| `lines` | array | Yes | - | Payment line items |
| `lines[].id` | integer | Yes | - | Line item ID |
| `lines[].student_id` | integer | Yes | - | Student ID |
| `lines[].enrollment_id` | integer | No | null | Enrollment ID |
| `lines[].amount` | float | Yes | - | Line amount |
| `lines[].description` | string | No | null | Line description |

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
      "amount": 150.00,
      "description": "Mathematics Level 2"
    }
  ]
}
```

### Response

**201 Created**
```json
{
  "data": {
    "id": 123,
    "receipt_number": "RCP-2026-00123",
    "payer_name": "John Smith",
    "total": 150.00,
    "method": "card",
    "created_at": "2026-04-09T14:30:00Z",
    "payment_ids": [45]
  },
  "message": "Receipt created successfully.",
  "error": null
}
```

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
    "header": {
      "id": 123,
      "receipt_number": "RCP-2026-00123",
      "payer_name": "John Smith",
      "total": 150.00,
      "created_at": "2026-04-09T14:30:00Z"
    },
    "lines": [
      {
        "id": 1,
        "student_id": 1,
        "enrollment_id": 5,
        "amount": 150.00,
        "description": "Mathematics Level 2"
      }
    ]
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
      "total": 150.00,
      "created_at": "2026-04-09T14:30:00Z",
      "method": "card"
    }
  ],
  "error": null
}
```

---

## Generate Receipt (Text)

Generate a formatted receipt as plain text.

### Endpoint
```
GET /receipts/{receipt_id}/generate
```

### Authentication
Any authenticated user

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `receipt_id` | integer | Receipt unique identifier |

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `template_name` | string | No | "standard" | Template to use: standard, detailed |
| `include_balance` | boolean | No | true | Include remaining balance |

### Response

**200 OK** - Returns `text/plain` content

```
RECEIPT #RCP-2026-00123
Date: 2026-04-09
Payer: John Smith

Mathematics Level 2 ............ $150.00

TOTAL .......................... $150.00
Payment Method: Card
Remaining Balance: $0.00
```

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
POST /receipts/{receipt_id}/mark-sent
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

Generate multiple receipts at once for batch processing.

### Endpoint
```
POST /receipts/batch-generate
```

### Authentication
Admin role required

### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `receipt_ids` | array | Yes | - | List of receipt IDs to generate |
| `template_name` | string | No | "standard" | Template to use |

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
  "data": [
    {
      "receipt_id": 123,
      "content": "RECEIPT #RCP-2026-00123..."
    },
    {
      "receipt_id": 124,
      "content": "RECEIPT #RCP-2026-00124..."
    },
    {
      "receipt_id": 125,
      "content": "Error: Receipt not found"
    }
  ],
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
| `method` | string | Yes | "cash" | Payment method |
| `notes` | string | No | null | Notes |
| `allow_credit` | boolean | No | false | Allow credit |
| `lines` | ReceiptLinePublic[] | Yes | - | Line items |

### ReceiptLinePublic

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Line item ID |
| `student_id` | integer | Yes | Student ID |
| `enrollment_id` | integer | No | Enrollment ID |
| `amount` | float | Yes | Line amount |
| `description` | string | No | Description |

### ReceiptCreatedPublic

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Receipt ID |
| `receipt_number` | string | Receipt number |
| `payer_name` | string | Payer name |
| `total` | float | Total amount |
| `method` | string | Payment method |
| `created_at` | datetime | Creation timestamp |
| `payment_ids` | integer[] | Associated payment IDs |

### ReceiptDetailPublic

| Field | Type | Description |
|-------|------|-------------|
| `header` | ReceiptHeaderPublic | Receipt header info |
| `lines` | ReceiptLinePublic[] | Line items |
| `total` | float | Total amount |

### ReceiptListItem

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Receipt ID |
| `receipt_number` | string | Receipt number |
| `payer_name` | string | Payer name |
| `total` | float | Total amount |
| `created_at` | datetime | Creation timestamp |
| `method` | string | Payment method |

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
