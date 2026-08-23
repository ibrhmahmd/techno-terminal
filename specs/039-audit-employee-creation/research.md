# Research: Employee Creation Endpoint Audit & Fixes

**Feature**: 039-audit-employee-creation | **Date**: 2026-08-23
All Technical Context items resolved during code investigation; no NEEDS CLARIFICATION remain.

## Preliminary Findings Catalog (from plan-phase investigation)

These are confirmed by reading code; implementation phase must re-verify each, then record final status in `findings.md` per FR-012.

| # | Severity | Location | Defect |
|---|----------|----------|--------|
| F-01 | ERROR | `EmployeeCrudService._validate_unique_fields` | Checks run sequentially and raise on first collision — admin discovers one problem per attempt (violates FR-004/FR-005 clarified behavior). |
| F-02 | ERROR | `StaffAccountService.create_account` L56-57 | EVERY Supabase exception becomes `ConflictError` (409 "Supabase error: …") — network/config failures and real email collisions are indistinguishable; midway failures violate FR-002 semantics. |
| F-03 | ERROR | `StaffAccountService.create_account` L59-64 | If local user/link creation fails AFTER the remote auth user was created, no compensation runs → orphaned auth identity; also no `uow.rollback()` before raising, so `get_db()` exit-commit risk (constitution UoW constraint). |
| F-04 | ERROR | `EmployeeCrudService.create/update` | Duplicate defense is SELECT-then-INSERT; concurrent duplicate insert hits DB UNIQUE (`uq_employees_*`) → uncaught `IntegrityError` → HTTP 500 (spec edge case: two admins, same moment). |
| F-05 | WARNING | `EmployeeCrudService.update` L64-65 | Normalization only runs when `employment_type` is provided; setting `contract_percentage` alone on a non-contract employee violates `employees_contract_pct_check` → IntegrityError → 500. `_normalize_update_employment_data` exists but is never called (dead code). |
| F-06 | WARNING | `hr_router.list_staff_accounts` L167-177 | Router maps missing fields to literal `None` placeholders ("would need extension") — permanent blank columns in accounts overview (violates FR-010). Underlying DTOs lack the fields. |
| F-07 | WARNING | HR module (absence) | No employee→account status linkage: deactivating an employee leaves their login active (FR-011 gap). Reverse direction only (`update_account_status` syncs employee from user). |
| F-08 | WARNING | `CreateEmployeeAccountRequest` / service | No email syntax validation before remote call (FR-007) — malformed emails surface as misclassified Supabase conflicts (compounds F-02). |
| F-09 | INFO | `hr/constants.py` vs schemas/models | National-ID minimum inconsistent: DTO/model enforce 10, `MIN_NATIONAL_ID_LENGTH = 14`; `validators/employee_validators.py` appears unreferenced; model-level `EmployeeCreate`/`EmployeeRead` duplicate schema-layer DTOs (dead-code audit required). |
| F-10 | INFO | `auth/constants.py`, DB CHECK | `UserRole` enum has only ADMIN/SYSTEM_ADMIN while `users_role_check` DB constraint allows 'instructor'; provisioning endpoint therefore cannot create instructor logins. Permission-model decision — out of scope per spec assumption; record as accepted-risk finding. |
| F-11 | INFO | `.specify/memory/constitution.md` §V | Constitution says role comes from JWT `app_metadata.role`; code truth is the local `users.role` column (`dependencies.py:101`). Flag for constitution amendment; do not change code to match stale text. |

## Decisions

### D1: Aggregate duplicate/conflict reporting
**Decision**: `_validate_unique_fields` collects violations across national_id, phone, and email probes, then raises ONE typed exception whose message enumerates every offending field (`national_id: already in use; phone: already in use`).
**Rationale**: Satisfies FR-004/FR-005 ("all problems at once") without inventing a response shape outside the standard envelope; message stays human-readable for admins.
**Alternatives considered**: Structured `errors[]` array in envelope (rejected: changes API contract surface beyond need); sequential single-error reporting (rejected: current broken behavior).

### D2: Race-safety via existing DB constraints
**Decision**: Keep SELECT-probes for friendly messages; catch `IntegrityError` around repository writes in the SERVICE layer, map constraint name → field (`uq_employees_national_id` etc.), roll back via UoW, re-raise as `ConflictError`. No new migrations.
**Rationale**: `uq_employees_email/national_id/phone/user_id` already exist in `db/schema/02_tables_core.sql`; adding triggers or advisory locks adds complexity for a ~20-row table. Constitution-compliant: typed exception at boundary, rollback + propagate pattern.
**Alternatives considered**: New migration adding ON CONFLICT handling (rejected: constraints sufficient); ignoring races as unlikely (rejected: SC-003/SC-004 demand zero unexplained failures).

### D3: Classify remote-auth failures
**Decision**: Wrap the `supabase.auth.admin.create_user` call; classify by exception signal — an "already registered/taken" style signal maps to `ConflictError("email already registered")`; every other failure maps to `BusinessRuleError("account provisioning temporarily unavailable — nothing was created; retry shortly", detail=<original>)`.
**Rationale**: Uses only constitution-sanctioned exception types (IV); makes FR-002's "clear failure message" honest instead of fake conflicts; keeps detail for logs only (exception contract).
**Alternatives considered**: New exception type + handler (rejected: expands global mapping for one call site); blanket 503 via HTTPException in router (rejected: violates IV — services raise domain exceptions).

### D4: Compensation for orphaned remote identities
**Decision**: After remote-user success, wrap local creation; on ANY local failure: best-effort `supabase.auth.admin.delete_user(uid)`, `uow.rollback()`, then re-raise original typed exception. Compensation failure is logged, never masks the original error.
**Rationale**: Delivers FR-002's zero-partial-state guarantee end-to-end; delete-after-create is idempotent-safe here because the UID was just created by us.
**Alternatives considered**: Pre-reserve username locally before remote call (rejected: still leaves window + complicates flow); leave orphans + periodic cleanup job (rejected: background infra for an interactive admin action).

### D5: Session ownership discipline in fixed paths
**Decision**: In failure paths touched by this feature, call `uow.rollback()` immediately before raising and always let the exception propagate. Do not add new mid-service `commit()` calls; existing explicit commits in happy paths stay (double-commit with `get_db()` exit-commit is benign).
**Rationale**: Directly implements the constitution's UoW rollback constraint; swallowed exceptions after rollback would cause `get_db()` to commit partial work.
**Alternatives considered**: Removing all explicit commits (rejected: broader behavioral change than this audit's scope; flagged as observation for a future cleanup).

### D6: Update-path employment normalization
**Decision**: Run normalization whenever `employment_type` OR `contract_percentage` appears in the update payload; single normalizer handles Optional fields correctly (clear percentage when type becomes non-contract; default 25% when becoming contract without explicit value). Delete dead `_normalize_update_employment_data`.
**Rationale**: Prevents `employees_contract_pct_check` violations (F-05) and satisfies Dead Code Discipline simultaneously.
**Alternatives considered**: DB-level trigger to auto-null (rejected: hidden business rule in wrong layer).

### D7: Deactivation linkage (FR-011)
**Decision**: `EmployeeCrudService.update` detects `is_active` True→False on an employee holding `user_id`, then calls new `StaffAccountRepository.set_user_active(user_id, False)` (added to repo Protocol + `StaffAccountsInterface`). Account→employee direction stays as-is.
**Rationale**: Single choke point (employee update is the only deactivation path today); keeps rule in service layer, query in repository, per constitution I/II.
**Alternatives considered**: DB trigger (rejected: business rule hidden from services); separate endpoint requirement (rejected: spec mandates automatic linkage).

### D8: Complete staff-account listing (FR-010)
**Decision**: Extend `StaffAccountLinkDTO`/`StaffAccountDTO` with employee email, job_title, and account created_at; repository JOIN already fetches both rows so it's field mapping; router passes values through and its None-placeholder mapping block is deleted. Response list wrapped in named result DTO if signature requires (III).
**Rationale**: Data already available in the joined query; blanks were purely mapping laziness (comment in router admits "would need extension").
**Alternatives considered**: Separate detail endpoint (rejected: overview must be complete per FR-010).

### D9: Credential pre-validation (FR-007)
**Decision**: Email syntax enforced on the API input schema via Pydantic `EmailStr` (API-specific shape — allowed in `app/api/schemas`/router input models), password length enforced in service against existing `MIN_PASSWORD_LENGTH = 12` (≥8 spec floor satisfied with margin). Both produce per-field reasons before any remote call.
**Rationale**: Earliest possible rejection, zero remote calls wasted; reuses framework validation instead of hand-rolled regex; constant already battle-tested.
**Alternatives considered**: Lowering constant to 8 (rejected: weakening security to match a floor is backwards); custom regex validator (rejected: duplicates what EmailStr provides).

### D10: Field-limit inconsistencies (F-09)
**Decision**: Effective behavior stays at the schema-enforced minimums (national_id ≥ 10 chars, phone ≥ 10 digits pattern) — no tightening without data migration evidence. During implementation, grep for callers of `validators/employee_validators.py` and model-level `EmployeeCreate`/`EmployeeRead`; delete if uncalled (expected), including the unused `MIN_NATIONAL_ID_LENGTH=14` constant path. Document actual limits in findings catalog.
**Rationale**: Spec forbids destructive resets and behavior surprises; dead-code discipline covers the rest. Egyptian national IDs are 14 digits, but enforcing that now could reject legacy rows' updates — needs product decision beyond this audit.
**Alternatives considered**: Enforce 14 immediately (rejected: may break updates of existing employees); leave duplication silently (rejected: violates Dead Code Discipline).

### D11: Instructor-account restriction (F-10)
**Decision**: Out of scope — record as accepted-risk finding. Provisioning remains admin/system_admin-only; expanding the role model is a permission-model change explicitly excluded by spec assumptions.
**Rationale**: Spec assumption locks the permission model; changing UserRole enums ripples into guards, JWT mocks, and DB CHECK constraints.
**Alternatives considered**: Add INSTRUCTOR to enum + allowlist (rejected: scope creep; needs product decision).

### D12: Regression test strategy (FR-013)
**Decision**: New `tests/test_hr_audit_regressions.py` mirrors findings catalog IDs (F-01…): each fixed defect gets ≥1 test reproducing the original failure mode (monkeypatched Supabase client for remote-failure classes; concurrent-insert simulation via direct IntegrityError injection where true parallelism isn't practical in-process). Follow existing fixture patterns: `client`, `override_auth`, `mock_admin_headers`.
**Rationale**: Deterministic, no external dependencies, matches conftest conventions; catalog↔test ID mapping makes SC-006 auditable.
**Alternatives considered**: Real Supabase integration tests (rejected: credentials/expiry flakiness; unit-level classification tests cover logic).

## Constitution staleness notes (for `/speckit.constitution` amendment, not code change)

1. §V claims role reads from JWT `app_metadata.role` — code truth: local `users.role` (`app/api/dependencies.py:101`, verified `_require_roles` guard).
2. §Operational says schema has 17 modular files — now 18 (`db/schema/11_tables_tasks.sql`).
3. §Development Workflow duplicate-prefix list omits `051`, `057`.
