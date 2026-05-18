# Tasks: Competition Module Enhancements

**Input**: Design documents from `specs/010-competition-feature-enhancements/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/overview.md

**Tests**: Included — existing test suite must be updated to reflect hard delete and new payment model.

**Organization**: Tasks organized by user story priority (P1 → P2 → P3). Each story is independently implementable and testable after the foundational phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project at repository root
- Models: `app/modules/competitions/models/`
- Repositories: `app/modules/competitions/repositories/`
- Services: `app/modules/competitions/services/`
- Schemas (module): `app/modules/competitions/schemas/`
- Schemas (API): `app/api/schemas/competitions/`
- Routers: `app/api/routers/competitions/`
- Tests: `tests/`
- Migrations: `db/migrations/`

---

## Phase 1: Database Migration (Blocking Prerequisite)

**Purpose**: Schema changes that ALL user stories depend on. Must be applied before any code changes.

- [x] T001 Create migration `db/migrations/054_competition_hard_delete_and_payment_model.sql` per data-model.md (drop GroupCompetitionParticipation, add project_name/project_description to teams, replace fee_paid/payment_id with amount_due/amount_paid on team_members, add team_member_id to payments, drop deleted_at/deleted_by from competitions and teams)
- [ ] T002 Apply migration to Supabase and verify schema changes (run `supabase_apply_migration` or `psql`, then verify columns via `SELECT column_name FROM information_schema.columns WHERE table_name IN ('competitions','teams','team_members','payments')`)
- [ ] T063 Remove `GroupCompetitionParticipation` model from `app/modules/academics/models/group_level_models.py`, remove exports from `app/modules/academics/models/__init__.py`, delete entire `app/modules/academics/group/competition/` slice (service, repository, interface), update `app/modules/academics/group/analytics/repository.py` to remove joins against GroupCompetitionParticipation
- [ ] T064 Run `pytest tests/test_competitions.py -v` — all tests pass (regenerate JWT via `python scripts/get_test_jwt.py` if expired, update `admin_token` in `tests/conftest.py`)
- [ ] T065 Verify `tests/test_academics_competitions.py` is deleted or updated (file should not exist after T063 dead code removal)
- [ ] T066 Run `pytest tests/ -v` — full suite passes (no regressions from migration or dead code removal)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core model, schema, and dead code changes that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Model Updates (Parallel)

- [ ] T003 [P] Update Competition model in `app/modules/competitions/models/competition_models.py` — remove `deleted_at`, `deleted_by` fields; verify `CompetitionBase` and `Competition` classes match data-model.md
- [ ] T004 [P] Update Team model in `app/modules/competitions/models/team_models.py` — add `project_name: Optional[str]`, `project_description: Optional[str]`; remove `deleted_at`, `deleted_by`
- [ ] T005 [P] Update TeamMember model in `app/modules/competitions/models/team_models.py` — add `amount_due: float = 0.0`, `amount_paid: float = 0.0`; remove `fee_paid`, `payment_id`, `member_share`
- [ ] T006 [P] Update Payment model in `app/modules/finance/models/payment.py` — add `team_member_id: Optional[int] = Field(default=None, foreign_key="team_members(id)")`

### Schema Updates (Module Schemas — Parallel)

- [ ] T007 [P] Update `TeamMemberDTO` in `app/modules/competitions/schemas/team_schemas.py` — replace `fee_paid`/`payment_id` with `amount_due`/`amount_paid`; add `model_config = ConfigDict(from_attributes=True)`
- [ ] T008 [P] Update `RegisterTeamInput` in `app/modules/competitions/schemas/team_schemas.py` — add `project_name: Optional[str]`, `project_description: Optional[str]`; rename `member_share` to `amount_due` in `student_fees` dict
- [ ] T009 [P] Update `AddTeamMemberInput` in `app/modules/competitions/schemas/team_schemas.py` — rename `fee: float` to `amount_due: float = 0.0`
- [ ] T010 [P] Update `PayCompetitionFeeInput` in `app/modules/competitions/schemas/team_schemas.py` — add `amount: float` (payment amount, supports partial); keep `parent_id`, `received_by_user_id`
- [ ] T011 [P] Update `PayCompetitionFeeResponseDTO` in `app/modules/competitions/schemas/team_schemas.py` — add `amount_paid: float` (running total), `amount_due: float`; keep `receipt_number`, `payment_id`, `amount`
- [ ] T012 [P] Update `TeamMemberRosterDTO` in `app/modules/competitions/schemas/team_schemas.py` — replace `member_share` with `amount_due`, add `amount_paid`; remove `fee_paid`, `payment_id`
- [ ] T013 [P] Update `TeamDTO` in `app/modules/competitions/schemas/team_schemas.py` — add `project_name`, `project_description` fields; add `model_config = ConfigDict(from_attributes=True)`
- [ ] T014 [P] Update `TeamRegistrationResultDTO` in `app/modules/competitions/schemas/team_schemas.py` — ensure output includes `team` (TeamDTO) and `members_added` (list of TeamMemberDTO)

### Schema Updates (API Schemas — Parallel)

- [ ] T015 [P] Update `UpdateTeamInput` in `app/api/schemas/competitions/team_schemas.py` — add `project_name: Optional[str] = Field(None, max_length=500)`, `project_description: Optional[str] = Field(None, max_length=5000)`

### Dead Code Removal (Parallel)

- [ ] T016 [P] Remove `restore_competition()` and `list_deleted_competitions()` from `app/modules/competitions/repositories/competition_repository.py`; update `__init__.py` exports
- [ ] T017 [P] Remove `restore_team()`, `list_deleted_teams()`, `get_members_by_payment_id()`, `mark_fee_paid()` from `app/modules/competitions/repositories/team_repository.py`; add `record_payment()`, `refund_payment()`, `hard_delete_team()`, `hard_delete_competition()` stubs; update `__init__.py` exports
- [ ] T018 [P] Remove `restore_competition()` and `list_deleted_competitions()` from `app/modules/competitions/services/competition_service.py`
- [ ] T019 [P] Remove `restore_team()`, `list_deleted_teams()`, `unmark_team_fee_for_payment()` from `app/modules/competitions/services/team_service.py`; remove `GroupCompetitionParticipation` auto-creation from `register_team()`
- [ ] T020 [P] Remove restore and deleted endpoints from `app/api/routers/competitions/competitions_router.py` — delete `/restore` and `/deleted` routes
- [ ] T021 [P] Remove restore and deleted endpoints from `app/api/routers/competitions/teams_router.py` — delete `/restore` and `/deleted` routes; remove `group_competitions_router` registration from `app/api/main.py`

**Checkpoint**: Foundation ready — models, schemas, and dead code removed. User story implementation can now begin.

---

## Phase 3: User Story 1 — Admin manages competition lifecycle with hard delete (Priority: P1) 🎯 MVP

**Goal**: Admins can create, edit, read, and permanently delete competitions. Deletion is blocked if teams exist.

**Independent Test**: Create competition → edit → delete permanently → verify gone from all lists. Attempt delete with teams → blocked with error.

### Implementation

- [ ] T022 [US1] Implement `hard_delete_competition()` repository function in `app/modules/competitions/repositories/competition_repository.py` — `DELETE FROM competitions WHERE id = :id`, raise `ConflictError` if any teams reference this competition (check `SELECT COUNT(*) FROM teams WHERE competition_id = :id`)
- [ ] T023 [US1] Implement `delete_competition()` service method in `app/modules/competitions/services/competition_service.py` — call repo hard_delete, catch conflict, raise `BusinessRuleError` with message "Cannot delete competition with registered teams. Remove teams first."
- [ ] T024 [US1] Update `DELETE /api/v1/competitions/{competition_id}` endpoint in `app/api/routers/competitions/competitions_router.py` — call `service.delete_competition()`, return standard envelope, ensure `require_admin` guard
- [ ] T025 [US1] Update `list_competitions()` repository function in `app/modules/competitions/repositories/competition_repository.py` — remove `deleted_at IS NULL` filter and `include_deleted` parameter
- [ ] T026 [US1] Update `list_competitions()` service method in `app/modules/competitions/services/competition_service.py` — remove `include_deleted` parameter, update return type to `list[CompetitionDTO]`
- [ ] T027 [US1] Update `get_competition_by_id()` repository function in `app/modules/competitions/repositories/competition_repository.py` — remove `deleted_at IS NULL` filter
- [ ] T028 [US1] Verify `GET /api/v1/competitions` and `GET /api/v1/competitions/{id}` endpoints return correct data without deleted_at/deleted_by fields

**Checkpoint**: US1 complete — competition hard-delete works independently. No soft-delete artifacts remain.

---

## Phase 4: User Story 2 — Admin manages teams with project info and hard delete (Priority: P1)

**Goal**: Admins can create teams with project_name/project_description, add/remove members, and permanently delete teams (blocked if any member has paid fees).

**Independent Test**: Create team with project info → verify project fields visible → delete team (no paid members) → verify gone. Attempt delete with paid member → blocked.

### Implementation

- [ ] T029 [US2] Implement `hard_delete_team()` repository function in `app/modules/competitions/repositories/team_repository.py` — check `SELECT COUNT(*) FROM team_members WHERE team_id = :id AND amount_paid > 0`, if > 0 raise conflict; else `DELETE FROM team_members WHERE team_id = :id`, then `DELETE FROM teams WHERE id = :id`
- [ ] T030 [US2] Implement `delete_team()` service method in `app/modules/competitions/services/team_service.py` — call repo hard_delete, catch conflict, raise `BusinessRuleError` with message "Cannot delete team with paid members. Refund fees first."
- [ ] T031 [US2] Update `register_team()` service method in `app/modules/competitions/services/team_service.py` — accept `project_name`, `project_description` from `RegisterTeamInput`; set on Team model; do NOT create `GroupCompetitionParticipation`
- [ ] T032 [US2] Update `POST /api/v1/teams` endpoint in `app/api/routers/competitions/teams_router.py` — pass `project_name`, `project_description` from request body to service; update response to include project fields
- [ ] T033 [US2] Update `update_team()` service method in `app/modules/competitions/services/team_service.py` — accept `project_name`, `project_description` updates
- [ ] T034 [US2] Update `PUT/PATCH /api/v1/teams/{team_id}` endpoint in `app/api/routers/competitions/teams_router.py` — pass project fields from `UpdateTeamInput` to service
- [ ] T035 [US2] Update `list_teams()` repository function in `app/modules/competitions/repositories/team_repository.py` — remove `deleted_at IS NULL` filter and `include_deleted` parameter
- [ ] T036 [US2] Update `get_team_by_id()` repository function in `app/modules/competitions/repositories/team_repository.py` — remove `deleted_at IS NULL` filter
- [ ] T037 [US2] Update `GET /api/v1/teams` and `GET /api/v1/teams/{id}` endpoints — verify project_name/project_description appear in response DTOs
- [ ] T038 [US2] Update `DELETE /api/v1/teams/{team_id}` endpoint — call `service.delete_team()`, return standard envelope, ensure `require_admin` guard
- [ ] T039 [US2] Update `add_team_member_to_existing()` service method — use `amount_due` instead of `fee`/`member_share`; set `amount_paid = 0`
- [ ] T040 [US2] Update `POST /api/v1/teams/{team_id}/members` endpoint — accept `amount_due` in request body per `AddTeamMemberInput`
- [ ] T041 [US2] Update `remove_team_member()` service method — check `amount_paid > 0` before removal (was `fee_paid`); raise `BusinessRuleError` if paid
- [ ] T042 [US2] Update `DELETE /api/v1/teams/{team_id}/members/{student_id}` endpoint — verify blocked when member has paid

**Checkpoint**: US2 complete — team CRUD with project info and hard-delete works independently.

---

## Phase 5: User Story 3 — Project tracking verification (Priority: P2)

**Goal**: Project name and description are visible on team detail page and in team lists. Already covered by US2 implementation.

**Independent Test**: Create team with project info → GET team detail → verify fields present → update → verify changes reflected.

### Verification

- [ ] T043 [US3] Verify `TeamDTO` includes `project_name` and `project_description` in all team list and detail responses
- [ ] T044 [US3] Verify `GET /api/v1/teams/{id}` response includes project fields per contract overview.md

**Checkpoint**: US3 complete — project tracking verified as part of US2.

---

## Phase 6: User Story 4 — Multi-payment fee tracking (Priority: P2)

**Goal**: Each team member has `amount_due` and `amount_paid`. Admins can process partial payments. Each payment creates a finance receipt. Atomic rollback on failure.

**Independent Test**: Add member with fee → verify `amount_due` shown → make partial payment → verify `amount_paid` updated and balance correct → make full payment → verify fee marked as paid.

### Repository Functions (Parallel)

- [ ] T045 [US4] Implement `record_payment(db, team_member_id, amount)` in `app/modules/competitions/repositories/team_repository.py` — `UPDATE team_members SET amount_paid = amount_paid + :amount WHERE id = :team_member_id`
- [ ] T046 [US4] Implement `refund_payment(db, team_member_id, amount)` in `app/modules/competitions/repositories/team_repository.py` — `UPDATE team_members SET amount_paid = amount_paid - :amount WHERE id = :team_member_id`

### Service Methods

- [ ] T047 [US4] Implement `pay_competition_fee()` service method in `app/modules/competitions/services/team_service.py` — validate team/member exists → create receipt via `FinanceUnitOfWork` → call `record_payment()` → log activity → commit; on failure rollback entire operation (no orphan receipt, no phantom fee update)
- [ ] T048 [US4] Implement `refund_competition_fee()` service method in `app/modules/competitions/services/team_service.py` — validate payment exists → create refund receipt via `FinanceUnitOfWork` → call `refund_payment()` → update payment row with `original_payment_id` → log activity → commit; on failure rollback
- [ ] T049 [US4] Update `_log_payment_activity()` in `app/modules/competitions/services/team_service.py` — log payment amount (not boolean fee_paid); include `amount_due`, `amount_paid`, balance

### Router Endpoints

- [ ] T050 [US4] Update `POST /api/v1/teams/{team_id}/members/{student_id}/pay` endpoint in `app/api/routers/competitions/teams_router.py` — accept `PayCompetitionFeeBody` with `amount` field; call `service.pay_competition_fee()`; return `PayCompetitionFeeResponseDTO` with `amount_paid`, `amount_due`
- [ ] T051 [US4] Add `POST /api/v1/teams/{team_id}/members/{student_id}/refund` endpoint in `app/api/routers/competitions/teams_router.py` — accept refund amount; call `service.refund_competition_fee()`; return standard envelope; ensure `require_admin` guard

### Fee Status Computation

- [ ] T052 [US4] Update `get_team_members()` service method — compute fee status from `amount_due` vs `amount_paid` (paid: `amount_paid >= amount_due`, partial: `0 < amount_paid < amount_due`, unpaid: `amount_paid = 0 AND amount_due > 0`, no_fee: `amount_due = 0`)
- [ ] T053 [US4] Update `GET /api/v1/teams/{team_id}/members` endpoint — verify response includes `amount_due`, `amount_paid`, and computed fee status per `TeamMemberRosterDTO`

**Checkpoint**: US4 complete — partial payments, refunds, and fee status computation work independently.

---

## Phase 7: User Story 6 — Admin records competition results (Priority: P2)

**Goal**: Admins can record placement (rank + label) for teams after competition date. Blocked before competition date.

**Independent Test**: Set placement after competition date → verify saved and visible. Attempt placement before competition date → blocked with error.

### Implementation

- [ ] T054 [US6] Add `validate_competition_date_passed()` helper in `app/modules/competitions/services/team_service.py` — compare `competition.competition_date` to today; allow if `<= today`; raise `BusinessRuleError` if future date
- [ ] T055 [US6] Update `record_placement()` service method in `app/modules/competitions/services/team_service.py` — call date validation before setting `placement_rank` and `placement_label`
- [ ] T056 [US6] Verify `PATCH /api/v1/teams/{team_id}/placement` endpoint in `app/api/routers/competitions/teams_router.py` — calls updated service method; returns 422/409 with clear error when competition date is in future; ensure `require_admin` guard

**Checkpoint**: US6 complete — placement recording with date validation works independently.

---

## Phase 8: User Story 5 — Subcategory filtering verification (Priority: P3)

**Goal**: Admins can filter teams by competition, category, and subcategory. Already implemented — verify only.

**Independent Test**: Create teams across categories/subcategories → filter by category → verify only matching teams → filter by subcategory → verify only matching teams.

### Verification

- [ ] T057 [US5] Verify `GET /api/v1/teams?competition_id=X&category=Y&subcategory=Z` returns correct filtered results (existing `list_teams()` in `app/modules/competitions/repositories/team_repository.py` already supports category/subcategory params)
- [ ] T058 [US5] Verify `GET /api/v1/competitions/{id}/categories` returns distinct (category, subcategory) tuples from teams data (existing `get_distinct_categories()` in `app/modules/competitions/repositories/team_repository.py`)

**Checkpoint**: US5 complete — subcategory filtering verified as pre-existing functionality.

---

## Phase 9: Coach Read-Only Access

**Goal**: Coaches (employees linked as team coach) can read their own teams' data but cannot modify.

**Independent Test**: Coach authenticates → GET teams → only sees teams where `coach_id` matches → POST/DELETE attempts return 403.

### Implementation

- [ ] T059 [P] Add `require_coach_or_admin` dependency in `app/api/dependencies.py` — check `current_user.is_admin` OR `current_user.employee_id == team.coach_id`; raise 403 if neither
- [ ] T060 Apply `require_coach_or_admin` to `GET /api/v1/teams/{team_id}` endpoint in `app/api/routers/competitions/teams_router.py` (read access for coach of specific team)
- [ ] T061 Update `GET /api/v1/teams` endpoint — add coach filtering: if user is not admin, filter results to only teams where `coach_id == current_user.employee_id`
- [ ] T062 Verify all write endpoints (`POST`, `PUT`, `PATCH`, `DELETE` on teams/competitions/members/payments/placement) retain `require_admin` guard and reject coach access with 403

**Checkpoint**: Coach read-only access complete. Admin write access unchanged.

---

## Phase 10: Test Updates

**Purpose**: Update test suite to reflect hard delete, new payment model, and coach access.

- [ ] T071 Update `tests/test_competitions.py` — replace soft-delete tests with hard-delete assertions; update payment tests for partial payment model (`amount_due`/`amount_paid`); add coach read-only test cases; add placement date validation test
- [ ] T072 Add test for `test_delete_competition_blocked_with_teams` — verify 409 when competition has teams
- [ ] T073 Add test for `test_delete_team_blocked_with_paid_members` — verify 409 when team has paid members
- [ ] T074 Add test for `test_partial_payment_updates_balance` — verify `amount_paid` increases correctly across multiple payments
- [ ] T075 Add test for `test_refund_decreases_amount_paid` — verify refund reduces `amount_paid` and creates refund receipt
- [ ] T076 Add test for `test_placement_blocked_before_competition_date` — verify 409/422 when competition date is future
- [ ] T077 Add test for `test_coach_can_read_own_teams` — verify coach sees only their teams
- [ ] T078 Add test for `test_coach_cannot_write` — verify coach gets 403 on POST/PUT/DELETE
- [ ] T079 Remove or update `tests/test_academics_competitions.py` — file should be deleted after T063 (GroupCompetitionParticipation removal)
- [ ] T080 Run `pytest tests/test_competitions.py -v` — all tests pass
- [ ] T081 Run `pytest tests/ -v` — full suite passes with no regressions

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T082 [P] Update AGENTS.md — update competition module gotchas section (hard delete, new payment model, removed GroupCompetitionParticipation, stateless service pattern)
- [x] T083 Verify constitution §III compliance — no new `-> dict` or `-> list[dict]` returns introduced in any service method; all returns are typed DTOs or ORM models
- [ ] T084 Run quickstart.md validation — execute all 4 integration scenarios manually or via smoke test (competition lifecycle, group pre-fill, coach read-only, subcategory filtering)
- [x] T085 [P] Clean up any remaining references to soft-delete in competition-related docstrings and comments
- [ ] T086 Run dead code audit — `grep -rn "restore\|deleted_at\|list_deleted\|GroupCompetitionParticipation\|fee_paid\|payment_id\|member_share" app/modules/competitions/ app/api/routers/competitions/ app/api/schemas/competitions/` — must return ZERO hits for removed artifacts
- [ ] T087 Add `User.is_admin` property to `app/modules/auth/models/auth_models.py` if not present (returns `True` for `role in ("admin", "system_admin")`) — used by coach read-only guard

---

## Dependencies & Execution Order

### Phase Dependencies

- **Migration (Phase 1)**: No dependencies — must be applied first
- **Foundational (Phase 2)**: Depends on Migration completion — BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1 (P1) → US2 (P1) → US3 (P2) → US4 (P2) → US6 (P2) → US5 (P3)
  - US3 and US5 are verification phases (already partially covered by earlier work)
- **Coach Access (Phase 9)**: Depends on US2 completion (team endpoints must exist)
- **Test Updates (Phase 10)**: Depends on all user story phases complete
- **Polish (Phase N)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Competition hard-delete — no dependencies on other stories, starts after Foundational
- **US2 (P1)**: Team hard-delete + project info — depends on US1 only for the "competition must exist" prerequisite; otherwise independent
- **US3 (P2)**: Project tracking — depends on US2 (project fields added to team model)
- **US4 (P2)**: Multi-payment fees — depends on US2 (team members exist); independent of US3
- **US6 (P2)**: Placement recording — depends on US2 (teams exist); independent of US3/US4
- **US5 (P3)**: Subcategory filtering — no dependencies (already implemented); verification only

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T003-T006 (model updates) can run in parallel
- T007-T015 (schema updates) can run in parallel
- T016-T021 (dead code removal) can run in parallel
- T045-T046 (US4 repo functions) can run in parallel
- T071-T079 (test updates) can run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch all model updates together:
Task: "Update Competition model (T003)"
Task: "Update Team model (T004)"
Task: "Update TeamMember model (T005)"
Task: "Update Payment model (T006)"

# Launch all schema updates together:
Task: "Update TeamMemberDTO (T007)"
Task: "Update RegisterTeamInput (T008)"
Task: "Update AddTeamMemberInput (T009)"
Task: "Update PayCompetitionFeeInput (T010)"
Task: "Update PayCompetitionFeeResponseDTO (T011)"
Task: "Update TeamMemberRosterDTO (T012)"
Task: "Update TeamDTO (T013)"
Task: "Update TeamRegistrationResultDTO (T014)"
Task: "Update UpdateTeamInput (T015)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Migration (apply to Supabase)
2. Complete Phase 2: Foundational (models, schemas, dead code)
3. Complete Phase 3: User Story 1 (competition hard-delete)
4. **STOP and VALIDATE**: Create competition → edit → delete permanently → verify gone
5. Deploy/demo if ready

### Incremental Delivery

1. Migration + Foundational → schema and models ready
2. Add US1 → Competition hard-delete → Test independently
3. Add US2 → Team hard-delete + project info → Test independently
4. Add US3 → Project tracking verification → Test independently
5. Add US4 → Multi-payment fees → Test independently (partial payments, refunds)
6. Add US6 → Placement recording → Test independently
7. Add US5 → Subcategory filtering verification → Test independently
8. Add Phase 9 → Coach read-only
9. Add Phase 10 → Test updates + dead code audit
10. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Migration + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (competition hard-delete)
   - Developer B: US2 (team hard-delete + project info)
   - Developer C: US4 (multi-payment fees) — after US2 team member changes
3. Stories complete and integrate independently
4. US3, US5, US6 can proceed in parallel with US1/US2/US4

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Migration 054 must be applied to Supabase BEFORE any code changes are deployed
- **CRITICAL**: Dead code audit (T086) must find ZERO remaining references to removed artifacts
- **CRITICAL**: Payment atomicity must be addressed — 3 separate transactions in `pay_competition_fee` is a data integrity risk

---

## Phase 11: N+1 Query Elimination (Performance)

**Purpose**: Replace N+1 query patterns with batch-loaded JOINs across 4 service methods. Total query reduction: ~746 → 4 queries.

**Independent Test**: Each refactored endpoint returns identical response data. Query count verified via test assertions.

### Repository Batch Functions (Parallel)

- [x] T101 [P] Add `list_team_members_with_students(db, team_ids: list[int])` in `app/modules/competitions/repositories/team_repository.py` — single JOIN query: `SELECT tm.*, s.full_name FROM team_members tm LEFT JOIN students s ON s.id = tm.student_id WHERE tm.team_id IN :team_ids`. Returns `dict[int, list[tuple]]` grouped by team_id.
- [x] T102 [P] Add `list_teams_with_members_batch(db, competition_id: int)` in `app/modules/competitions/repositories/team_repository.py` — single JOIN query: `SELECT t.*, tm.*, s.full_name FROM teams t LEFT JOIN team_members tm ON tm.team_id = t.id LEFT JOIN students s ON s.id = tm.student_id WHERE t.competition_id = :competition_id`. Returns `(list[Team], dict[int, list[tuple]])`.
- [x] T103 [P] Add `list_student_memberships_enriched(db, student_id: int)` in `app/modules/competitions/repositories/team_repository.py` — single JOIN query: `SELECT tm.*, t.*, c.* FROM team_members tm JOIN teams t ON t.id = tm.team_id LEFT JOIN competitions c ON c.id = t.competition_id WHERE tm.student_id = :student_id`. Returns enriched rows with team + competition data.
- [x] T104 [P] Add `get_competition_summary_data(db, competition_id: int)` in `app/modules/competitions/repositories/competition_repository.py` — single query returning competition + all teams + all members + all student names. Uses JOINs across competitions → teams → team_members → students. Returns structured data for DTO assembly.

### Service Layer Refactoring (Parallel)

- [x] T105 Refactor `get_competition_summary()` in `app/modules/competitions/services/competition_service.py` — replace nested loops (lines 104-166) with single `get_competition_summary_data()` call. Assemble DTOs from pre-fetched data. Query count: 602 → 1.
- [x] T106 Refactor `get_teams_with_members()` in `app/modules/competitions/services/team_service.py` — replace loop (lines 308-326) with `list_teams_with_members_batch()` call. Assemble DTOs from pre-fetched data. Query count: 101 → 1.
- [x] T107 Refactor `list_team_members()` in `app/modules/competitions/services/team_service.py` — replace loop (lines 466-490) with `list_team_members_with_students()` call for single team. Query count: 22 → 1.
- [x] T108 Refactor `get_student_competitions()` in `app/modules/competitions/services/team_service.py` — replace loop (lines 25-62) with `list_student_memberships_enriched()` call. Query count: 21 → 1.

### Verification

- [x] T109 [P] Add performance regression test for `get_competition_summary` — assert ≤ 3 queries for 100 teams × 5 members in `tests/test_competitions.py`
- [x] T110 [P] Add performance regression test for `get_teams_with_members` — assert ≤ 2 queries for 100 teams in `tests/test_competitions.py`
- [x] T111 [P] Add performance regression test for `list_team_members` — assert ≤ 2 queries for 20 members in `tests/test_competitions.py`
- [x] T112 [P] Add performance regression test for `get_student_competitions` — assert ≤ 2 queries for 10 memberships in `tests/test_competitions.py`
- [x] T113 Run `pytest tests/test_competitions.py -v` — all existing tests pass (no behavioral regression)
- [ ] T114 Run `pytest tests/ -v` — full suite passes
- **CRITICAL**: Payment atomicity (T047) — if receipt creation or fee update fails, entire operation MUST roll back with no orphan data
