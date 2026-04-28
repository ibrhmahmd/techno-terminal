# Finance Simplification Implementation Report

## Scope Completed

This report covers the implemented phases for finance simplification toward:
- payments-only runtime source of truth,
- split routers with non-overlapping responsibilities,
- mandatory write-audit to `student_payment_history` and `student_activity_log`,
- admin receipt-template governance,
- deprecation of allocation-based balance triggers.

## Implemented Changes

### 1) Receipt Contract and Competition Linking
- Updated `ReceiptLineRequest` to include `team_member_id`.
- Mapped `team_member_id` into service DTO conversion in finance router.

Files:
- `app/api/schemas/finance/receipt.py`
- `app/api/routers/finance/finance_router.py`

### 2) Atomic Finance Write Audit
- Added repository helpers to write:
  - `student_payment_history`,
  - `student_activity_log`.
- Added service helper to enforce mandatory dual history writes from the same transaction.
- Applied to:
  - receipt creation lines,
  - refund line creation.

Files:
- `app/modules/finance/finance_repository.py`
- `app/modules/finance/finance_service.py`

### 3) Refund Traceability
- Added `original_payment_id` support to payment model and payment insert path.
- Added migration for schema support and index.

Files:
- `app/modules/finance/finance_models.py`
- `app/modules/finance/finance_repository.py`
- `db/migrations/022_add_original_payment_id.sql`

### 4) Balance Service Simplification
- Removed runtime dependency on `payment_allocations` in balance calculations.
- `calculate_balance()` now reads canonical values from payments-based balance view.
- `get_enrollment_balance()` now computes from `payments`.
- `list_unpaid_enrollments()` now reads from `v_unpaid_enrollments`.
- `adjust_balance()` marked deprecated for payments-only mode.

Files:
- `app/modules/finance/services/balance_service.py`

### 5) Receipt Router Boundary Cleanup
- Moved receipt read/search/pdf endpoints from `finance_router` to `receipt_router`.
- Kept endpoint paths unchanged (API compatibility).
- `finance_router` now focused on write actions and competition fee reads.

Files:
- `app/api/routers/finance/finance_router.py`
- `app/api/routers/finance/receipt_router.py`

### 6) Receipt Template Admin Governance
- Added endpoints:
  - `GET /receipts/templates`
  - `POST /receipts/templates/{template_name}/set-default`
- Added service methods:
  - `list_templates()`
  - `set_default_template()`

Files:
- `app/api/routers/finance/receipt_router.py`
- `app/modules/finance/services/receipt_generation_service.py`

### 7) Allocation-Trigger Deprecation Cutover
- Added migration to disable allocation-based balance triggers/functions.

Files:
- `db/migrations/023_deprecate_allocation_balance_triggers.sql`

### 8) Tests
- Added template endpoint tests (auth/admin access behavior).

Files:
- `tests/test_finance.py`

## Deprecated Runtime Objects

Deprecated from active runtime:
- Trigger: `trg_update_balance_on_payment`
- Trigger: `trg_update_balance_on_enrollment`
- Function: `update_student_balance()`
- Function: `update_balance_on_enrollment_change()`

Migration:
- `db/migrations/023_deprecate_allocation_balance_triggers.sql`

Legacy objects intentionally retained physically for compatibility (not removed in this sprint):
- `payment_allocations`
- allocation-focused views and services
- `student_balances` as non-canonical cache candidate

## API Contract Notes

### Preserved
- Existing finance receipt/read/search/pdf endpoint paths preserved.
- Router internal ownership changed only (no path break).

### Additive
- Receipt line payload now supports `team_member_id`.

## Verification Notes

- Python compile checks passed for modified finance modules.
- `tests/test_finance.py` still fails in this environment primarily due external Supabase auth token validation (`401`).
- New template tests were added with auth-aware assertions.

## Remaining Optional Follow-ups

- Replace auth-dependent integration tests with fully mocked auth fixtures for deterministic CI.
- Remove dead allocation services after one stabilization sprint.
- Add idempotency key for receipt creation to prevent duplicate submits.
