# Tasks: Auth Module Bug Fixes & Audit Remediation

**Input**: Design documents from `specs/014-auth-audit-fixes/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test tasks are included in US4 (test coverage). Individual stories include test tasks where appropriate.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `app/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No project initialization needed — this is a bug-fix/cleanup feature within an existing codebase. No new dependencies, config, or tooling required.

*No tasks in this phase.*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No blocking infrastructure changes needed. Each user story is independently implementable within its own files.

*No tasks in this phase.*

---

## Phase 3: User Story 1 — Fix Runtime Bugs (Priority: P1) 🎯 MVP

**Goal**: Fix 3 runtime bugs: orphaned Supabase identity on failed user creation, email leakage via debug print, and unreachable dead code after raise in login endpoint.

**Independent Test**: Call `POST /api/v1/auth/users` with valid data but cause a local DB failure — verify Supabase user is cleaned up. Check login endpoint no longer prints emails to stdout.

### Implementation for User Story 1

- [X] T001 [P] [US1] Remove unreachable `print(f"Login attempt: email={body.email}")` and commented-out `print(f"Supabase URL: {settings.SUPABASE_URL}")` in `app/api/routers/auth_router.py:58-60`
- [X] T002 [US1] Add orphan cleanup to `link_employee_to_new_user` in `app/modules/auth/services/auth_service.py:71-90` — wrap local DB insert in try/except, call `admin.auth.admin.delete_user(supabase_uid)` on failure, re-raise the original exception

**Checkpoint**: User Story 1 complete ✅ — no more orphaned Supabase identities, no email leakage, no unreachable code.

---

## Phase 4: User Story 2 — Secure Password Reset for Inactive Users (Priority: P2)

**Goal**: Add inactive-user guard to `force_reset_password` so deactivated accounts cannot have their passwords reset.

**Independent Test**: Call `POST /api/v1/auth/users/{id}/reset-password` with a user where `is_active = False` — expect `409 BusinessRuleError`.

### Implementation for User Story 2

- [X] T003 [US2] Add inactive user check to `force_reset_password` in `app/modules/auth/services/auth_service.py:32-47` — after verifying user exists, check `if not user.is_active: raise BusinessRuleError(...)` before calling Supabase admin update

**Checkpoint**: User Story 2 complete ✅ — deactivated users are protected from password reset.

---

## Phase 5: User Story 3 — Remove Dead Code & Fix Architecture Violations (Priority: P2)

**Goal**: Remove 4 dead code items, fix `create_user` to accept typed DTO, add `ConfigDict` to DTOs, fix import paths.

**Independent Test**: Grep for removed symbols returns nothing. `create_user` accepts `UserCreate` not `dict`. DTOs have `from_attributes=True`. Imports use module root.

### Implementation for User Story 3

- [X] T004 [P] [US3] Remove `get_users_for_employee` method from `app/modules/auth/services/auth_service.py:28-30`
- [X] T005 [P] [US3] Remove `update_user` function from `app/modules/auth/repositories/auth_repository.py:30-38`
- [X] T006 [P] [US3] Remove `update_user` from imports and `__all__` in `app/modules/auth/repositories/__init__.py`
- [X] T007 [P] [US3] Remove `PasswordResetBody` class from `app/modules/auth/schemas/auth_schemas.py:13-15`
- [X] T008 [P] [US3] Remove `UserRead` class from `app/modules/auth/schemas/auth_schemas.py:21-26`
- [X] T009 [P] [US3] Remove `PasswordResetBody` and `UserRead` from imports and `__all__` in `app/modules/auth/schemas/__init__.py`
- [X] T010 [P] [US3] Remove `get_users_for_employee` alias and `UserRead` from imports and `__all__` in `app/modules/auth/__init__.py`
- [X] T011 [US3] Change `create_user(session, user_data: dict)` to `create_user(session, data: UserCreate)` in `app/modules/auth/repositories/auth_repository.py:18` — update call site in `auth_service.py:90` to pass `user_in` directly instead of `user_in.model_dump()`
- [X] T012 [P] [US3] Add `model_config = ConfigDict(from_attributes=True)` to `UserCreate` and `UserPublic` in `app/modules/auth/schemas/auth_schemas.py`
- [X] T013 [P] [US3] Fix `AuthService` import in `app/api/routers/auth_router.py:31` — change from `app.modules.auth.services.auth_service` to `app.modules.auth`
- [X] T014 [P] [US3] Fix `AuthService` import in `app/api/dependencies.py:121` — change from `app.modules.auth.services.auth_service` to `app.modules.auth`

**Checkpoint**: User Story 3 complete ✅ — dead code gone, typed DTO in repo, DTOs compliant, import paths fixed.

---

## Phase 6: User Story 4 — Add Missing Auth Tests (Priority: P2)

**Goal**: Add test coverage for all 5 untested auth endpoints. Fix 2 broken tests.

**Independent Test**: Run `pytest tests/test_auth.py -v` — all auth endpoint paths pass, coverage >90%.

### Implementation for User Story 4

- [X] T015 [US4] Fix `test_hr_employees_requires_auth` in `tests/test_auth.py:104` — add missing assertion `assert response.status_code == 401`
- [X] T016 [US4] Fix `test_enrollments_requires_auth` in `tests/test_auth.py:106` — change URL to `/api/v1/enrollments` and add assertion
- [X] T017 [US4] Add `test_login_success` — mock `get_supabase_anon().auth.sign_in_with_password` to return valid session, verify 200 + TokenResponse shape
- [X] T018 [US4] Add `test_login_invalid_credentials` — mock `sign_in_with_password` to raise exception, verify 401
- [X] T019 [US4] Add `test_create_login_user_success` — mock `get_supabase_admin().auth.admin.create_user` + `override_auth`, verify 200 + UserPublic shape
- [X] T020 [US4] Add `test_refresh_token_success` — mock `refresh_session` to return valid session, verify 200
- [X] T021 [US4] Add `test_refresh_token_invalid` — mock `refresh_session` to raise, verify 401
- [X] T022 [US4] Add `test_logout_success` — mock `sign_out`, verify 200
- [X] T023 [US4] Add `test_reset_password_success` — mock `admin.update_user_by_id`, verify 200
- [X] T024 [US4] Add `test_reset_password_inactive_user` — call with deactivated user, verify 409 BusinessRuleError

**Checkpoint**: User Story 4 complete ✅ — all 5 untested endpoints now covered, broken tests fixed.

---

## Phase 7: User Story 5 — Fix `User.is_admin` Property (Priority: P3)

**Goal**: Replace hardcoded string literals in `is_admin` with enum references.

**Independent Test**: Check the property references `UserRole.ADMIN.value` and `UserRole.SYSTEM_ADMIN.value`.

### Implementation for User Story 5

- [X] T025 [US5] Fix `is_admin` property in `app/modules/auth/models/auth_models.py:33-34` — change `return self.role in ("admin", "system_admin")` to `return self.role in (UserRole.ADMIN.value, UserRole.SYSTEM_ADMIN.value)`

**Checkpoint**: User Story 5 complete ✅ — no hardcoded role strings.

---

## Phase 8: User Story 6 — Fix Logout Error Handling (Priority: P3)

**Goal**: Replace silent `except: pass` in logout endpoint with proper error logging.

**Independent Test**: Inspect logout handler — exceptions from `sign_out` are logged via the application logger.

### Implementation for User Story 6

- [X] T026 [US6] Fix logout error handling in `app/api/routers/auth_router.py:119-127` — replace `except: pass` with `except Exception as e: logger.warning("Supabase logout failed: %s", e)`, add `import logging` at top of file, use the existing module-level logger or create one

**Checkpoint**: User Story 6 complete ✅ — logout errors are logged, not swallowed.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Verification that all fixes work together, final validation pass.

- [X] T027 [P] Run `pytest tests/test_auth.py -v` — **20/20 pass**
- [X] T028 [P] Verify dead code removal: grep for `get_users_for_employee|update_user|PasswordResetBody|UserRead` — zero matches (only `update_user_by_id` — Supabase API — is a false positive)
- [X] T029 [P] Verify no dict types: `grep -r "-> dict" app/modules/auth/repositories/` — zero matches
- [X] T030 [P] Verify no direct service imports: `grep -r "from app.modules.auth.services" app/api/` — zero matches
- [X] T031 [P] Verify module imports: `py -c "import app.modules.auth; from app.modules.auth import AuthService, User, UserCreate, UserPublic"` — OK, `UserCreate.model_config` has `from_attributes=True`
- [X] T032 Run `pytest tests/ -v` — full suite pass confirmed

---

## Dependencies & Execution Order

### Phase Dependencies

- **US1 (Phase 3)**: No dependencies — can start immediately
- **US2 (Phase 4)**: No dependencies on other stories — independent
- **US3 (Phase 5)**: No dependencies — independent (files don't overlap with US1/US2)
- **US4 (Phase 6)**: Depends on US1, US2, US3 being complete (tests validate fixed code)
- **US5 (Phase 7)**: No dependencies — independent
- **US6 (Phase 8)**: No dependencies — independent
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: MVP — fix runtime bugs first
- **US2 (P2)**: Independent of US1 (different code path)
- **US3 (P2)**: Independent of US1/US2 (different files)
- **US4 (P2)**: Depends on US1, US2, US3 (tests must validate fixed code)
- **US5 (P3)**: Independent of all others
- **US6 (P3)**: Independent of all others

### Within Each User Story

- All tasks are implementation-only (no tests to write first)
- Tasks marked [P] can run in parallel within the same story
- No sequential dependencies within stories (all tasks are independent edits)

### Parallel Opportunities

- US1, US2, US3, US5, US6 can all run in parallel (different files, no conflicts)
- US4 must wait for US1, US2, US3
- Polish phase must wait for all stories

---

## Parallel Example: Maximum Parallelism

```bash
# Launch all independent stories in parallel:
Task: T001-T002 "US1 — Fix runtime bugs"
Task: T003 "US2 — Secure password reset"
Task: T004-T014 "US3 — Dead code + architecture violations"
Task: T025 "US5 — is_admin property"
Task: T026 "US6 — Logout error handling"

# After all above complete, launch tests:
Task: T015-T024 "US4 — Add missing tests"

# Final polish:
Task: T027-T032 "Polish & verification"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 3: US1 — Runtime bugs
2. **STOP and VALIDATE**: Verify orphan cleanup works, no email leakage
3. Deploy if ready — these are the highest-severity fixes

### Incremental Delivery

1. US1 (P1) → Deploy/Demo (MVP — runtime bugs fixed)
2. US2 (P2) → Deploy/Demo (security hardening)
3. US3 (P2) → Deploy/Demo (code quality)
4. US4 (P2) + US5 (P3) + US6 (P3) → Deploy/Demo (test coverage + remaining fixes)
5. Polish → Final validation

### Parallel Team Strategy

With multiple developers:
- Developer A: US1 (P1) + US4 (tests for US1)
- Developer B: US3 (P2) architecture fixes
- Developer C: US2 (P2) + US5 (P3) + US6 (P3)
- All converge on US4 tests then Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- 32 total tasks across 7 phases
- US4 (tests) is intentionally last among P2 stories — tests validate the fixed code
- Commit after each phase or logical group
