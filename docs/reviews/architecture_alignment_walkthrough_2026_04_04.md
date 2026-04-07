# Architecture Alignment Walkthrough - 2026-04-04

## Purpose

This document explains the cleanup pass completed on 2026-04-04 across:

- role handling
- finance router/service/repository/DTO alignment
- academics session router architecture
- memory bank documentation refresh

The goal of this pass was not to add new product features. It was to bring the codebase back into alignment with the intended architecture and with the current domain rules already agreed for the project.

---

## Change Summary

### 1. Role System Alignment

The application has already been simplified to two valid roles only:

- `admin`
- `system_admin`

The cleanup pass reinforced that rule in code and documentation.

#### What changed

- Updated stale dependency comments in `app/api/dependencies.py` so the documented API guards now match the real code.
- Removed live BI analytics dependence on the deleted `instructor` auth role.

#### Why this mattered

Some code and docs had already moved to the two-role model, but analytics still contained SQL predicates like `u.role = 'instructor'`.

That created a real behavior bug:

- instructor metrics could silently return incomplete or empty data
- the app concept of “person teaching groups” had drifted away from the auth-role model

#### How it works now

Instructor analytics now derive from real teaching assignments and active employees instead of deleted auth roles:

- `groups.instructor_id`
- `employees.is_active`

#### Files changed

- `app/api/dependencies.py`
- `app/modules/analytics/repositories/bi_repository.py`
- `app/modules/analytics/analytics_repository.py`

---

### 2. Finance Module Review and Fixes

The finance pass reviewed the stack from API router through schemas, service logic, and repository queries.

#### Main issues found

##### A. Refund helper call used stale naming

`issue_refund()` called `_open_receipt_in_session()` with `parent_id=None`, but the helper expects `payer_name`.

This was a hard runtime bug in the refund path.

##### B. Refund rules were too weak

The previous flow did not block:

- refunding a refund line
- refunding more than the original amount

Both can corrupt financial history and balances.

##### C. Receipt PDF flow still used old CRM assumptions

The code still assumed a direct `student.parent_id` relationship when building the receipt PDF.

That no longer matches the CRM model, which uses:

- `student_parents`
- `is_primary`

##### D. Router treated receipt detail like an object instead of a dict

The PDF download endpoint called `get_receipt_detail()` and then accessed:

- `receipt.receipt_number`

But the finance service returns a dictionary structure:

- `{"receipt": ..., "lines": ..., "total": ...}`

That mismatch could break filename generation.

##### E. DTO/query naming drift

Search query rows used `parent_name` in SQL output while the API schema uses `payer_name`.

There was also drift between:

- `discount_amount` in persistence/model output
- `discount` in API DTO output

#### What changed

##### Refund path

- Fixed `_open_receipt_in_session()` call to use `payer_name`
- Added a guard preventing refunds against refund lines
- Added a guard preventing refund amounts larger than the original payment
- Normalized `new_balance` to `float`

##### PDF path

- Added `get_primary_parent_name_for_student()` in the finance repository
- Switched PDF parent lookup to the `student_parents` junction table
- Fixed the router filename generation to read from the receipt detail dict correctly

##### Schema and query alignment

- Changed finance search/list SQL output to use `payer_name`
- Updated receipt line output DTO to accept `discount_amount` from persistence and expose it as `discount`
- Tightened finance request DTOs so payment method and payment type use the shared domain literals

#### Why this mattered

Finance had become one of the areas with the most architectural drift:

- mixed old and new naming
- mixed old and new CRM relationship assumptions
- weak validation on a sensitive path

This pass did not fully refactor finance into class-based services, but it removed the most dangerous inconsistencies and brought it closer to the standards already used in newer modules.

#### Files changed

- `app/api/routers/finance_router.py`
- `app/api/schemas/finance/receipt.py`
- `app/modules/finance/finance_schemas.py`
- `app/modules/finance/finance_repository.py`
- `app/modules/finance/finance_service.py`

---

### 3. Academics Sessions Router Refactor

One endpoint in the academics router was bypassing the module architecture:

- `GET /academics/sessions/{session_id}`

#### Old behavior

The router directly imported:

- `get_session`
- `CourseSession`

and queried the DB itself.

That violated the codebase architecture:

- router
- service
- repository
- model

#### Why this was a problem

This creates long-term drift because:

- validation logic becomes split between router and service
- error handling becomes inconsistent
- future changes to session retrieval must be made in two places

#### New behavior

The direct DB lookup was moved into the academics service layer:

- added `SessionService.get_session_by_id()`
- router now depends on the service only
- repository access stays inside the module layer

This restores the expected boundary:

- router -> service -> repository

#### Files changed

- `app/api/routers/academics/sessions.py`
- `app/modules/academics/services/session_service.py`
- `app/modules/academics/__init__.py`

---

### 4. Memory Bank Refresh

The documentation update focused on making the memory bank safe to use as a current handoff source again.

#### Main corrections

- updated the memory bank date
- corrected daily schedule docs from `day=...` to `target_date=...`
- corrected finance workflow naming from `parent_id` to `payer_name`
- documented that Phase 5 router implementation is live, not merely planned
- documented that finance and HR still use flatter service-module patterns than academics and competitions
- refreshed active context to reflect the current cleanup work rather than the old “testing just finished” state

#### Files changed

- `docs/MEMORY_BANK.md`
- `memory-bank/systemPatterns.md`
- `memory-bank/activeContext.md`

---

## Detailed File Walkthrough

### `app/api/dependencies.py`

Only comment/documentation cleanup was applied here. The runtime guard behavior was already correct, but the explanatory header still referenced removed role ideas.

This matters because future agents and engineers often use this file first to understand access control.

### `app/modules/analytics/repositories/bi_repository.py`

Two BI queries were updated:

- `get_instructor_performance()`
- `get_instructor_value_matrix()`

Instead of filtering on a deleted auth role, both now infer instructors from active employees who are actually assigned to groups.

### `app/modules/finance/finance_service.py`

This file carried the most important correctness fixes:

- refund argument mismatch fixed
- refund-over-refund prevented
- oversized refund prevented
- PDF parent lookup corrected
- returned balance normalized to float

### `app/modules/finance/finance_repository.py`

This file was adjusted to support the corrected finance behavior:

- receipt search/list rows now use `payer_name`
- added `get_primary_parent_name_for_student()`

### `app/api/schemas/finance/receipt.py`

This file now better reflects actual service/repository output:

- request `method` uses `PaymentMethod`
- `ReceiptLinePublic` maps `discount_amount` into `discount`
- `ReceiptListItem` matches the repository output shape

### `app/api/routers/academics/sessions.py`

The session detail endpoint no longer owns persistence logic.

This is the core architecture fix from the academics side of the pass.

---

## What Was Verified

### Passed

- Python compile validation for all touched Python files via `py_compile`
- focused schema validation for the updated finance DTO mapping

### Blocked

The broader API pytest run was blocked by external auth in this sandbox.

Observed limitation:

- request auth attempted live Supabase JWT validation
- sandbox/network limits caused `ConnectError`
- tests therefore failed at the auth boundary with `401` before reaching most endpoint logic

So the current verification status is:

- syntax/import safety: verified
- DTO mapping sanity: verified
- full integration behavior: not fully verified in this sandbox

---

## Remaining Follow-Up

### Recommended next cleanup

1. Refactor finance from flat module-style service functions into the same class-based pattern used by academics and competitions.
2. Add regression tests for:
- refunding a refund line
- refunding more than the original payment
- finance PDF generation when parent data is linked through `student_parents`
- session detail endpoint behavior after the router refactor
3. Consider reducing duplicate legacy analytics SQL in `app/modules/analytics/analytics_repository.py` if that module is no longer a real runtime dependency.

### Important note

This pass intentionally avoided broad refactors beyond the requested scope. The emphasis was:

- fix real bugs
- restore architectural boundaries
- align the docs with the actual codebase

---

## Net Result

After this pass:

- the two-role model is more consistently enforced
- finance no longer mixes several stale assumptions from older schema shapes
- the academics sessions router no longer bypasses the module architecture
- the memory bank is materially closer to the real implementation
