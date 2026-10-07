# API Contracts: Staff Onboarding Endpoints

**Feature**: 039-audit-employee-creation | **Date**: 2026-08-23

Contracts for the four in-scope endpoints. All responses use the standard envelope
`{"success": bool, "data": ..., "message": ..., "error": ...}`. All require
`Authorization: Bearer <jwt>` with an `admin` or `system_admin` role.

Error taxonomy (envelope `error` field = exception class name):

| Outcome | error | HTTP |
|---------|-------|------|
| Record/identifier not found | NotFoundError | 404 |
| Field format/validation problem, credential rules | ValidationError | 422 |
| Duplicate identifier, email registered, already-has-account | ConflictError | 409 |
| Remote provisioning unavailable (non-conflict failure) | BusinessRuleError | 409 |

---

## POST /api/v1/hr/employees — Create employee

Request body (`EmployeeCreateInput`): full_name*, phone* (≥10 digits), national_id*
(≥10 chars), university*, major*, email?, is_graduate?=false, job_title?,
employment_type?=`full_time|part_time|contract` (default full_time),
monthly_salary?, contract_percentage?, is_active?=true

Responses:

- **201** envelope with created `EmployeePublic` — every submitted value round-trips exactly.
- **409** ConflictError — message names EVERY colliding identifier at once:
  `"national_id: already in use; phone: already in use"` (aggregated reporting).
  Same 409 class when a concurrent insert wins the race (DB constraint translated to a named-field conflict; never a raw 500).
- **422** ValidationError — all invalid fields named together in one message.
- **401/403** for missing/invalid/non-admin auth on every staff endpoint uniformly.

## PUT /api/v1/hr/employees/{employee_id} — Update employee

Same input schema, all fields optional. Partial payloads accepted.

- **200** envelope with updated `EmployeePublic`.
- **404** unknown id.
- **409** aggregated conflicts excluding the target employee's own current values.
- **422** validation problems — including contract-rule protection: setting/changing
  employment data never produces a state where a non-contract employee carries
  contract_percentage.
- Deactivating (`is_active: true → false`) an employee who owns an account also
  blocks that account automatically (observable via subsequent GET of staff accounts:
  `is_active: false`).

## POST /api/v1/hr/employees/{employee_id}/create-account — Provision login

Request body: email* (must be syntactically valid), password* (≥12 chars — exceeds the 8-char floor), role* (`admin|system_admin`).

Outcomes:

- **201** `EmployeeAccountResponse{employee_id, user_id, email, role, created_at}`.
- **404** employee not found.
- **409** one of, each explicitly distinguished:
  - employee already has an account;
  - email already registered as an identity;
  - provisioning service temporarily unavailable — message states nothing was
    created and a retry may succeed (BusinessRuleError class). Zero partial state in
    every failure case: no orphaned remote identity, no half-linked local rows.
- **422** per-field credential violations (email syntax, password length) — rejected
  before any remote call.

## GET /api/v1/hr/staff-accounts — Accounts overview

- **200** envelope with a list where every entry includes complete fields:
  `{user_id, username(email), role, is_active, employee_id, full_name, phone,
  employee_email, job_title, created_at}` — no permanent null placeholders for
  fields the underlying data provides.
