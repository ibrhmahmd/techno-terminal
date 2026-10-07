# Tasks: Self-Service Auth Features

**Input**: Design documents from `specs/015-self-service-auth/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test tasks are included within each user story phase (TDD: tests before implementation).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `app/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No project initialization needed. No new dependencies, config, or tooling required.

*No tasks in this phase.*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure needed by all user stories — DTOs, schema exports, imports.

- [X] T001 [P] Add `ChangePasswordInput`, `ForgotPasswordInput`, `UpdateProfileInput` DTOs to `app/modules/auth/schemas/auth_schemas.py`
- [X] T002 [P] Export new DTOs from `app/modules/auth/schemas/__init__.py` and `app/modules/auth/__init__.py`
- [X] T003 [P] Add `ChangePasswordRequest`, `ForgotPasswordRequest`, `UpdateProfileRequest` API DTOs to `app/api/schemas/auth.py`

**Checkpoint**: Foundation ready — DTOs defined and exported for all three endpoints.

---

## Phase 3: User Story 1 — Change Own Password (Priority: P1) 🎯 MVP

**Goal**: Authenticated users can change their own password by verifying current password and setting a new one.

**Independent Test**: Call `POST /api/v1/auth/change-password` with valid credentials — expect 200.

### Tests for User Story 1

- [X] T004 [P] [US1] Add `test_change_password_success` in `tests/test_auth.py` — mock `sign_in_with_password` to succeed, mock `admin.update_user_by_id`, verify 200
- [X] T005 [P] [US1] Add `test_change_password_wrong_current` in `tests/test_auth.py` — mock `sign_in_with_password` to raise, verify 401
- [X] T006 [P] [US1] Add `test_change_password_short_new` in `tests/test_auth.py` — provide `<12 char` password, verify 422
- [X] T007 [P] [US1] Add `test_change_password_unauthorized` in `tests/test_auth.py` — no token, verify 401

### Implementation for User Story 1

- [X] T008 [US1] Add `change_password(self, user: User, current_password: str, new_password: str) -> None` method to `AuthService` in `app/modules/auth/services/auth_service.py` — verify current via `sign_in_with_password`, set new via `admin.update_user_by_id`
- [X] T009 [US1] Add `POST /api/v1/auth/change-password` endpoint to `app/api/routers/auth_router.py` — inject `get_current_user`, call `auth_svc.change_password()`, return standard envelope

**Checkpoint**: US1 complete — users can change their own password.

---

## Phase 4: User Story 2 — Forgot Password / Reset Flow (Priority: P2)

**Goal**: Users can trigger Supabase's built-in password reset email via a public endpoint.

**Independent Test**: Call `POST /api/v1/auth/forgot-password` with an email — expect 200 (no email info leakage).

### Tests for User Story 2

- [X] T010 [P] [US2] Add `test_forgot_password_success` in `tests/test_auth.py` — mock `reset_password_email`, verify 200
- [X] T011 [P] [US2] Add `test_forgot_password_unregistered_email` in `tests/test_auth.py` — still returns 200 (no-info-leakage)
- [X] T012 [P] [US2] Add `test_forgot_password_no_email` in `tests/test_auth.py` — empty/invalid email, verify 422

### Implementation for User Story 2

- [X] T013 [US2] Add `forgot_password(self, email: str) -> None` method to `AuthService` in `app/modules/auth/services/auth_service.py` — call `get_supabase_anon().auth.reset_password_email(email)`, catch all exceptions (no-info-leakage)
- [X] T014 [US2] Add `POST /api/v1/auth/forgot-password` endpoint to `app/api/routers/auth_router.py` — no auth required, call `auth_svc.forgot_password()`, return 200 always

**Checkpoint**: US2 complete — forgot-password flow works without email enumeration.

---

## Phase 5: User Story 3 — Update Own Profile (Priority: P2)

**Goal**: Authenticated users can update their own username via PATCH endpoint.

**Independent Test**: Call `PATCH /api/v1/auth/me` with a new username — expect 200 with updated `UserPublic`.

### Tests for User Story 3

- [X] T015 [P] [US3] Add `test_update_profile_success` in `tests/test_auth.py` — mock `AuthService.update_profile`, verify 200 with updated username
- [X] T016 [P] [US3] Add `test_update_profile_duplicate_username` in `tests/test_auth.py` — mock repo to raise `ConflictError`, verify 409
- [X] T017 [P] [US3] Add `test_update_profile_unauthorized` in `tests/test_auth.py` — no token, verify 401

### Implementation for User Story 3

- [X] T018 [US3] Add `update_profile(self, user: User, dto: UpdateProfileInput) -> User` method to `AuthService` in `app/modules/auth/services/auth_service.py` — update username via repo `update_user`, catch duplicate constraint violation
- [X] T019 [US3] Add `PATCH /api/v1/auth/me` endpoint to `app/api/routers/auth_router.py` — inject `get_current_user`, call `auth_svc.update_profile()`, return updated `UserPublic`

**Checkpoint**: US3 complete — users can update their own profile.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verification that all endpoints work together, final test run.

- [X] T020 Run `pytest tests/test_auth.py -v` — all tests pass
- [X] T021 [P] Verify imports: `py -c "from app.modules.auth import ChangePasswordInput, ForgotPasswordInput, UpdateProfileInput"` — no import errors
- [X] T022 [P] Verify server starts: `py -c "from app.api.main import create_app; app = create_app()"` — no import errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: No dependencies — DTOs can be created immediately
- **US1 (Phase 3)**: Depends on Phase 2 (DTOs) + T001, T003
- **US2 (Phase 4)**: Depends on Phase 2 (DTOs) — independent of US1
- **US3 (Phase 5)**: Depends on Phase 2 (DTOs) — independent of US1/US2
- **Polish (Phase 6)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: MVP — independent
- **US2 (P2)**: Independent of US1 (different endpoint, different auth requirement)
- **US3 (P2)**: Independent of US1/US2 (different endpoint)

### Within Each User Story

- Tests should be written and verified to fail (or be skipped) before implementation
- Service method before endpoint
- Story complete before moving to next priority

### Parallel Opportunities

- All Foundational tasks marked [P] can run in parallel
- All stories can be implemented in parallel once Phase 2 completes
- All tests within a story marked [P] can run in parallel

---

## Parallel Example

```bash
# Phase 2 — DTOs (all parallel):
Task: T001 "Module DTOs"
Task: T002 "Schema exports"
Task: T003 "API DTOs"

# All 3 stories can run in parallel after Phase 2:
Task: T004-T009 "US1 — Change password"
Task: T010-T014 "US2 — Forgot password"
Task: T015-T019 "US3 — Update profile"

# Final verification:
Task: T020-T022 "Polish & verification"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 2: DTOs
2. Complete Phase 3: US1 — Change password
3. **STOP and VALIDATE**: Test independently
4. Deploy/demo if ready

### Incremental Delivery

1. US1 (P1) → Deploy/Demo (MVP — self-service password change)
2. US2 (P2) → Deploy/Demo (forgot password flow)
3. US3 (P2) → Deploy/Demo (profile management)

### Parallel Team Strategy

- Developer A: US1 (P1 — MVP)
- Developer B: US2 (P2)
- Developer C: US3 (P2)
- All converge on Polish phase

---

## Notes

- 22 total tasks across 5 phases
- No new models or migrations required
- All endpoints reuse existing `AuthService` stateless pattern
- US2 (forgot-password) is the only public endpoint — no auth required
- US1 and US3 require `get_current_user` (any active user)
