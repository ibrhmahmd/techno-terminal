# API Contract: POST /api/v1/finance/receipts

## Endpoint
```
POST /api/v1/finance/receipts
Authorization: Bearer <jwt>
Content-Type: application/json
```

## Request Body

### CreateReceiptRequest

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `method` | `string` | No | `"cash"` | Payment method — **format-flexible** (see mapping below) |
| `payer_name` | `string \| null` | No | `null` | Payer name for receipt |
| `notes` | `string \| null` | No | `null` | Free-text notes |
| `allow_credit` | `boolean` | No | `true` | Allow overpayment/credit |
| `lines` | `array[ReceiptLineInput]` | **Yes** | — | Payment line items |

### Payment Method Input Mapping

The `method` field accepts any of these values (case-insensitive) and normalizes them:

| Accepted Inputs | Stores As |
|----------------|-----------|
| `"cash"`, `"Cash"`, `"payments"` | `"cash"` |
| `"card"`, `"Card"` | `"card"` |
| `"transfer"`, `"Transfer"` | `"transfer"` |
| `"online"`, `"Online"` | `"online"` |
| `"ewallet"`, `"E-Wallet"`, `"e-wallet"`, `"e_wallet"`, `"account_balance_wallet"` | `"ewallet"` |
| `"instapay"`, `"instaPay"`, `"insta_pay"`, `"insta-pay"`, `"bolt"` | `"instapay"` |
| `"other"`, `"Other"`, `"more_horiz"` | `"other"` |

Any value not in the mapping returns a 422 ValidationError.

### Example Requests

```json
{
  "method": "bolt",
  "payer_name": "Ahmed Ali",
  "allow_credit": true,
  "lines": [
    {"student_id": 1, "amount": 500.0, "payment_type": "course_level"}
  ]
}
```

```json
{
  "method": "E-Wallet",
  "payer_name": "Sara Mohamed",
  "allow_credit": false,
  "lines": [
    {"student_id": 2, "amount": 300.0, "payment_type": "course_level"}
  ]
}
```

## Response

### 201 Created

```json
{
  "success": true,
  "data": {
    "receipt_id": 42,
    "receipt_number": "RCP-2026-0042",
    "payment_method": "ewallet",
    "paid_at": "2026-06-10T12:00:00Z",
    "lines": 1,
    "total": 500.0,
    "payment_ids": [101]
  },
  "message": "Receipt created successfully."
}
```

### 422 Validation Error — Invalid Payment Method

```json
{
  "success": false,
  "error": "ValidationError",
  "message": "('body', 'method'): Input should be 'cash', 'card', 'transfer', 'online', 'ewallet', 'instapay' or 'other'",
  "details": [
    {
      "input": "unknown_value",
      "loc": ["body", "method"],
      "msg": "Input should be 'cash', 'card', 'transfer', 'online', 'ewallet', 'instapay' or 'other'",
      "type": "enum"
    }
  ]
}
```
