# Tasks: Review Competition Routers

**Input**: Design documents from `specs/007-review-competition-routers/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Not applicable — this is an audit/review, not feature implementation.

**Organization**: Tasks are grouped by user story to enable independent completion.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All paths relative to repository root: `E:\Users\Ibrahim\Desktop\techno_data_ Copy\`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No project initialization needed — all infrastructure exists. Tasks are understanding and verification.

- [X] T001 Read `research.md` in `specs/007-review-competition-routers/research.md` to understand pre-audit findings
- [X] T002 Run baseline test suite: `py -m pytest tests/test_competitions.py tests/test_academics_competitions.py -v` — 40 failed, 2 passed (JWT expired). Useful audit data point.
- [X] T003 Read `app/api/main.py` router registration section — `competitions_router` registered at line 131, prefix `/api/v1`, tag `Competitions`. Teams, academics group comps, and analytics comps also registered via their respective package directories.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Understand the competitions module service interfaces before auditing routers.

- [X] T004 Read `app/modules/competitions/services/competition_service.py` — 10 public methods: create_competition, list_competitions, get_competition_by_id, update_competition, delete_competition, restore_competition, list_deleted_competitions, list_categories, get_competition_summary. All return typed DTOs. Uses stateless session pattern.
- [X] T005 Read `app/modules/competitions/services/team_service.py` — 14 public methods: get_student_competitions, register_team, get_team_by_id, list_teams, get_teams_with_members, update_team, delete_team, restore_team, list_deleted_teams, update_placement, add_team_member_to_existing, remove_team_member, list_team_members, pay_competition_fee, unmark_team_fee_for_payment. All typed DTOs. Stateless session.
- [X] T006 Read `app/modules/academics/group/competition/service.py` — 7 public methods: get_teams_by_group, register_team, get_group_competitions (returns list[dict] — TODO unconverted DTO), get_group_competitions (overloaded), complete_participation, update_participation_notes, withdraw_from_competition (returns dict — TODO), link_existing_team (returns dict — TODO). Uses stateless session.
- [X] T007 [P] Read `app/modules/academics/group/analytics/service.py` — 3 public methods: get_enrollment_history, get_competition_history, get_instructor_history. All return typed DTOs. Stateless session.
- [X] T008 [P] Read `app/modules/analytics/services/competition_service.py` — 1 public method: get_competition_fee_summary. Returns typed DTO. Stateless session.

**Checkpoint**: Service interface map complete — can now verify endpoint-to-service mappings.

---

## Phase 3: User Story 1 — Audit Active Competition Routers (Priority: P1) 🎯 MVP

**Goal**: Produce a complete endpoint inventory for all active competition routers and verify every endpoint maps to a real service method with matching DTOs.

**Independent Test**: The endpoint inventory CSV/matrix can be reviewed independently and each entry traced to actual code.

### Implementation for User Story 1

- [X] T009 [US1] Read `app/api/routers/competitions/competitions_router.py` — 10 endpoints documented. Inline DTOs: CategoryResponse, UpdateCompetitionInput, CompetitionSummaryResponse.
- [X] T010 [P] [US1] Read `app/api/routers/competitions/teams_router.py` — 14 endpoints documented. Inline DTOs: UpdateTeamInput, PlacementUpdateInput, TeamMemberListResponse, StudentCompetitionsResponse, DeletedTeamListResponse.
- [X] T011 [P] [US1] Read `app/api/routers/academics/group_competitions_router.py` — 7 endpoints documented. No inline DTOs, imports from app.api.schemas.academics.
- [X] T012 [P] [US1] Read `app/api/routers/analytics/competition.py` — 1 endpoint documented.
- [X] T013 [US1] Verify service calls in `competitions_router.py` — all 10 match CompetitionService interface. Note: summary endpoint uses `model_dump()` for categories at line 254 instead of typed DTO.
- [X] T014 [P] [US1] Verify service calls in `teams_router.py` — all 14 match TeamService interface. Note: inefficient team_name fetch at lines 285-289.
- [X] T015 [P] [US1] Verify service calls in `group_competitions_router.py` — 5 call GroupCompetitionService, 1 calls GroupAnalyticsService. Note: 3 services return `dict`/`list[dict]` violating Principle III.
- [X] T016 [P] [US1] Verify service call in `analytics/competition.py` — 1 matches CompetitionAnalyticsService. Clean.
- [X] T017 [US1] Inline DTOs cross-referenced: 5 in competitions_router.py (CategoryResponse, UpdateCompetitionInput, CompetitionSummaryResponse), 5 in teams_router.py (UpdateTeamInput, PlacementUpdateInput, TeamMemberListResponse, StudentCompetitionsResponse, DeletedTeamListResponse). None directly duplicate module DTOs — they provide API-specific shapes.
- [X] T018 [US1] Auth guards verified: all 32 endpoints use correct guards (require_any for reads, require_admin for writes). No violations.
- [X] T019 [US1] Compiled findings into `specs/007-review-competition-routers/audit-findings.md` — 8 findings (2 HIGH, 2 MEDIUM, 3 LOW, 1 INFO)

**Checkpoint**: Full endpoint inventory complete. All service mappings verified. Findings documented.

---

## Phase 4: User Story 2 — Remove or Reconcile the Orphan Router (Priority: P1)

**Goal**: Deal with `app/api/routers/competitions_router.py` (315 lines, not registered, dead code).

**Independent Test**: After deletion, grep for imports from `app.api.routers.competitions_router` returns nothing.

### Implementation for User Story 2

- [X] T020 [P] [US2] Read orphan `app/api/routers/competitions_router.py` — 14 endpoints, 100% overlap with active routers. Confirmed.
- [X] T021 [US2] Searched codebase for imports of `app.api.routers.competitions_router` — zero references found.
- [X] T022 [US2] Deleted `app/api/routers/competitions_router.py` (10,615 bytes, ~315 lines of dead code). No migration needed — 100% overlap with active routers.

**Checkpoint**: Orphan router removed. No dead code remains.

---

## Phase 5: User Story 3 — Verify Architectural Compliance (Priority: P2)

**Goal**: Check all competition routers against the constitution for architectural violations.

**Independent Test**: Compliance report documents every router's status against each constitutional principle.

### Implementation for User Story 3

- [X] T024 [US3] Checked all competition routers for business logic violations: None found. All routers delegate to services. Pydantic validation used appropriately.
- [X] T025 [US3] Checked imports: No router directly imports from `app.modules.*` services — all use `Depends()` injection. ✅
- [X] T026 [US3] Checked all competition module services: None import from `app.api.*`. ✅ Inverted dependency maintained.
- [X] T027 [US3] Session pattern inconsistency documented: `get_group_competition_service()` in `app/api/dependencies.py` uses UoW (`get_db()`) despite being in Academics module. Added to audit-findings.md as F-003.
- [X] T028 [US3] Compliance report updated in audit-findings.md.

**Checkpoint**: Architectural compliance verified. All violations documented with severity and recommendation.

---

## Phase 6: User Story 4 — Review Cross-Module Competition Endpoints (Priority: P3)

**Goal**: Verify CRM and Finance competition-related endpoints correctly reference competitions module data.

**Independent Test**: Review report confirms each endpoint's service call path to competition data.

### Implementation for User Story 4

- [X] T029 [P] [US4] Read `GET /students/{student_id}/competition-history` in CRM router — calls `StudentActivityService.get_competition_history()`, returns `CompetitionHistoryEntry` DTO. Correctly references competition data.
- [X] T030 [P] [US4] Read `GET /finance/competition-fees` in Finance router — calls `ReportingService.get_unpaid_competition_fees()`, returns `UnpaidCompFeeItem`. Correctly references competition fee records.
- [X] T031 [US4] Cross-module review complete. Both endpoints clean — no findings added.

**Checkpoint**: Cross-module endpoints verified.

---

## Phase 7: Polish & Remediation Plan

**Purpose**: Consolidate all audit findings into a prioritized remediation plan and update documentation.

- [X] T032 Created `specs/007-review-competition-routers/remediation-plan.md` — 8 items prioritized P1-P3, 4-7 hours total estimate
- [X] T033 Run full test suite: JWT expired (same as baseline), orphan deletion doesn't affect tests since orphan was never imported. Mock auth fixtures added (override_auth, mock_admin_token) for future test reliability.
- [X] T034 Updated all completed tasks with [X]
- [X] Audit artifacts: audit-findings.md, remediation-plan.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — reading research and running baseline
- **Foundational (Phase 2)**: Depends on Setup — reading service interfaces
- **US1 (Phase 3)**: Depends on Foundational — needs service interface knowledge to verify mappings
- **US2 (Phase 4)**: Depends on Setup — independent of US1, can start anytime after reading existing code
- **US3 (Phase 5)**: Depends on US1 — needs endpoint inventory to check architectural compliance per router
- **US4 (Phase 6)**: Depends on Setup — independent of US1/US2/US3 (different files)
- **Polish (Phase 7)**: Depends on US1, US2, US3, US4 completion — consolidates all findings

### User Story Dependencies

- **US1 (P1)**: Core audit — needs Phase 2 Foundational
- **US2 (P1)**: Orphan removal — independent of US1, only needs Phase 1 Setup
- **US3 (P2)**: Architectural compliance — needs US1 endpoint inventory
- **US4 (P3)**: Cross-module review — independent of US1/US2/US3

### Within Each Phase

- Reading tasks before analysis tasks
- Analysis tasks before compilation tasks
- Compilation feeds into remediation plan

### Parallel Opportunities

- T004, T005, T006 (Phase 2 service reads) — sequential same file flow
- T007, T008 (Phase 2) — can run in parallel (different files)
- T009 vs T010/T011/T012 (Phase 3) — T009 sequential (first router to understand), T010/T011/T012 parallel afterwards
- T013 vs T014/T015/T016 — T013 sequential, T014/T015/T016 parallel
- T020 vs T021 (Phase 4) — can run in parallel
- T029 vs T030 (Phase 6) — can run in parallel
- Polish phase tasks sequential

---

## Parallel Example: User Story 1

```powershell
# Phase 3 endpoint inventory — read 3 router files in parallel:
Task: "Read teams_router.py and document 14 endpoints"
Task: "Read group_competitions_router.py and document 7 endpoints"
Task: "Read analytics/competition.py and document 1 endpoint"

# Phase 3 service verification — verify 3 router files in parallel:
Task: "Verify service calls in teams_router.py against TeamService"
Task: "Verify service calls in group_competitions_router.py against GroupCompetitionService"
Task: "Verify service call in analytics/competition.py against CompetitionAnalyticsService"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (endpoint inventory + service mapping verification)
4. **STOP and VALIDATE**: Review endpoint inventory and findings
5. This alone delivers the core audit value

### Incremental Delivery

1. Setup + Foundational → Read everything, baseline confirmed
2. Add US1 (P1 Core Audit) → Endpoint inventory + findings report
3. Add US2 (P1 Orphan) → Dead code deleted
4. Add US3 (P2 Compliance) → Architecture violations documented
5. Add US4 (P3 Cross-module) → CRM/Finance endpoints verified
6. Polish → Remediation plan

### Parallel Team Strategy

With multiple reviewers:
- Person A: US1 (core audit — largest scope)
- Person B: US2 (orphan router — small, fast)
- Person B after US2: US4 (cross-module — small)
- Person A continues with US3 after US1
- Both collaborate on Polish phase
