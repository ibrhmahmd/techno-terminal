---
description: "Task list for 031-unified-student-listing-dto"
---

# Tasks: Unified Student Listing DTO

**Input**: Design documents from `specs/031-unified-student-listing-dto/`  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data model**: [data-model.md](./data-model.md) | **Contracts**: [contracts/api-contracts.md](./contracts/api-contracts.md)

**Tests**: Test tasks included for SC-003 through SC-006 per spec measurable outcomes.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete sibling tasks)
- **[Story]**: User story label (US1–US4)
- **No story label**: Setup or Foundational phase tasks

---

## Phase 1: Setup

**Purpose**: Confirm `StudentValidator.compute_age` handles `None` safely — the single shared utility underpinning all age computations.

- [x] T001 Verify `StudentValidator.compute_age(None)` returns `None` in `app/modules/crm/schemas/student_schemas.py` — read the method and confirm null-safe behavior. If not null-safe, add the guard before any other work begins.

**Checkpoint**: `compute_age(None) → None` confirmed or fixed. All story phases may now proceed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The `StudentListingDTO` API schema and the updated `StudentFilterDTO` input DTO must exist before any endpoint or service work can reference them. These two changes have zero dependencies between each other and can be done in parallel.

⚠️ **CRITICAL**: No user story work (Phase 3+) can begin until T002 and T003 are complete.

- [x] T002 [P] Add `StudentListingDTO` to `app/api/schemas/crm/student.py` — define the unified schema with fields: `id`, `full_name`, `status`, `phone`, `date_of_birth` (`Optional[date]`), `age` (`Optional[int]`), `gender`, `current_group_name` (`Optional[str]`), `has_unpaid_balance` (`bool = False`). Add `field_validator` for `date_of_birth` to coerce `datetime` → `date`. Set `model_config = ConfigDict(from_attributes=True)`.

- [x] T003 [P] Rename `has_unpaid_balance` → `has_any_outstanding_balance` in `app/modules/crm/interfaces/dtos/student_filter_dto.py` — field on line 43. Update its docstring. No logic change; semantics preserved (all-enrollment scope).

**Checkpoint**: `StudentListingDTO` importable, `StudentFilterDTO.has_any_outstanding_balance` defined. User story phases can now begin.

---

## Phase 3: User Story 1 — Frontend Student Directory Loads with Consistent Data (Priority: P1) 🎯 MVP

**Goal**: `GET /crm/students` (paginated list) returns `StudentListingDTO` items including `age`, `date_of_birth`, `gender`, `current_group_name`, and `has_unpaid_balance` on every record.

**Independent Test**: Call `GET /crm/students?limit=5` — verify every item in the response contains all unified DTO fields and that a student with an active unpaid enrollment has `has_unpaid_balance: true`.

### Implementation for User Story 1

- [ ] T004 [US1] Rewrite the paginated list SQL query in `app/modules/crm/services/search_service.py` (`list_all` method or its repository call) to include: `LEFT JOIN enrollments e ON e.student_id = s.id AND e.status = 'active'`, `LEFT JOIN groups g ON g.id = e.group_id`, `DISTINCT ON (s.id) ORDER BY s.id, e.id DESC`, and an EXISTS subquery against `v_unpaid_enrollments vue WHERE vue.student_id = s.id` as `has_unpaid_balance`. The query must remain paginated at the DB level (`OFFSET :skip LIMIT :limit`).

- [ ] T005 [US1] Update the paginated list service method in `app/modules/crm/services/search_service.py` to map raw SQL rows → `StudentListingDTO` items: call `StudentValidator.compute_age(row.date_of_birth)` for `age`; map all other fields directly. Return `list[StudentListingDTO]`.

- [ ] T006 [US1] Update `GET /crm/students` router handler in `app/api/routers/crm/students_router.py` to use `StudentListingDTO` as the response item type. Remove any mapping from `StudentListItem`. Update the `response_model` annotation.

- [ ] T007 [US1] Write test in `tests/test_crm.py` (or nearest student test file): `test_student_list_unified_dto` — calls `GET /crm/students?limit=50`, records response time as baseline, asserts every item has `has_unpaid_balance` (bool), `age` (int or None), `current_group_name` (str or None), `date_of_birth` (str or None). Assert response time < 2× baseline (SC-003 proxy).

- [ ] T008 [US1] Write test `test_student_has_unpaid_balance_true` — seeds a student with an active enrollment that has `amount_due > 0` and no payment, calls `GET /crm/students`, asserts that student's `has_unpaid_balance` is `true`. Write companion `test_student_has_unpaid_balance_false` for fully-paid enrollment (SC-005).

**Checkpoint**: `GET /crm/students` returns unified DTO. Tests pass. US1 independently verifiable.

---

## Phase 4: User Story 2 — Search Results Match the Unified Shape (Priority: P2)

**Goal**: `GET /crm/students?q={query}` returns `StudentListingDTO` items including `age` (previously missing).

**Independent Test**: Call `GET /crm/students?q=a` — verify every result item contains `age` field (may be null) and `has_unpaid_balance` (bool). A student with `date_of_birth = null` must return `age: null`.

### Implementation for User Story 2

- [ ] T009 [US2] Update `search` method in `app/modules/crm/services/search_service.py`: add `EXISTS (SELECT 1 FROM v_unpaid_enrollments vue WHERE vue.student_id = s.id) AS has_unpaid_balance` and the active enrollment LEFT JOIN for `current_group_name` to the existing search SQL. Map results to `StudentListingDTO` (call `compute_age` for `age`).

- [ ] T010 [US2] Update the `GET /crm/students?q=` branch in `app/api/routers/crm/students_router.py` to use `StudentListingDTO` as response item type. Confirm it shares the same router handler as the paginated list (if `q` is a query param on the same endpoint) or update separately.

- [ ] T011 [US2] Write test `test_student_search_unified_dto` — calls `GET /crm/students?q=a`, asserts every item has `age` (int or None) and `has_unpaid_balance` (bool). Write `test_student_search_null_dob_age` — seeds a student with `date_of_birth = NULL`, searches for them, asserts `age: null` (SC-005 age null check).

**Checkpoint**: Search results match unified DTO. Tests pass. US2 independently verifiable.

---

## Phase 5: User Story 3 — Filter Results Match the Unified Shape (Priority: P3)

**Goal**: `GET /crm/students/filter` uses renamed query param `has_any_outstanding_balance`, returns `date_of_birth`, and replaces `unpaid_balance` (float) with `has_unpaid_balance` (bool) and `enrollment_count` with `current_enrollment_count`.

**Independent Test**: Call `GET /crm/students/filter` (no params), verify items have `date_of_birth`, `has_unpaid_balance` (bool). Call with `?has_any_outstanding_balance=true`, verify only students with any outstanding balance appear. Confirm `?has_unpaid_balance=true` is NOT accepted (old param gone).

### Implementation for User Story 3

- [ ] T012 [US3] Update `StudentFilterItemDTO` in `app/modules/crm/interfaces/dtos/student_filter_result_dto.py`: rename `enrollment_count` → `current_enrollment_count`; replace `unpaid_balance: Optional[float]` with `has_unpaid_balance: bool = False`; add `date_of_birth: Optional[date] = None`.

- [ ] T013 [US3] Update `filter_students` SQL in `app/modules/crm/services/search_service.py`: rename the `has_unpaid_balance` WHERE-clause key to `has_any_outstanding_balance` (matching the renamed `StudentFilterDTO` field from T003). Add `date_of_birth` to the SELECT list. Change the `unpaid_balance` numeric column to a boolean `has_unpaid_balance` (`CASE WHEN total_due > 0 THEN TRUE ELSE FALSE END`). Rename the CTE output alias `enrollment_count` → `current_enrollment_count`.

- [ ] T014 [US3] Update the `GET /crm/students/filter` router handler in `app/api/routers/crm/students_router.py`: rename the `has_unpaid_balance` query parameter to `has_any_outstanding_balance`. Update the `StudentFilterDTO` construction to use the new field name. Update response item mapping from `StudentFilterItemDTO` → `StudentListingDTO` (preserving filter-specific extras as extended fields or alongside the core DTO).

- [ ] T015 [US3] Write test `test_filter_renamed_param` — calls `GET /crm/students/filter?has_any_outstanding_balance=true`, asserts only students with any outstanding balance appear. Calls `GET /crm/students/filter?has_unpaid_balance=true` and asserts it either returns a 422 or is ignored (old param gone — SC-006).

- [ ] T016 [US3] Write test `test_filter_response_fields` — calls `GET /crm/students/filter`, asserts items have `date_of_birth` and `has_unpaid_balance` (bool). Asserts `unpaid_balance` (float) field is NOT present. Asserts `current_enrollment_count` is present and `enrollment_count` is NOT.

**Checkpoint**: Filter endpoint uses new param name, returns unified shape. Tests pass. US3 independently verifiable.

---

## Phase 6: User Story 4 — Grouped and Waiting-List Views Match the Unified Shape (Priority: P4)

**Goal**: `GET /crm/students/grouped` student objects include `age` and `has_unpaid_balance`. `GET /crm/students/waiting-list` items include `age` and `has_unpaid_balance` (all-enrollment scope), while preserving `waiting_since`, `waiting_priority`, `waiting_notes`.

**Independent Test**: Call `GET /crm/students/grouped?group_by=status` — verify student objects inside each bucket have `age` (int or None) and `has_unpaid_balance` (bool). Call `GET /crm/students/waiting-list` — verify items have `has_unpaid_balance` and `waiting_since` both present.

### Implementation for User Story 4 — Grouped

- [ ] T017 [P] [US4] Add `has_unpaid_balance: bool = False` to `StudentSummaryDTO` in `app/modules/crm/interfaces/dtos/student_summary_dto.py`.

- [ ] T018 [P] [US4] Update `get_all_enriched()` repository SQL in `app/modules/crm/repositories/student_repository.py` (or wherever `list_all_enriched` raw SQL lives): add `EXISTS (SELECT 1 FROM v_unpaid_enrollments vue WHERE vue.student_id = s.id) AS has_unpaid_balance` to the SELECT. Map result to `StudentSummaryDTO`.

- [ ] T019 [US4] Update `get_grouped` service method in `app/modules/crm/services/search_service.py`: after Python-side grouping, map each `StudentSummaryDTO` → `StudentListingDTO` (calling `compute_age` for `age`). Python-side grouping/pagination retained (known tradeoff per plan).

- [ ] T020 [US4] Update `GET /crm/students/grouped` router handler in `app/api/routers/crm/students_router.py` to serialize grouped bucket students as `StudentListingDTO`.

### Implementation for User Story 4 — Waiting List

- [ ] T021 [P] [US4] Update `get_waiting_list` SQL in `app/modules/crm/services/search_service.py`: add `EXISTS (SELECT 1 FROM v_enrollment_balance veb WHERE veb.student_id = s.id AND veb.amount_remaining > 0) AS has_unpaid_balance` to the SELECT. This is the all-enrollment-scope variant (not `v_unpaid_enrollments`). Map to response objects including waiting-list extras (`waiting_since`, `waiting_priority`, `waiting_notes`).

- [ ] T022 [US4] Update `GET /crm/students/waiting-list` router handler in `app/api/routers/crm/students_router.py` to include `has_unpaid_balance` and `age` (via `compute_age`) in the response. Waiting-specific fields must be preserved alongside unified DTO fields.

- [ ] T023 [US4] Write test `test_grouped_unified_dto` — calls `GET /crm/students/grouped?group_by=status`, asserts first student in any bucket has `age` (int or None) and `has_unpaid_balance` (bool).

- [ ] T024 [US4] Write test `test_waiting_list_unpaid_balance` — seeds a waiting student who has a prior completed enrollment with unpaid balance; calls `GET /crm/students/waiting-list`; asserts `has_unpaid_balance: true`. Write companion for a waiting student with no prior enrollment history asserting `has_unpaid_balance: false`.

**Checkpoint**: All five endpoints return unified DTO. All story tests pass.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T025 Dead code audit: grep for all callers of `StudentListItem` across `app/`. If no callers remain after the router updates, delete `StudentListItem` from `app/api/schemas/crm/student.py`. If callers exist outside the student router (e.g., detail endpoint), note them in a comment for follow-up.

- [ ] T026 Audit `__init__.py` exports: check `app/modules/crm/interfaces/dtos/__init__.py` — if `StudentFilterItemDTO` or `StudentSummaryDTO` are exported under old field assumptions, verify the exports still hold after field renames (they should, since class names unchanged).

- [ ] T027 [P] Run full test suite `pytest tests/ -v` and confirm all existing tests pass (SC-004). Address any test failures caused by field renames before merging.

- [ ] T028 [P] Notify frontend team of two coordinated breaking changes: (1) filter query param `has_unpaid_balance` → `has_any_outstanding_balance`; (2) filter response fields `enrollment_count` → `current_enrollment_count` and `unpaid_balance` (float) → `has_unpaid_balance` (bool). Provide the contracts doc at `specs/031-unified-student-listing-dto/contracts/api-contracts.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **blocks all story phases**
- **Phase 3 (US1)**: Depends on Phase 2
- **Phase 4 (US2)**: Depends on Phase 2 — independent of Phase 3 (different SQL method)
- **Phase 5 (US3)**: Depends on Phase 2 AND T003 (filter DTO rename) — independent of US1/US2
- **Phase 6 (US4)**: Depends on Phase 2 — T017/T018 (grouped) independent of T021/T022 (waiting-list)
- **Phase 7 (Polish)**: Depends on all story phases complete

### Within Each Story

- DTO/schema tasks → service SQL tasks → router wiring → tests
- T017 and T018 (grouped) can parallelize with T021 (waiting-list SQL) since they touch different methods

### Parallel Opportunities

```
Phase 2:  T002 ‖ T003          (different files: api schemas vs service DTOs)
Phase 4:  T009–T011 ‖ Phase 3 tasks (different search method, different SQL)
Phase 6:  T017 ‖ T018 ‖ T021  (different files/methods)
Phase 7:  T027 ‖ T028          (tests vs communication)
```

---

## Parallel Example: Phase 6

```text
# Grouped sub-track (can start after T002):
T017 → Add has_unpaid_balance to StudentSummaryDTO
T018 → Update get_all_enriched() SQL
T019 → Update get_grouped() service mapping
T020 → Update grouped router handler

# Waiting-list sub-track (can start after T002, independently):
T021 → Update get_waiting_list() SQL (v_enrollment_balance scope)
T022 → Update waiting-list router handler
```

---

## Implementation Strategy

### MVP First (User Story 1 — Phase 3 Only)

1. Complete Phase 1 (T001)
2. Complete Phase 2 (T002, T003)
3. Complete Phase 3 (T004–T008)
4. **STOP and VALIDATE**: `GET /crm/students` returns unified DTO — frontend can use it for the directory page immediately
5. Ship Phase 3 and iterate on US2–US4

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundational ready
2. Phase 3 (US1) → Paginated list unified → **Demo-ready, frontend unblocked on directory page**
3. Phase 4 (US2) → Search unified → Frontend search bar consistent
4. Phase 5 (US3) → Filter unified + param renamed → **Breaking change lands, frontend migration required**
5. Phase 6 (US4) → Grouped + waiting-list unified → Complete coverage
6. Phase 7 → Dead code cleanup + test validation

---

## Notes

- All `[P]` tasks operate on different files with no shared state — safe to run simultaneously
- The filter param rename (T003, T013, T014) is a coordinated breaking change — land with frontend PR in the same deploy window
- `has_unpaid_balance` in the waiting-list SQL uses `v_enrollment_balance` (all-history), NOT `v_unpaid_enrollments` (active-only) — this distinction is intentional per spec FR-008 and must not be accidentally normalized
- Python-side grouping in the grouped endpoint is a documented known tradeoff — do not refactor to DB-level in this sprint
- Commit after each phase checkpoint for clean rollback points
