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
- [ ] T002 Apply migration to Supabase and verify schema changes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core model, schema, and dead-code removal that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 [P] Update Competition model in `app/modules/competitions/models/competition_models.py` — remove `deleted_at` and `deleted_by` fields
- [x] T004 [P] Update Team model in `app/modules/competitions/models/team_models.py` — remove `deleted_at`, `deleted_by`; add `project_name: Optional[str]`, `project_description: Optional[str]`
- [x] T005 [P] Update TeamMember model in `app/modules/competitions/models/team_models.py` — replace `member_share`, `fee_paid`, `payment_id` with `amount_due: float = 0.0`, `amount_paid: float = 0.0`
- [x] T006 [P] Update Payment model in `app/modules/finance/models/payment.py` — add `team_member_id: Optional[int] = Field(default=None, foreign_key="team_members.id")`
- [x] T007 Update TeamMemberDTO in `app/modules/competitions/schemas/team_schemas.py` — replace `member_share`, `fee_paid`, `payment_id` with `amount_due`, `amount_paid`
- [x] T008 Update RegisterTeamInput in `app/modules/competitions/schemas/team_schemas.py` — add `project_name: Optional[str]`, `project_description: Optional[str]`
- [x] T009 Update AddTeamMemberInput in `app/modules/competitions/schemas/team_schemas.py` — rename `fee` to `amount_due`
- [x] T010 Update PayCompetitionFeeInput in `app/modules/competitions/schemas/team_schemas.py` — add `amount: float` field (payment amount for partial payments)
- [x] T011 Update PayCompetitionFeeResponseDTO in `app/modules/competitions/schemas/team_schemas.py` — add `amount_paid: float`, `amount_due: float`
- [x] T012 Update TeamMemberRosterDTO in `app/modules/competitions/schemas/team_schemas.py` — replace `member_share`, `fee_paid`, `payment_id` with `amount_due`, `amount_paid`
- [x] T013 Update UpdateTeamInput in `app/api/schemas/competitions/team_schemas.py` — add `project_name`, `project_description` fields
- [x] T014 Update TeamDTO in `app/modules/competitions/schemas/team_schemas.py` — add `project_name`, `project_description`
- [x] T015 Remove GroupCompetitionParticipation model from `app/modules/academics/models/group_level_models.py`
- [x] T016 Update `app/modules/academics/models/__init__.py` — remove GroupCompetitionParticipation export
- [x] T017 Remove `app/modules/academics/group/competition/` entire slice (service.py, repository.py, interface.py, __init__.py)
- [x] T018 Remove `app/api/routers/academics/group_competitions_router.py`
- [x] T019 Update `app/api/routers/academics/__init__.py` — remove group_competitions_router import/export
- [x] T020 Update `app/api/main.py` — remove `group_competitions_router` import and `app.include_router` call (lines 112-116)
- [x] T021 Update `app/modules/academics/group/analytics/repository.py` — remove query that joins against GroupCompetitionParticipation (lines 298-313)
- [x] T022 [P] Add coach read-only guard in `app/api/dependencies.py` — new `require_coach_or_admin(team_id)` dependency that checks `current_user.employee.id == team.coach_id`

**Checkpoint**: Foundation ready — models, schemas, dead code removed, migration applied. User story implementation can now begin.

---

## Phase 3: User Story 1 — Admin manages competition lifecycle with hard delete (Priority: P1) 🎯 MVP

**Goal**: Competition CRUD with permanent (hard) delete. Blocked if teams exist.

**Independent Test**: Create a competition, edit it, view it, delete it permanently (with and without teams). No restore endpoints exist.

### Implementation for User Story 1

- [x] T023 [US1] Replace `delete_competition()` in `app/modules/competitions/repositories/competition_repository.py` — hard delete: `db.delete(c)` instead of setting `deleted_at`; remove `restore_competition()` and `list_deleted_competitions()` functions
- [x] T024 [US1] Update `list_competitions()` in `app/modules/competitions/repositories/competition_repository.py` — remove `include_deleted` parameter and `deleted_at IS NULL` filter
- [x] T025 [US1] Update `delete_competition()` in `app/modules/competitions/services/competition_service.py` — call hard delete; remove `restore_competition()` and `list_deleted_competitions()` methods
- [x] T026 [US1] Update `GET /api/v1/competitions` in `app/api/routers/competitions/competitions_router.py` — remove `include_deleted` query parameter
- [x] T027 [US1] Update `DELETE /api/v1/competitions/{id}` in `app/api/routers/competitions/competitions_router.py` — change summary from "Soft delete" to "Hard delete"
- [x] T028 [US1] Remove `POST /api/v1/competitions/{id}/restore` endpoint from `app/api/routers/competitions/competitions_router.py`
- [x] T029 [US1] Remove `GET /api/v1/competitions/deleted` endpoint from `app/api/routers/competitions/competitions_router.py`

**Checkpoint**: Competition hard-delete lifecycle fully functional. No soft-delete or restore artifacts remain.

---

## Phase 4: User Story 2 — Admin manages teams with project info and hard delete (Priority: P1)

**Goal**: Team CRUD with project_name/project_description, hard delete (blocked if any member has paid), group as student pre-fill source only.

**Independent Test**: Create a team with project info, add/remove members, delete team (with and without paid members). No restore endpoints exist.

### Implementation for User Story 2

- [x] T030 [US2] Replace `delete_team()` in `app/modules/competitions/repositories/team_repository.py` — hard delete: `db.delete(t)`; remove `restore_team()` and `list_deleted_teams()` functions; update `list_teams()` to remove `include_deleted` and `deleted_at` filters; update `get_team()` to remove `include_deleted` and soft-delete check; update `check_student_in_competition()` to remove `deleted_at` filter
- [x] T031 [US2] Update `create_team()` in `app/modules/competitions/repositories/team_repository.py` — add `project_name` and `project_description` parameters
- [x] T032 [US2] Update `register_team()` in `app/modules/competitions/services/team_service.py` — pass `project_name` and `project_description` to `create_team()`; remove `GroupCompetitionParticipation` auto-creation block (lines 139-149); update delete check from `m.fee_paid` to `m.amount_paid > 0`
- [x] T033 [US2] Update `delete_team()` in `app/modules/competitions/services/team_service.py` — call hard delete; change check from `m.fee_paid` to `m.amount_paid > 0`; remove `restore_team()` and `list_deleted_teams()` methods
- [x] T034 [US2] Update `remove_team_member()` in `app/modules/competitions/services/team_service.py` — change check from `member.fee_paid` to `member.amount_paid > 0`
- [x] T035 [US2] Update `add_team_member_to_existing()` in `app/modules/competitions/services/team_service.py` — rename `fee` parameter to `amount_due`
- [x] T036 [US2] Update `list_team_members()` in `app/modules/competitions/services/team_service.py` — use `amount_due` and `amount_paid` instead of `member_share` and `fee_paid`
- [x] T037 [US2] Update `get_competition_summary()` in `app/modules/competitions/services/competition_service.py` — use `amount_due`/`amount_paid` instead of `member_share`/`fee_paid`; remove `payment_id` from member DTOs
- [x] T038 [US2] Update `update_placement()` in `app/modules/competitions/services/team_service.py` — remove GroupCompetitionParticipation sync block (lines 378-387)
- [x] T039 [US2] Update `DELETE /api/v1/teams/{id}` in `app/api/routers/competitions/teams_router.py` — change summary from "Soft delete" to "Hard delete"
- [x] T040 [US2] Remove `POST /api/v1/teams/{id}/restore` endpoint from `app/api/routers/competitions/teams_router.py`
- [x] T041 [US2] Remove `GET /api/v1/teams/deleted` endpoint from `app/api/routers/competitions/teams_router.py`
- [x] T042 [US2] Remove `DeletedTeamListResponse` from `app/api/schemas/competitions/team_schemas.py` (no longer needed)

**Checkpoint**: Team hard-delete lifecycle with project tracking fully functional. No soft-delete or restore artifacts remain. GroupCompetitionParticipation removed.

---

## Phase 5: User Story 3 — Admin tracks team project information (Priority: P2)

**Goal**: Project name and description visible on team detail and list views. (Already covered by T030-T032 in Phase 4 — this phase is verification and any remaining display work.)

**Independent Test**: Create a team with project name/description, verify they appear in team details and list views, update them later.

### Implementation for User Story 3

- [x] T043 [US3] Verify project_name and project_description are included in all team-related API responses (GET /teams, GET /teams/{id}, GET /competitions/{id}/summary) — already covered by DTO updates in Phase 2
- [x] T044 [US3] Update `get_student_competitions()` in `app/modules/competitions/services/team_service.py` — ensure project_name/project_description are included in nested team data (TeamDTO already has these fields from Phase 2)

**Checkpoint**: Project information visible in all team views.

---

## Phase 6: User Story 4 — Admin manages competition fees like enrollment fees (Priority: P2)

**Goal**: Multi-payment support with `amount_due`/`amount_paid`. Partial payments. Atomic rollback. Refund support.

**Independent Test**: Create a team member with a fee, make a partial payment (verify balance updates), make a full payment (verify fee shows as paid), test overpayment handling.

### Implementation for User Story 4

- [x] T045 [US4] Add `record_payment()` in `app/modules/competitions/repositories/team_repository.py` — increments `amount_paid` by given amount for a team_member_id
- [x] T046 [US4] Add `refund_payment()` in `app/modules/competitions/repositories/team_repository.py` — decrements `amount_paid` by given amount for a team_member_id
- [x] T047 [US4] Remove `mark_fee_paid()` from `app/modules/competitions/repositories/team_repository.py` (replaced by record_payment)
- [x] T048 [US4] Remove `get_members_by_payment_id()` from `app/modules/competitions/repositories/team_repository.py` (no single payment_id)
- [x] T049 [US4] Rewrite `pay_competition_fee()` in `app/modules/competitions/services/team_service.py` — accept `amount` parameter; create receipt with `payment_type="competition"` and `team_member_id`; call `record_payment()`; maintain atomic rollback (try/except with refund); update `_log_payment_activity()` to use amount instead of member_share
- [x] T050 [US4] Rewrite `unmark_team_fee_for_payment()` in `app/modules/competitions/services/team_service.py` → rename to `refund_competition_fee()` — use `team_member_id` on payment row to find affected TeamMember; call `refund_payment()` to decrement `amount_paid`
- [x] T051 [US4] Update `POST /api/v1/teams/{id}/members/{sid}/pay` in `app/api/routers/competitions/teams_router.py` — accept `amount` in request body (new `PayCompetitionFeeBody` DTO in `app/api/schemas/competitions/team_schemas.py`); pass amount to service
- [x] T052 [US4] Update finance refund integration — ensure `RefundService._unlink_competition_payment()` (if it exists) uses `team_member_id` instead of `payment_id` on TeamMember

**Checkpoint**: Multi-payment fee tracking fully functional. Partial payments, atomic rollback, and refunds working.

---

## Phase 7: User Story 6 — Admin records competition results (Priority: P2)

**Goal**: Placement recording after competition date. Blocked before competition date.

**Independent Test**: Set placement after competition date (succeeds), attempt placement before competition date (blocked with clear error).

### Implementation for User Story 6

- [x] T053 [US6] Update `update_placement()` in `app/modules/competitions/services/team_service.py` — fix date comparison: allow placement when `competition_date <= date.today()` (currently blocks same-day); verify placement_rank validation (>= 1)
- [x] T054 [US6] Update `PATCH /api/v1/teams/{id}/placement` in `app/api/routers/competitions/teams_router.py` — update description to clarify same-day placement is allowed

**Checkpoint**: Placement recording works correctly with proper date validation.

---

## Phase 8: User Story 5 — Admin filters and groups teams by category and subcategory (Priority: P3)

**Goal**: Subcategory filtering and grouping. (Already implemented — this phase is verification.)

**Independent Test**: Create teams across multiple categories and subcategories, filter by specific category+subcategory, verify correct results.

### Implementation for User Story 5

- [x] T055 [US5] Verify `GET /api/v1/teams` in `app/api/routers/competitions/teams_router.py` — confirm `category` and `subcategory` query params work (lines 48-58)
- [x] T056 [US5] Verify `list_teams()` in `app/modules/competitions/repositories/team_repository.py` — confirm category/subcategory filters use citext case-insensitive comparison
- [x] T057 [US5] Verify `GET /api/v1/competitions/{id}/categories` returns distinct category/subcategory tuples for autocomplete

**Checkpoint**: Subcategory filtering and grouping verified functional.

---

## Phase 9: Coach Read-Only Access (Cross-Cutting)

**Goal**: Coaches can read their own teams but cannot modify any data.

- [x] T058 Apply `require_coach_or_admin` guard to all team read endpoints in `app/api/routers/competitions/teams_router.py` — GET /teams, GET /teams/{id}, GET /teams/{id}/members, GET /students/{sid}/competitions
- [x] T059 Verify all team write endpoints remain `require_admin` only (POST /teams, PUT/PATCH /teams/{id}, DELETE /teams/{id}, POST /teams/{id}/members, DELETE /teams/{id}/members/{sid}, POST /teams/{id}/members/{sid}/pay, PATCH /teams/{id}/placement)

---

## Phase 10: Test Updates & Dead Code Audit

**Purpose**: Update existing tests to reflect hard delete, new payment model, and removed endpoints. Run full dead code audit per constitution.

- [x] T060 [P] Update `tests/test_competitions.py` — change soft-delete tests to hard-delete tests; update payment tests for amount_due/amount_paid model; remove any tests for restore/deleted endpoints
- [x] T061 [P] Update `tests/test_academics_competitions.py` — remove/update tests that reference GroupCompetitionParticipation; update for removed group_competitions_router endpoints
- [x] T062 [P] Update `tests/test_analytics_competition.py` — verify analytics queries work without GroupCompetitionParticipation
- [x] T063 Run full dead code audit: grep for `restore_competition`, `restore_team`, `list_deleted_competitions`, `list_deleted_teams`, `GroupCompetitionParticipation`, `fee_paid`, `payment_id` (in competitions context), `member_share` (in competitions context), `deleted_at` (in competitions context) across entire codebase
- [ ] T064 Run `pytest tests/test_competitions.py -v` — all tests pass
- [ ] T065 Run `pytest tests/test_academics_competitions.py -v` — all tests pass
- [ ] T066 Run `pytest tests/ -v` — full suite passes

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T067 [P] Update AGENTS.md — update competition module gotchas section (hard delete, new payment model, removed GroupCompetitionParticipation)
- [x] T068 Verify constitution §III compliance — no new `-> dict` or `-> list[dict]` returns introduced in any service method
- [ ] T069 Run quickstart.md validation — execute all 4 integration scenarios manually or via smoke test
- [x] T070 [P] Clean up any remaining references to soft-delete in competition-related docstrings and comments

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
- T007-T014 (schema updates) can run in parallel
- T015-T021 (dead code removal) can run in parallel
- T023-T029 (US1) must be sequential (repo → service → router)
- T030-T042 (US2) can be partially parallel (repo tasks T030-T031 parallel, then service tasks, then router tasks)
- T045-T048 (US4 repo) can run in parallel
- T060-T062 (test updates) can run in parallel

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
Task: "Update UpdateTeamInput (T013)"
Task: "Update TeamDTO (T014)"
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
- **CRITICAL**: Dead code audit (T063) must find ZERO remaining references to removed artifacts
