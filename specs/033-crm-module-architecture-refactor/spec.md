# Spec: CRM Module Architecture Refactor — Dead Code, Tuple Contracts & DTO Normalization

**Spec ID**: `033-crm-module-architecture-refactor`
**Date**: 2026-06-12
**Status**: Draft — Awaiting Clarification
**Builds on**: `031-unified-student-listing-dto` (done), `032-crm-module-finalization` (done)

---

## Background

The `module-architecture-guide` skill was run on `app/modules/crm/`. The module is on **Pattern A**
(traditional horizontal layers) — which is **correct and will not change**. The academics `group/`
module uses D+ (sliced by concern). CRM does not need that: it has two ORM entities (Student, Parent)
plus a cross-cutting Activity concern. D+ would add indirection without benefit at this scale.

After specs 031 and 032 landed, one category of violations remains: **raw `Tuple` return types** in
service and repository contracts, **dead repository methods** that were superseded by raw-SQL service
logic, and **fragile positional tuple destructuring** in the profile service. These are the targets
of this sprint.

---

## Scope

**In scope**:
- `app/modules/crm/repositories/student_repository.py`
- `app/modules/crm/services/student_crud_service.py`
- `app/modules/crm/services/student_profile_service.py`
- `app/modules/crm/services/activity_service.py`
- `app/modules/crm/repositories/activity_repository.py`
- `app/modules/crm/interfaces/__init__.py`
- `app/modules/crm/interfaces/iactivity_repository.py`
- `app/modules/crm/interfaces/dtos/` (new files only)
- `app/modules/crm/schemas/student_details.py`
- `app/modules/crm/schemas/student_schemas.py`

**Out of scope**:
- `app/api/routers/crm/` — no endpoint signature changes
- `app/api/schemas/crm/` — no API-boundary schema changes
- `SearchService` — already clean (raw SQL, correct DTOs)
- `ParentCrudService` / `ParentRepository` — covered by 032, not re-opened here

---

## Audit Findings (post-031, post-032 baseline)

### A. Dead Repository Methods

These methods exist in `StudentRepository` but are **never called through the UoW** anywhere in CRM.
They were superseded when `SearchService` took over listing/counting with raw SQL.

| ID | Method | Location | Superseded by |
|----|--------|----------|---------------|
| A1 | `search(query)` | `student_repository.py:57` | `SearchService.search()` |
| A2 | `count(active_only)` | `student_repository.py:65` | `SearchService.count()` |
| A3 | `count_by_status(status)` | `student_repository.py:71` | `SearchService.count_by_status()` |
| A4 | `update_status(...)` | `student_repository.py:76` | `StudentCrudService.update_status()` mutates model directly |
| A5 | `set_waiting_priority(...)` | `student_repository.py:90` | `StudentCrudService.set_waiting_priority()` mutates model directly |
| A6 | `get_with_parent(...)` | `student_repository.py:210` | Deprecated alias — `get_student_with_parent()` is the live method |
| A7 | `get_all_enriched(...)` | `student_repository.py:224` | `SearchService._list_all_enriched()` (also contains an `.group_name` bug — `Group.name` is correct) |
| A8 | `get_by_status(status)` | `student_repository.py:402` | `SearchService.get_by_status()` raw SQL |
| A9 | `get_waiting_list()` | `student_repository.py:407` | `SearchService.get_waiting_list()` raw SQL |

### B. Stale IStudentRepository Protocol

`interfaces/__init__.py` declares all dead A-series methods in the Protocol. The Protocol must be
pruned to match only the methods services actually call through the UoW.

Methods **to keep**: `create`, `get_by_id`, `get_by_name_and_dob`, `get_all`, `delete`, `get_with_parent` (renamed to `get_student_with_parent`), `link_parent`, `get_student_parents`, `get_student_balance_summary`, `get_student_siblings_with_details`, `get_attendance_stats`, `get_active_enrollment_with_details`, `soft_delete_student`, `restore_student`, `hard_delete`, `get_deleted`.

Methods **to remove**: `search`, `count`, `count_by_status`, `update_status`, `set_waiting_priority`, `get_all_enriched`, `get_with_parent` (wrong name).

### C. Raw `Tuple` Return Types (typed-contract violation)

| ID | File | Method | Current return | Target |
|----|------|--------|---------------|--------|
| C1 | `student_repository.py:418` | `get_active_enrollment_with_details` | `Optional[Tuple[int, str, int, str, int, Optional[str], int]]` | `Optional[ActiveEnrollmentDTO]` |
| C2 | `activity_repository.py:175` | `get_enrollment_history_by_student` | `Tuple[List[EnrollmentHistoryDTO], int]` | `EnrollmentHistoryResultDTO` |
| C3 | `activity_repository.py:250` | `get_status_history_by_student` | `Tuple[List[StatusHistoryDTO], int]` | `StatusHistoryResultDTO` |
| C4 | `activity_repository.py:307` | `get_competition_history_by_student` | `Tuple[List[CompetitionHistoryDTO], int]` | `CompetitionHistoryResultDTO` |
| C5 | `activity_service.py:292` | `get_enrollment_history` | same Tuple passthrough | `EnrollmentHistoryResultDTO` |
| C6 | `activity_service.py:298` | `get_status_history` | same Tuple passthrough | `StatusHistoryResultDTO` |
| C7 | `activity_service.py:304` | `get_competition_history` | same Tuple passthrough | `CompetitionHistoryResultDTO` |

### D. Fragile Positional Tuple Destructuring

`student_profile_service.py` destructures the 7-element tuple from `get_active_enrollment_with_details`
in two places by positional index — once by name at line 40, once by integer index at lines 95–105
(`enrollments_data[0]`, `enrollments_data[1]`, …`enrollments_data[6]`). Resolving C1 eliminates both
fragile call sites.

### E. Silent Data-Loss Bug

`student_profile_service.py:177` passes `attendance_stats=attendance_stats` to `StudentWithDetails()`
constructor, but `StudentWithDetails` has no `attendance_stats` field — Pydantic silently ignores the
extra kwarg. Two options: add the field or remove the dead kwarg (see Open Question OQ-1 below).

### F. commit/flush Ordering Bug

`student_crud_service.py:update_student` (lines 118–119) calls `self._uow.commit()` then
`self._uow.flush()`. `flush()` after `commit()` is a no-op and incorrect; the correct order for a
UoW pattern is `flush()` → `commit()`. This is a correctness bug (flush propagates pending state
before the commit finalises it).

### G. model_config Normalization

Several DTOs in `schemas/student_details.py` use the raw dict syntax `model_config = {"from_attributes": True}` instead of the Pydantic v2 canonical `ConfigDict(from_attributes=True)`. Missing `model_config` entirely on `StudentStatusSummaryDTO` and `StudentSiblingDTO`.

---

## Open Questions (Clarifications Needed)

### OQ-1 — `attendance_stats` field: add or remove?

`StudentWithDetails` is missing an `attendance_stats: AttendanceStatsDTO` field. The service already
computes the value and tries to pass it. Two paths:

- **Option A (Add)**: Add `attendance_stats: Optional[AttendanceStatsDTO] = None` to `StudentWithDetails` and keep the existing computation. The frontend would then receive this data in the student profile response — is this wanted?
- **Option B (Remove)**: The `get_attendance_stats()` call in `get_student_details` is dead weight — `enrollment_attendance` already provides the same data more granularly. Remove the call and the kwarg entirely.

> **Recommendation**: Option B (remove) — the richer `enrollment_attendance` field already exposes per-session breakdown, which subsumes what `AttendanceStatsDTO` provides. But this needs product confirmation.

---

### OQ-2 — `get_active_enrollment_with_details` multi-enrollment behavior

The repository currently returns only the **most recent** active enrollment (`.limit(1)`). If a student
has two simultaneous active enrollments (rare edge case), only one is surfaced. Should:

- **Option A (keep)**: Retain single-enrollment behavior — the profile shows "current group" as singular.
- **Option B (multi)**: Return `List[ActiveEnrollmentDTO]` and update the profile service to handle all. The `enrollments` list on `StudentWithDetails` already attempts this but it is populated by the same single-result query.

> **Recommendation**: Option A — the business domain (one student, one active group at a time) supports this; multi-enrollment is a future product question.

---

### OQ-3 — Are callers of `IStudentRepository` protocol methods (outside CRM) relying on `get_all_enriched` or `update_status`?

Before deleting dead methods from the Protocol, need to confirm no other module imports and calls
`IStudentRepository` to use `get_all_enriched` / `update_status` via the protocol type.

> **Action**: `grep -rn "IStudentRepository" app/` to confirm scope of usage before deletion.

---

### OQ-4 — `get_student_with_parent` vs `get_with_parent` naming

The live implementation is `get_student_with_parent` but the Protocol declares the stale alias
`get_with_parent`. Renaming the Protocol method is safe since the Protocol is only used for type
checking. Confirm no runtime `isinstance(repo, IStudentRepository)` check depends on method name.

---

## Reference: academics/group D+ Pattern (NOT the target for CRM)

The academics `group/` module uses D+ pattern: split into `core/`, `directory/`, `lifecycle/`,
`analytics/`, `details/`, `level/` slices. Each slice has `interface.py`, `service.py`,
`repository.py`, `schemas.py`. Models stay horizontal in `models/`.

**CRM does NOT adopt this structure.** Reasons:
- CRM has only 2 ORM entities vs Group's single dominant entity with many concerns
- CRM services are already cleanly separated by concern (crud / profile / search / activity)
- Adding slices would require splitting the UoW, which currently gives all services transactional coherence
- Pattern A already works; D+ is for dominant-entity complexity, not two-entity CRUD

The `group/core/interface.py` is shown below as the target style for how CRM's `IStudentRepository`
Protocol should look after pruning — concise, typed, no dead methods:

```python
# group/core/interface.py (reference style)
@runtime_checkable
class GroupCoreRepositoryInterface(Protocol):
    def create_group(self, session, group: Group) -> Group: ...
    def get_group_by_id(self, session, group_id: int) -> Group | None: ...
    def update_group_status(self, session, group_id: int, status: str) -> Group | None: ...
    def increment_group_level(self, session, group_id: int) -> Group | None: ...
```

---

## Implementation Order

```
Phase 0 — Dead Code Deletion (MANDATORY FIRST)
  └─ A1–A9: Delete 9 dead methods from student_repository.py
  └─ B:     Prune IStudentRepository Protocol to live methods only
  └─ Verify: grep for deleted method names, confirm 0 import references

Phase 1 — New Result DTOs
  └─ NEW interfaces/dtos/active_enrollment_dto.py  → ActiveEnrollmentDTO
  └─ NEW interfaces/dtos/history_result_dtos.py    → EnrollmentHistoryResultDTO,
                                                     StatusHistoryResultDTO,
                                                     CompetitionHistoryResultDTO
  └─ MODIFY interfaces/dtos/__init__.py            → export new DTOs

Phase 2 — Repository Fixes (C1–C4)
  └─ student_repository.py: get_active_enrollment_with_details returns ActiveEnrollmentDTO
  └─ activity_repository.py: 3 history methods return result DTOs
  └─ iactivity_repository.py: update 3 Protocol signatures

Phase 3 — Service Fixes (C5–C7, D, E, F)
  └─ student_profile_service.py:
       - _get_current_enrollment_info: use ActiveEnrollmentDTO fields
       - get_student_details: use dto attributes not positional indices
       - Resolve OQ-1 (add or remove attendance_stats)
  └─ activity_service.py:
       - 3 history methods return result DTOs
       - Remove Tuple from typing imports
  └─ student_crud_service.py:
       - Fix update_student: flush() before commit()

Phase 4 — Schema Normalization (G)
  └─ schemas/student_details.py: ConfigDict(from_attributes=True) on all DTOs
  └─ schemas/student_schemas.py: add missing model_config to output DTOs

Phase 5 — Verify
  └─ pytest tests/test_crm*.py -v
  └─ grep -rn "Tuple\[List\[" app/modules/crm/ → 0 results
  └─ grep -rn "def search\|def count\|def get_all_enriched" app/modules/crm/repositories/student_repository.py → 0 results
  └─ python -c "from app.modules.crm import StudentCrudService, SearchService, StudentProfileService, StudentActivityService"
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| A router uses `students.search()` directly via UoW (grep missed it) | Very Low | High | Run `grep -rn "\.students\.search\|\.students\.count\|\.students\.get_all_enriched"` across entire `app/` before deletion |
| `get_active_enrollment_with_details` callers outside CRM | Low | High | `grep -rn "get_active_enrollment_with_details" app/` before changing signature |
| `ActivityService` callers (in finance, enrollments) unpack the returned Tuple | Medium | Medium | Check all callers of `get_enrollment_history`, `get_status_history`, `get_competition_history` in API routers before changing return types |
| `flush()` → `commit()` fix changes transaction semantics | Very Low | Low | `flush()` before `commit()` is always the correct order in SQLAlchemy |

---

## Success Criteria

| ID | Criterion |
|----|-----------|
| SC-001 | `grep -rn "Tuple\[List\[" app/modules/crm/` returns 0 results |
| SC-002 | `grep -rn "Optional\[Tuple\[" app/modules/crm/` returns 0 results |
| SC-003 | `student_repository.py` has no dead methods: search, count, count_by_status, update_status, set_waiting_priority, get_with_parent, get_all_enriched, get_by_status, get_waiting_list |
| SC-004 | `IStudentRepository` Protocol matches only the live method set (no dead stubs) |
| SC-005 | `student_profile_service.py` contains no `enrollments_data[0]`, `enrollments_data[1]` etc (no positional tuple indexing) |
| SC-006 | All existing CRM tests pass with 0 regressions |
| SC-007 | `update_student` calls `flush()` before `commit()` |
| SC-008 | All output DTOs in `schemas/student_details.py` use `ConfigDict(from_attributes=True)` |
