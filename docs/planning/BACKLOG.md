# Techno Terminal — Master Backlog & Technical Debt Register

> **Single source of truth** for all pending work.  
> Updated: 2026-03-31 | Canonical path: `docs/planning/BACKLOG.md`

---

## 🔴 Stream A — FastAPI Rollout (Active Sprint)

**Goal:** Ship a stateless REST API layer on top of the existing domain services.  
**Reference:** [`phase5_api_execution_roadmap_2026.md`](phase5_api_execution_roadmap_2026.md) · [`phase5_api_technical_plan.md`](../memory_bank/04_architecture/09_phase5_api_technical_plan.md)

| # | Task | Status |
|---|------|--------|
| A1 | `app/api/schemas/common.py` — `ApiResponse[T]`, `PaginatedResponse[T]`, `ErrorResponse` | ⬜ |
| A2 | `app/api/dependencies.py` — role guards + service factories | ⬜ |
| A3 | `app/api/schemas/crm/` — `StudentPublic`, `ParentPublic` | ⬜ |
| A4 | `app/api/routers/crm.py` — 9 CRM endpoints | ⬜ |
| A5 | `app/api/schemas/academics/` — `CoursePublic`, `GroupPublic`, `SessionPublic` | ⬜ |
| A6 | `app/api/routers/academics.py` — Courses, Groups, Sessions | ⬜ |
| A7 | `app/api/routers/attendance.py` — Attendance mark/read | ⬜ |
| A8 | `app/api/schemas/enrollments/` + `finance/` | ⬜ |
| A9 | `app/api/routers/enrollments.py` | ⬜ |
| A10 | `app/api/routers/finance.py` | ⬜ |
| A11 | `app/api/routers/competitions.py` (read-first) | ⬜ |
| A12 | `app/api/routers/hr.py` (read-only) | ⬜ |
| A13 | `app/api/routers/analytics.py` (stubs) | ⬜ |
| A14 | `app/api/main.py` — mount all routers | ⬜ |
| A15 | `app/api/middleware/logging_middleware.py` | ⬜ |
| A16 | Smoke test via Swagger `/api/v1/docs` | ⬜ |

---

## 🟡 Stream B — Feature Backlog (Phase 2)

**Goal:** New business capabilities once the API is stable.  
**Reference:** [`phase2_competition_fees_design_doc.md`](phase2_competition_fees_design_doc.md)

| # | Task | SP | Status |
|---|------|----|--------|
| B1 | **Competition Fees** — Link team registration to Finance Desk; snapshot `member_share` at registration; charge per category/edition (P9) | 13 | ⬜ |
| B2 | **Financial Desk — Student Search** (U2/B3) — Search by student, parent total (P5), debt-only toggle (P7) | 5 | ⬜ |
| B3 | **Overpayment Warning** (U9/P8) — Confirm step before credit-creating payment | 3 | ⬜ |
| B4 | **PDF Export Enhancement** — Logo, multi-signature blocks, further layout refinement | 2 | ⬜ |

---

## ⚪ Stream C — Architecture Technical Debt (Post-Delivery Sprint)

> These are explicitly **deferred** so the API ships on time.  
> None are forgotten — all are estimated and ordered.

### C1 — Session Injection Refactor *(~35 SP)*
**Risk if skipped forever:** Multi-service writes (e.g., enroll + create receipt) cannot be atomic.  
Every service method across all 7 modules needs `db: Session` as its first argument, passed down from `Depends(get_db)` in the router.

**Modules:** `academics` (3 services) · `crm` (2) · `enrollments` · `finance` · `hr` · `competitions` (2) · `attendance`

### C2 — Deep-SOLID: `hr` + `finance` Modules *(~21 SP)*
Both remain as flat monolithic files. Must be split into `models/ schemas/ repositories/ services/` per the [module_refactoring_guide.md](../architecture/module_refactoring_guide.md) SOP.
- `hr`: **8 SP**
- `finance`: **13 SP**

### C3 — Facade `__init__.py` Retirement *(8 SP)*
Once SOLID refactors complete, remove singleton re-exports from `crm/__init__.py` and `academics/__init__.py`. UI components import directly from service classes.

### C4 — Role Guard Helper Functions *(3 SP)*
Convenience `require_admin` / `require_instructor` dependency wrappers to avoid inline role checks in every router. Can start **alongside** API work.

### C5 — Automated Test Suite *(21 SP)*
`pytest` + FastAPI `TestClient`. Cover all happy paths + error flows for auth, CRM, enrollment, finance. Mock Supabase JWT with short-lived test tokens.

### Debt Summary Table

| ID | Item | Priority | SP | Unlock Condition |
|----|------|----------|----|-----------------|
| C1 | Session Injection (all 7 modules) | 🔴 High | 35 | After API delivery validated |
| C2 | `hr` + `finance` SOLID refactor | 🔴 High | 21 | After C1 complete |
| C3 | Facade `__init__.py` retirement | 🟡 Medium | 8 | After C2 complete |
| C4 | Role guard helpers | 🟡 Medium | 3 | Can start now |
| C5 | Automated test suite | ⚪ Low | 21 | After delivery + stable API |
| **Total** | | | **~88 SP** | 2–3 post-delivery sprints |

---

## ✅ Completed (Reference Only)

| Item | Completed |
|------|-----------|
| Sprint 1 — Receipt # integrity (B2/U3) | ✅ 2026-03 |
| Sprint 2 — HR identity & constraints (D1/D2/D5/D6/B1/B4/U1/U4) | ✅ 2026-03 |
| Sprint 3 — Audit timestamps D4 | ✅ 2026-03 |
| Sprint 4 — Dashboard receipt browser (B9/U8) | ✅ 2026-03 |
| Sprint 5/6 — Balance model P6 flip + `v_enrollment_balance` | ✅ 2026-03 |
| Sprint 6b — Financial Desk student search, overpay warning | ✅ 2026-03 |
| Sprint 7 — Course aggregates (B5/D3/U5) | ✅ 2026-03 |
| Phase 2 partial — PDF receipts (U6/B6) | ✅ 2026-03 |
| Core Logic Refactoring (Phases 1–6) — Guardian→Parent, payer_name, status state machine, session cancel, attendance badges, notes expanders | ✅ 2026-03-29 |
| FastAPI Phase 5.1 — Scaffold, CORS, `get_current_user`, `/auth/me`, `/health` | ✅ 2026-03 |

---

*Archived sprint docs: [`docs/planning/archive/`](archive/)*  
*Last Updated: 2026-03-31*
