# Tasks: Audit & Fix Employee Creation Endpoints

**Input**: Design documents from `/specs/039-audit-employee-creation/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/hr-staff-api.md ✅, quickstart.md ✅

**Tests**: INCLUDED — FR-013 mandates a regression suite mirroring the findings catalog (`tests/test_hr_audit_regressions.py`, IDs F-NN).

**Organization**: Tasks grouped by user story (US1 reliable creation → US2 precise rejections → US3 trustworthy provisioning → US4 documented findings).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story from spec.md (US1–US4)
- Every description includes exact file paths

## Path Conventions

Single project (FastAPI backend): `app/` modules + `tests/` at repo root. All fixes land in-place in `app/modules/hr/**` — no new migrations, no new endpoints.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the audit artifact that every later phase updates

- [X] T001 Create findings catalog scaffold at specs/039-audit-employee-creation/findings.md with entries F-01 through F-11 (fields: severity tier ERROR/WARNING/INFO, affected_behavior, evidence with file:line refs from research.md, reproduction_steps, resolution_status=`pending`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the pre-change baseline so regressions we introduce are distinguishable from pre-existing failures

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Run baseline `pytest tests/test_hr.py tests/test_hr_full.py -v`; record pass/fail summary in the header of specs/039-audit-employee-creation/findings.md

**Checkpoint**: Baseline recorded — user story implementation can now begin

---

## Phase 3: User Story 1 — Reliable Employee Creation & Updates (Priority: P1) 🎯 MVP

**Goal**: Creating/updating an employees reports EVERY duplicate identifier at once, survives concurrent inserts with a typed 409 (never 500), and never violates employment-type constraints on partial updates.

**Independent Test**: POST an employee whose phone+national_id both collide → single 409 naming BOTH fields; two rapid identical creates → one 201, one named-field 409; PATCH setting only `contract_percentage` on a salaried employee → 200, not 500.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T003 [P] [US1] Write failing regression tests in tests/test_hr_audit_regressions.py tagged F-01 (duplicate probe reports all colliding fields in one 409 message), F-04 (simulated concurrent insert → ConflictError envelope, never 500), F-05 (update with only contract_percentage on non-contract employee succeeds without CHECK violation) — follow existing fixture style (`override_auth` + `mock_admin_headers`, `_unique()` payload helper)

### Implementation for User Story 1

- [X] T004 [US1] Rework `_validate_unique_fields` in app/modules/hr/services/employee_crud_service.py: probe national_id/phone/email independently against existing employees, collect ALL collisions, raise ONE ConflictError enumerating every offending field (research D1)
- [X] T005 [US1] Create app/modules/hr/services/integrity_error_mapper.py translating psycopg/SQLAlchemy IntegrityError constraint names (`uq_employees_email|national_id|phone|user_id`) to field labels; wire into `EmployeeCrudService.create` and `update`: catch → `uow.rollback()` → re-raise ConflictError (research D2, D5 rollback discipline)
- [X] T006 [US1] Fix update-path normalization in app/modules/hr/services/employee_crud_service.py: normalize whenever `employment_type` OR `contract_percentage` is present in the payload (clear percentage when leaving contract type; default 25% when entering without value); DELETE dead `_normalize_update_employment_data` (research D6, Dead Code Discipline)
- [X] T007 [US1] Verify tests/test_hr_audit_regressions.py US1 cases green plus baseline suites still pass; update findings.md entries F-01, F-04, F-05 → `fixed` with evidence

**Checkpoint**: User Story 1 independently functional — creation/update flows are race-safe and fully reported

---

## Phase 4: User Story 2 — Precise Rejection Messages (Priority: P2)

**Goal**: Credential problems (invalid email syntax, too-short password) are rejected with every field problem named together BEFORE any remote call is attempted.

**Independent Test**: POST create-account with malformed email AND 5-char password → single 422 naming both fields; assert zero calls reached the (monkeypatched) Supabase client.

### Tests for User Story 2 ⚠️

- [X] T008 [US2] Write failing regression tests in tests/test_hr_audit_regressions.py tagged F-08 (malformed email + short password → one 422 listing both; monkeypatched supabase admin client asserts no remote invocation)

### Implementation for User Story 2

- [X] T009 [P] [US2] Change email field to pydantic EmailStr on the account-creation input schema in app/modules/hr/schemas/staff_account_schemas.py (research D9)
- [X] T010 [P] [US2] Enforce password minimum in `StaffAccountService.create_account` (app/modules/hr/services/staff_account_service.py) using existing `MIN_PASSWORD_LENGTH` from app/shared/constants.py; raise ValidationError collecting field-specific reasons before any remote call (research D9)
- [X] T011 [US2] Verify US2 tests green + baseline suites pass; update findings.md entry F-08 → `fixed`

**Checkpoint**: Stories 1 AND 2 work independently — bad input never reaches remote provisioning

---

## Phase 5: User Story 3 — Trustworthy Account Provisioning (Priority: P3)

**Goal**: Remote failures are classified honestly, midway failures leave zero partial state (remote identity compensated), deactivated employees lose login access automatically, and the accounts overview shows complete data.

**Independent Test**: With unreachable Supabase, create-account returns clear "nothing created" failure and no local User row exists afterward; deactivating a linked employee flips their account to inactive in GET /api/v1/hr/staff-accounts; overview rows carry real email/job_title/created_at.

### Tests for User Story 3 ⚠️

- [X] T012 [US3] Write failing regression tests in tests/test_hr_audit_regressions.py: F-02 (email-already-taken signal → ConflictError; network-style failure → BusinessRuleError with retry wording, NOT fake conflict), F-03 (local-side failure after remote user created → best-effort delete_user called, no local rows persisted, original typed error surfaces), F-06 (list_staff_accounts returns non-null email/job_title/created_at), F-07 (employee is_active true→false deactivates linked account)

### Implementation for User Story 3

- [X] T013 [US3] Classify exceptions around `supabase.auth.admin.create_user` in app/modules/hr/services/staff_account_service.py: registration-conflict signal → ConflictError("email already registered"); all other failures → BusinessRuleError("account provisioning temporarily unavailable — nothing was created; retry shortly") with original detail preserved for logs (research D3)
- [X] T014 [US3] Wrap local creation in compensation block in `create_account` (app/modules/hr/services/staff_account_service.py): on ANY local failure after remote user exists → best-effort `supabase.auth.admin.delete_user(uid)` (log, never mask), `uow.rollback()`, re-raise original typed exception (research D4/D5)
- [X] T015 [P] [US3] Add `set_user_active(user_id: int, active: bool)` to StaffAccountRepository (app/modules/hr/repositories/staff_account_repository.py), declare it on `StaffAccountsInterface` (app/modules/hr/repositories/interface.py) and `StaffAccountServiceInterface` (app/modules/hr/services/interface.py), invoke from `EmployeeCrudService.update` when linked employee transitions is_active True→False (research D7)
- [X] T016 [P] [US3] Extend StaffAccountLinkDTO/StaffAccountDTO with employee_email/job_title/created_at in app/modules/hr/schemas/staff_account_schemas.py; populate from existing JOINed rows; DELETE the permanent-None placeholder mapping block in `hr_router.list_staff_accounts` (app/api/routers/hr_router.py) (research D8)
- [X] T017 [US3] Verify US3 tests green + baseline suites pass; update findings.md entries F-02, F-03, F-06, F-07 → `fixed`

**Checkpoint**: All core stories functional — provisioning is honest, compensated, linked, and fully visible

---

## Phase 6: User Story 4 — Documented Findings & Accepted-Risk Record (Priority: P4)

**Goal**: The audit catalog is complete and honest: every defect has severity/evidence/repro/status; accepted risks documented with rationale; ERROR-tier count fixed = 100% (SC-006).

**Independent Test**: Reading findings.md alone tells an auditor what was broken, how it was proven, and what remains intentionally unfixed.

### Implementation for User Story 4

- [X] T018 [US4] Dead-code sweep: grep callers of app/modules/hr/validators/employee_validators.py, model-level `EmployeeCreate`/`EmployeeRead` in app/modules/hr/models/employee_models.py, and the `MIN_NATIONAL_ID_LENGTH` constant path (app/modules/hr/constants.py); delete uncalled code, record actual effective limits and outcome in findings.md F-09 (research D10)
- [X] T019 [P] [US4] Finalize specs/039-audit-employee-creation/findings.md: record accepted-risk entries F-10 (instructor-account restriction out of scope, research D11) and F-11 (constitution §V staleness → amendment proposal only, research D12-notes); confirm every ERROR-tier entry status=fixed (SC-006)

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Whole-feature verification

- [X] T020 Run full verification: `pytest tests/test_hr.py tests/test_hr_full.py tests/test_hr_audit_regressions.py -v` all green; execute the manual flow in specs/039-audit-employee-creation/quickstart.md steps 1–5 and confirm each expected outcome matches contracts/hr-staff-api.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001)** → **Foundational (T002)** → all user story phases
- **US1 → US2 → US3**: strictly ordered by priority; also share the single regression test FILE (append sequentially) and US3's crud-service edit depends on US1's rewrite of the same methods
- **US4** requires US1–US3 complete (statuses must reflect reality)
- **Polish (T019)** last

### Within Each Story

- Regression tests written FIRST and confirmed failing (except where the defect is a crash — assert the typed-envelope outcome instead of 500)
- Service/repository changes next; findings.md update closes each story

### Parallel Opportunities

- T009 ∥ T010 (schemas vs service, disjoint files)
- T015 ∥ T016 (repository/interfaces vs schemas/router, disjoint files)
- T018 ∥ T017 (findings finalize vs dead-code sweep — coordinate F-09 wording after T017 lands)

---

## Parallel Example

```text
# Phase 4 (after its test task):
Task: "T009 EmailStr on staff_account_schemas.py"
Task: "T010 Password enforcement in staff_account_service.py"

# Phase 5 (after T014):
Task: "T015 set_user_active across repository + interfaces + crud linkage"
Task: "T016 DTO extension + hr_router placeholder removal"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 → T002 (catalog scaffold + baseline)
2. T003–T007: creation/update reliability
3. STOP and validate: duplicates fully reported, races return 409, updates constraint-safe

### Incremental Delivery

- +US2: invalid credentials die at the door → demo clean 422s
- +US3: provisioning failures are truthful and stateless → demo forced-failure scenario
- +US4/P Polish: catalog audit-ready, full suite green## Notes

- No DB migrations expected — uniqueness enforced by existing `uq_employees_*` constraints
- Never swallow exceptions after `uow.rollback()` — always re-raise (constitution UoW constraint)
- Findings catalog IDs ↔ regression test IDs must stay 1:1 for SC-006 traceability
