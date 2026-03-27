# Sprint 6b — Financial Desk completion (U2, U9, B3, P8 phase A)

**Status:** Implementation plan (ready to execute)  
**Depends on:** P6 **`v_enrollment_balance.balance`** shipped (**`007_p6_enrollment_balance.sql`**, `finance_overview` debt defaults).  
**Related:** [sprint_roadmap_post_qa_2026.md](./sprint_roadmap_post_qa_2026.md) · [qa_backlog_2026_03_testing_findings.md](./qa_backlog_2026_03_testing_findings.md) (U2, U9, B3, P8)

---

## 1. Sprint goal

Finish **product-backed** Financial Desk behaviour that was left after the **B8 / P6** view flip:

| ID | Outcome |
|----|---------|
| **U2** | Operators can reach a family via **student** search, see **per-enrollment** lines and **guardian-level total** (P5), optionally narrow to **debt-only** families (P7). |
| **B3** | Desk logic consistently uses **P6** predicates (**debt ⇒ `balance < 0`**) for eligibility and filtering. |
| **U9** | If a line would create **credit** (pay more than debt on an enrollment), show **warning** + **Confirm** / **Cancel** before calling `create_receipt_with_charge_lines` (P8 intent). |
| **P8 (phase A)** | Credit is **visible** (positive balance) and **allowed** after confirm; **no** cross-enrollment auto-apply in this sprint (phase B = later design). |

**Out of scope for 6b:** PDF receipts (U6/B6), competition fee model (B7/U7), course stats (Sprint 7), automatic **consumption** of credit against a *different* enrollment (P8 phase B).

---

## 2. Work breakdown (recommended order)

### Epic A — Discovery & family context (U2 / B3 / P5 / P7)

| # | Task | Details | Primary files |
|---|------|---------|----------------|
| A1 | **Student entry path** | At top of `render_finance_overview`, add student name search (`crm_service.search_students`, min 2 chars). On select: load **primary guardian** (or list if multiple — use primary first); set `session_state` `fd_focus_guardian_id` + optional `fd_focus_student_id` to expand/highlight that child. Reuse existing parent selectbox or auto-fill flow. | `app/ui/components/finance_overview.py`, `crm_service` |
| A2 | **Guardian total (P5)** | After parent resolved, compute `total_account_balance = sum(b["balance"] for child in children for b in get_student_financial_summary(child.id))` over **active** enrollments only (filter enrollments in UI or add `finance_service.guardian_balance_rollup(guardian_id)` that SQLs or loops consistently). Display one line: **“Household account balance (sum of enrollments): X EGP”** with P6 caption. | `finance_overview.py`, optionally `finance_service.py` |
| A3 | **“Owed money only” toggle (P7)** | `st.toggle` default **off** (show all linked students). When **on**, hide students (or collapse expanders) where **every** active enrollment has `balance >= 0`. If **on** and selected guardian has no debt at all, show info + suggest turning toggle off. | `finance_overview.py` |
| A4 | **Parent search respects toggle** | When toggle on, optional: filter `search_guardians` results — expensive if N guardians. **Pragmatic v1:** filter **after** parent selection (if no debt, message); **v1.5:** add `finance_repository.guardian_ids_with_any_enrollment_debt()` and intersect with search results if product requires. | `finance_repository.py` (optional), `finance_overview.py` |

**Acceptance (Epic A):** User can open Financial Desk from **student** search, see household sum, and use **debt-only** UI without contradicting P6/P7.

---

### Epic B — Overpayment gate (U9)

| # | Task | Details | Primary files |
|---|------|---------|----------------|
| B1 | **Pure helper** | `def enrollment_debt_egp(balance: float) -> float: return max(-balance, 0.0)` and `def line_creates_credit(current_balance: float, pay_amount: float) -> bool` where credit means **new balance > 0** after payment: `current_balance + pay_amount > 0` (P6). Edge: already have credit (`balance > 0`) and pay more → always “extra credit” warning. | `app/modules/finance/` small module or `finance_service` private helpers |
| B2 | **Pre-flight scan** | Given `lines: list[ReceiptLineInput]` and DB session, load each enrollment’s current `get_enrollment_balance`; build list of **(enrollment_id, excess_egp, new_balance)** for lines that would create or increase credit beyond settled. | `finance_service.py` |
| B3 | **Streamlit two-step** | On “Confirm Payment”, if scan non-empty: **do not** call create yet — show `st.warning` with table (enrollment, amount entered, debt, excess credit) and buttons **Confirm overpayment** / **Adjust amounts**. Use `st.session_state["fd_overpay_confirm"]` or `st.dialog` (Streamlit ≥1.33) to avoid duplicate submits. | `finance_overview.py` |
| B4 | **Service API** | Either add `allow_credit: bool = False` to `create_receipt_with_charge_lines` and validate server-side, or keep validation only in UI for Streamlit-only path — **prefer** service check when `allow_credit` is False to protect future API. | `finance_service.py` |

**Acceptance (Epic B):** Paying **more than debt** on an enrollment requires an explicit second confirm; cancel returns to editor without receipt.

---

### Epic C — P8 phase A (visibility, no auto-allocate)

| # | Task | Details | Primary files |
|---|------|---------|----------------|
| C1 | **Credit line in expander** | When `balance > 0` for an enrollment, show **“Credit: X EGP”** (green) instead of only debt wording. | `finance_overview.py` |
| C2 | **Docs** | One paragraph in `MEMORY_BANK` §5.6: P8 phase A = manual credit on same enrollment; phase B TBD. | `docs/MEMORY_BANK.md` |

---

## 3. Testing checklist (QA)

- [ ] Student with two guardians — primary used; secondary documented if ambiguous.
- [ ] Guardian with three children — sum matches manual sum of per-enrollment `balance` (P6).
- [ ] Toggle “owed only” — student with all enrollments settled/credit hidden when appropriate.
- [ ] Pay **exact** debt — no overpay dialog.
- [ ] Pay **1 EGP over** debt — dialog; confirm creates receipt; balance +1 vs net_due.
- [ ] Pay on enrollment **already in credit** — dialog (or block — product choice; recommend warn + confirm).

---

## 4. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Double submit on Streamlit | Disable primary button while pending; clear `fd_lines` only after success (existing). |
| API later bypasses U9 | `allow_credit` + default False in `create_receipt_with_charge_lines`. |
| Guardian total includes dropped enrollments | Restrict rollup to `enrollment.status == 'active'` only. |

---

## 5. Estimates (rough)

| Epic | Dev days (1 engineer) |
|------|-------------------------|
| A | 1.5–2 |
| B | 1–1.5 |
| C | 0.25 |
| **Total** | **~3–4 days** |

---

## 6. After 6b

- **Sprint 7** (roadmap): course aggregates **B5 / D3 / U5**.  
- **P8 phase B:** design note for applying credit across enrollments / levels (may need product sign-off).

---

*Revision: initial plan 2026-03-21.*
