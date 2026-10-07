# Implementation Plan: Payment Void and Refund Workflows

**Branch**: `034-payment-void-refund` | **Date**: 2026-07-11 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/034-payment-void-refund/spec.md`

---

## Summary

Implement two MVP endpoints (`POST /finance/payments/{id}/void` and `POST /finance/payments/{id}/refund`) plus a VoidService that enforces all clarified business rules. The existing `RefundService` already handles the happy path for refunds; this plan closes the remaining gaps: the Void operation (US1), the mutual-exclusion guards (FR-005), competition-payment void unlinking (FR-006b), mandatory reason validation (FR-002), and audit log entries (FR-007).

The `v_daily_collections`, `v_enrollment_balance`, and `v_unpaid_enrollments` views already filter `deleted_at IS NULL` and correctly separate `collected_amount` from `refunded_amount` — **no DB view changes needed**.

---

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: FastAPI, SQLModel, SQLAlchemy 2.x  
**Storage**: PostgreSQL via `app/db/connection.py` (pool_size=10, max_overflow=5)  
**Testing**: pytest + SQLModel test session  
**Target Platform**: Linux server (Leapcell)  
**Project Type**: Web service (FastAPI)  
**Performance Goals**: N/A for this feature (low-frequency admin operation)  
**Constraints**: `statement_timeout=30000` (30 s global); all ops are single-row soft-deletes — well within limit  
**Scale/Scope**: ~17 contract instructors, ~689 students — negligible load

---

## Constitution Check

| Rule | Status |
|------|--------|
| §I Router → Service → Repository | ✅ — new endpoints delegate entirely to services |
| §I Two-Layer Schema Rule | ✅ — new request/response schemas in `app/api/schemas/finance/`; services never import from `app.api.schemas.*` |
| §II Module Organization | ✅ — Finance uses flat Horizontal Layer (≤2 entity types); no D+ needed |
| §III Typed Contracts | ✅ — all service return types are named DTOs; `get_total_refunded` uses `Decimal`; new `VoidResultDTO` to be added |
| §III Dead Code — `get_payments_by_group_with_levels` | ⚠️ returns `list[dict]` — pre-existing violation, out of scope for this feature; log for future cleanup |
| §IV Exception Mapping | ✅ — `BusinessRuleError` → 409, `NotFoundError` → 404, `ValidationError` → 422 |
| §V Auth Guard | ✅ — both endpoints use `require_admin` |
| §VI UoW Rollback | ✅ — VoidService will re-raise after rollback; no silent swallowing |

---

## Project Structure

### Documentation (this feature)

```text
specs/034-payment-void-refund/
├── spec.md        ✅ (clarified)
└── plan.md        ← this file
```

### Source Code Changes

```text
app/
├── api/
│   ├── routers/finance/
│   │   └── finance_router.py          [MODIFY] — add void + refund endpoints
│   └── schemas/finance/
│       └── payment.py                 [MODIFY] — add VoidPaymentRequest, VoidPaymentResponse
│
└── modules/finance/
    ├── interfaces/
    │   ├── dto/
    │   │   └── void_dto.py            [NEW] — VoidPaymentInput, VoidResultDTO
    │   ├── services/
    │   │   └── Ivoid_service.py       [NEW] — IVoidService Protocol
    │   └── __init__.py                [MODIFY] — export new DTOs + IVoidService
    │
    ├── services/
    │   ├── void_service.py            [NEW] — VoidService implementation
    │   └── refund_service.py          [MODIFY] — add voided-payment guard + mandatory reason check
    │
    └── repositories/
        └── payment_repository.py      [MODIFY] — add void-specific query helpers

app/api/dependencies.py                [MODIFY] — add get_void_service factory

db/migrations/
└── 077_void_payment_audit_activity_subtype.sql  [NEW] — ensure 'void' is a valid subtype in student_activity_log (if constrained)

tests/
└── test_payment_void_refund.py        [NEW] — full test coverage
```

---

## Detailed Change Breakdown

### 1. New DTOs — `app/modules/finance/interfaces/dto/void_dto.py`

```python
class VoidPaymentInput(BaseModel):
    voided_by_user_id: int
    reason: str  # non-empty enforced by validator

class VoidResultDTO(BaseModel):
    payment_id: int
    voided_at: datetime
    message: str
```

### 2. New Interface — `app/modules/finance/interfaces/services/Ivoid_service.py`

```python
@runtime_checkable
class IVoidService(Protocol):
    def void_payment(self, payment_id: int, dto: VoidPaymentInput) -> VoidResultDTO: ...
```

### 3. New Service — `app/modules/finance/services/void_service.py`

Business rules to enforce in order:

1. **Fetch payment** — `get_by_id(payment_id)`. If missing → `NotFoundError`.
2. **Check already voided** — if `payment.deleted_at is not None` → `BusinessRuleError("Payment already voided.")`.
3. **Check active refunds** (only when voiding a `transaction_type='payment'` row) — call `has_active_refunds(payment_id)`. If true → `BusinessRuleError("Cannot void payment with active refunds. Void the refunds first.")`.
4. **Soft-delete** — set `payment.deleted_at = utc_now()`, `payment.deleted_by = dto.voided_by_user_id`, `payment.notes = dto.reason` (appended or set).
5. **Competition unlinking** — if `payment.payment_type == 'competition'`, call `_unlink_competition_payment(payment_id, payment.amount)` (same helper as refund service, but add instead of subtract for a refund-void scenario — see below).
6. **Commit** via `uow.commit()`.
7. **Audit log** — `student_activity_log` entry: `activity_type='payment'`, `activity_subtype='void'`, `reference_type='payment'`, `reference_id=payment_id`, `performed_by=dto.voided_by_user_id`.

**Competition logic nuance**:
- Voiding a `transaction_type='payment'` row (cash in) → **decrement** `amount_paid` by the voided amount.
- Voiding a `transaction_type='refund'` row (refund in error) → **add back** the refund amount to `amount_paid` (reverse the decrement that the refund created).

### 4. Modify `refund_service.py`

Two gaps to close:

a. **Voided payment guard** — before current validation, check: `if original.deleted_at is not None → BusinessRuleError("Cannot refund a voided payment.")`.

b. **Mandatory reason** — `IssueRefundDTO.reason` must be non-empty. Add a field validator to the DTO (or validate in service if DTO is shared). 422 if empty.

### 5. Modify `payment_repository.py`

Add two new query methods:

```python
def has_active_refunds(self, payment_id: int) -> bool:
    """Return True if payment has any non-deleted refund rows."""

def soft_delete(self, payment: Payment, deleted_by: int, notes: str) -> Payment:
    """Apply soft-delete fields and flush."""
```

The `get_total_refunded` method already filters `deleted_at` — **it does not** (it queries `WHERE original_payment_id = :pid AND transaction_type = 'refund'` without a `deleted_at IS NULL` filter). This must be fixed to exclude voided refunds from the available balance calculation.

### 6. Modify `finance_router.py`

Add two new endpoints:

```python
POST /finance/payments/{payment_id}/void
    body: VoidPaymentRequest { reason: str }
    auth: require_admin
    → calls void_service.void_payment(payment_id, dto)
    → returns ApiResponse[VoidPaymentResponse]

POST /finance/payments/{payment_id}/refund
    body: IssueRefundRequest (existing schema, add reason validation)
    auth: require_admin
    → calls refund_service.issue(dto)
    → returns ApiResponse[RefundResponse]
```

### 7. Modify `app/api/dependencies.py`

Add `get_void_service()` factory following the same UoW-based pattern as `get_refund_service()`.

### 8. Migration `077_void_payment_audit_activity_subtype.sql`

Check if `student_activity_log.activity_subtype` has a CHECK constraint or enum that needs `'void'` added. If not constrained, no migration needed — just document.

---

## Critical Bug Fix Included

**`get_total_refunded` missing `deleted_at IS NULL`**:

Current query:
```sql
SELECT COALESCE(SUM(amount), 0)
FROM payments
WHERE original_payment_id = :pid
AND transaction_type = 'refund'
```

This includes voided refund rows in the sum, which reduces the `available` refundable amount incorrectly. Fix:

```sql
SELECT COALESCE(SUM(amount), 0)
FROM payments
WHERE original_payment_id = :pid
AND transaction_type = 'refund'
AND deleted_at IS NULL   -- ← add this
```

---

## Verification Plan

### Automated Tests — `tests/test_payment_void_refund.py`

| Test | Covers |
|------|--------|
| `test_void_payment_basic` | US1 happy path — payment soft-deleted, balance restored |
| `test_void_payment_no_reason` | FR-002 — 422 on empty reason |
| `test_void_payment_already_voided` | FR-005 — 409 on double-void |
| `test_void_payment_with_active_refund` | FR-005 / Q3 decision — 409, must void refund first |
| `test_void_payment_competition` | FR-006b — `TeamMember.amount_paid` decremented |
| `test_refund_voided_payment` | Q4 decision — 409 on refund of voided payment |
| `test_refund_basic` | US2 happy path — refund row created, balance reduced |
| `test_refund_exceeds_available` | FR-004 — 409 on over-refund |
| `test_void_refund_row` | Q5 decision — refund soft-deleted, balance restored |
| `test_void_refund_competition` | Q5 + FR-006 — competition amount_paid restored |
| `test_get_total_refunded_excludes_voided` | Bug fix — voided refunds excluded from available calc |
| `test_audit_log_written_on_void` | FR-007 — activity_log entry created |
| `test_audit_log_written_on_refund` | FR-007 — activity_log entry created |

### Run command
```bash
pytest tests/test_payment_void_refund.py -v
```

### Manual Verification

After deployment, verify via Supabase SQL console:
1. Void a payment — confirm `deleted_at` set, balance view reflects change immediately.
2. Attempt to void again — confirm 409.
3. Attempt to refund voided payment — confirm 409.
4. Issue refund, void the refund — confirm parent payment refundable balance restored.
