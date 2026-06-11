# API Contracts: CRM Module Finalization

**Spec**: `032-crm-module-finalization`  
**Date**: 2026-06-11  
**Base spec**: `031-unified-student-listing-dto/contracts/api-contracts.md` (unified DTO shape preserved)

---

## Summary of Changes

| Category | Change | Scope |
|---|---|---|
| DTO replacement | `-> dict` → typed DTOs | Service/repository layer |
| Schema deletion | `StudentListItem` removed | API boundary |
| Schema deletion | `ParentCreate`, `ParentUpdate` removed | API boundary |
| Schema move | `StudentWithDetails` et al. moved from `api/schemas` → `module/schemas` | Internal (re-exported) |
| Endpoint removal | `GET /students/{id}/status-history` stub deleted | API |
| Endpoint response | `/admin/deleted-students`: `StudentListItem` → `StudentListingDTO` | Breaking |
| Endpoint response | `/students/waiting-list`: `StudentResponseDTO` → `WaitingStudentDTO` | Breaking |
| Endpoint response | `/students/{id}/soft`, `/restore`, `/hard`: `dict` → `StudentDeletionResult` | Additive |
| Input schema | `POST /parents/`: `ParentCreate` → `RegisterParentInput` | Additive (phone validation added) |
| Input schema | `PATCH /parents/{id}`: `ParentUpdate` → `UpdateParentDTO` | Internal only |
| Method rename | `get_recent_activity(limit)` → `get_recent_activities(days, limit)` | Internal API (no HTTP change) |
| Property added | `StudentUnitOfWork.session` (public property) | Internal |

---

## 1. `GET /crm/students` — Paginated Student List

**route**: `students_router.py:62`  
**response_model**: `PaginatedResponse[StudentListingDTO]`

### Request Parameters (unchanged)
- `skip: int = 0`
- `limit: int = 50`

### Response Item Shape: `StudentListingDTO`

```json
{
  "id": 42,
  "full_name": "Ahmed Hassan",
  "status": "active",
  "phone": "01012345678",
  "date_of_birth": "2012-03-15",
  "age": 14,
  "gender": "male",
  "current_group_name": "Level 2 - Saturday",
  "has_unpaid_balance": true
}
```

**Nullable**: `phone`, `date_of_birth`, `age`, `gender`, `current_group_name`  
**Always present**: `id`, `full_name`, `status`, `has_unpaid_balance`  

**🔴 Issue**: `date_of_birth` type is `Optional[date]` in `StudentListingDTO` but source data from `StudentSummaryDTO` can contain `datetime` objects. The `@field_validator("date_of_birth", mode="before")` handles this conversion — works but relies on Pydantic validation rather than type alignment.

---

## 2. `GET /crm/students?q=...` — Search

**route**: same as #1 (shared list endpoint)  
**response_model**: `PaginatedResponse[StudentListingDTO]` — same item shape.

---

## 3. `GET /crm/students/grouped` — Grouped Listing

**route**: `students_router.py:131`  
**response_model**: `ApiResponse[StudentGroupedResultDTO]`

### Envelope shape (unchanged outer structure)

```json
{
  "success": true,
  "data": {
    "group_by": "status",
    "total_unique_students": 95,
    "total": 95,
    "groups": [
      {
        "key": "active",
        "label": "Active",
        "count": 80,
        "students": [ { ...StudentListingDTO... } ]
      }
    ]
  }
}
```

**Default limit per group**: 50 (query param: `limit: int = Query(50, ge=1, le=200)`)

**Implementation note**: `get_grouped()` now calls `_list_all_enriched()` (raw SQL with `v_unpaid_enrollments` subquery). The `StudentSummaryDTO` instances are rebuilt with `age` computed via `StudentValidator.compute_age()`. Previously it delegated to `self._uow.students.get_all_enriched()` which returned ORM-based objects.

---

## 4. `GET /crm/students/filter` — Multi-criteria Filter

**route**: `students_router.py:159`  
**response_model**: `ApiResponse[StudentFilterResultDTO]`

### Query Parameters

| Parameter | Type | Prev Name | Notes |
|---|---|---|---|
| `has_any_outstanding_balance` | `bool \| null` | `has_unpaid_balance` | **Breaking rename** |
| *(all other params unchanged)* | | | |

### Response Item Changes

| Field | Old | New | Notes |
|---|---|---|---|
| `has_unpaid_balance` | float `unpaid_balance` | boolean | **Breaking** |
| `current_enrollment_count` | `enrollment_count` | renamed | **Breaking** |
| `date_of_birth` | — | added | Additive |

**Preserved filter-specific fields**: `current_group_id`, `group_default_day`, `instructor_id`, `instructor_name`, `current_enrollment_count`, `enrolled_courses`.

---

## 5. `GET /crm/students/waiting-list` — Waiting List

**route**: `students_router.py:220`  
**response_model**: `ApiResponse[list[WaitingStudentDTO]]`  
**🔴 Breaking change**: previously returned `ApiResponse[list[StudentResponseDTO]]`.

### Response Item Shape: `WaitingStudentDTO` (extends `StudentListingDTO`)

```json
{
  "id": 15,
  "full_name": "Sara Ali",
  "status": "waiting",
  "phone": "01098765432",
  "date_of_birth": "2014-07-20",
  "age": 11,
  "gender": "female",
  "current_group_name": null,
  "has_unpaid_balance": true,
  "waiting_since": "2026-05-01T10:00:00Z",
  "waiting_priority": 1,
  "waiting_notes": "Preferred Saturday morning"
}
```

### Layer Gap ⚠️

Service returns `List[WaitingListStudentDTO]` (module schema, no `current_group_name`, `date_of_birth` is `datetime`).  
Router declares `response_model=ApiResponse[list[WaitingStudentDTO]]` (API schema, has `current_group_name`, `date_of_birth` is `date`).  
Serialization works because FastAPI fills missing fields with defaults and the `field_validator` converts datetime→date, but these two DTOs should ideally be aligned.

**🔴 Issue**: `WaitingListStudentDTO.date_of_birth` is `Optional[datetime]` while `WaitingStudentDTO` (via `StudentListingDTO`) is `Optional[date]`. Output is consistent after validation, but the type mismatch is confusing and fragile.

---

## 6. `POST /crm/students` — Register Student

**route**: `students_router.py:107`  
**response_model**: `ApiResponse[StudentPublic]` — **unchanged from consumer perspective**.

### Internal Change

`register_student()` now returns `RegisterStudentResultDTO` instead of `Tuple[Student, List[dict]]`:

```python
class RegisterStudentResultDTO(BaseModel):
    student: Student               # ORM model
    siblings: List[StudentSiblingDTO]
```

The router extracts `result.student` and wraps it as `StudentPublic.model_validate(result.student)`.  
No impact on API response shape.

---

## 7. `DELETE /crm/students/{id}/soft` — Soft Delete

**route**: `students_router.py:492`  
**response_model**: `ApiResponse[StudentDeletionResult]`  
**Additive change**: was `ApiResponse[dict]` (untyped).

### Response Shape

```json
{
  "success": true,
  "data": {
    "student_id": 42,
    "status": "soft_deleted"
  }
}
```

`status` values: `"soft_deleted"`, `"restored"`, `"permanently_deleted"`.

---

## 8. `POST /crm/students/{id}/restore` — Restore Student

**route**: `students_router.py:520`  
**response_model**: same as #7 — `ApiResponse[StudentDeletionResult]`.

---

## 9. `DELETE /crm/students/{id}/hard` — Permanent Delete

**route**: `students_router.py:545`  
**response_model**: same as #7 — `ApiResponse[StudentDeletionResult]`.

---

## 10. `GET /crm/admin/deleted-students` — List Deleted Students (Admin)

**route**: `students_router.py:570`  
**response_model**: `ApiResponse[List[StudentListingDTO]]`  
**🔴 Breaking change**: was `ApiResponse[List[StudentListItem]]`.

New response includes: `date_of_birth`, `age`, `gender`, `has_unpaid_balance` (all previously absent).

---

## 11. `POST /crm/parents/` — Create Parent

**route**: `parents_router.py:72`  
**input schema**: `RegisterParentInput` (was `ParentCreate`)  
**response_model**: `ApiResponse[ParentPublic]` — unchanged.

### Input Schema Change

`RegisterParentInput` (re‑exported from `app/modules/crm/schemas/parent_schemas`) enforces phone validation via `validate_phone()` — the `+` prefix is stripped and minimum length is enforced. The old `ParentCreate` had no validation.

**Additive change**: no breaking impact on valid inputs. Phone numbers with `+` prefix now have it stripped on create.

---

## 12. `PATCH /crm/parents/{id}` — Update Parent

**route**: `parents_router.py:90`  
**input schema**: `UpdateParentDTO` (was `ParentUpdate`)  
**response_model**: `ApiResponse[ParentPublic]` — unchanged.

### Input Schema Change

`UpdateParentDTO` has the same fields as `ParentUpdate` (all optional). No functional change from consumer perspective.

---

## 13. `GET /crm/students/{id}/details` — Student Details

**route**: `students_router.py:434`  
**response_model**: `ApiResponse[StudentWithDetails]` — **API shape unchanged**.

### Internal Change

`StudentWithDetails`, `ParentInfo`, `SiblingInfo`, `EnrollmentInfo`, `StudentBalanceSummary`, `SessionAttendanceItem`, `StudentEnrollmentAttendanceItem` were moved from `app/api/schemas/crm/student_details.py` → `app/modules/crm/schemas/student_details.py` and re‑exported from the API layer. No change to field names or types.

---

## 14. `GET /crm/students/{id}/siblings` — Student Siblings

**route**: `students_router.py:460`  
**response_model**: `ApiResponse[list[SiblingInfo]]` — unchanged.

---

## 15. Endpoints Removed

| Method | Path | Reason |
|---|---|---|
| `GET` | `/crm/students/{id}/status-history` | Was a stub returning `[]` — `get_student_status_history` method never existed |

The actual status history endpoint lives at `/crm/students/{id}/status-history` in `students_history_router.py:161` (returns `PaginatedResponse[StatusHistoryEntry]`).

---

## 16. `GET /crm/students/{id}/activity-summary` — Activity Summary

**route**: `students_history_router.py:96`  
**response_model**: `ApiResponse[List[ActivitySummaryItem]]` — **API shape unchanged**.

### Internal Change

`get_activity_summary()` now returns `ActivitySummaryDTO` (typed) instead of `Dict[str, Any]`:

```python
class ActivitySummaryDTO(BaseModel):
    student_id: int
    total_activities: int
    activities_by_type: Dict[str, int]
    first_activity_date: Optional[datetime]
    last_activity_date: Optional[datetime]
```

The API response still uses `ActivitySummaryItem` (a different schema wrapping this data into a list). The `ActivitySummaryDTO` is used only at the repository/service boundary.

---

## 17. `GET /history/recent` — Recent Activity Feed

**route**: `students_history_router.py:336`  
**response_model**: unchanged — `ApiResponse[List[RecentActivityItemDTO]]`.

### Internal Change

Fixed method call: `get_recent_activity(limit)` → `get_recent_activities(days=7, limit=limit)`.

---

## 18. Method Renames

| Old | New | File |
|---|---|---|
| `get_recent_activity(limit)` | `get_recent_activities(days, limit)` | `activity_service.py` |
| `get_student_attendance_stats()` | `get_attention_stats()` | awaiting verification |

---

## Removed Symbols

| Symbol | File | Replacement |
|---|---|---|
| `StudentListItem` | `api/schemas/crm/student.py` | `StudentListingDTO` |
| `ParentCreate` | `api/schemas/crm/parent.py` | `RegisterParentInput` (re‑exported) |
| `ParentUpdate` | `api/schemas/crm/parent.py` | `UpdateParentDTO` (re‑exported) |
| `StatusHistoryEntryDTO` | `modules/crm/interfaces/dtos/` | — (dead, zero callers) |
| `StudentStatusSummaryDTO` | `modules/crm/interfaces/dtos/` | — (dead, zero callers) |
| `StudentActivitySummary` | `modules/crm/models/activity_models.py` | `ActivitySummaryDTO` |
| `EnrollmentTimelineEntry` | `modules/crm/models/activity_models.py` | — (dead, zero callers) |
| `StudentEnrollmentTimeline` | `modules/crm/models/activity_models.py` | — (dead, zero callers) |
| `IStudentService` | `modules/crm/interfaces/__init__.py` | — (dead protocol) |
| `ISearchService` | `modules/crm/interfaces/__init__.py` | — (dead protocol) |
| `IGroupingService` | `modules/crm/interfaces/__init__.py` | — (dead protocol) |
| `IReportingService` | `modules/crm/interfaces/__init__.py` | — (dead protocol) |
| `IParentRepository.update(parent_id, data: dict)` | `modules/crm/repositories/parent_repository.py` | — (dead, zero callers) |

---

## Issues Requiring Attention Before Deployment

### Issue 1: `WaitingListStudentDTO` vs `WaitingStudentDTO` type drift ⚠️
- **File**: `app/modules/crm/schemas/waiting_list.py:13` vs `app/api/schemas/crm/student.py:66`
- `WaitingListStudentDTO.date_of_birth` is `Optional[datetime]` (module) but `WaitingStudentDTO` (API) inherits `Optional[date]` from `StudentListingDTO`
- Also: service DTO lacks `current_group_name` field that the API DTO inherits
- **Impact**: Works at runtime due to Pydantic validation + defaults, but diverged DTOs can cause silent breakage if the module DTO is refactored independently
- **Fix**: Align `WaitingListStudentDTO` with `StudentListingDTO` shape, or make `WaitingStudentDTO` a standalone model instead of inheriting

### Issue 2: `datetime.utcnow()` deprecation ⚠️
- **Files**: `activity_repository.py:52`, `student_repository.py:111`, `activity_service.py:141`, `db_helpers.py:277-278`
- 4 source files + 2 test files use deprecated `datetime.utcnow()` → should migrate to `datetime.now(datetime.UTC)`
- **Impact**: Non-critical but will fail on Python 3.14+

### Issue 3: `@validator` vs `@field_validator` mix ⚠️
- **Files**: `student_filter_dto.py:13`, `history.py:127`
- Pydantic V1 `@validator` in a V2 codebase — deprecated, will be removed in Pydantic V3
- **Impact**: Non-critical but generates warnings on every request

### Issue 4: Activity summary uses two different DTOs ⚠️
- Repository returns `ActivitySummaryDTO`, API responds with `ActivitySummaryItem` (different schema)
- The router endpoint uses `ApiResponse[List[ActivitySummaryItem]]` but the service returns a single `ActivitySummaryDTO`
- The `ActivitySummaryItem` list is assembled in the router from the `ActivitySummaryDTO` — fine but adds complexity
- **Impact**: Maintenance burden — two DTOs for the same concept

### Issue 5: `RegisterStudentResultDTO.student` exposes ORM model
- The DTO carries a raw `Student` ORM instance as a field
- The router immediately wraps it in `StudentPublic.model_validate()`, so no data leaks
- **Impact**: Violates the typed-contract principle slightly — a `StudentPublic` or dedicated DTO would be cleaner
