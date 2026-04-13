# Finance API - Schema Reference

Complete reference for all DTOs, request schemas, and response models used in the Finance API.

---

## Table of Contents

1. [Balance Schemas](#balance-schemas)
2. [Receipt Schemas](#receipt-schemas)
3. [Credit Schemas](#credit-schemas)
4. [Allocation Schemas](#allocation-schemas)
5. [Risk Assessment Schemas](#risk-assessment-schemas)
6. [Common Schemas](#common-schemas)

---

## Balance Schemas

### StudentBalanceDTO

**File:** `app/modules/finance/models/balance_models.py`

Complete student balance with enrollment breakdown.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_id` | integer | Yes | Student ID |
| `total_amount_due` | decimal | Yes | Sum of all enrollment amounts |
| `total_discounts` | decimal | Yes | Total discounts applied |
| `total_paid` | decimal | Yes | Total payments received |
| `net_balance` | decimal | Yes | Negative = debt, Positive = credit |
| `enrollment_details` | EnrollmentBalanceDetail[] | Yes | Per-enrollment details |

**Example:**
```json
{
  "student_id": 1,
  "total_amount_due": 450.00,
  "total_discounts": 50.00,
  "total_paid": 300.00,
  "net_balance": -100.00,
  "enrollment_details": [
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

---

### EnrollmentBalanceResponse

**File:** `app/api/schemas/finance/balance.py`

Detailed balance for a single enrollment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enrollment_id` | integer | Yes | Enrollment ID |
| `student_id` | integer | Yes | Student ID |
| `group_id` | integer | Yes | Group ID |
| `level_number` | integer | Yes | Current level |
| `amount_due` | decimal | Yes | Amount owed |
| `discount_applied` | decimal | Yes | Discount amount |
| `total_paid` | decimal | Yes | Amount paid |
| `total_refunded` | decimal | Yes | Refunds issued |
| `remaining_balance` | decimal | Yes | Balance remaining |
| `status` | string | Yes | Enrollment status |
| `is_paid` | boolean | Yes | Fully paid flag |

---

### UnpaidEnrollmentResponse

**File:** `app/api/schemas/finance/balance.py`

Unpaid enrollment item for listing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enrollment_id` | integer | Yes | Enrollment ID |
| `student_id` | integer | Yes | Student ID |
| `student_name` | string | Yes | Student name |
| `group_id` | integer | Yes | Group ID |
| `group_name` | string | Yes | Group name |
| `course_name` | string | Yes | Course name |
| `level_number` | integer | Yes | Level number |
| `amount_due` | decimal | Yes | Amount due |
| `discount_applied` | decimal | Yes | Discount applied |
| `total_paid` | decimal | Yes | Total paid |
| `remaining_balance` | decimal | Yes | Remaining balance |
| `enrolled_at` | string | Yes | Enrollment timestamp |

---

### BalanceAdjustmentRequest

**File:** `app/api/schemas/finance/balance.py`

Request to adjust student balance.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enrollment_id` | integer | No | Target enrollment |
| `adjustment_amount` | float | Yes | Amount to adjust |
| `adjustment_type` | string | Yes | Adjustment type |
| `reason` | string | Yes | Adjustment reason |
| `notes` | string | No | Additional notes |

---

### BalanceAdjustmentResponseDTO

**File:** `app/api/schemas/finance/balance.py`

Response after balance adjustment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_id` | integer | Yes | Student ID |
| `previous_balance` | float | Yes | Balance before |
| `adjustment_amount` | float | Yes | Amount adjusted |
| `new_balance` | float | Yes | Balance after |
| `reason` | string | Yes | Reason |
| `adjustment_type` | string | Yes | Type |
| `adjusted_at` | datetime | Yes | Timestamp |
| `adjusted_by` | integer | Yes | User ID |

---

## Receipt Schemas

### ReceiptFinalizedDTO

**File:** `app/api/schemas/finance/receipt.py`

Response after creating a receipt with charge lines. Replaces raw dict return (Issue C1 fix).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `receipt_id` | integer | Yes | Receipt ID |
| `receipt_number` | string | Yes | Generated receipt number |
| `payment_method` | string | Yes | Payment method used |
| `paid_at` | datetime | Yes | Payment timestamp |
| `lines` | integer | Yes | Count of charge lines |
| `total` | float | Yes | Total amount |
| `payment_ids` | List[int] | Yes | IDs of created payment records |

**Example:**
```json
{
  "receipt_id": 123,
  "receipt_number": "RCP-2026-00123",
  "payment_method": "cash",
  "paid_at": "2026-04-13T08:30:00Z",
  "lines": 1,
  "total": 250.00,
  "payment_ids": [45]
}
```

---

### ReceiptGeneratedDTO

**File:** `app/api/schemas/finance/receipt.py`

Structured response for receipt generation. Default format for `GET /receipts/{id}/generate` (Issue M2 fix).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `receipt_id` | integer | Yes | Receipt ID |
| `content` | string | Yes | Formatted receipt text |
| `template_name` | string | Yes | Template used ("standard", "detailed") |
| `include_balance` | boolean | Yes | Balance info included |
| `generated_at` | datetime | Yes | Generation timestamp |
| `content_type` | string | Yes | Always "text/plain" |

**Example:**
```json
{
  "receipt_id": 123,
  "content": "RECEIPT #RCP-2026-00123\n...",
  "template_name": "standard",
  "include_balance": true,
  "generated_at": "2026-04-13T08:35:00Z",
  "content_type": "text/plain"
}
```

**Usage:**
- Default: Returns JSON with `ReceiptGeneratedDTO`
- Legacy: Use `?as_text=true` for plain text response

---

### BatchReceiptResultDTO

**File:** `app/api/schemas/finance/receipt.py`

Individual result item for batch receipt generation. Part of structured batch response (Issue H2 fix).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `receipt_id` | integer | Yes | Receipt ID |
| `success` | boolean | Yes | Generation successful |
| `content` | string \| null | Yes | Receipt content (null if error) |
| `error_message` | string \| null | Yes | Error description (null if success) |
| `error_code` | string \| null | Yes | Error code: `not_found`, `invalid`, `server_error` |

**Example:**
```json
{
  "receipt_id": 124,
  "success": false,
  "content": null,
  "error_message": "Receipt 124 not found",
  "error_code": "not_found"
}
```

---

### CreateReceiptRequest

**File:** `app/api/schemas/finance/receipt.py`

Request to create a receipt.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `payer_name` | string | No | null | Payer name |
| `method` | string | No | "cash" | Payment method |
| `notes` | string | No | null | Notes |
| `allow_credit` | boolean | No | false | Allow credit |
| `lines` | ReceiptLinePublic[] | Yes | - | Line items |

---

### ReceiptLinePublic

**File:** `app/api/schemas/finance/receipt.py`

Receipt line item.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Line ID |
| `student_id` | integer | Yes | Student ID |
| `enrollment_id` | integer | No | Enrollment ID |
| `amount` | float | Yes | Amount |
| `description` | string | No | Description |

---

### ReceiptCreatedPublic

**File:** `app/api/schemas/finance/receipt.py`

Created receipt response.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Receipt ID |
| `receipt_number` | string | Yes | Receipt number |
| `payer_name` | string | Yes | Payer name |
| `total` | float | Yes | Total amount |
| `method` | string | Yes | Payment method |
| `created_at` | datetime | Yes | Timestamp |
| `payment_ids` | integer[] | Yes | Payment IDs |

---

### ReceiptDetailPublic

**File:** `app/api/schemas/finance/receipt.py`

Detailed receipt information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `header` | ReceiptHeaderPublic | Yes | Header info |
| `lines` | ReceiptLinePublic[] | Yes | Line items |
| `total` | float | Yes | Total amount |

---

### ReceiptHeaderPublic

**File:** `app/api/schemas/finance/receipt.py`

Receipt header information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Receipt ID |
| `receipt_number` | string | Yes | Receipt number |
| `payer_name` | string | Yes | Payer name |
| `total` | float | Yes | Total amount |
| `created_at` | datetime | Yes | Timestamp |

---

### ReceiptListItem

**File:** `app/api/schemas/finance/receipt.py`

Receipt item for search results.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Receipt ID |
| `receipt_number` | string | Yes | Receipt number |
| `payer_name` | string | Yes | Payer name |
| `total` | float | Yes | Total amount |
| `created_at` | datetime | Yes | Timestamp |
| `method` | string | Yes | Payment method |

---

### MarkReceiptSentRequest

**File:** `app/api/schemas/finance/receipt.py`

Request to mark receipt as sent.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `parent_email` | string | No | Parent email |

---

### BatchGenerateRequest

**File:** `app/api/schemas/finance/receipt.py`

Batch generation request.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `receipt_ids` | integer[] | Yes | - | Receipt IDs |
| `template_name` | string | No | "standard" | Template |

---

### BatchGenerateResponse

**File:** `app/api/schemas/finance/receipt.py`

Batch generation response item.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `receipt_id` | integer | Yes | Receipt ID |
| `content` | string | Yes | Content or error |

---

## Credit Schemas

### CreditApplicationItemDTO

**File:** `app/api/schemas/finance/credit.py`

Individual credit application record.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `credit_id` | integer | Yes | Credit record ID |
| `amount_applied` | float | Yes | Amount applied |
| `applied_at` | datetime | Yes | Timestamp |

---

### ApplyCreditRequestDTO

**File:** `app/api/schemas/finance/credit.py`

Request to apply credit.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_id` | integer | Yes | Student ID |
| `enrollment_id` | integer | Yes | Target enrollment |
| `amount` | float | No | Amount to apply |

---

### ApplyCreditResponseDTO

**File:** `app/api/schemas/finance/credit.py`

Response after applying credit.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_id` | integer | Yes | Student ID |
| `enrollment_id` | integer | Yes | Enrollment ID |
| `amount_applied` | float | Yes | Amount applied |
| `remaining_credit` | float | Yes | Remaining credit |
| `applied_at` | datetime | Yes | Timestamp |

---

### CreditBalanceResponseDTO

**File:** `app/api/schemas/finance/credit.py`

Credit balance response.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_id` | integer | Yes | Student ID |
| `available_credit` | float | Yes | Available amount |

---

### StudentCreditInfoDTO

**File:** `app/api/schemas/finance/credit.py`

Detailed credit information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `credit_id` | integer | Yes | Credit ID |
| `student_id` | integer | Yes | Student ID |
| `amount` | float | Yes | Credit amount |
| `available` | float | Yes | Available |
| `reserved` | float | Yes | Reserved |
| `created_at` | datetime | Yes | Timestamp |

---

## Allocation Schemas

### AllocationReversalResponseDTO

**File:** `app/api/schemas/finance/allocations.py`

Allocation reversal response.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `original_allocation_id` | integer | Yes | Original ID |
| `reversal_allocation_id` | integer | Yes | Reversal ID |
| `amount_reversed` | float | Yes | Amount reversed |
| `reason` | string | Yes | Reason |
| `reversed_at` | datetime | Yes | Timestamp |
| `reversed_by` | integer | Yes | User ID |

---

### PaymentAllocationItemDTO

**File:** `app/api/schemas/finance/allocations.py`

Payment allocation item.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `allocation_id` | integer | Yes | Allocation ID |
| `payment_id` | integer | Yes | Payment ID |
| `enrollment_id` | integer | Yes | Enrollment ID |
| `amount` | float | Yes | Allocated amount |
| `allocated_at` | datetime | Yes | Timestamp |
| `is_reversal` | boolean | Yes | Is reversal |

---

### PaymentAllocationsResponseDTO

**File:** `app/api/schemas/finance/allocations.py`

All allocations for a payment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `payment_id` | integer | Yes | Payment ID |
| `allocations` | PaymentAllocationItemDTO[] | Yes | Allocations |

---

## Risk Assessment Schemas

### PreviewRiskRequest

**File:** `app/api/schemas/finance/risk.py`

Overpayment risk preview request.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lines` | ReceiptLineInput[] | Yes | Lines to preview |

---

### OverpaymentRiskItem

**File:** `app/api/schemas/finance/risk.py`

Risk item for overpayment preview.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_id` | integer | Yes | Student ID |
| `enrollment_id` | integer | Yes | Enrollment ID |
| `amount` | float | Yes | Payment amount |
| `debt_before` | float | Yes | Current debt |
| `projected_balance` | float | Yes | Projected balance |
| `excess_credit` | float | Yes | Credit amount |

---

## Common Schemas

### FinancialSummaryPublic

**File:** `app/api/schemas/finance/balance.py`

Financial summary per enrollment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enrollment_id` | integer | Yes | Enrollment ID |
| `amount_due` | float | Yes | Amount due |
| `total_paid` | float | Yes | Total paid |
| `discount_applied` | float | Yes | Discount |
| `remaining_balance` | float | Yes | Remaining |
| `status` | string | Yes | Status |

### IssueRefundRequest

**File:** `app/api/schemas/finance/receipt.py`

Refund request.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `payment_id` | integer | Yes | - | Payment ID |
| `amount` | float | Yes | - | Refund amount |
| `reason` | string | Yes | - | Reason |
| `method` | string | Yes | "cash" | Method |

### RefundResultPublic

**File:** `app/api/schemas/finance/receipt.py`

Refund result. Replaces raw dict return from `issue_refund()` (Issue C1 fix).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refund_id` | integer | Yes | Refund ID |
| `payment_id` | integer | Yes | Payment ID |
| `amount` | float | Yes | Amount |
| `method` | string | Yes | Method |
| `reason` | string | Yes | Reason |
| `new_balance` | float | Yes | New balance |
| `processed_at` | datetime | Yes | Timestamp |

**Example:**
```json
{
  "refund_id": 67,
  "payment_id": 45,
  "amount": 50.00,
  "method": "transfer",
  "reason": "Student withdrawal",
  "new_balance": 100.00,
  "processed_at": "2026-04-09T14:30:00Z"
}
```

### StudentBalanceSummaryDTO

**File:** `app/api/schemas/finance/balance.py`

Quick balance summary.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_id` | integer | Yes | Student ID |
| `net_balance` | float | Yes | Net balance |
| `balance_type` | string | Yes | in_debt, credit, settled |
| `enrollment_count` | integer | Yes | Enrollment count |

---

## Enums and Constants

### Adjustment Types
- `manual` - Manual adjustment
- `correction` - Error correction
- `waiver` - Fee waiver
- `scholarship` - Scholarship award
- `refund` - Refund processing

### Payment Methods
- `cash` - Cash payment
- `card` - Credit/debit card
- `transfer` - Bank transfer

### Fee Types (Competition)
- `registration` - Registration fee
- `materials` - Materials/supplies
- `transportation` - Transportation
- `accommodation` - Accommodation

---

*Last updated: 2026-04-09*
