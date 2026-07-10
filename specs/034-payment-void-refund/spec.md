# Feature Specification: Payment Void and Refund Workflows

**Feature Branch**: `034-payment-void-refund`  
**Created**: 2026-06-21  
**Status**: Draft  
**Input**: User request: "Discuss how to achieve a refund feature accurately without balance issues/bugs, compare options, and handle false payments (undoing wrong student payments via voids vs. refunds) and edge cases."

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
4. An audit log entry is added to Student A's activity log.

**Acceptance Scenarios**:
1. **Given** a student has an enrollment with EGP 1000 due and EGP 1000 paid (balance EGP 0),  
   **When** the EGP 1000 payment is voided,  
   **Then** the enrollment balance changes back to EGP 1000 unpaid, and the payment is marked as deleted.
2. **Given** a payment is being voided,  
   **When** no reason is provided,  
   **Then** the system rejects the request with a validation error.

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
   **When** a refund of EGP 600 is processed,  
   **Then** a new receipt of type "refund" is created, and the remaining refundable amount for the original payment is EGP 400.
2. **Given** a payment has already been refunded EGP 600,  
   **When** a user attempts to refund another EGP 500,  
   **Then** the request is rejected with a business rule violation indicating the refund exceeds the available limit of EGP 400.

---

### Edge Cases

- **Voiding a Refunded Payment**: If a payment has active refunds linked to it, voiding the original payment must be **blocked**. Otherwise, the refund records would refer to a non-existent payment, causing positive balance anomalies.
- **Refunding a Voided Payment**: If a payment is soft-deleted/voided, it cannot be refunded. The system must raise a `NotFoundError` or `BusinessRuleError`.
- **Voiding a Refund Receipt**: If a refund receipt itself was created in error, voiding the refund line must restore the original payment's refundable balance.
- **Competition Fee Refunds**: When refunding a competition fee payment (linked to `team_member_id`), the system must decrement the corresponding `TeamMember.amount_paid` field by the refunded amount.

---

## Requirements

### Functional Requirements

- **FR-001 (Soft Delete Voids)**: System MUST void payments using a soft-delete mechanism (`deleted_at` and `deleted_by` fields) to maintain an audit trail of clerk mistakes. Hard deletion is forbidden for posted transactions.
- **FR-002 (Void Reason)**: Users MUST provide a reason (stored in payment/receipt notes) when voiding a payment or receipt.
- **FR-003 (Dynamic Balance Sync)**: Dynamic balance views (`v_enrollment_balance`, `v_unpaid_enrollments`, and `v_daily_collections`) MUST filter out soft-deleted/voided payments (`WHERE deleted_at IS NULL`).
- **FR-004 (Double-Refund Validation)**: The system MUST calculate cumulative refunds against an original payment ID and reject any new refund that causes total refunds to exceed the original payment amount.
- **FR-005 (Mutual Exclusion)**: 
  - System MUST prevent voiding a payment that has any active (non-deleted) refund transactions.
  - System MUST prevent refunding a payment that is voided.
- **FR-006 (Competition Unlinking)**: Refunding a competition payment MUST decrement `TeamMember.amount_paid` atomically.

### Key Entities

- **`Payment`**:
  - `deleted_at`: datetime (soft-delete timestamp for voids).
  - `deleted_by`: int (user who voided the transaction).
  - `original_payment_id`: int (self-referencing FK to link refunds to their original payments).
  - `transaction_type`: String (enum: `payment`, `refund`, `adjustment`).
- **`Receipt`**:
  - Contains one or more payment/refund lines. Acts as the invoice container.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of payment voids and refunds must be audited with the performing user's ID and timestamp.
- **SC-002**: The dynamic `v_enrollment_balance` view must calculate enrollment balances correctly under concurrent void/refund actions with zero balance drift.
- **SC-003**: 100% of attempts to refund more than the original payment's available amount must be rejected at the API layer with a 400 BusinessRuleError.
- **SC-004**: 100% of attempts to void a payment that has active refunds must be rejected with a 400 BusinessRuleError.

---

## Assumptions

- **A-001**: No cash drawers or physical cash registers are integrated; all cash reconciliation is done via soft ledger reports.
- **A-002**: Voids can only be initiated by administrators or system administrators (`require_admin` guard).
- **A-003**: A voided payment cannot be un-voided; a new payment receipt must be generated instead.
