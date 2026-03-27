# Phase 5 API — execution roadmap (2026)

**Document type:** Engineering handoff — REST API rollout  
**Audience:** Backend engineers, API consumers, tech lead  
**Parent spec:** [09_phase5_api_technical_plan.md](../memory_bank/04_architecture/09_phase5_api_technical_plan.md) (architecture blueprint)  
**Related:** [MEMORY_BANK.md](../MEMORY_BANK.md) §7 (current API snapshot), [sprint_roadmap_post_qa_2026.md](./sprint_roadmap_post_qa_2026.md) (product QA sprints — parallel track)

---

## 1. Purpose

This document turns **Phase 5** from a high-level blueprint into **ordered execution work**: what is already shipped, what each sub-phase delivers, acceptance criteria, dependencies, and security notes. It is intended for **sprint planning** alongside domain backlogs (CRM, finance, QA).

---

## 2. Architectural anchors (non-negotiable)

| Anchor | Rule |
|--------|------|
| **Business logic** | HTTP handlers call **`app.modules.*.service`** (or thin orchestration only). No SQL in routers. |
| **Sessions** | Use **`get_db`** → `get_session()` per request; do not stash ORM objects on `app.state`. |
| **DTOs** | Expose **Create / Read / Public** Pydantic models at the boundary — never return raw `SQLModel(table=True)` rows that include internal keys unless explicitly a safe read schema. |
| **Auth** | **Supabase** issues JWTs; FastAPI validates via **`get_current_user`** (Bearer token → Supabase verify → local `users` row). No duplicate password store in API. |
| **Errors** | Map `NotFoundError`, `ValidationError`, `ConflictError`, `BusinessRuleError`, `AuthError` via **`app/api/exceptions.py`** (already registered). |

---

## 3. Current state vs original blueprint

The technical plan mentioned a **local `POST /auth/token` JWT dispenser**. The implemented stack uses **Supabase Auth** for sign-in; tokens are obtained from Streamlit or Supabase tooling, then sent as **`Authorization: Bearer`**. The API exposes **`GET /api/v1/auth/me`** for the mapped **`UserPublic`** — this is the **intentional** pattern (ADR-10).

| Blueprint item (09) | As implemented today |
|---------------------|----------------------|
| Scaffold + CORS | Done — `app/api/main.py` |
| `get_db`, `get_current_user` | Done — `app/api/dependencies.py` |
| Global exception mapping | Done — `app/api/exceptions.py` |
| Auth token route | **Not used** — Supabase JWT + `/me` instead |
| Domain routers (CRM, …) | **Not mounted** — placeholders in `main.py` |

---

## 4. Execution phases (detailed)

### Phase 5.1 — Scaffold and auth (**substantially complete**)

**Goal:** Runnable FastAPI app, secure identity hook, health check, shared error JSON.

| Work item | Status | Notes |
|-----------|--------|--------|
| `run_api.py` / Uvicorn entry | Done | Prefer `uvicorn app.api.main:app` in production with workers. |
| `create_app()`, CORS | Done | `allow_origins=["*"]` is **dev-only**; tighten per environment before public deploy. |
| `get_db` generator | Done | Yields one `Session` per request. |
| `get_current_user` (Bearer → Supabase → DB user) | Done | Inactive users → HTTP 403. |
| `GET /api/v1/auth/me` → `UserPublic` | Done | `app/api/routers/auth.py` |
| `GET /health` | Done | |
| Exception handlers | Done | Align status codes with client expectations (422 vs 409). |

**Hardening backlog (optional mini-sprint)**

- Environment-based **CORS** allowlist.
- Structured **logging** (request id, user id) on 401/403.
- OpenAPI **description** for Bearer auth (already usable via Swagger “Authorize”).
- Integration test: valid JWT → 200 `UserPublic`; invalid → 401.

**Acceptance:** Any client can call `/me` with a valid Supabase access token and receive safe JSON without `supabase_uid` leakage.

---

### Phase 5.2 — CRM API

**Goal:** JSON CRUD for guardians and students aligned with `crm_service` / `crm_repository`.

| Suggested routes (draft) | Service entrypoints (verify before implement) |
|--------------------------|-----------------------------------------------|
| `POST /api/v1/crm/guardians` | `register_guardian` / `find_or_create_guardian` |
| `GET /api/v1/crm/guardians` | search / list (paginated) |
| `GET /api/v1/crm/guardians/{id}` | `get_guardian_by_id` |
| `POST /api/v1/crm/students` | `register_student` |
| `GET /api/v1/crm/students/{id}` | `get_student_by_id` |
| `GET /api/v1/crm/students` | `search_students` |

**Prerequisites**

- Stable **request/response DTOs** in `crm_schemas` or `crm_models` (Create/Read) — pattern already started for registration inputs.
- **Role policy:** which `UserRole` values may create guardians/students (document in router deps).

**Acceptance**

- OpenAPI documents all bodies; no mass-assignment of primary keys on create.
- Errors propagate as structured JSON via existing handlers.

---

### Phase 5.3 — Academics API

**Goal:** Courses, groups, sessions, attendance mutations via `academics_service` / attendance module.

| Suggested route groups | Notes |
|------------------------|--------|
| Courses / groups | Map to `update_course`, `update_group`, list/get helpers as exist today. |
| Sessions | `update_session`, `add_extra_session`, schedule flows — align with idempotency rules. |
| Attendance | `PUT` or `PATCH` style updates per enrollment+session; respect DB unique `(student_id, session_id)`. |

**Prerequisites**

- Confirm **ORM unique constraint** is mirrored by **database** unique index for attendance if DB must enforce races.

**Acceptance**

- Session time validation (11:00–21:00 business rule) enforced via service, not duplicated ad hoc in router.

---

### Phase 5.4 — Transactions API (enrollments + finance)

**Goal:** Safe enrollment and receipt flows over HTTP.

| Area | Notes |
|------|--------|
| Enrollments | `enroll_student`, `transfer_student`, `drop_enrollment` — expose minimal DTOs; handle `ConflictError` for capacity / unique active enrollment. |
| Finance | `open_receipt`, `add_charge_line`, `finalize_receipt`, refunds — **high risk**; require role gate + idempotency discussion for double POST. |

**Prerequisites**

- QA backlog **B2** (receipt number persistence) should be **resolved or understood** before exposing `POST /receipts` to external clients.

**Acceptance**

- Financial operations audit-friendly (actor user id from `get_current_user` once D4 audit work lands).

---

### Phase 5.5 — Analytics API

**Goal:** Read-only aggregates for external dashboards (Flutter/React).

| Work item | Notes |
|-----------|--------|
| New `routers/analytics.py` | Thin handlers calling `analytics_service` functions. |
| Query params | Date ranges, course/group filters as needed. |
| Performance | Prefer existing repo SQL; add indexes if endpoints hit large tables. |

**Prerequisites**

- If **balance semantics** change (QA backlog **B8** / `v_enrollment_balance`), update analytics SQL in the **same release** or version the API.

**Acceptance**

- All endpoints **GET** (or POST only for large filter bodies if justified); rate-limit story documented for production.

---

## 5. Cross-cutting workstreams

| Stream | Applies to phases | Action |
|--------|-------------------|--------|
| **Pagination** | 5.2–5.5 | Standard `skip`/`limit` or cursor for list endpoints. |
| **Versioning** | All | Prefix remains `/api/v1/`; breaking changes → `/v2/` or header negotiation. |
| **OpenAPI / clients** | All | Export schema for mobile; consider `openapi-generator` for Flutter. |
| **Testing** | 5.1+ | Pytest + `TestClient`; mock Supabase or use short-lived test JWTs. |

---

## 6. Security checklist (before external exposure)

- [ ] CORS not `*` in production; HTTPS termination documented.  
- [ ] Service role key **never** in API process except dedicated admin jobs (seed is separate).  
- [ ] Rate limiting / WAF for public ingress.  
- [ ] No PII in error **detail** strings in production builds.  
- [ ] Role-based dependencies (`require_admin`, `require_system_admin`) mirrored from Streamlit policy.

---

## 7. Summary table

| Phase | Theme | Primary deliverable | Status |
|-------|--------|---------------------|--------|
| **5.1** | Scaffold + auth | FastAPI app, `/me`, `/health`, DI, exceptions | **Largely done** |
| **5.2** | CRM | Guardian + student routes | Planned |
| **5.3** | Academics | Courses, groups, sessions, attendance | Planned |
| **5.4** | Transactions | Enrollments + finance | Planned (finance after receipt fix) |
| **5.5** | Analytics | Read-only reporting API | Planned |

---

## 8. Revision history

| Version | Date | Notes |
|---------|------|--------|
| 1.0 | 2026-03 | Initial execution roadmap from 09_phase5 + code reality |

---

*End of document.*
