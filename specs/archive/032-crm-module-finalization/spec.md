# Spec: CRM Module Finalization — Dead Code & Deprecation Cleanup

**Spec ID**: `032-crm-module-finalization`
**Date**: 2026-06-11
**Status**: Draft

---

## Problem

The CRM module has accumulated dead code, duplicate DTOs, and `dict` return types over several iterations. Six open `TODO` markers explicitly call for typed DTO replacements. These violations degrade maintainability:

- Dead model classes that compile but are never instantiated
- Duplicate schemas with identical field sets (different validation behavior)
- `-> dict`, `-> List[dict]`, and `-> Dict[str, Any]` return types that bypass AGENTS.md typed-contract rules
- A stale `StudentListItem` DTO superseded by `StudentListingDTO` in all but one endpoint

---

## Scope

**In scope**: Code within `app/modules/crm/` and `app/api/routers/crm/` + `app/api/schemas/crm/`.

**Out of scope**: Other modules, cross-module interface changes, API contract changes visible to frontend (this is strictly internal cleanup).

---

## Audit Findings

### A. Dead Code (zero callers outside defining file)

| # | Symbol | File | Action |
|---|--------|------|--------|
| A1 | `EnrollmentTimelineEntry` | `models/activity_models.py:84` | Delete (model class, not a DB table) |
| A2 | `StudentEnrollmentTimeline` | `models/activity_models.py:95` | Delete (model class, not a DB table) |

### B. Stale / Superseded DTOs

| # | Symbol | File | Reason | Action |
|---|--------|------|--------|--------|
| B1 | `StudentListItem` | `api/schemas/crm/student.py:41` | Superseded by `StudentListingDTO`. Only remaining caller: `GET /admin/deleted-students` | Migrate deleted-students endpoint to `StudentListingDTO`, then delete `StudentListItem` + remove from `__all__` |
| B2 | `ParentCreate` | `schemas/parent.py:6` | Duplicate of `RegisterParentInput` (same fields, missing phone validation) | Consolidate: make `RegisterParentInput` the canonical create DTO, update callers, delete `ParentCreate` |
| B3 | `ParentUpdate` | `schemas/parent.py:16` | Duplicate of `UpdateParentDTO` (same fields) | Consolidate: make `UpdateParentDTO` the canonical update DTO, update callers, delete `ParentUpdate` |

### C. `-> dict` / `-> List[dict]` Violations

| # | Location | Return Type | Action |
|---|----------|-------------|--------|
| C1 | `services/student_crud_service.py:31` — `register_student()` | `Tuple[Student, List[dict]]` | Create `RegisterStudentResultDTO` with typed fields: `student: Student`, `siblings: List[SiblingInfo]` |
| C2 | `repositories/parent_repository.py:53` — `update()` param | `data: dict` | Create `ParentUpdateDataDTO` or use `UpdateParentDTO` |
| C3 | `repositories/activity_repository.py:501` — `get_activity_summary()` | `Dict[str, Any]` | Return `ActivitySummaryDTO` directly |
| C4 | `interfaces/__init__.py:60` — `IParentRepository.update` | `data: dict` | Same as C2 |
| C5 | `interfaces/iactivity_repository.py:77` — `get_activity_summary` | `Dict[str, Any]` | Same as C3 |
| C6 | `models/activity_models.py:79` — `StudentActivitySummary.activities_by_type` | `dict[str, int]` | Replace with `Dict[str, int]` typed field (minor; keep or defer) |

### D. Naming & Export Inconsistencies

| # | Issue | Action |
|---|-------|--------|
| D1 | `parent.py` vs `parent_schemas.py` — two files with near-identical DTOs | Consolidate into `parent_schemas.py` (has validation), delete `parent.py` |
| D2 | `services/__init__.py` has comment `# New SOLID services only - no legacy exports` but exports `StudentActivityService` alongside 4 others | Verify the comment is still accurate; remove if stale |

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| §I Router → Service → Repository | ✅ | All cleanup stays within module boundary |
| §I Two-Layer Schema Rule | ✅ | No new `from app.api` inversions |
| §II Module Organization | ✅ | Pattern A (horizontal layers) preserved |
| §III Typed Contracts | ⬆️ **Improved** | C1–C5 eliminate all remaining `-> dict` returns in CRM |
| §IV Response Envelope | ✅ | No envelope changes |
| §V Auth Guards | ✅ | No auth changes |
| Dead Code Discipline | ⬆️ **Improved** | A1–A2, B1–B3 remove unused/duplicate code |

---

## Implementation Order

```
Phase 1 — Dead Code Deletion (A1–A2)
  └─ Delete EnrollmentTimelineEntry, StudentEnrollmentTimeline from models/activity_models.py

Phase 2 — StudentListItem Migration (B1)
  └─ Update GET /admin/deleted-students to use StudentListingDTO
  └─ Delete StudentListItem from api/schemas/crm/student.py + __init__.py

Phase 3 — Dict-to-DTO Cleanup (C1–C5)
  └─ C1: Create RegisterStudentResultDTO, update register_student() return + callers
  └─ C2/C4: Replace data: dict with UpdateParentDTO in ParentRepository.update + interface
  └─ C3/C5: Return ActivitySummaryDTO from get_activity_summary + interface

Phase 4 — Parent Schema Consolidation (B2–B3, D1)
  └─ Migrate parent_crud_service.py from ParentCreate/Update → RegisterParentInput/UpdateParentDTO
  └─ Update re-exports in schemas/__init__.py and api/schemas/crm/parent.py
  └─ Delete schemas/parent.py

Phase 5 — Verify
  └─ Run full CRM test suite (tests/test_crm*.py)
  └─ Verify 78 tests pass with 0 regressions
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Phone validation behavior change after ParentCreate → RegisterParentInput migration | Low | Medium | `RegisterParentInput` has phone validation; `ParentCreate` doesn't. The router already uses `RegisterParentInput`, so the validator is already active for API calls. Service-level callers currently bypass validation — verify they get the same behavior. |
| Inline `from app.modules.crm.schemas` imports in parent_crud_service.py | Low | Low | Single file to update |
| Something else imports `StudentListItem` from a location grep didn't find | Low | Low | Run `pytest` + `python -c "from app.api.schemas.crm import StudentListItem"` after deletion to confirm |
| `StudentEnrollmentTimeline` / `EnrollmentTimelineEntry` are referenced from outside `app/` (docs, scripts) | Low | Medium | Only referenced in planning docs — no runtime impact |
