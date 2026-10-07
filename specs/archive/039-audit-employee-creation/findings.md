# Findings Catalog: Employee Creation Endpoint Audit

**Feature**: 039-audit-employee-creation
**Status legend**: `pending` → `fixed` (with evidence) or `accepted-risk` (with rationale)

## Baseline (recorded at T002)

- Baseline run (`pytest tests/test_hr.py tests/test_hr_full.py -q`): **56 passed, 1 failed (pre-existing), 1 skipped, 2 xpassed**.
- Pre-existing failure: `tests/test_hr.py::TestHRAuth::test_all_hr_endpoints_require_admin` — GET /api/v1/hr/employees returns 200 without auth headers under the test app. Unrelated to this feature's defect catalog; do not misattribute future failures to our changes.

## Entries

| ID | Severity | Status |
|----|----------|--------|
| F-01 | ERROR | fixed |
| F-02 | ERROR | fixed |
| F-03 | ERROR | fixed |
| F-04 | ERROR | fixed |
| F-05 | WARNING | fixed |
| F-06 | WARNING | fixed |
| F-07 | WARNING | fixed |
| F-08 | WARNING | fixed |
| F-09 | INFO | fixed |
| F-10 | INFO | accepted-risk |
| F-11 | INFO | accepted-risk |

---

### F-01 — ERROR — Duplicate checks short-circuit
- **Affected behavior**: `_validate_unique_fields` probes national_id/phone/email sequentially and raises on the first collision; admin discovers one problem per attempt.
- **Evidence**: `app/modules/hr/services/employee_crud_service.py` (`_validate_unique_fields`).
- **Reproduction**: POST an employee whose national_id AND phone both collide with an existing row → 409 mentions only one field.
- **Resolution status**: fixed — probes now collect all collisions and raise one ConflictError (`national_id: already in use; phone: already in use`); verified by `TestF01AggregatedDuplicateReporting` in tests/test_hr_audit_regressions.py.

### F-02 — ERROR — Supabase failures misclassified as conflicts
- **Affected behavior**: Every exception from the remote create-user call is mapped to `ConflictError` (409 "Supabase error: …"), making network/config failures indistinguishable from real email collisions.
- **Evidence**: `app/modules/hr/services/staff_account_service.py`, `create_account`.
- **Reproduction**: Run with unreachable SUPABASE_URL and provision an account → fake conflict message instead of clear failure.
- **Resolution status**: fixed — create-user exceptions are classified (`_is_email_taken_signal` → `ConflictError("email: already registered")`; all others → `BusinessRuleError` with "nothing was created; retry" wording); verified by `TestF02RemoteFailureClassification`.

### F-03 — ERROR — No compensation for orphaned remote identities
- **Affected behavior**: If local user creation fails after the remote auth user exists, nothing deletes the remote record; also no `uow.rollback()` before raising.
- **Evidence**: `app/modules/hr/services/staff_account_service.py`, `create_account`; `app/modules/hr/repositories/staff_account_repository.py` (`create_linked_account`).
- **Reproduction**: Force a local-side failure after remote creation → orphaned Supabase user remains.
- **Resolution status**: fixed — local creation is wrapped: on failure the service best-effort deletes the remote identity (`_compensate_remote_user`), rolls back the UoW, and re-raises (typed errors pass through; unexpected ones become `BusinessRuleError` "nothing was created; safe to retry"); verified by `TestF03ZeroPartialStateOnMidwayFailure` including no-User-row and employee-stays-unlinked assertions.

### F-04 — ERROR — Concurrent duplicate insert returns 500
- **Affected behavior**: Duplicate defense is SELECT-then-INSERT; a concurrent insert hitting `uq_employees_*` constraints raises unhandled IntegrityError.
- **Evidence**: `app/modules/hr/services/employee_crud_service.py` (`create`, `update`).
- **Reproduction**: Two simultaneous identical creates → one succeeds, other returns HTTP 500.
- **Resolution status**: fixed — service catches IntegrityError around write+flush+commit, rolls back the UoW, and re-raises a field-named ConflictError via `app/modules/hr/services/integrity_error_mapper.py`; verified by `TestF04RaceSafeConflictTranslation`.

### F-05 — WARNING — Update-path employment normalization bug
- **Affected behavior**: Setting only `contract_percentage` on a non-contract employee violates the DB CHECK; `_normalize_update_employment_data` is dead code.
- **Evidence**: `app/modules/hr/services/employee_crud_service.py` (`update` + dead method).
- **Reproduction**: PATCH contract_percentage=50 on a full_time employee → IntegrityError/500.
- **Resolution status**: fixed — `_normalize_update_employment` runs whenever employment fields are touched using the effective (incoming-or-stored) type; dead `_normalize_update_employment_data` deleted; repository honors explicit None clears; PUT now accepts partial payloads via new `EmployeeUpdateInput`; verified by `TestF05UpdateEmploymentNormalization`.

### F-06 — WARNING — Staff accounts overview has permanent blank fields
- **Affected behavior**: Router maps email/job_title/created_at to literal None placeholders despite JOINed data availability.
- **Evidence**: `app/api/routers/hr_router.py` (`list_staff_accounts`); DTOs in `app/modules/hr/schemas/staff_account_schemas.py`.
- **Reproduction**: GET /api/v1/hr/staff-accounts → null columns for fields that exist.
- **Resolution status**: fixed — two additional root causes surfaced during the fix: (1) `create_linked_account` never wrote `user.employee_id`, so the overview JOIN silently excluded every provisioned account; (2) SQLModel wrote explicit NULL `created_at` over the DB default. Both corrected alongside DTO/router completion (`StaffAccountLinkDTO`/`StaffAccountDTO` now carry email/job_title/created_at); verified by `TestF06CompleteStaffAccountListing`.

### F-07 — WARNING — Deactivating employee leaves login active
- **Affected behavior**: No employee→account status linkage anywhere; only reverse direction exists.
- **Evidence**: absence across `app/modules/hr/**`; reverse-only sync in `update_account_status`.
- **Reproduction**: Deactivate a linked employee → account still authenticates.
- **Resolution status**: fixed — `EmployeeCrudService.update` detects is_active true→false on a linked employee and calls the new `StaffAccountRepository.set_user_active` inside the same transaction (Protocols updated in both layers); verified by `TestF07DeactivationBlocksLinkedAccount`.

### F-08 — WARNING — Credentials not pre-validated before remote call
- **Affected behavior**: Malformed emails / short passwords reach Supabase unvalidated, surfacing as misclassified conflicts (compounds F-02).
- **Evidence**: `CreateEmployeeAccountRequest` schema + service validation gap.
- **Reproduction**: Provision with invalid email syntax → confusing remote-derived error.
- **Resolution status**: fixed — audit found the API boundary already used `EmailStr` (earlier finding overstated the gap); residual defect was layer misalignment (API allowed 8-char passwords while the service enforces `MIN_PASSWORD_LENGTH=12`). The request schema now imports the shared constant, and the service message is field-named (`password: must be at least 12 characters`). Both problems in one submission are reported together by the RequestValidationError handler; verified by `TestF08CredentialPreValidation` (includes zero-remote-call assertion).

### F-09 — INFO — Field-limit inconsistencies and dead code
- **Affected behavior**: National-ID minimum differs between layers (10 vs 14); validators module and model-level DTOs may be unreferenced.
- **Evidence**: `app/modules/hr/constants.py`, `app/modules/hr/validators/employee_validators.py`, `app/modules/hr/models/employee_models.py`.
- **Reproduction**: Static inspection + caller grep.
- **Resolution status**: fixed — caller grep confirmed zero consumers of `app/modules/hr/validators/` (module deleted), model-level `EmployeeCreate`/`EmployeeRead` (classes deleted), `MIN_NATIONAL_ID_LENGTH`, and `MIN_PHONE_LENGTH` (constants removed with their dead validation block). Effective limits remain those enforced at the API boundary (national_id ≥ 10 chars, phone ≥ 10 digits) — no behavior change.

### F-10 — INFO — ACCEPTED RISK — Instructor accounts impossible via API
- **Affected behavior**: `UserRole` enum lacks INSTRUCTOR while DB CHECK allows it; provisioning restricted to admin/system_admin.
- **Rationale**: Permission-model change explicitly out of scope per spec assumptions (research D11). Requires product decision.
- **Resolution status**: accepted-risk

### F-11 — INFO — ACCEPTED RISK — Constitution staleness
- **Affected behavior**: `.specify/memory/constitution.md` §V claims role comes from JWT `app_metadata.role`; code truth is local `users.role` (`dependencies.py:101`). Schema file count also stale.
- **Rationale**: Documentation governance issue; amendment proposal only — no code change (research D12-notes).
- **Resolution status**: accepted-risk

---

## Post-Analysis Remediations (from /speckit.analyze report)

### R-1 — HIGH — FR-003 had no working coverage (pre-existing failing auth test)
- **Affected behavior**: `TestHRAuth::test_all_hr_endpoints_require_admin` used the `override_auth` fixture, whose mock returns an admin user unconditionally (`conftest.py:101-102`) — so its own "unauthenticated" branch could never observe 401. Guards themselves were correct (`require_admin` on all HR endpoints).
- **Resolution status**: fixed — test split into `test_all_hr_endpoints_reject_missing_credentials` (real dependency chain; probe confirmed uniform 401 envelopes) and `test_all_hr_endpoints_accept_admin_auth`. Baseline failure eliminated: full HR suite now 72 passed / 0 failed.

### R-2 — MEDIUM — FR-008 (second-account refusal) had no automated lock
- **Affected behavior**: Service refused re-provisioning but nothing asserted it anywhere (analysis grep).
- **Resolution status**: fixed — `TestFR008SecondAccountRefusal::test_refused_before_any_remote_call` seeds a linked employee, installs an exploding fake Supabase admin (any remote touch fails the test), asserts 409 + "already has an account" and zero local identities created.

### R-3 — CRITICAL — Constitution §III: `-> tuple` on Protocol-declared repository methods
- **Affected behavior**: `EmployeeRepositoryInterface.list_all -> tuple[list[Employee], int]` and `StaffAccountRepositoryInterface.create_linked_account -> tuple[Employee, "User"]` violated the typed-contracts rule (private-helper exemption requires absence from the Protocol).
- **Resolution status**: fixed — new `EmployeeListResult` DTO (`items`/`total`) returned by `list_all`; `create_linked_account` now returns the created `User` alone (service already holds the employee). Side benefit: employee existence is resolved in `_validate_account_creation` BEFORE the remote call, so a missing employee can no longer produce a doomed Supabase identity requiring compensation. Call-site grep confirms only the updated consumers exist.
