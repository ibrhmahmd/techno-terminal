# Sprint roadmap — post–QA backlog (2026)

**Document type:** Engineering & product planning handoff  
**Audience:** Engineering, QA, product owner  
**Related:** [qa_backlog_2026_03_testing_findings.md](./qa_backlog_2026_03_testing_findings.md) (issues, story points, **P1–P9** product decisions)  
**Assumption:** One sprint ≈ **two weeks**; adjust scope if your cadence differs.

---

## 1. Purpose

This roadmap turns the QA backlog into **ordered sprints** with clear goals, backlog references, and acceptance themes. It is meant for **sprint planning**, not as a substitute for task-level tickets (those should be broken out in your tracker).

---

## 2. Guiding principles

| Principle | Implication |
|-----------|-------------|
| **Unblock finance first** | Receipt numbering (**B2/U3**) is treated as a **release blocker**; defer PDF (**U6/B6**) until receipts are trustworthy. |
| **Schema before strict UI** | Staff uniqueness and mandatory fields (**D1, D2, D6**) should land before or with app validation (**B1, U1, U4**). |
| **Design before balance epic** | Product balance rules (**P5–P8**) conflict with today’s `v_enrollment_balance` semantics; a **short design note** precedes the large **B8** implementation. |
| **DB and ORM alignment** | Attendance already has an ORM **unique constraint**; ensure **database** unique index exists where you rely on DB-enforced idempotency. |

---

## 3. Prerequisites (before Sprint 1)

| Item | Owner | Notes |
|------|--------|--------|
| Apply `db/migrations/003_employees_employment_full_time.sql` on non-greenfield DBs | DBA / dev | If not already applied. |
| Confirm `run_ui` / `apply_analytics_views()` runs against target environments | DevOps / dev | Ensures `v_enrollment_balance` and related views exist. |
| Link QA backlog IDs to tracker epics | PM / tech lead | **U** = UI, **B** = backend, **D** = database. |

---

## 4. Sprint sequence (detailed)

### Sprint 1 — Finance: receipt number integrity (**release blocker**)

**Theme:** Every finalized receipt must have a persisted, readable **receipt number** end-to-end.

**Implementation note (2026-03):** Financial Desk and competition fee payment now call **`finance_service.create_receipt_with_charge_lines`**, which runs **receipt header + `set_receipt_number` + all payment lines in one DB transaction** (avoids multi-session edge cases). `set_receipt_number` **flushes** immediately so the number is written before lines are added.

| Backlog | Work summary |
|---------|----------------|
| **B2** | Trace full path: `open_receipt` → `set_receipt_number` → commit → `get_receipt_detail` / Streamlit. Verify `receipts.receipt_number` in DB for new rows. Rule out schema drift (Supabase vs local), ORM mapping, and stale object usage. |
| **U3** | UI must not show `N/A` for committed receipts once **B2** is fixed; optional interim copy only if draft receipts are introduced later. |

**Suggested acceptance criteria**

- After “Confirm Payment” (Financial Desk flow), the new row in `receipts` has **non-null** `receipt_number`.
- Receipt detail view displays the same value returned by the service layer.
- Short **test checklist** or automated test for one happy-path receipt creation.

**Risks:** Environment-specific DB (missing column, old migration); double-commit/session edge cases.

**Out of scope this sprint:** PDF export (**U6/B6**), Dashboard receipt browser (**U8/B9**).

---

### Sprint 2 — HR: employee identity, constraints, and forms

**Theme:** Align **P1–P3** (national ID required; unique phone/email; mandatory education + employment fields) across **DB, services, and UI**.

**Implementation note (2026-03):** **`db/schema.sql`** and **`db/migrations/004_employees_sprint2_identity.sql`** add **`national_id`**, **`university`**, **`major`**, **`is_graduate`**, NOT NULL **`employment_type`** and **`phone`**, UNIQUE constraints, and D5 **`contract_percentage`** CHECK. **`hr_models.EmployeeCreate`**, **`hr_repository`** duplicate lookups, **`hr_service`** `ConflictError` + merge-on-update (preserves **`monthly_salary`** when omitted). **`employee_form`** / **`employee_directory`** updated for **U1/U4**.

| Backlog | Work summary |
|---------|----------------|
| **D6** | Add `national_id` (unique, NOT NULL after backfill strategy). |
| **D2** | Add `university`, `major`, `is_graduate`; tighten `employment_type` NOT NULL after backfill; keep CHECK aligned with `full_time` / `part_time` / `contract`. |
| **D1** | Partial **UNIQUE** indexes on `employees.phone`, `employees.email` where not null (PostgreSQL). |
| **D5** | DB or app rule: `contract_percentage` only meaningful for `employment_type = 'contract'` (CHECK or enforced in service — see backlog). |
| **B1** | Service + API behavior: clear errors on duplicate phone/email/national_id (e.g. 409 / `ConflictError`). |
| **B4** | Extend create/update validation for all **P3** fields; keep existing contract-% normalization in `hr_service`. |
| **U1** | Disable double submit; surface duplicate / validation errors clearly. |
| **U4** | Forms for **national_id**, **university**, **major**, **is_graduate**; employment type + conditional contract %. |

**Suggested acceptance criteria**

- Cannot create two employees with the same national ID or same non-null phone/email (per product rules).
- Create/edit employee requires **P3** fields; contract % hidden unless type is contract.
- Migration path documented for existing rows (defaults, manual cleanup, or one-off script).

**Dependency:** Sprint 1 not required for HR work; can run **parallel** if capacity allows (separate branch/release).

---

### Sprint 3 — Platform: audit fields (**D4**)

**Theme:** `created_at`, `updated_at`, `created_by` (and analogous fields) populated consistently — comparable to attendance **`marked_by`**.

**Implementation note (2026-03):** **`app/shared/audit_utils.py`** (`apply_create_audit` / `apply_update_audit`) stamps CRM creates/updates, **`student_guardians`** links, and enrollment creates/status/discount changes. **`db/migrations/005_audit_d4_timestamps.sql`** backfills NULLs, sets **`DEFAULT CURRENT_TIMESTAMP`**, and adds **`tf_set_updated_at`** triggers (also in greenfield **`db/schema.sql`**). Streamlit passes **`state.get_current_user_id()`** into enroll/transfer, student registration, and Financial Desk receipts (fixes reliance on a non-existent `session_state["user_id"]`).

| Backlog | Work summary |
|---------|----------------|
| **D4** | Inventory tables with NULL audit columns; choose **DB defaults**, triggers, and/or **service-layer** writes; align Streamlit and FastAPI call paths. |

**Suggested acceptance criteria**

- Agreed list of tables/columns covered in this sprint.
- New writes in scope show non-null timestamps where required; actor set where product expects it.

---

### Sprint 4 — Finance: receipt discovery on Dashboard

**Theme:** Operators can find receipts without only relying on post-payment redirect.

| Backlog | Work summary |
|---------|----------------|
| **B9** | Service/repository: list receipts by date, optional filters (guardian, student, receipt #). |
| **U8** | Dashboard entry: today’s receipts, search, open detail view (reuse existing receipt component where possible). |

**Suggested acceptance criteria**

- From Dashboard, user can open a recent receipt and see correct **receipt #** (depends on Sprint 1).
- Performance acceptable for expected daily volume (no full-table scan without index if needed).

**Dependency:** **Sprint 1** strongly recommended first.

---

### Sprint 5 — Spike + Sprint 6 — Finance: balance model & Financial Desk (**epic**)

**Theme:** Implement product semantics **P5–P8** (debt negative, credit positive, guardian total, “owed only” list, overpayment warn → confirm).

| Phase | Backlog | Work summary |
|-------|---------|----------------|
| **Sprint 5 (spike, ~3–5 days)** | **B8** (design) | Document target: replace or extend `v_enrollment_balance` (e.g. `account_balance = total_paid - net_due` vs rename `balance`); migration order; list every consumer (finance UI, analytics SQL, services). |
| **Sprint 6 (build)** | **B8**, **B3**, **U2**, **U9** | Implement view/service changes; student search; guardian aggregate; filter “in debt only”; overpayment warning + confirm; apply credit to future payments per **P8**. |

**Suggested acceptance criteria**

- Single documented **sign convention** in code and user-facing labels (**P6**).
- Financial Desk can search by **student**; optional toggle to hide families with no debt (**P7**).
- Paying more than amount due shows **warning** then **confirm**; positive balance behaves as **credit** per **P8**.

**Risks:** Analytics queries (**e.g.** `get_flight_risk_students`) assume current `balance` meaning — must be updated in the same release or flagged.

**Dependency:** Spike (**Sprint 5**) gate before full build (**Sprint 6**).

---

### Sprint 7 — Reporting: course aggregates (**Could**)

| Backlog | Work summary |
|---------|----------------|
| **B5**, **D3**, **U5** | `get_course_stats` (or view): groups count, students count (define active vs historical); course management table columns. |

---

### Phase 2 (prioritize when revenue/ops need it)

| Area | Backlog | Notes |
|------|---------|--------|
| PDF receipts | **U6**, **B6** | After receipt # and listing are stable. |
| Competition fees | **U7**, **B7** | Edition × category fees; equal team split; **P9**. |

---

## 5. Summary table (sprint → main backlog IDs)

| Sprint | Focus | Primary IDs |
|--------|--------|-------------|
| 1 | Receipt # blocker | B2, U3 |
| 2 | Staff identity & HR | D6, D2, D1, D5, B1, B4, U1, U4 |
| 3 | Audit columns | D4 |
| 4 | Dashboard receipts | B9, U8 |
| 5 | Balance design spike | B8 (analysis + doc) |
| 6 | Balance + Financial Desk | B8, B3, U2, U9 |
| 7 | Course stats | B5, D3, U5 |
| Phase 2 | PDF, competitions | U6, B6, U7, B7 |

---

## 6. Definition of Done (sprint-wide)

- Code reviewed; migrations tested on a **copy** of production-like data where applicable.
- User-facing copy matches **P6** once balance work ships.
- **MEMORY_BANK** or module README updated when schema or views change.
- QA verifies against acceptance criteria; regressions on payment and staff flows checked.

---

## 7. Revision history

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03 | Product/engineering | Initial roadmap from QA backlog MoSCoW and dependencies |
| 1.1 | 2026-03-21 | Engineering | Sprint 1: atomic `create_receipt_with_charge_lines` + repo flush in `set_receipt_number` (B2/U3). |
| 1.2 | 2026-03-21 | Engineering | Sprint 2: employees schema + migration 004, HR service/repo/UI (D1/D2/D5/D6/B1/B4/U1/U4). |
| 1.3 | 2026-03-21 | Engineering | Sprint 3 (D4): `audit_utils`, migration 005 + schema defaults/triggers, CRM/enrollment/UI actor threading. |

---

*End of document.*
