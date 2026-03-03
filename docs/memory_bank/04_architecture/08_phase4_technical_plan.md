# Phase 4 — Technical Plan: Financial Ledger

---

## 1. Scope & Objective

Phase 4 implements the full accounting layer: receipts, payment lines, balance tracking, and refunds. All financial records are stored at the point of collection against individual student enrollments.

**Key Deliverables:**

- Point-of-sale receipt creation (one receipt can cover multiple children of the same guardian)
- Line-item payment recording per enrollment
- Live balance lookup via `v_enrollment_balance` database view
- Refund issuance tracked as negative-direction payment lines
- Daily collection summary by payment method
- Integration into Student and Parent detail pages

**Modules Touched:**

- `app/modules/finance/` (NEW — models, repository, service)
- `app/ui/components/finance_overview.py` (NEW)
- `app/ui/components/finance_receipt.py` (NEW)
- `app/ui/pages/7_Finance.py` (NEW)
- `app/ui/components/student_detail.py` (UPDATED — balance column)
- `app/ui/components/parent_detail.py` (UPDATED — financial overview block)
- `app/modules/crm/service.py` (UPDATED — `get_guardian_students`)

---

## 2. Data Design Decisions

### Receipt ≠ Payment

A `Receipt` is the transaction header (guardian, method, date, receipt number).
A `Payment` is a single line item on the receipt — one per student, per enrollment.

This means a parent paying for two children generates:

- 1 `Receipt`
- 2 `Payment` rows (one per child's enrollment)

### No `total_amount` on receipts

The receipt total is always **derived** from the `payments` table:

```
total = SUM(amount WHERE type IN ('payment','charge')) - SUM(amount WHERE type = 'refund')
```

Never stored as a column. The `v_enrollment_balance` view handles this.

### `transaction_type` semantics

| Value | Meaning |
|---|---|
| `'charge'` | New obligation added (student owes X EGP) |
| `'payment'` | Money received from guardian (settles the obligation) |
| `'refund'` | Money returned to guardian (increases outstanding balance) |

All `amount` values are stored **positive**. The `transaction_type` sets the direction.

### Receipt numbering

Format: `TK-{YYYY}-{id:05d}` (e.g. `TK-2026-00001`).
Generated immediately after the receipt row is inserted, using the auto-incremented `id`.

---

## 3. File-by-File Breakdown: `finance` Module

### `app/modules/finance/models.py`

```python
class Receipt(SQLModel, table=True):
    __tablename__ = "receipts"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    guardian_id: Optional[int] = Field(default=None, foreign_key="guardians.id")
    payment_method: Optional[str] = None  # cash | card | transfer | online
    received_by: Optional[int] = Field(default=None, foreign_key="users.id")
    receipt_number: Optional[str] = None  # set after insert: TK-YYYY-XXXXX
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class Payment(SQLModel, table=True):
    __tablename__ = "payments"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipts.id")
    student_id: int = Field(foreign_key="students.id")
    enrollment_id: Optional[int] = Field(default=None, foreign_key="enrollments.id")
    amount: float                                     # always positive
    transaction_type: str                             # charge | payment | refund
    payment_type: Optional[str] = None                # course_level | competition | other
    discount_amount: float = 0.0
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
```

### `app/modules/finance/repository.py`

| Function | Description |
|---|---|
| `create_receipt(db, guardian_id, method, received_by, paid_at, notes)` | Inserts receipt header row |
| `set_receipt_number(db, receipt_id)` | Updates `receipt_number` to `TK-YYYY-{id:05d}` |
| `get_receipt(db, receipt_id)` | Returns `Receipt | None` |
| `get_receipt_with_lines(db, receipt_id)` | Returns `{receipt, lines: [Payment]}` |
| `get_receipt_total(db, receipt_id)` | SQL sum of payments minus refunds |
| `add_payment_line(db, receipt_id, student_id, enrollment_id, amount, transaction_type, ...)` | Inserts one `Payment` row |
| `get_enrollment_balance(db, enrollment_id)` | Queries `v_enrollment_balance` view |
| `get_student_balances(db, student_id)` | All enrollments with balance for a student |
| `list_receipts_by_date(db, date)` | All receipts issued on a given date with totals |
| `list_unpaid_enrollments(db, group_id)` | Students with `balance > 0` in a group |
| `get_daily_collections(db, date)` | Sum of payments per method for the day |

### `app/modules/finance/service.py`

| Function | Description |
|---|---|
| `open_receipt(guardian_id, method, received_by_user_id, notes)` | Creates receipt + generates receipt number |
| `add_charge_line(receipt_id, student_id, enrollment_id, amount, ...)` | Validates enrollment active, inserts payment line |
| `finalize_receipt(receipt_id)` | Validates ≥1 line, returns summary dict |
| `issue_refund(enrollment_id, amount, reason, received_by_user_id)` | Opens new receipt, adds refund line, returns updated balance |
| `get_student_financial_summary(student_id)` | All enrollment balances for a student |
| `get_daily_collections(target_date)` | Payments per method for the day |
| `get_daily_receipts(target_date)` | All receipts issued on a date |
| `get_receipt_detail(receipt_id)` | Receipt + lines + total |
| `get_enrollment_balance(enrollment_id)` | Single enrollment balance dict |

---

## 4. UI Layer

### `app/ui/pages/7_Finance.py`

Lightweight router:

- If `st.session_state["selected_receipt_id"]` is set → renders `finance_receipt.py`
- Otherwise → renders `finance_overview.py`

### `app/ui/components/finance_overview.py`

Three tabs:

**💵 New Receipt tab flow:**

1. Search for guardian (name or phone)
2. Select payment method (cash / card / transfer / online)
3. For each active child of that guardian, expand their active enrollments
4. Check which enrollments to pay → enter amount per enrollment (pre-filled with outstanding balance)
5. Review receipt summary (student, enrollment, amount)
6. Click **Finalize Receipt** → creates receipt + payment lines atomically

**📊 Balances tab:**

- Search student by name
- See per-enrollment table: Net Due | Paid | Outstanding Balance

**📅 Daily Summary tab:**

- Pick a date (defaults to today)
- Left column: per-method metrics (collected - refunded)
- Right column: clickable receipt table → selecting a row navigates to Receipt Detail

### `app/ui/components/finance_receipt.py`

Read-only receipt detail view:

- Shows receipt header (number, guardian, method, date)
- Shows all payment lines (student, enrollment, type, amount)
- Shows total collected
- Refund expander: select an enrollment line → enter amount + reason → issues a refund receipt

---

## 5. Cross-Module Integration

### Student Detail page (`student_detail.py`)

- **Balance column** added to the Enrollments & Academic History table (pulls from `v_enrollment_balance`)
- **💰 Go to Finance** button shown when the student has any active enrollment

### Parent Detail page (`parent_detail.py`)

- **💳 Financial Overview** section added below Registered Children table
- Per-child status: 🔴 Owes X EGP (with per-enrollment breakdown) or 🟢 No outstanding balance
- **💰 Create Receipt for this Parent** button shown when any child has a balance

---

## 6. Key Service Chain: Receipt Creation

```text
UI: finance_overview.py
  └──► finance.service.open_receipt(guardian_id, method, received_by)
         │
         ├──► finance.repository.create_receipt()    [inserts row]
         │
         └──► finance.repository.set_receipt_number()  [TK-YYYY-XXXXX]
  
  └──► finance.service.add_charge_line(receipt_id, student_id, enrollment_id, amount)
         │
         ├──► enrollments.models.Enrollment  [validates status == 'active']
         │
         └──► finance.repository.add_payment_line()  [inserts Payment row]
  
  └──► finance.service.finalize_receipt(receipt_id)
         │
         ├──► validates ≥1 payment line
         │
         └──► returns {receipt_number, total, method, paid_at, lines}
```

---

## 7. Phase 4 Completion Checklist

- [x] `app/modules/finance/__init__.py`
- [x] `app/modules/finance/models.py` — `Receipt`, `Payment`
- [x] `app/modules/finance/repository.py` — 11 functions
- [x] `app/modules/finance/service.py` — 9 service functions
- [x] `app/ui/pages/7_Finance.py` — router
- [x] `app/ui/components/finance_overview.py` — 3-tab UI
- [x] `app/ui/components/finance_receipt.py` — receipt detail + refund
- [x] `app/modules/crm/service.py` — `get_guardian_students` added
- [x] `app/ui/components/student_detail.py` — balance column + Pay Now button
- [x] `app/ui/components/parent_detail.py` — financial overview + Create Receipt button
- [x] Daily Summary receipt table wired to receipt detail navigation
