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
- [ ] T064 Run `pytest tests/test_competitions.py -v` — all tests pass (BLOCKED: Supabase JWT expired — regenerate via `python scripts/get_test_jwt.py` and update `admin_token` in `tests/conftest.py`)
- [ ] T065 Run `pytest tests/test_academics_competitions.py -v` — all tests pass (SKIPPED: test file deleted — group_competitions_router removed)
- [ ] T066 Run `pytest tests/ -v` — full suite passes (BLOCKED: Supabase JWT expired)

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
