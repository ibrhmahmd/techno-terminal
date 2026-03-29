# Sprint 5 — Balance design spike (B8)

**Type:** Engineering design note (implementation is **Sprint 6**, not this sprint)  
**Related:** [sprint_roadmap_post_qa_2026.md](./sprint_roadmap_post_qa_2026.md) · [qa_backlog_2026_03_testing_findings.md](./qa_backlog_2026_03_testing_findings.md) §4.2 (P5–P8)

---

## 0. Status (2026-03-21)

**Option A (single column)** is implemented in code: **`balance`** = **`total_paid - net_due`** in **`v_enrollment_balance`** (see **`db/migrations/007_p6_enrollment_balance.sql`**). Consumers listed in §3 were updated in the same pass. Remaining Sprint 6 work: **U2, U9, B3, P8** per roadmap.

---

## 1. Goal of this sprint

Produce a **single agreed design** so Sprint 6 can implement without thrash:

- Target **sign convention** (**P6**): negative = owes, zero = settled, positive = credit.
- How **`v_enrollment_balance`** should expose columns (rename vs add vs replace).
- **Ordered migration plan** (DB → services → UI → analytics).
- **Complete consumer list** with required code/SQL changes.

**Out of scope for Sprint 5:** shipping UI (U2/U9), service validation (B3), or credit consumption logic (**P8** build) — those belong to **Sprint 6**.

---

## 2. Current state vs product rules

### 2.1 Formula today

`db/schema.sql` view `v_enrollment_balance`:

- `net_due` = `amount_due - discount_applied`
- `total_paid` = net of payment/charge minus refunds (same as today’s business meaning)
- **`balance`** = `net_due - total_paid` → **positive = still owed**, **negative = overpaid**

So **`balance` is the negative of P6 “account balance”** (see QA backlog: *positive owed vs P6 positive credit*).

### 2.2 Product target (P5–P8, summarized)

| ID | Rule |
|----|------|
| **P5** | Per-enrollment balance + **parent total** = sum of dependents’ balances (same convention). |
| **P6** | **Negative** = debt, **zero** = settled, **positive** = credit. |
| **P7** | Collection flows: emphasize or filter to **debt** (under P6: **balance &lt; 0** once flipped). |
| **P8** | Overpayment: warn → confirm; credit applies to **future** charges (implementation in Sprint 6). |

---

## 3. Consumer inventory (must update with view semantics)

Anything that assumes **`balance > 0` means debt** must flip to **`balance < 0`** (if you adopt P6 in the `balance` column) **or** use explicit names (recommended during transition).

### 3.1 Database & bootstrap

| Location | What to do |
|----------|------------|
| `db/schema.sql` | `CREATE OR REPLACE VIEW v_enrollment_balance` — define target columns and formulas. |
| `app/db/init_db.py` | `RAW_VIEWS_SQL` duplicates the same view; **must stay identical** to `schema.sql` (or extract one source in Sprint 6). |

### 3.2 Finance repository / service

| Location | Usage |
|----------|--------|
| `finance_repository.get_enrollment_balance` | `SELECT * FROM v_enrollment_balance` — dict keys follow view. |
| `finance_repository.get_student_balances` | `vb.*` for student summary. |
| `finance_repository.list_unpaid_enrollments` | `WHERE vb.balance > 0` — today means “still owes”; under P6 becomes **`balance < 0`** (debt) or rename column. |
| `finance_service.get_student_financial_summary` | Wraps `get_student_balances`. |
| `finance_service.issue_refund` | Returns `new_balance` from view — labels in UI must match P6. |
| `finance_service.get_enrollment_balance` | Pass-through. |

### 3.3 Streamlit UI

| Location | Usage |
|----------|--------|
| `finance_overview.py` | `balance`, `net_due`; `max(balance, 0)` for default payment amount; copy “Balance: … EGP”. |
| `student_detail.py` | Displays balance per enrollment. |
| `parent_detail.py` | `active_balances = balance > 0`, sums `balance` as “owed” — **inverted vs P6**. |
| `finance_receipt.py` | Shows `new_balance` after refund. |

### 3.4 Analytics (raw SQL)

| Function / area | `v_enrollment_balance` usage |
|-------------------|------------------------------|
| `get_today_unpaid_attendees` | `vb.balance > 0`, `SUM(vb.balance)` as debt |
| `get_outstanding_by_group` | `vb.balance > 0`, `SUM(vb.balance)` |
| `get_top_debtors` | `vb.balance > 0`, `SUM(vb.balance)` |
| `get_group_roster` | `COALESCE(vb.balance, 0) AS balance` |
| `get_instructor_value_matrix` | `SUM(vb.total_paid)` only — **total_paid unchanged** |
| `get_flight_risk_students` | `vb.balance AS amount_owed`, `vb.balance > 0` |

**Sprint 6:** update every predicate and label; add regression checks or SQL fixtures if possible.

### 3.5 API / docs (future)

| Location | Note |
|----------|------|
| `docs/reviews/phase5_api_execution_roadmap_2026.md` | Already warns: balance semantics changes must ship with analytics/API updates. |

---

## 4. Design options (choose one in Sprint 5)

### Option A — Single column flip (breaking)

- Redefine **`balance`** = `total_paid - net_due` (P6).
- **Pros:** One column, matches mental model. **Cons:** every `> 0` / `< 0` test and label flips in one release; high regression risk if anything missed.

### Option B — Two columns, then deprecate (safer)

- Add **`account_balance`** = `total_paid - net_due` (P6).
- Keep **`balance_legacy`** or document **`amount_owed`** = `-account_balance` for one release, or keep old `balance` name temporarily as alias with clear comment.
- **Pros:** Gradual migration, diff-friendly. **Cons:** short-lived duplication; must remove alias in a follow-up.

### Option C — No view change; normalize in service layer

- Keep DB view as today; map to P6 in `finance_service` only.
- **Pros:** DB stable. **Cons:** analytics SQL still wrong unless duplicated helpers or views — **not recommended** as final state; at most a bridge.

**Recommendation for the spike:** pick **A or B**; document **exact column names** and **debt predicate** (`account_balance < 0` vs legacy).

---

## 5. Migration order (for Sprint 6 execution)

1. **DB:** Update `v_enrollment_balance` in `schema.sql` + migration file for existing DBs + `init_db.py` mirror.
2. **Finance repo:** Adjust `list_unpaid_enrollments` and any SQL using `balance` predicates.
3. **Services:** Refund return payload; any suggested payment = **min(amount, debt)** under P6 (debt = `-min(account_balance, 0)` or equivalent).
4. **UI:** Financial Desk, parent/student detail, receipt copy; **U9** overpayment dialog (Sprint 6).
5. **Analytics:** All functions in §3.4; re-verify Reports CSVs and Dashboard unpaid widgets.
6. **Docs:** `MEMORY_BANK`, QA backlog alignment note.

---

## 6. Open questions (resolve in Sprint 5)

- **Parent total (P5):** Confirm aggregation is **SUM(account_balance)** over active enrollments only vs all non-dropped.
- **Enrollment “closed”:** Are balances frozen when status ≠ `active`? (Affects lists and sums.)
- **Competition fees:** `parent_detail` mixes enrollment balances with competition unpaid — confirm whether credit (**P8**) can apply across competition vs course in v1.
- **Naming in Arabic/English UI:** Single glossary for “debt”, “credit”, “settled” (**P6**).

---

## 7. Sprint 5 checklist (this spike)

- [ ] Walk through **§3** with the team and mark any missed grep hits (competitions, exports).
- [ ] Decide **Option A vs B** (§4) and document **exact** view DDL sketch.
- [ ] Write **debt / credit / settled** predicates in one box (for engineers + QA).
- [ ] Review **Sprint 6** scope: B8 + B3 + U2 + U9; split tickets (view, repo, UI, analytics, overpay).
- [ ] Optional: **1-page** executive summary for non-engineers (link from `executive_features_brief` if useful).

---

## 8. Sprint 6 handoff (preview)

| ID | Work |
|----|------|
| **B8** | Implement chosen view + repo + service normalization. |
| **B3** | Financial desk eligibility + debt-only filter (**P7**). |
| **U2** | Student search + parent totals (**P5**). |
| **U9** | Overpayment warn + confirm (**P8**). |

---

*End of Sprint 5 design spike template. Update this file as decisions are made; revision date in git history is the audit trail.*
