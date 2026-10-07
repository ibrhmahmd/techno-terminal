# Research: Unified Student Listing DTO

**Feature**: 031-unified-student-listing-dto  
**Date**: 2026-06-10

---

## Finding 1: `has_unpaid_balance` — Two-Tier Query Strategy

**Decision**: Use two different DB views depending on endpoint context.

| Endpoint | View Used | Rationale |
|---|---|---|
| `/students`, `?q=`, `/grouped`, `/filter` response | `v_unpaid_enrollments` | Filters `e.status = 'active'` AND `remaining_balance > 0`. EXISTS subquery short-circuits on first match. |
| `/students/waiting-list` | `v_enrollment_balance` | No enrollment-status filter — waiting students have no active enrollments by definition. Checks `amount_remaining > 0` across all enrollment history. |

**SQL pattern (directory/search/grouped)**:
```sql
EXISTS (
  SELECT 1 FROM v_unpaid_enrollments vue
  WHERE vue.student_id = s.id
) AS has_unpaid_balance
```

**SQL pattern (waiting-list)**:
```sql
EXISTS (
  SELECT 1 FROM v_enrollment_balance veb
  WHERE veb.student_id = s.id
  AND veb.amount_remaining > 0
) AS has_unpaid_balance
```

**Alternatives considered**:
- Full JOIN on payments + aggregation per row — rejected; too expensive for a boolean flag on large lists.
- Subquery on raw `payments` + `enrollments` tables — rejected; the views already encode the correct aggregation logic and are already tested via the existing finance module.

---

## Finding 2: `age` Computation — Use `StudentValidator.compute_age`

**Decision**: Reuse the existing `StudentValidator.compute_age(date_of_birth)` helper across all five listing methods.

**Rationale**: Already used in `filter_students()`. The `v_students` DB view also computes age server-side via `EXTRACT(year FROM age(date_of_birth))` but mixing DB-computed and Python-computed age in the same codebase would be inconsistent. Python-side is preferred.

**Edge case**: `date_of_birth is None` → `compute_age(None)` → `age = None`. This must be verified; no code change needed if the helper already handles this.

---

## Finding 3: `current_group_name` on Paginated List — Reuse `list_all_enriched` Pattern

**Decision**: Extend the raw SQL in `list_all()` to include the same LEFT JOIN pattern already used in `list_all_enriched()`:

```sql
SELECT DISTINCT ON (s.id)
  s.id, s.full_name, s.phone, s.status, s.date_of_birth, s.gender,
  g.id as current_group_id,
  g.name as current_group_name,
  EXISTS (...) as has_unpaid_balance,
  -- age computed in Python post-query
FROM students s
LEFT JOIN enrollments e ON e.student_id = s.id AND e.status = 'active'
LEFT JOIN groups g ON g.id = e.group_id
WHERE s.deleted_at IS NULL
ORDER BY s.id, e.id DESC
OFFSET :skip LIMIT :limit
```

**Rationale**: `list_all_enriched()` already does this JOIN correctly with `DISTINCT ON` to resolve multi-enrollment students. The paginated `list_all()` currently does `SELECT * FROM students` with no JOIN — it needs to be promoted to match.

**Note**: `list_all_enriched()` has no pagination (loads all students). `list_all()` has DB-level pagination (`OFFSET/LIMIT`). The new paginated list query will carry the JOIN at DB level, which is correct.

---

## Finding 4: Filter Parameter Rename — `has_unpaid_balance` → `has_any_outstanding_balance`

**Decision**: Three-layer rename:
1. **Router query parameter** (`students_router.py`): `has_unpaid_balance` → `has_any_outstanding_balance`
2. **Input DTO** (`StudentFilterDTO`): field `has_unpaid_balance` → `has_any_outstanding_balance`
3. **SQL WHERE clause** (`search_service.py`): condition key updated to match new field name

**Scope of the filter**: The `student_enrollments` CTE in `filter_students()` already includes ALL enrollments (no `e.status = 'active'` filter), so the renamed parameter preserves the existing all-enrollment semantics. No SQL logic change needed — only the field/parameter name changes.

**Breaking change**: Frontend must update `?has_unpaid_balance=true` → `?has_any_outstanding_balance=true` on the filter page.

---

## Finding 5: `StudentSummaryDTO` Extension (grouped endpoint)

**Decision**: Add `has_unpaid_balance: bool` to `StudentSummaryDTO`. The `get_all_enriched()` repository method (called by `get_grouped()`) must be updated to return this field. Since this method loads all students via raw SQL, the EXISTS subquery against `v_unpaid_enrollments` is added to that query.

`age` is NOT added to `StudentSummaryDTO` — it is computed in Python by the service/router layer when building the final `StudentListingDTO`, same as for other endpoints.

---

## Finding 6: Constitution Compliance

| Principle | Status | Notes |
|---|---|---|
| Router → Service → Repository | ✅ | All changes follow layering — router passes to service, service queries via raw SQL |
| Two-Layer Schema Rule | ✅ | `StudentListingDTO` lives in `app/api/schemas/crm/` (API boundary). `StudentSummaryDTO`, `StudentFilterItemDTO` live in `app/modules/crm/interfaces/dtos/` (service layer). No cross-contamination. |
| Typed Contracts | ✅ | New `StudentListingDTO` replaces fragmented schemas. All service methods continue to return typed DTOs. |
| No `-> dict` or `-> tuple` | ✅ | No new loose return types introduced. |
| Dead Code Discipline | ⚠️ | After migration: `StudentListItem` in `app/api/schemas/crm/student.py` may become dead code if no other endpoint uses it. Must audit callers and delete if unused. |
| Response Envelope | ✅ | All five endpoints already use `ApiResponse` / `PaginatedResponse` wrappers. No change needed. |
