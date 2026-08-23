# Data Model: Employee Creation Endpoint Audit & Fixes

**Feature**: 039-audit-employee-creation | **Date**: 2026-08-23
No schema changes. Existing entities, their constraints, and the state rules this feature enforces.

## Entities

### Employee (existing — `employees` table)

A staff member record. Owned by the HR module (`app/modules/hr/models/employee_models.py`), DDL in `db/schema/02_tables_core.sql`.

| Field | Type | Rules |
|-------|------|-------|
| id | SERIAL PK | |
| full_name | TEXT NOT NULL | 2–100 chars at input boundary |
| phone | TEXT NOT NULL | **UNIQUE** (`uq_employees_phone`); digits-only normalized; ≥10 digits pattern at input |
| email | TEXT NULL | **UNIQUE** (`uq_employees_email`); NULLs don't collide (Postgres semantics) → "email optional but must not collide when present"; syntactic validity enforced at account-provisioning input (D9) |
| national_id | TEXT NOT NULL | **UNIQUE** (`uq_employees_national_id`); ≥10 chars at input (effective limit — see research D10) |
| university / major | TEXT NOT NULL | |
| is_graduate | BOOLEAN | default false |
| job_title | TEXT NULL | surfaced in staff accounts overview after FR-010 fix |
| employment_type | TEXT NOT NULL | CHECK: `full_time \| part_time \| contract` |
| monthly_salary / contract_percentage | NUMERIC NULL | CHECK `employees_contract_pct_check`: percentage only when type = 'contract' (update-path normalization fix D6 protects this) |
| is_active | BOOLEAN | True→False transition triggers linked-account block (FR-011, D7) |
| hired_at / created_at / updated_at | DATE/TIMESTAMPTZ | |
| metadata | JSONB | |
| user_id | INT NULL FK→users.id | **UNIQUE** (`uq_employees_user_id`) — one active login link max |

### User / Staff Account (existing — `users` table, managed via auth + HR modules)

Login identity linked to at most one employee.

| Field | Type | Rules |
|-------|------|-------|
| id | SERIAL PK | |
| username | TEXT NOT NULL UNIQUE | stores the account email for staff accounts |
| supabase_uid | TEXT NULL UNIQUE | remote identity handle; compensation deletes the remote record on local failure (D4) |
| role | TEXT NOT NULL | CHECK: `admin \| instructor \| system_admin`; provisioning endpoint currently allows only admin/system_admin (accepted-risk finding F-10) |
| is_active | BOOLEAN | set false automatically when linked employee deactivates (FR-011) |
| employee_id | INT NULL FK→employees.id ON DELETE SET NULL | reverse side of the 1:1 link |
| last_login / created_at / invite_* | | created_at surfaces in accounts overview after FR-010 fix |

**Link invariant**: exactly one active account per employee, enforced jointly by `uq_employees_user_id` + service-level already-has-account check (F-class fixes keep both layers honest).

### Finding (new — documentation artifact only, `specs/039-audit-employee-creation/findings.md`)

Audit catalog entry; no database representation.

| Field | Rules |
|-------|-------|
| id | F-NN, mirrors regression test IDs |
| severity | ERROR (blocks/breaks flow) \| WARNING (wrong/misleading behavior) \| INFO (hygiene/polish) |
| affected_behavior / evidence / reproduction_steps / resolution_status | fixed or accepted-risk with rationale |

## State Transitions

```text
Employee.is_active:  true ──(admin update)──▶ false
                              │
                              └─▶ linked User.is_active := false   [FR-011, automatic]

Account provisioning (per employee):
  no account ──(create-account OK)──▶ linked account          [user row + employee.user_id set]
  no account ──(remote failure)────▶ no account               [nothing persisted; clear retry message]
  no account ──(local failure post-remote)──▶ no account      [remote identity compensated/deleted; rollback]
  linked ─────(create-account again)──▶ refused (409)         [already has an account]
```

## Integrity Rules Enforced by This Feature

1. Uniqueness of national_id / phone / email checked independently, reported together, race-safe via DB constraints translated to typed conflicts (D1/D2).
2. Zero partial state across any failure midpoint (D3/D4/D5).
3. Contract employees exclusively carry contract_percentage (update path included — D6).
4. Deactivated employee ⇒ blocked login (D7).
