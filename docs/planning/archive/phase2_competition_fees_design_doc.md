# Phase 2: Competition Fees Architecture & Design

**Status:** Deferred to later sprint  
**Depends on:** Sprint 1..7 completion (Done)

## Overview
Currently, teams are registered manually without a financial link to the CRM's billing/receipt system. The goal of this phase is to charge fees per member based on the competition category, and persist that fee snapshot per user so they can pay it via the Financial Desk.

## Schema Changes Needed (Migration 008/009)

When this is picked up, the following database schema changes must be applied:

### 1. Fee Definition Source
If fees change per year (e.g. FLL 2025 is 500 EGP, FLL 2026 is 800 EGP), we cannot just add a `fee_per_student` column to the `competition_categories` lookup table, as updating it would break historical data unless we also snapshot it at the team/member level.

**Options for the canonical source of truth for the fee:**
- **Option A (Simpler):** Add `fee_per_student` to the `competitions` table itself. Since each row in `competitions` represents a specific event instance (e.g., "FLL 2026 Egypt"), the fee is locked to that time.
- **Option B (More flexible):** Create a new `competition_category_fees` table linked to an `edition` year.

**Recommendation:** Option A. It's much simpler to manage and maps directly to the real-world concept of "This specific event costs X to enter."

```sql
ALTER TABLE competitions ADD COLUMN fee_per_student NUMERIC(10,2) NOT NULL DEFAULT 0.0;
```

### 2. Snapshotting the Member Share
When a team of 4 registers, we need to know exactly what each student owes at the time of registration. If the team size changes later, or the competition fee changes, already-issued receipts must remain mathematically valid.

**Decision:** Add `member_share` to `team_members`.

```sql
ALTER TABLE team_members ADD COLUMN member_share NUMERIC(10,2);
```

## Backend Service Changes

### 1. Registration (`competition_service.register_team`)
When a team is created:
1. Fetch the `fee_per_student` from the `competitions` row.
2. (Optional, if team-based pricing ever applies) Calculate `member_share = total_fee / len(students)`. Currently it's a fixed per-student fee, so `member_share = fee_per_student`.
3. Save the `member_share` onto each `team_members` row as it is inserted.

### 2. Financial Desk (`finance_service` & `finance_overview.py`)
Modify the Financial Desk to read unpaid `team_members` rows for the selected parent's students:
1. Find all `team_members` where `fee_paid = false` for the matched students.
2. Display them in the checkout UI as checkable charge lines (just like enrollments).
3. When paid, the `create_receipt_with_charge_lines` function records a payment where `payment_type='competition'`.
4. The transaction atomic block must mark `team_members.fee_paid = true` and link `team_members.payment_id` to the new payment line ID.

## Acceptance Criteria
- [ ] Schema updated and `member_share` exists on `team_members`.
- [ ] Teams can be successfully created with the fee snapshotted for each member.
- [ ] Financial Desk UI displays pending competition fees alongside regular course debt.
- [ ] Issuing a receipt marks the fee as paid. Refunds un-mark the fee.
