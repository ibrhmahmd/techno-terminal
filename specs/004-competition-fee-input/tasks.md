---

description: "Task list for competition fee user input feature"

---

# Tasks: Competition Fee User Input

**Input**: Design documents from `/specs/004-competition-fee-input/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md, contracts/

**Tests**: Test update tasks are included (existing tests must be updated to match schema removal and new input fields).

**Organization**: Tasks grouped by user story — each story independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1–US4)
- Exact file paths in all descriptions

---

## Phase 1: Schema & Migration (Shared Foundational)

**Purpose**: Database column drop + schema file update. Blocks all stories.

- [X] T001 Create migration `db/migrations/050_remove_team_fee_column.sql` to drop `teams.fee` column
- [X] T002 [P] Remove `fee` column from `teams` table definition in `db/schema/07_tables_competitions.sql`

**Checkpoint**: `teams.fee` column no longer exists in schema definition. Migration ready to apply.

---

## Phase 2: User Story 1 — Register team with per-student fees (Priority: P1) 🎯 MVP

**Goal**: Admin can register a team with per-student fees via `RegisterTeamInput.student_fees`. Missing entries default to 0. No auto-splitting.

**Independent Test**: Create a team with `student_ids=[1,2]`, `student_fees={1:50}` → verify `TeamMember[1].member_share=50`, `TeamMember[2].member_share=0`.

### Implementation for User Story 1

- [X] T003 [P] [US1] Remove `fee: Optional[Decimal]` field from `TeamBase` in `app/modules/competitions/models/team_models.py`
- [X] T004 [P] [US1] Add `student_fees: Optional[dict[int, float]] = None` to `RegisterTeamInput` in `app/modules/competitions/schemas/team_schemas.py`
- [X] T005 [P] [US1] Remove `fee: Optional[float]` from `TeamDTO` in `app/modules/competitions/schemas/team_schemas.py`
- [X] T006 [US1] Replace auto-split (`team.fee / len(student_ids)`) with per-student lookup from `cmd.student_fees` in `register_team()` at `app/modules/competitions/services/team_service.py`

**Checkpoint**: US1 fully functional — admin can register team with per-student fees via API.

---

## Phase 3: User Story 2 — Add member with fee (Priority: P1)

**Goal**: Admin can add a member to an existing team with a specific fee. No hardcoded `team.fee / 2`.

**Independent Test**: Add member to team with `fee=25` → verify `TeamMember.member_share=25`. Add member without fee → verify `TeamMember.member_share=0`.

### Implementation for User Story 2

- [X] T007 [P] [US2] Add `fee: float = 0.0` field to `AddTeamMemberInput` in `app/modules/competitions/schemas/team_schemas.py`
- [X] T008 [P] [US2] Add `fee: float = 0.0` to `AddTeamMemberInput` in `app/api/routers/competitions/teams_router.py`
- [X] T009 [US2] Replace hardcoded `team.fee / 2` with `fee` param (default 0.0) in `add_team_member_to_existing()` at `app/modules/competitions/services/team_service.py`

**Checkpoint**: US2 complete — adding member with or without fee works independently of US1.

---

## Phase 4: User Story 3 — Remove team-level fee from API (Priority: P2)

**Goal**: `UpdateTeamInput` no longer accepts a `fee` field. Clean up router-level references.

**Independent Test**: Verify `UpdateTeamInput` has no `fee` field. Update a team without `fee` → 200 OK.

### Implementation for User Story 3

- [X] T010 [US3] Remove `fee: Optional[Decimal]` field from `UpdateTeamInput` in `app/api/routers/competitions/teams_router.py`

**Checkpoint**: US3 complete — team update endpoint no longer references `fee`.

---

## Phase 5: User Story 4 — Retain `fee_per_student` on Competition (Priority: P3)

**Goal**: `Competition.fee_per_student` remains as UI reference on all competition input/output DTOs. Not used in any calculation.

**Independent Test**: Create competition with `fee_per_student=50` → fetch via API → DTO contains `fee_per_student=50`.

### Implementation for User Story 4

- [X] T011 [US4] Verify `fee_per_student` field remains on `CreateCompetitionInput`, `UpdateCompetitionInput`, and `CompetitionDTO` in `app/api/routers/competitions/competitions_router.py` (no changes expected — confirm-only task)

**Checkpoint**: US4 complete — no regression on `fee_per_student`.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Update existing tests, run verification suite.

- [X] T012 [P] Update `tests/test_competitions.py`: remove `fee` references from team creation payloads and assertions
- [X] T013 [P] Add test cases in `tests/test_competitions.py` for US1 scenarios: `student_fees` with partial dict, empty dict, None, and extraneous keys
- [X] T014 [P] Add test cases in `tests/test_competitions.py` for US2 scenarios: add member with `fee=25`, add member without `fee`, add member with `fee=0`
- [X] T015 Run verification: `pytest tests/test_competitions.py -v && pytest tests/test_analytics_competition.py -v && pytest tests/test_finance.py -v -k "unpaid"`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Schema (Phase 1)**: No dependencies — start immediately
- **US1 (Phase 2)**: Depends on Phase 1 — model + schema changes must come first
- **US2 (Phase 3)**: Depends on Phase 1 — can run parallel with US1 (different code sections)
- **US3 (Phase 4)**: Depends on Phases 1 + 2 — model `fee` removal must precede router cleanup
- **US4 (Phase 5)**: No dependencies on other stories — independent verification
- **Polish (Phase 6)**: Depends on all implementation phases

### User Story Dependencies

| Story | Depends On | Can run parallel with |
|-------|-----------|----------------------|
| US1 (P1) | Phase 1 | US2 |
| US2 (P1) | Phase 1 | US1 |
| US3 (P2) | Phases 1+2 | US4 |
| US4 (P3) | None (verification only) | All |

### Within Each Phase

- **[P] tasks** can run in parallel (different files)
- Non-[P] tasks run sequentially
- Model/schema changes before service logic
- Implementation before tests

---

## Parallel Opportunities

- T001 + T002: migration + schema SQL (different files)
- T003 + T004 + T005: model + schema changes (3 different files/sections)
- T007 + T008: schema + router changes for US2 (different files)
- T012 + T013 + T014: test updates (different test sections in same file — sequential recommended)
- US1 and US2 can be implemented by different developers in parallel after Phase 1

---

## Parallel Example: US1 + US2

```bash
# Phase 2 (US1) parallel launch:
Task: "T003 Remove fee from TeamBase"
Task: "T004 Add student_fees to RegisterTeamInput"
Task: "T005 Remove fee from TeamDTO"

# Wait for T003-T005, then:
Task: "T006 Update register_team() service logic"

# Phase 3 (US2) can run same time as T006:
Task: "T007 Add fee to AddTeamMemberInput schema"
Task: "T008 Add fee to AddTeamMemberInput router"
```

---

## Implementation Strategy

### MVP (Phases 1 + 2)

1. Complete Phase 1: Schema + migration
2. Complete Phase 2: US1 (register team with per-student fees)
3. **STOP and VALIDATE**: Register a team with `student_fees`, verify DB rows
4. MVP done — core behavioral change delivered

### Incremental Delivery

1. MVP: Phase 1 + 2 → US1 working
2. Add Phase 3 → US2 working (add member with fee)
3. Add Phase 4 → US3 working (clean API surface)
4. Add Phase 5 → US4 verified (fee_per_student retained)
5. Add Phase 6 → Test suite green

### Total Tasks: 15
- Phase 1: 2 tasks (0 [P])
- Phase 2 (US1): 4 tasks (3 [P])
- Phase 3 (US2): 3 tasks (2 [P])
- Phase 4 (US3): 1 task (0 [P])
- Phase 5 (US4): 1 task (0 [P])
- Phase 6 (Tests/Polish): 4 tasks (3 [P])

---

## Notes

- Repository `create_team()` accepts `fee` param but will receive `None` after removal — no change needed there
- All finance/analytics/CRM code is untouched — confirmed zero regression risk
- Migration drops `teams.fee` column — existing `member_share` on `TeamMember` is source of truth
- Pre-existing bug in `finance/reporting_repository.py:69` (`fee_share` vs `member_share`) is out of scope
