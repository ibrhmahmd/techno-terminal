# Finance Reporting API

Daily collection summaries and receipt listings for financial reporting.

**Base Path:** `/api/v1`  
**Authentication:** JWT Bearer token required. Admin access only.

---

## Endpoints Overview

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/finance/reports/daily-collections` | GET | Daily collection summary by payment method | Admin |
| `/finance/reports/daily-receipts` | GET | All receipts issued on a specific date | Admin |

---

## GET /finance/reports/daily-collections

Returns daily collection summary grouped by payment method.

### Authentication
`require_admin` - Admin access only.

### Query Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `target_date` | date | No | today | Target date in YYYY-MM-DD format |

### Response: `ApiResponse<List<DailyCollectionItem>>`

**Success (200):**
```json
{
  "data": [
    {
      "payment_method": "cash",
      "total_amount": 15000.00,
      "receipt_count": 12,
      "target_date": "2026-04-16"
    },
    {
      "payment_method": "bank_transfer",
      "total_amount": 8500.00,
      "receipt_count": 5,
      "target_date": "2026-04-16"
    },
    {
      "payment_method": "credit_card",
      "total_amount": 3200.00,
      "receipt_count": 3,
      "target_date": "2026-04-16"
    }
  ],
  "success": true
}
```

**Empty Result:**
```json
{
  "data": [],
  "success": true
}
```

**Unauthorized (401):**
```json
{
  "detail": "Could not validate credentials"
}
```

**Forbidden (403):**
```json
{
  "detail": "Access denied. Required role(s): ['admin', 'system_admin']"
}
```

---

## GET /finance/reports/daily-receipts

Returns all receipts issued on a specific date.

### Authentication
`require_admin` - Admin access only.

### Query Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `target_date` | date | No | today | Target date in YYYY-MM-DD format |

### Response: `ApiResponse<List<DailyReceiptItem>>`

**Success (200):**
```json
{
  "data": [
    {
      "receipt_id": 123,
      "receipt_number": "REC-2026-00123",
      "payer_name": "Ahmed Mohamed",
      "total_amount": 1500.00,
      "payment_method": "cash",
      "issued_at": "2026-04-16T10:30:00"
    },
    {
      "receipt_id": 124,
      "receipt_number": "REC-2026-00124",
      "payer_name": "Sara Ali",
      "total_amount": 2000.00,
      "payment_method": "bank_transfer",
      "issued_at": "2026-04-16T11:15:00"
    }
  ],
  "success": true
}
```

**Empty Result:**
```json
{
  "data": [],
  "success": true
}
```

---

## Schemas

### DailyCollectionItem

| Field | Type | Description |
|-------|------|-------------|
| `payment_method` | string | Payment method (cash, bank_transfer, credit_card, etc.) |
| `total_amount` | float | Total amount collected via this method |
| `receipt_count` | integer | Number of receipts for this method |
| `target_date` | date | The date of the collection |

### DailyReceiptItem

| Field | Type | Description |
|-------|------|-------------|
| `receipt_id` | integer | Internal receipt ID |
| `receipt_number` | string | Display receipt number (e.g., "REC-2026-00123") |
| `payer_name` | string\|null | Name of the payer |
| `total_amount` | float | Receipt total amount |
| `payment_method` | string | Payment method used |
| `issued_at` | datetime | When the receipt was issued |

---

## Usage Examples

### Get today's collections (default)
```bash
curl -X GET "https://api.example.com/api/v1/finance/reports/daily-collections" \
  -H "Authorization: Bearer <token>"
```

### Get collections for specific date
```bash
curl -X GET "https://api.example.com/api/v1/finance/reports/daily-collections?target_date=2026-04-15" \
  -H "Authorization: Bearer <token>"
```

### Get daily receipts
```bash
curl -X GET "https://api.example.com/api/v1/finance/reports/daily-receipts?target_date=2026-04-15" \
  -H "Authorization: Bearer <token>"
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 401 | Missing or invalid JWT token |
| 403 | User lacks admin privileges |
| 422 | Invalid date format |
