# Research: Employee Soft Delete with Restore & Re-hire

**Feature**: 040-employee-soft-delete | **Date**: 2026-08-24
All decisions below are resolved; none remain NEEDS CLARIFICATION.

## D1 — Migration mechanics for the unique-index swap (LIVE-VERIFIED)

**Decision**: `ALTER TABLE employees DROP CONSTRAINT uq_employees_email/national_id/phone` followed by `CREATE UNIQUE INDEX <same name> ON employees (col) WHERE deleted_at IS NULL`. `uq_employees_user_id` stays a plain constraint.

**Rationale**: Live production catalog (`techno-terminal`, queried via pg_constraint/pg_indexes during planning) shows all four uniques are **table-level constraints** (`contype='u'`) whose backing indexes share the constraint name. Dropping the constraint drops its index cleanly; recreating as a partial index with the IDENTICAL name keeps `integrity_error_mapper.py` signals (`uq_employees_email` etc.) working unchanged.

**Alternatives considered**:
- Keep plain constraints and mangle values on delete — loses data integrity, breaks restore.
- New differently-named partial indexes without dropping constraints — impossible: both would enforce, deleted rows still blocked.
- Defensive DO-block probing catalog at migration time — unnecessary now that live state is verified; CI fresh DBs get the synced schema files directly.

## D2 — Deletion marker columns

**Decision**: `deleted_at TIMESTAMPTZ NULL`, `deleted_by INTEGER NULL REFERENCES users(id)`, mirroring `student_models.py:58-59`.

**Rationale**: Exact precedent exists in CRM students including the FK target and nullability; audit attribution (FR: actor) is a stated requirement.

**Alternatives considered**: Single `deleted JSONB` blob — over-engineered; boolean-only flag — loses when/who for audit.

## D3 — Duplicate probes ignore deleted rows

**Decision**: `get_by_national_id` / `get_by_phone` / `get_by_email` gain an unconditional `.where(Employee.deleted_at.is_(None))`.

**Rationale**: FR-006/FR-007 (re-hire). Probes are repository-level; filtering there fixes create AND update flows simultaneously with zero service changes.

**Alternatives considered**: Service-side post-filtering of probe results — duplicated logic across three call sites, easy to miss one.

## D4 — Staff accounts overview excludes deleted employees

**Decision**: `list_all_with_employees()` JOIN gains `Employee.deleted_at.is_(None)` in its WHERE.

**Rationale**: FR-002; the overview is an admin operational surface — a deleted employee's account must not appear manageable there.

**Alternatives considered**: Show with "deleted" badge — contradicts clarified spec decision (auto-block + hide).

## D5 — Auto-block reuses F-07 machinery

**Decision**: `delete_employee` calls existing `StaffAccountRepository.set_user_active(user_id, False)` inside the same UoW transaction, single commit at service end.

**Rationale**: Battle-tested path from feature 039 (deactivation hook); no new account-touching code needed. Idempotent for already-inactive accounts.

**Alternatives considered**: Supabase admin delete of auth user — out of scope; local-block pattern already proven to gate authentication (dependencies.py checks `user.is_active` → 403).

## D6 — `include_deleted` plumbing

**Decision**: Router `Query(include_deleted: bool = False)` → service `list_employees(page, page_size, include_deleted)` → repository branch skips the filter. `EmployeeReadDTO` gains optional `deleted_at`/`deleted_by` fields (None for live rows).

**Rationale**: Minimal surface change (no new endpoint); qualifier data rides the existing typed DTO per constitution III naming rules.

**Alternatives considered**: Dedicated `/deleted` trash endpoint — more surface for identical data; separate `DeletedEmployeeDTO` — duplicate DTO churn for two nullable fields.

## D7 — Restore collision detection

**Decision**: Before clearing markers, run the 039-built `_validate_unique_fields` aggregation against LIVE rows excluding the restored record itself; any collision → single `ConflictError("email: already in use; ...")` listing every colliding field together.

**Rationale**: Direct reuse of the field-named aggregated rejection pattern locked by feature 039 (F-01) and extended by clarification Q1; fail-before-mutate means no rollback complexity.

**Alternatives considered**: Let the partial index reject mid-flush — surfaces as IntegrityError translation with less precise messaging and wasted work; blank/mangle colliding values on restore — data loss, violates user's no-duplicates stance.

## D8 — Actor attribution

**Decision**: Router passes `current_user.id` (already returned by `require_admin`) into the service; `deleted_by` is set from it.

**Rationale**: Fail-closed edge case in spec: if the actor cannot be resolved, `require_admin` has already rejected the request upstream — `deleted_by` can never be unknown on a successful delete.

**Alternatives considered**: Resolving actor inside the service — inverted dependency on request context; forbidden by constitution I.

## D9 — Response contracts

**Decision**: `DELETE /{id}` → envelope `{success:true, data:true, message:"Employee deleted"}`. `POST /{id}/restore` → envelope carrying the restored full `EmployeeReadDTO` (with markers cleared). List flag leaves shape otherwise unchanged.

**Rationale**: Matches house conventions (tasks module deletes return `ApiResponse[bool]`); returning the restored record lets UIs confirm recovery without a second GET.

**Alternatives considered**: Returning archived snapshot on delete — no consumer need identified; restore returning bool only — weaker UX contract.

## D10 — Restore does not touch account activation

**Decision**: Restore clears ONLY the two deletion markers. A login auto-blocked at delete time stays blocked until an explicit `PUT {"is_active": true}`.

**Rationale**: Clarification locked pre-plan (spec FR-011); prevents surprise access re-grants.

**Alternatives considered**: Symmetric unblock on restore — silent access grant risk; explicitly rejected by spec.

## D11 — Test strategy

**Decision**: New `tests/test_hr_delete.py` covering the lifecycle matrix (delete→hidden everywhere / login blocked / rehire same triple succeeds / restore visible again / double-delete 404 / restore-live 409 / restore-collision 409 with all fields named / include_deleted flag + non-admin rejection / uniform 401s). Extend `test_hr_audit_regressions.py` with FR-007 lock (probes skip deleted). CI green requires `db/schema/02_tables_core.sql` + `20_indexes.sql` synced with the migration.

**Rationale**: One dedicated suite mirrors 039's finding-traceability style; schema sync prevents CI drift since it builds from `schema.sql` fresh.

**Alternatives considered**: Scattering tests across existing files — weaker traceability to FRs.

## D12 — Performance note

**Decision**: No additional indexes beyond the three partials.

**Rationale**: At ~20 employees every query is trivially fast; partial indexes keep uniqueness enforcement cost identical for the live set while shrinking index size as deletions accumulate.

**Alternatives considered**: Index on `deleted_at` — pointless at this scale.
