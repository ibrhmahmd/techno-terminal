# QA Backlog — Testing Findings (March 2026)

**Document type:** Product / engineering backlog  
**Audience:** Product owner, developers, QA  
**Status:** Discussion & prioritization (no implementation committed by this document)  
**Source:** Manual testing notes + alignment with `docs/memory_bank/01_business_domain/02_business_requirements.md` and `docs/MEMORY_BANK.md`  
**Product decisions:** Stakeholder answers recorded March 2026 — see **Product decisions (locked answers)**.

---

## Executive summary

Testing surfaced gaps in **staff data quality** (duplicates, missing employment classification), **finance UX and balance semantics** (receipt display, search, overpayment), **auditability** (nullable timestamps and actor columns), and **reporting** (course and competition modeling). Items below are grouped **UI → Backend → Database / data model**, each with **story points** (Fibonacci: 1 = trivial, 2 = small, 3 = medium, 5 = large, 8 = epic).

---

## Product decisions (locked answers)

| # | Topic | Decision |
|---|--------|----------|
| P1 | **Staff — national ID** | **Required** for every employee. |
| P2 | **Staff — uniqueness** | **Phone** and **email** must be **unique among employees** (DB + application validation). |
| P3 | **Staff — mandatory fields** | **full_name**, **phone**, **national_id**, **university**, **major**, **is_graduate**, **employment_type**. *(Email was not listed as mandatory; enforce **uniqueness** when provided. Flows that create a login may still require a username/email per `users` rules.)* |
| P4 | **Receipt # `N/A`** | Occurs on **every** newly created receipt in testing. **Dashboard** currently has **no** way to open/browse receipts (only after payment redirect). |
| P5 | **Balances — levels** | **Per-student** balance (enrollment-level as today) plus **guardian total** = **sum of balances** of all related students (same sign convention). |
| P6 | **Balance sign convention** | **Negative** = **owes** money. **Zero** = **settled** (nothing owed, no credit). **Positive** = **credit** (overpayment / prepayment for future use). |
| P7 | **“Settled” / collection list** | **Do not** surface in “collect money” contexts when **balance ≥ 0**. **Do** surface when **balance < 0** (debt). |
| P8 | **Overpayment** | **Warn** first; on **confirm**, record payment; balance becomes **positive** (credit). Credit **applies to future** payments. |
| P9 | **Competitions — fees** | Fees vary by **competition**, **category**, and **edition**; **each edition** has its own fees. **Team** cost split **equally** per member (persist each member’s share at registration). |

### Engineering note — balance vs current database

`v_enrollment_balance` defines `balance` as **`net_due - total_paid`** (`db/schema.sql`): **positive** = amount **still owed**, **negative** = **overpaid**. That is the **inverse** of **P6**. Align the view (or expose a clearly named column such as `account_balance = total_paid - net_due`), then update **all** services, Streamlit labels, and tests. Relabeling alone without formula changes will confuse finance.

---

## 1. UI issues

| # | Issue | Current behavior / context | Expected / target | Depends on | SP |
|---|--------|------------------------------|-------------------|------------|-----|
| U1 | **Duplicate staff creation** | Multiple clicks on “Adding Employee Data” can create the same person repeatedly; no inline uniqueness feedback. | Disable submit while in flight; errors for duplicate **phone**, **email**, or **national_id**; enforce **P3** required fields. | B1, D1, D6 | 3 |
| U2 | **Financial desk search & filtering** | Search is guardian-only; no student search; settled families still discoverable. | Search by **student**; default or toggle **“owed money only”** using **P6/P7** (show guardians with any enrollment still **in debt**); show **per-student** and **guardian total** (**P5**). | B3, B8 | 5 |
| U3 | **Receipt header shows `Receipt #: N/A`** | Confirmed **P4** on every new receipt; UI shows `r.receipt_number or 'N/A'` (`finance_receipt.py`). | Fix persistence/refresh (**B2**); never show N/A for committed receipts. | B2 | 2 |
| U4 | **Staff profile attributes** | Form lacks **national_id**, **university**, **major**, **is_graduate**, **employment_type** (mandatory per **P3**). | Full create/edit per **P3**; **contract %** only when `employment_type = contract`. | B4, D2, D6 | 5 |
| U5 | **Course management table** | User cannot see **how many groups** and **how many students** (current / historical) per course in one place. | Table or drill-down: counts per course (definitions: active only vs all time). | B5, D3 | 5 |
| U6 | **PDF receipt** | No downloadable PDF; success message only. | Printable / downloadable **PDF receipt** (branding, receipt #, lines, totals, method, date). | B2, B6 | 5 |
| U7 | **Competitions — fees UX** | Fees vary by competition, category, edition (**P9**). | UI reflects **edition-scoped** fees; team registration shows **equal per-member** share. | B7 | 5 |
| U8 | **Dashboard — receipts** | No way to open receipt history from Dashboard (**P4**). | Link or section: today’s receipts / search by receipt #, parent, or student. | B2, B9 | 3 |
| U9 | **Overpayment warning** | No confirm step when a payment would create **credit** under **P6**. | **P8:** warn + **Confirm** / **Cancel**; copy and number inputs aligned with **P6** (debt negative, credit positive). | B8 | 3 |

**Code references (for devs):** `app/ui/components/employee/employee_form.py`, `app/ui/components/finance_overview.py`, `app/ui/components/finance_receipt.py`, `app/ui/pages/0_Dashboard.py`.

---

## 2. Backend issues

| # | Issue | Current behavior / context | Expected / target | SP |
|---|--------|------------------------------|-------------------|-----|
| B1 | **Uniqueness for employees** | Duplicates allowed in practice. | **UNIQUE** on **phone**, **email** (where not null per DB design), **national_id**; app validation + API 409; Streamlit errors. | 5 |
| B2 | **Receipt number persistence** | **P4:** `N/A` on every new receipt despite `set_receipt_number` in code — treat as **release-blocker**: trace `Receipt` load path, commits, column mapping, and Supabase vs local schema drift. | **Acceptance:** After finalize, DB row and `get_receipt_detail` always have non-null `receipt_number`. | 5 |
| B3 | **Financial desk eligibility** | Uses `v_enrollment_balance`; sign convention **inverted** vs **P6** until migrated. | Implement **P5–P7**: student search; guardian aggregate; filter **debt only** (after balance convention fix). | 5 |
| B4 | **Employment type & contract %** | `employment_type` optional in model; DB allows `full_time` / `part_time` / `contract` (see migration `003`). | Enforce **P3**; **national_id**, **university**, **major**, **is_graduate** on create/update; contract % only for contract (service normalizes). | 5 |
| B5 | **Course aggregates** | Counts require queries across `course_offerings`, `groups`, `enrollments` (or equivalent). | Repository + service: `get_course_stats(course_id)` → groups count, students count (specify time scope). | 3 |
| B6 | **PDF generation** | Not present. | Choose library (e.g. WeasyPrint, fpdf2, or server-side template → PDF); endpoint or Streamlit download; same data as receipt detail. | 5 |
| B7 | **Competition fees (domain)** | Fees vary by competition, category, edition (**P9**); equal split per team member. | Schema: fee rows scoped to **edition + category** (and competition as needed); persist **member_share** on `team_members` at registration. | 8 |
| B8 | **Balance convention & credit application** | View/UI match old view: `balance = net_due − paid` (positive = still owed). | Align to **P6** (debt negative, credit positive); default suggested payment = **−balance** when balance is debt; persist and **consume credit** (positive balance) on later payments per **P8**. | 8 |
| B9 | **Receipt listing for Dashboard** | No service/UI slice for “receipts today / by guardian / by student”. | Queries + thin API or direct service calls for Streamlit (**U8**). | 3 |

---

## 3. Database / data integrity issues

| # | Issue | Current behavior / context | Expected / target | SP |
|---|--------|------------------------------|-------------------|-----|
| D1 | **Employee uniqueness** | `db/schema.sql` has no UNIQUE on `employees.phone` / `employees.email`. | Add UNIQUE (nullable columns: partial unique indexes in PostgreSQL); dedupe before enforce. | 3 |
| D2 | **`employment_type` + mandatory columns** | `employment_type` nullable; no `national_id`, `university`, `major`, `is_graduate` on `employees`. | Migration: new columns; NOT NULL after backfill; CHECK includes `full_time`, `part_time`, `contract` (see `003_employees_employment_full_time.sql` + `schema.sql`). | 5 |
| D6 | **`national_id`** | Column missing today. | `national_id TEXT NOT NULL UNIQUE` (or national format validated in app). | 2 |
| D3 | **Analytics / reporting views** | Course stats may need a **view** or materialized query for performance. | Add view or indexed query; document in `MEMORY_BANK`. | 3 |
| D4 | **Audit columns (`created_at`, `updated_at`, `created_by`)** | Some tables show NULLs; attendance uses **`marked_by`** pattern. | Standardize: DB defaults (`now()`), triggers or service-layer population, and **user id** where applicable; align FastAPI + Streamlit writers. | 5 |
| D5 | **`contract_percentage` only for contract** | Column nullable; business rule: only meaningful for contract instructors (BR §4.2). | CHECK: `(employment_type = 'contract') OR (contract_percentage IS NULL)` — exact formulation TBD with legal/payroll. | 2 |

---

## 4. Product / domain discussion (cross-cutting)

### 4.1 Staff attributes (aligned with **P1–P3**)

| Field | Status |
|--------|--------|
| **full_name**, **phone**, **national_id** | Mandatory; **phone** + **email** unique among employees; **national_id** unique. |
| **university**, **major**, **is_graduate** | Mandatory. |
| **employment_type** | Mandatory; allowed values: **`full_time`**, **`part_time`**, **`contract`**. |
| **Contract %** | Only when type = contract; default 25% per **02_business_requirements.md** §4.2. |
| **Optional / later** | `college`, `graduation_year`, `job_title`, `employee_metadata` JSONB for extras. |

### 4.2 Balances, settlement, and overpayment (**P5–P8**)

- **Per student (enrollment):** one balance per the chosen grain (today: enrollment via `v_enrollment_balance`).  
- **Per guardian:** **sum** of related students’ balances (same convention).  
- **Signs:** **negative** = debt; **zero** = settled; **positive** = credit.  
- **Collection UX:** prioritize or filter to families with **any** debt (negative balance under **P6**).  
- **Overpayment:** warn → on confirm, allow; credit **positive** balance; **apply toward future** charges.

*Implementation must replace the current view meaning (`net_due − paid`) with **P6** or expose two columns during transition (`amount_owed` vs `account_balance`) to avoid regressions.*

### 4.3 Competitions — fees (**P9**)

- Fees are **not** global: they differ by **competition**, **category**, and **edition**.  
- Model **edition-level** (and category-level) fee configuration; each registration stores the **fee snapshot** or computed **per-member share** for teams (**equal split**).

---

## 5. Suggested priority (MoSCoW)

| Priority | Items |
|----------|--------|
| **Must** | **B2, U3** (receipt # — blocker); **B8, U2, U9** (balance **P6** + financial desk + overpay warn); **U1, B1, D1, D2, D6** (staff mandatory fields + uniqueness + national_id); D4 (audit); B4, D5 (employment + contract %) |
| **Should** | **U8, B9** (Dashboard receipts); U4 (staff form completeness) |
| **Could** | U5, B5, D3 (course stats); U6, B6 (PDF) |
| **Won’t (now)** / **Phase 2** | U7, B7 (competition fee schema) — unless revenue-critical |

---

## 6. Story point totals (rough)

| Area | Items | Approx. sum (SP) |
|------|--------|------------------|
| UI | U1–U9 | ~36 |
| Backend | B1–B9 | ~47 |
| DB | D1–D6 | ~20 |

*D6 is tightly coupled to D2 (national_id column); de-duplicate effort in sprint planning. Re-estimate per sprint.*

---

## 7. References

- `app/ui/components/finance_overview.py` — Financial Desk flow, `open_receipt` / `finalize_receipt`.  
- `app/ui/components/finance_receipt.py` — Receipt # display.  
- `app/modules/finance/finance_service.py` — Receipt lifecycle.  
- `app/modules/hr/hr_models.py` — Employee fields.  
- `docs/memory_bank/01_business_domain/02_business_requirements.md` — Contract 25%, payroll V2, admin flexibility.  
- `docs/MEMORY_BANK.md` — Schema and module map.

---

*End of document.*
