# Feature Specification: Payment Void and Refund Workflows

**Feature Branch**: `034-payment-void-refund`  
**Created**: 2026-06-21  
**Clarified**: 2026-07-11  
**Status**: Clarified ✅  
**Input**: User request: "Discuss how to achieve a refund feature accurately without balance issues/bugs, compare options, and handle false payments (undoing wrong student payments via voids vs. refunds) and edge cases."

---

## Clarification Decision Log

| # | Question | Decision |
|---|----------|----------|
| Q3 | Voiding a partially refunded payment | **Block** — clerk must void active refunds first before voiding the parent payment (Strict Reversal) |
| Q4 | Refunding a voided payment | **409 BusinessRuleError** — "Cannot refund a voided payment" |
| Q5 | Voiding a refund receipt | **Allowed** — same soft-delete mechanism; restores parent payment's refundable balance dynamically |
| Q6 | Competition fee refund | **Atomic** — decrement `TeamMember.amount_paid` in the same DB transaction as the refund |
| Q6b | Competition fee void | **Atomic** — void also decrements `TeamMember.amount_paid` by the voided amount |
| Q7 | Reason field | **Mandatory** for both voids and refunds — 422 if `reason` is empty/null |
| Q8 | Authorization | **`require_admin`** guard for both void and refund endpoints |
| Q9 | Balance after voiding a refund | **Soft-delete only** — `refundable_amount` recalculated dynamically as `original_amount - SUM(refunds WHERE deleted_at IS NULL)` |
| Q10 | Audit trail | **`student_activity_log`** entry written for every void and refund |
| Q11 | API shape | **Separate endpoints** — `POST /finance/payments/{id}/void` and `POST /finance/payments/{id}/refund` |
| Q12 | `v_daily_collections` | **Payments only** — only `transaction_type='payment'` and `deleted_at IS NULL` count as collections. Voids and refunds are excluded from collected totals (they already appear in `refunded_amount` column) |
| Q13 | Refund storage | **Same `payments` table** — `transaction_type='refund'` + `original_payment_id` FK pointing to parent |

---

## User Scenarios & Testing

### User Story 1 - Void/Undo Accidental Payments (Priority: P1) 🎯 MVP

**Description**:  
As a Financial Desk staff member, I want to void (undo) a payment that was accidentally applied to the wrong student or contains clerical errors, so that the student's balance is corrected immediately without distorting actual cash flow/refund reporting.

**Why this priority**:  
Staff clerical errors are common. Undoing them via a "Void" preserves audit history while instantly restoring the student's debt and keeping accounting collections accurate.

**Independent Test**:  
Post a test payment for Student A. Call the `POST /finance/payments/{payment_id}/void` endpoint. Verify that:
1. The payment record is soft-deleted (`deleted_at` and `deleted_by` populated).
2. The student's balance summary immediately reflects the restored debt.
3. The payment is excluded from collections reporting.
4. An audit log entry is added to Student A's `student_activity_log`.

**Acceptance Scenarios**:
1. **Given** a student has an enrollment with EGP 1000 due and EGP 1000 paid (balance EGP 0),  
   **When** the EGP 1000 payment is voided with a reason,  
   **Then** the enrollment balance changes back to EGP 1000 unpaid, and the payment is soft-deleted.
2. **Given** a payment is being voided,  
   **When** no reason is provided,  
   **Then** the system rejects the request with a 422 validation error.
3. **Given** a payment has an active refund of EGP 400 linked to it,  
   **When** a clerk attempts to void the parent payment,  
   **Then** the system rejects with 409 BusinessRuleError: "Cannot void this payment — it has active refunds. Please void the refunds first."
4. **Given** a competition payment of EGP 500 is voided,  
   **Then** `TeamMember.amount_paid` is decremented by EGP 500 in the same transaction.

---

### User Story 2 - Accurate Refunds with Double-Refund Protection (Priority: P1) 🎯 MVP

**Description**:  
As a Financial Desk staff member, I want to issue a full or partial refund against a student's prior payment, so that the customer is paid back, and the refund is tracked dynamically without exceeding the original transaction amount.

**Why this priority**:  
Refunds are legitimate financial transactions where money is returned. Restricting refunds to the original transaction limit prevents fraudulent or clerical over-refunding.

**Independent Test**:  
Select a payment of EGP 1500. Issue a partial refund of EGP 1000. Assert it succeeds and the remaining refundable balance is EGP 500. Try to issue another refund of EGP 600 and assert it is blocked.

**Acceptance Scenarios**:
1. **Given** a payment of EGP 1000 exists,  
   **When** a refund of EGP 600 is processed with a reason,  
   **Then** a new `payments` row with `transaction_type='refund'` and `original_payment_id` is created, and the remaining refundable amount is EGP 400.
2. **Given** a payment has already been refunded EGP 600,  
   **When** a user attempts to refund another EGP 500,  
   **Then** the request is rejected 409 BusinessRuleError: "Refund exceeds available limit of EGP 400."
3. **Given** a voided payment,  
   **When** a clerk attempts to refund it,  
   **Then** the request is rejected 409 BusinessRuleError: "Cannot refund a voided payment."
4. **Given** no reason is provided for a refund,  
   **Then** the system rejects with a 422 validation error.
5. **Given** a competition payment of EGP 500, partially refunded EGP 300,  
   **Then** `TeamMember.amount_paid` is decremented by EGP 300 atomically in the same DB transaction.

---

### User Story 3 - Void a Refund Receipt (Priority: P2)

**Description**:  
As a Financial Desk staff member, I want to void a refund that was issued in error (e.g., issued to the wrong student), so that the original payment's refundable balance is restored and the audit trail reflects the correction.

**Acceptance Scenarios**:
1. **Given** a parent payment of EGP 1000 with an active refund of EGP 400,  
   **When** the EGP 400 refund is voided with a reason,  
   **Then** the refund payment row is soft-deleted, and the parent payment's refundable balance dynamically recalculates to EGP 1000.
2. **Given** a competition refund of EGP 300 is voided,  
   **Then** `TeamMember.amount_paid` is restored by EGP 300 atomically (i.e., the decrement from the refund is reversed).

---

## Edge Cases (Locked Decisions)

| Scenario | System Behaviour |
|---|---|
| Voiding a payment with active refunds | **Blocked** — 409: "void the refunds first" |
| Refunding a voided payment | **Blocked** — 409: "Cannot refund a voided payment" |
| Voiding a refund row | **Allowed** — soft-delete, dynamic balance recalculation |
| Competition payment voided | `TeamMember.amount_paid` decremented atomically |
| Competition payment refunded | `TeamMember.amount_paid` decremented atomically |
| Competition refund voided | `TeamMember.amount_paid` restored atomically (add back) |
| Missing reason on void/refund | **Blocked** — 422 validation error |
| Double-refund exceeding original | **Blocked** — 409 BusinessRuleError |

---

## Requirements

### Functional Requirements

- **FR-001 (Soft Delete Voids)**: System MUST void payments using a soft-delete mechanism (`deleted_at` and `deleted_by` fields) to maintain an audit trail of clerk mistakes. Hard deletion is forbidden for posted transactions.
- **FR-002 (Void Reason)**: Users MUST provide a non-empty reason when voiding or refunding a payment. 422 if `reason` is null or blank.
- **FR-003 (Dynamic Balance Sync)**: Dynamic balance views (`v_enrollment_balance`, `v_unpaid_enrollments`) filter by `deleted_at IS NULL` on payments. The `v_daily_collections` view already handles this: voided payments are excluded; refunds appear in the `refunded_amount` column (not `collected_amount`). No view changes needed.
- **FR-004 (Double-Refund Validation)**: The system MUST calculate `SUM(amount WHERE original_payment_id=X AND transaction_type='refund' AND deleted_at IS NULL)` and reject any new refund causing total to exceed the original payment amount.
- **FR-005 (Mutual Exclusion)**:
  - Voiding a payment with any active (non-deleted) refund rows MUST be blocked — 409.
  - Refunding a voided payment MUST be blocked — 409.
- **FR-006 (Competition Unlinking)**: Voiding or refunding a competition payment MUST atomically adjust `TeamMember.amount_paid` (decrement on refund/void; restore on refund-void).
- **FR-007 (Audit)**: Every void and refund MUST write a `student_activity_log` entry with `activity_type='payment'`, `activity_subtype='void'` or `'refund'`, `reference_id=payment_id`, `performed_by=user_id`.
- **FR-008 (Separate Endpoints)**: Void and refund are exposed as distinct endpoints: `POST /finance/payments/{id}/void` and `POST /finance/payments/{id}/refund`.
- **FR-009 (Authorization)**: Both endpoints require `require_admin` guard (admin + system_admin roles).
- **FR-010 (Void Refund endpoint)**: `POST /finance/payments/{id}/void` handles both voiding a regular payment AND voiding a refund row — the same endpoint with the same logic (soft-delete + reason).

### Key Entities

- **`Payment`**:
  - `deleted_at`: datetime (soft-delete timestamp for voids).
  - `deleted_by`: int (user who voided the transaction).
  - `original_payment_id`: int (self-referencing FK to link refunds to their original payments).
  - `transaction_type`: String (enum: `payment`, `refund`, `adjustment`).
  - `notes`: String (stores the void/refund reason).
- **`Receipt`**:
  - Contains one or more payment/refund lines. Acts as the invoice container.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of payment voids and refunds must be audited with the performing user's ID and timestamp in `student_activity_log`.
- **SC-002**: The dynamic `v_enrollment_balance` view must calculate enrollment balances correctly under concurrent void/refund actions with zero balance drift (already handled by existing view logic).
- **SC-003**: 100% of attempts to refund more than the original payment's available amount must be rejected at the service layer with a 409 BusinessRuleError.
- **SC-004**: 100% of attempts to void a payment that has active refunds must be rejected with a 409 BusinessRuleError.
- **SC-005**: 100% of attempts to refund a voided payment must be rejected with a 409 BusinessRuleError.
- **SC-006**: 100% of competition payment voids/refunds must atomically update `TeamMember.amount_paid`.

---

## Assumptions

- **A-001**: No cash drawers or physical cash registers are integrated; all cash reconciliation is done via soft ledger reports.
- **A-002**: Voids and refunds can only be initiated by administrators or system administrators (`require_admin` guard).
- **A-003**: A voided payment cannot be un-voided; a new payment receipt must be generated instead.
- **A-004**: The existing `v_daily_collections` and `v_enrollment_balance` views already correctly handle `deleted_at IS NULL` filtering — no view schema changes are required for this feature.
- **A-005**: Refund rows live in the `payments` table alongside payment rows — distinguished by `transaction_type='refund'` and a non-null `original_payment_id`.
