# Data Model: Group Level Management

**Feature**: 037-group-level-management  
**Date**: 2026-07-10

---

## New Schemas

### 1. `DeleteLevelResult` (API/Service Boundary)

**File**: `app/modules/academics/group/lifecycle/schemas.py`  
**Layer**: Service result DTO.

```python
class DeleteLevelResult(BaseModel):
    """Result of undoing/deleting a level."""
    level_number_deleted: int
    reverted_to_level: int
    sessions_deleted: int
    enrollments_deleted: int
    enrollments_reactivated: int
    group_level_number_after: int
```

---

### 2. `UpdateLevelInput` (API/Service Boundary)

**File**: `app/modules/academics/group/level/schemas.py`  
**Layer**: Service input DTO.

```python
class UpdateLevelInput(BaseModel):
    """Partial update input for a group level."""
    instructor_id: Optional[int] = None
    course_id: Optional[int] = None
    price_override: Optional[Decimal] = None
    notes: Optional[str] = None
```

---

## Schema Updates

### 1. `GroupLevelPublic` (API Boundary)

We will verify `price_override` type compatibility (`Decimal` vs `float`).

---

## Data Model Removals

### 1. `GroupLevelCourseAssignment` (Dead Model)

**File**: `app/modules/academics/models/group_level_models.py`  
**Status**: Removed.

---

## Database Transaction Cascades

All cascading changes for undo/delete level are executed within a single transaction in `GroupLifecycleService.delete_level()`:

```sql
-- 1. Remove enrollment level history
DELETE FROM enrollment_level_history WHERE group_level_id = :level_id;

-- 2. Hard delete new enrollments at this level
DELETE FROM enrollments WHERE group_id = :group_id AND level_number = :level_number;

-- 3. Restore status of previous enrollments
UPDATE enrollments SET status = 'active', updated_at = now() 
WHERE group_id = :group_id AND level_number = :prev_level_number AND status = 'completed';

-- 4. Hard delete all sessions
DELETE FROM sessions WHERE group_level_id = :level_id;

-- 5. Delete activity logs and history
DELETE FROM student_activity_log 
WHERE activity_subtype = 'level_started' 
  AND reference_type = 'enrollment' 
  AND reference_id IN (:deleted_enrollment_ids);

-- 6. Hard delete group_levels record
DELETE FROM group_levels WHERE id = :level_id;

-- 7. Sync group current level pointer
UPDATE groups SET level_number = :prev_level_number WHERE id = :group_id;
```
