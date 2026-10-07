# Implementation Plan: Fix Course Creation Persistence & Data Integrity

**Branch**: `main` | **Date**: 2026-05-14 | **Spec**: specs/006-daily-report-fixes/spec.md
**Input**: Bug analysis from code review of `app/modules/academics/course/service.py`

## Summary

Three bugs in `CourseService` prevent course data from persisting to the database:
1. **Missing `session.commit()`** in `add_new_course()` — API returns 201 but course is never committed, transaction rolls back on session close.
2. **Missing `notes` propagation** — `AddNewCourseInput.notes` is accepted by the schema but silently dropped from the `Course()` constructor.
3. **Missing `session.commit()`** in `update_course_price()` — same root cause as Bug 1: price changes return 200 but never commit.

All fixes have been applied. Remaining work: add persistence-verification tests to close the test gap.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, SQLModel, SQLAlchemy 2.0  
**Storage**: PostgreSQL via SQLAlchemy `Session` with `engine.begin()` / context-managed sessions  
**Testing**: pytest with `TestClient`, real Supabase JWT for `admin_headers`  
**Target Platform**: Linux server (Leapcell)  
**Project Type**: Web service (REST API)  
**Performance Goals**: N/A (bug fix, no new perf targets)  
**Constraints**: `get_session()` context manager auto-rollbacks on close if no explicit `commit()` — this was the root cause  
**Scale/Scope**: 1 service file, 2 test methods to update

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **III. Typed Contracts**: `add_new_course()` returns `Course` (ORM model) — no bare dicts. No violation.
- [x] **I. Layer Separation**: Router → Service → Repository is respected. Service owns session lifecycle. No violation.
- [x] **II. Stateless Pattern**: `CourseService` creates own `get_session()` — consistent with AGENTS.md stateless pattern for Academics module. No violation.
- [x] **IV. Domain Exceptions**: `ConflictError` for duplicate names, `NotFoundError` for missing courses. Correct usage.
- [x] **VI. Session Lifecycle**: Bug was precisely that the `get_session()` context manager was not being committed before exit. Fix aligns with documented behavior.

**Gate result**: PASS — no constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/006-daily-report-fixes/
├── plan.md              # This file
└── research.md          # Bug analysis from code review
```

### Source Code (repository root)

```text
app/modules/academics/course/
├── service.py           # FIXED: added session.commit() + session.refresh(), notes propagation

tests/
└── test_academics_courses.py  # TO UPDATE: add persistence verification
```

**Structure Decision**: Single project (Python FastAPI monolith), no structural changes needed.

## Complexity Tracking

> No constitution violations — section not required.

## Phase 0: Outline & Research

Research is complete — bugs were identified through code tracing in the previous session. No NEEDS CLARIFICATION items remain.

### Research Artifacts

**Bug 1 — Missing commit in `add_new_course()`**:
- Root cause: `get_session()` context manager auto-rollbacks on `Session.close()` if no explicit `session.commit()` was called.
- Fix: Added `session.commit()` + `session.refresh(course)` after `repo.create_course()`.
- Test gap: `test_create_course_success` only checks POST response body, not subsequent GET.

**Bug 2 — Notes field silently dropped**:
- Root cause: Constructor at line 23 omitted `data.notes`.
- Fix: Added `notes=data.notes` to `Course()` constructor call.

**Bug 3 — Missing commit in `update_course_price()`**:
- Root cause: Same as Bug 1 — no `session.commit()` after mutation.
- Fix: Added `session.commit()` + `session.refresh(course)`.

## Phase 1: Design & Contracts

No new entities or interfaces needed — this is a bug fix. The changes are confined to existing methods within the same class.

### Data Model

No model changes. `Course` model at `app/modules/academics/models/course_models.py` remains unchanged.

### Contracts

No contract changes. The `CourseServiceInterface` protocol is unchanged — same public methods, same signatures.

### Test Plan

The following tests need updating in `tests/test_academics_courses.py`:

1. **`test_create_course_success`**: After POST, add a GET to verify the course is actually in the database and the data round-trips correctly (name, category, price, notes).

2. **`test_create_course_with_notes`** (new): Create a course with explicit `notes` field, verify notes are returned in both POST response and subsequent GET.

3. **`test_update_course_price_persists`** (new): Update price via PATCH, then GET the course and verify the new price is returned.

4. **`test_create_course_boundary_price`**: This test currently accepts both 201 and 422 for `price_per_level=0`. Since the validator (`validate_positive_amount`) rejects <=0, this should be 422. Consider tightening.
