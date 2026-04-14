# Finance Endpoints Comprehensive Audit

**Audit Date:** April 2026  
**Scope:** All 17 finance endpoints across 3 routers  
**Auditor:** Cascade (AI Code Assistant)

---

## Executive Summary

This audit covers 17 finance endpoints across `finance_router.py`, `receipt_router.py`, and `balance_router.py`. The finance module handles student billing, receipt generation, refunds, and balance tracking.

### Key Findings
- **Total Endpoints:** 17 (8 + 3 + 6)
- **Critical Issues:** 1 → **RESOLVED ✓** (all services now return typed DTOs)
- **High Issues:** 2 → **RESOLVED ✓** (refund validation + batch error handling)
- **Medium Issues:** 3 → **RESOLVED ✓** (pagination, JSON contracts, date limits)

---

## Endpoint Audit Table

### 1. Finance Router Endpoints (finance_router.py)

#### 1.1 POST /finance/receipts - Create Receipt
| Field | Details |
|-------|---------|
| **Method** | POST |
| **Auth** | Admin only (`require_admin`) |
| **Request** | `CreateReceiptRequest` |
| **Request Fields** | `payer_name?: str`, `method: str = "cash"`, `notes?: str`, `allow_credit: bool = true`, `lines: ReceiptLineRequest[]` |
| **Response** | `ApiResponse[ReceiptCreationResponse]` |
| **Response Fields** | `receipt_id, receipt_number, payment_method, paid_at, lines, total, payment_ids` |
| **When to Use** | Creating new payment receipts for enrollments, competition fees, or other charges |
| **Status** | ✅ **FIXED** (Issue C1) - Now returns typed `ReceiptCreationResponse` instead of raw dict |

#### 1.2 GET /finance/receipts/{receipt_id} - Get Receipt Details
| Field | Details |
|-------|---------|
| **Method** | GET |
| **Auth** | Any authenticated user (`require_any`) |
| **Request** | Path param: `receipt_id: int` |
| **Response** | `ApiResponse[ReceiptDetailResponse]` |
| **Response Fields** | `receipt_number, created_at, payer_name, method, total, status, lines[]` |
| **When to Use** | Displaying receipt details, printing receipts, verifying payment history |
| **Potential Issues** | ⚠️ Returns 404 if receipt not found; no soft-delete check |

#### 1.3 GET /finance/receipts - Search Receipts
| Field | Details |
|-------|---------|
| **Method** | GET |
| **Auth** | Admin only |
| **Request Query** | `from_date: date (required)`, `to_date: date (required)`, `payer_name?: str`, `student_id?: int`, `receipt_number?: str`, `limit: int = 200 (max 1000)` |
| **Response** | `ApiResponse[ReceiptListItem[]]` |
| **Response Fields** | `receipt_id, receipt_number, payer_name, total, created_at, status` |
| **Validation** | ✅ Maximum date range: **90 days** (Issue M3 fix). Returns HTTP 422 if exceeded |
| **When to Use** | Admin dashboard receipt search, daily reconciliation, audit reports |
| **Potential Issues** | ⚠️ No pagination (only limit) |

#### 1.4 POST /finance/refunds - Issue Refund
| Field | Details |
|-------|---------|
| **Method** | POST |
| **Auth** | Admin only |
| **Request** | `IssueRefundRequest` |
| **Request Fields** | `payment_id: int`, `amount: float`, `reason: str`, `method: str = "cash"` |
| **Response** | `ApiResponse[RefundResponse]` |
| **Response Fields** | `refund_id, payment_id, amount, method, reason, new_balance, processed_at` |
| **Validation** | ✅ Refund amount validated against (original - already_refunded) - Returns HTTP 422 if exceeds available |
| **When to Use** | Processing refunds for overpayments, cancelled enrollments, or errors |
| **Potential Issues** | ⚠️ Competition fee unmarking logic in service layer may have race conditions |

#### 1.5 GET /finance/balance/student/{student_id} - Get Student Balance
| Field | Details |
|-------|---------|
| **Method** | GET |
| **Auth** | Any authenticated user |
| **Request** | Path: `student_id: int`; Query: `use_materialized: bool = true` |
| **Response** | `ApiResponse[StudentBalanceResponse]` |
| **Response Fields** | `student_id, total_due, total_paid, total_discount, net_balance, enrollments[]` |
| **When to Use** | Student profile balance display, payment portal, debt collection |
| **Potential Issues** | ⚠️ Materialized view may be stale; flag allows real-time calc but slower |

#### 1.6 GET /finance/balance/enrollment/{enrollment_id} - Get Enrollment Balance
| Field | Details |
|-------|---------|
| **Method** | GET |
| **Auth** | Any authenticated user |
| **Request** | Path: `enrollment_id: int` |
| **Response** | `ApiResponse[EnrollmentBalanceResponse]` |
| **Response Fields** | `enrollment_id, amount_due, discount_applied, total_paid, remaining_balance, is_paid` |
| **When to Use** | Enrollment detail page, payment plan calculations |
| **Potential Issues** | ✅ Clean implementation |

#### 1.7 GET /finance/competition-fees/student/{student_id} - Get Unpaid Competition Fees
| Field | Details |
|-------|---------|
| **Method** | GET |
| **Auth** | Any authenticated user |
| **Request** | Path: `student_id: int` |
| **Response** | `ApiResponse[CompetitionFeeItem[]]` |
| **Response Fields** | `competition_id, name, fee_amount, due_date, is_paid` |
| **When to Use** | Competition registration flow, fee reminders |
| **Potential Issues** | ⚠️ Cross-module dependency on competitions; may need caching for large datasets |

#### 1.8 POST /finance/receipts/preview-risk - Preview Overpayment Risk
| Field | Details |
|-------|---------|
| **Method** | POST |
| **Auth** | Admin only |
| **Request** | `PreviewOverpaymentRequest` |
| **Request Fields** | `student_id: int`, `planned_amount: float` |
| **Response** | `ApiResponse[OverpaymentRiskResponse[]]` |
| **Response Fields** | `enrollment_id, current_balance, would_result_in_credit, suggested_amount` |
| **When to Use** | Pre-payment validation, payment plan suggestions, credit warnings |
| **Potential Issues** | ✅ Good UX pattern; should be called before all payments |

---

### 2. Receipt Router Endpoints (receipt_router.py)

#### 2.1 GET /receipts/{receipt_id}/generate - Generate Receipt Text
| Field | Details |
|-------|---------|
| **Method** | GET |
| **Auth** | Any authenticated user |
| **Request** | Path: `receipt_id: int`; Query: `template_name: str = "standard"`, `include_balance: bool = true`, `as_text: bool = false` |
| **Response** | `ApiResponse[ReceiptGenerationResponse]` (default) or Plain text (`text/plain`) with `?as_text=true` |
| **Response Fields** | `receipt_id, content, template_name, include_balance, generated_at, content_type` |
| **When to Use** | Receipt printing, email attachments, POS displays |
| **Status** | ✅ **FIXED** (Issue M2) - Now returns structured JSON by default; use `?as_text=true` for legacy plain text |

#### 2.2 POST /receipts/{receipt_id}/mark-sent - Mark Receipt as Sent
| Field | Details |
|-------|---------|
| **Method** | POST |
| **Auth** | Admin only |
| **Request** | `MarkReceiptSentRequest` |
| **Request Fields** | `parent_email?: str` |
| **Response** | `ApiResponse[dict]` |
| **Response Fields** | `receipt_id, receipt_number, sent_to_parent, sent_at?, parent_email?` |
| **When to Use** | Tracking receipt delivery, email audit trail |
| **Potential Issues** | ✅ Simple, focused endpoint |

#### 2.3 POST /receipts/batch-generate - Batch Generate Receipts
| Field | Details |
|-------|---------|
| **Method** | POST |
| **Auth** | Admin only |
| **Request** | `BatchGenerateRequest` |
| **Request Fields** | `receipt_ids: int[]`, `template_name: str = "standard"` |
| **Response** | `ApiResponse[BatchReceiptItem[]]` |
| **Response Fields** | `receipt_id, success, content, error_message, error_code` |
| **When to Use** | End-of-day batch processing, monthly statement generation |
| **Status** | ✅ **FIXED** (Issue H2) - Structured response with explicit `success` flag and `error_code`; individual failures don't abort batch |

---

### 3. Balance Router Endpoints (balance_router.py)

#### 3.1 GET /students/{student_id}/balance - Get Student Balance
| Field | Details |
|-------|---------|
| **Method** | GET |
| **Auth** | Any authenticated user |
| **Request** | Path: `student_id: int`; Query: `use_materialized: bool = true` |
| **Response** | `ApiResponse[StudentBalanceResponse]` |
| **Response Fields** | `student_id, total_due, total_discount, total_paid, net_balance, credit_balance, enrollments[]` |
| **When to Use** | Student financial summary, dashboard widgets, payment decisions |
| **Status** | ✅ Clean endpoint - Returns typed `StudentBalanceResponse` |

#### 3.2 GET /students/{student_id}/balance/enrollments/{enrollment_id} - Get Enrollment Balance
| Field | Details |
|-------|---------|
| **Method** | GET |
| **Auth** | Any authenticated user |
| **Request** | Path: `student_id: int`, `enrollment_id: int` |
| **Response** | `ApiResponse[EnrollmentBalanceResponse]` |
| **Response Fields** | `enrollment_id, amount_due, discount_applied, total_paid, remaining_balance, status, is_paid` |
| **When to Use** | Enrollment payment page, installment tracking |
| **Potential Issues** | ✅ Clean endpoint |

#### 3.3 GET /balance/unpaid-enrollments - List Unpaid Enrollments
| Field | Details |
|-------|---------|
| **Method** | GET |
| **Auth** | Any authenticated user |
| **Request** | Query: `group_id?: int`, `skip: int = 0`, `limit: int = 50 (max 200)` |
| **Response** | `PaginatedResponse[UnpaidEnrollmentItem]` |
| **Response Fields** | `data[], total, skip, limit` with enrollment details and balances |
| **When to Use** | Debt collection reports, group balance reports, admin dashboards |
| **Status** | ✅ **FIXED** (Issue M1) - Database-level pagination in service layer; returns `(items, total_count)` tuple |
| **Note** | ⚠️ No sorting options currently available |

#### 3.4 POST /students/{student_id}/balance/adjust - Adjust Balance
| Field | Details |
|-------|---------|
| **Method** | POST |
| **Auth** | Admin only |
| **Request** | `BalanceAdjustmentRequest` |
| **Request Fields** | `amount: float`, `reason: str`, `adjustment_type: str` |
| **Response** | `ApiResponse[BalanceAdjustmentResponse]` |
| **Response Fields** | `student_id, previous_balance, adjustment_amount, new_balance, reason, adjustment_type, adjusted_at` |
| **When to Use** | Correcting billing errors, applying scholarships, writing off bad debt |
| **Potential Issues** | ⚠️ No approval workflow; ⚠️ No automatic audit log entry (manual) |

#### 3.5 GET /students/{student_id}/balance/credit - Get Credit Balance
| Field | Details |
|-------|---------|
| **Method** | GET |
| **Auth** | Any authenticated user |
| **Request** | Path: `student_id: int` |
| **Response** | `ApiResponse[CreditBalanceResponse]` |
| **Response Fields** | `student_id, credit_balance, available_credit, reserved_credit, credit_history[]` |
| **When to Use** | Credit application decisions, refund eligibility |
| **Potential Issues** | ✅ Clean endpoint |

#### 3.6 POST /students/{student_id}/balance/apply-credit - Apply Credit
| Field | Details |
|-------|---------|
| **Method** | POST |
| **Auth** | Admin only |
| **Request** | `ApplyCreditRequest` |
| **Request Fields** | `enrollment_id: int`, `amount?: float` (defaults to full credit) |
| **Response** | `ApiResponse[ApplyCreditResponse]` |
| **Response Fields** | `student_id, enrollment_id, amount_applied, credit_applications[], enrollment_balance_after` |
| **When to Use** | Applying overpayment credit to new enrollments, credit transfers |
| **Potential Issues** | ⚠️ Complex nested dict structure in response; ⚠️ Partial credit application edge cases not documented |

---

## Bugs & Issues Summary

### Critical Issues (RESOLVED ✓)

| ID | Issue | Location | Impact | Status |
|----|-------|----------|--------|--------|
| C1 | Services return raw `dict` instead of DTOs | `balance_service.py`, `finance_service.py` | Type safety violations, schema drift | **FIXED** ✓ |

**Resolution:**
- All service methods now return typed DTOs:
  - `create_receipt_with_charge_lines()` → `ReceiptCreationResponse`
  - `preview_overpayment_risk()` → `List[OverpaymentRiskResponse]`
  - `issue_refund()` → `RefundResponse`
  - `finalize_receipt()` → `ReceiptCreationResponse`
  - `get_receipt_detail()` → `ReceiptDetailResponse`
  - `generate_batch_receipts()` → `List[BatchReceiptItem]`
- See [Schema Reference](./schemas.md) for updated DTO definitions

### High Issues (RESOLVED ✓)

| ID | Issue | Location | Impact | Status |
|----|-------|----------|--------|--------|
| H1 | No validation that refund amount ≤ original payment | `finance_service.py:issue_refund()` | Potential over-refunding | **FIXED** ✓ |
| H2 | Batch receipt errors embedded in response strings | `receipt_generation_service.py` | UI must parse errors manually | **FIXED** ✓ |

**H1 Resolution:**
- Added `get_total_refunded_for_payment()` in repository
- `issue_refund()` now validates: `refund_amount ≤ (original_amount - already_refunded)`
- HTTP 422 error with detailed message: `"Refund amount (X) exceeds available amount (Y). Original: Z, already refunded: W"`

**H2 Resolution:**
- `BatchReceiptItem` now returns structured list with:
  - `receipt_id`, `success`, `content`, `error_message`, `error_code`
- Errors no longer embedded in strings
- Individual failures don't abort entire batch

### Medium Issues (RESOLVED ✓)

| ID | Issue | Location | Impact | Status |
|----|-------|----------|--------|--------|
| M1 | Manual pagination in router instead of service | `balance_router.py:list_unpaid_enrollments()` | Inconsistent pattern, no sorting | **FIXED** ✓ |
| M2 | Receipt generation returns plain text (breaks JSON contract) | `receipt_router.py:generate_receipt()` | UI must handle content-type switch | **FIXED** ✓ |
| M3 | No max date range limit on receipt search | `finance_router.py:search_receipts()` | Potential performance issues | **FIXED** ✓ |

**M1 Resolution:**
- `list_unpaid_enrollments()` service now accepts `skip` and `limit` parameters
- Service performs database-level pagination
- Returns `(items, total_count)` tuple to router
- Router uses `PaginatedResponse[T]` wrapper

**M2 Resolution:**
- `generate_receipt` endpoint now returns `ReceiptGenerationResponse` (JSON) by default
- Added `?as_text=true` query parameter for backward compatibility
- Response includes `content`, `template_name`, `include_balance`, `generated_at`, `content_type`

**M3 Resolution:**
- Added 90-day maximum date range validation on receipt search
- Returns HTTP 422 with message: `"Date range too large. Maximum allowed is 90 days. Requested: X days."`

### Low Issues

| ID | Issue | Location | Impact | Fix Priority |
|----|-------|----------|--------|--------------|
| L1 | Missing `created_by` field in some balance responses | Various | Incomplete audit trail | Low |
| L2 | Inconsistent error message formats | Various | Minor UX inconsistency | Low |

---

## Architectural Observations

### Service Layer Patterns

| Pattern | Status | Notes |
|---------|--------|-------|
| **Dependency Injection** | ✅ Good | `Depends(get_balance_service)` pattern used consistently |
| **DTO Contracts** | ✅ Good | All services now return typed DTOs (Issue C1 fix) |
| **Session Management** | ✅ Good | `get_session()` context manager used properly |
| **Error Handling** | ✅ Good | Custom exceptions map to HTTP codes; validation errors return HTTP 422 |

### Schema Patterns

| Aspect | Status | Notes |
|--------|--------|-------|
| **Request Validation** | ✅ Good | Pydantic schemas with proper types and defaults |
| **Response Wrapping** | ✅ Good | `ApiResponse[T]` and `PaginatedResponse[T]` used consistently |
| **Optional Fields** | ⚠️ Inconsistent | Some DTOs use `Optional` liberally, others strictly required |

### Security Patterns

| Aspect | Status | Notes |
|--------|--------|-------|
| **Authentication** | ✅ Good | `require_admin` vs `require_any` used appropriately |
| **Authorization** | ⚠️ Partial | No row-level security (any user can query any student_id) |
| **Input Sanitization** | ✅ Good | Pydantic handles type coercion and validation |

---

## Recommendations

### Completed Actions ✓
1. **✅ Fix C1:** All services now return typed DTOs instead of raw dicts
2. **✅ Fix H1:** Refund validation against original payment amount implemented
3. **✅ Fix H2:** Batch receipt generation returns structured `BatchReceiptItem`
4. **✅ Fix M1:** Pagination moved to service layer with database-level implementation
5. **✅ Fix M2:** Receipt generation returns `ReceiptGenerationResponse` (JSON) by default
6. **✅ Fix M3:** 90-day maximum date range limit on receipt search enforced

### Remaining Actions
7. **Add tests:** Cover edge cases for credit application and refunds
8. **Add audit:** Log all balance adjustments automatically
9. **Add RLS:** Implement row-level security for student data
10. **Caching:** Add Redis caching for materialized balance views
11. **Monitoring:** Add metrics for refund rates, credit usage

---

## Appendix: Schema Reference

### Key DTOs by Category

**Receipts:**
- `CreateReceiptRequest` → `ReceiptCreationResponse` (Issue C1 fix)
- `ReceiptDetailResponse` (full receipt with lines)
- `ReceiptListItem` (search results)
- `ReceiptGenerationResponse` - Receipt generation response (Issue M2 fix)
- `BatchReceiptItem` - Batch generation result item (Issue H2 fix)

**Refunds:**
- `IssueRefundRequest` → `RefundResponse` (Issue C1 fix)

**Balance:**
- `StudentBalanceResponse` (comprehensive balance)
- `EnrollmentBalanceResponse` (single enrollment)
- `UnpaidEnrollmentItem` (unpaid enrollment item)
- `BalanceAdjustmentRequest` → `BalanceAdjustmentResponse`

**Credit:**
- `ApplyCreditRequest` → `ApplyCreditResponse`
- `CreditBalanceResponse`
- `CreditInfoDTO`

**Risk:**
- `PreviewOverpaymentRequest` → `OverpaymentRiskResponse[]` (Issue C1 fix)

### New DTOs Added (Audit Fixes)

| DTO | Purpose | Issue Fixed |
|-----|---------|-------------|
| `ReceiptCreationResponse` | Response from `create_receipt_with_charge_lines()` | C1 |
| `ReceiptGenerationResponse` | Structured receipt generation response | M2 |
| `BatchReceiptItem` | Individual batch result with success/error | H2 |
| `RefundResponse` | Typed refund response | C1 |
| `OverpaymentRiskResponse` | Risk preview result item | C1 |
